import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/localization/locale_controller.dart';
import '../../../core/networking/api_failure.dart';
import '../../farm/presentation/selected_farm.dart';
import '../data/assistant_repository.dart';
import '../data/sse_parser.dart';
import '../data/voice_services.dart';

@immutable
class ChatSource {
  const ChatSource({required this.source, this.title, this.confidence, this.url});
  final String source;
  final String? title;
  final double? confidence;
  final String? url;

  static List<ChatSource> listFrom(Map<String, Object?> data) {
    final raw = data['sources'];
    if (raw is! List) return const [];
    return [
      for (final s in raw)
        if (s is Map)
          ChatSource(
            source: s['source'] is String ? s['source'] as String : '',
            title: s['title'] is String ? s['title'] as String : null,
            confidence: s['confidence'] is num ? (s['confidence'] as num).toDouble() : null,
            url: s['url'] is String ? s['url'] as String : null,
          ),
    ];
  }
}

enum ChatRole { user, assistant }

/// Conversational voice state machine: IDLE -> LISTENING -> THINKING -> SPEAKING -> IDLE.
/// ERROR is entered on a recoverable voice failure (see [VoiceNotice]) and cleared by the next
/// user action.
enum AssistantVoiceState { idle, listening, thinking, speaking, error }

/// Why the voice loop could not complete. Drives the explanatory banner (never raw errors).
enum VoiceNotice {
  none,
  micPermission,

  /// No on-device recognizer; audio is NOT captured and nothing is uploaded. Typing still works.
  offlineUnavailable,

  /// On-device recognition exists but the offline pack for this language is not installed.
  offlineLanguageMissing,
  sttError,

  /// No installed (non-network) voice for the answer's language.
  ttsVoiceMissingTamil,
  ttsVoiceMissingEnglish,
  ttsFailed,
}

class VoiceNoticeController extends Notifier<VoiceNotice> {
  @override
  VoiceNotice build() => VoiceNotice.none;

  void set(VoiceNotice n) => state = n;
}

final voiceNoticeProvider = NotifierProvider<VoiceNoticeController, VoiceNotice>(VoiceNoticeController.new);

@immutable
class ChatMessage {
  const ChatMessage({
    required this.role,
    required this.text,
    this.spokenText,
    this.pending = false,
    this.stage,
    this.sources,
    this.failure,
    this.isFallback,
    this.grounded,
    this.question,
  });

  final ChatRole role;
  final String text;
  final String? spokenText;

  /// Assistant message still streaming.
  final bool pending;

  /// Last progress event type (drives the stage indicator).
  final String? stage;

  /// Non-null ONLY when a `sources` event arrived.
  final List<ChatSource>? sources;

  /// Set on failure. `network` → server unreachable; the UI never shows raw
  /// server text for an error.
  final ApiFailure? failure;
  final bool? isFallback;
  final bool? grounded;

  /// The question this assistant message answers (for Retry).
  final String? question;

  bool get isError => failure != null;
  bool get isFinalAnswer => role == ChatRole.assistant && !pending && !isError && text.isNotEmpty;

  ChatMessage copyWith({
    String? text,
    String? spokenText,
    bool? pending,
    String? stage,
    List<ChatSource>? sources,
    ApiFailure? failure,
    bool? isFallback,
    bool? grounded,
  }) =>
      ChatMessage(
        role: role,
        text: text ?? this.text,
        spokenText: spokenText ?? this.spokenText,
        pending: pending ?? this.pending,
        stage: stage ?? this.stage,
        sources: sources ?? this.sources,
        failure: failure ?? this.failure,
        isFallback: isFallback ?? this.isFallback,
        grounded: grounded ?? this.grounded,
        question: question,
      );
}

@immutable
class ChatState {
  const ChatState({this.messages = const [], this.sessionId});
  final List<ChatMessage> messages;
  final String? sessionId;

  bool get busy => messages.isNotEmpty && messages.last.pending;
}

/// Progress events that move the stage indicator.
const progressEvents = {
  'session_started',
  'intent_detected',
  'planning',
  'tool_complete',
  'evidence_ready',
  'grounding',
  'reasoning',
  'response_complete',
};

class VoiceConversationEnabledController extends Notifier<bool> {
  @override
  bool build() => false;

  void toggle() => state = !state;
  void setEnabled(bool val) => state = val;
}

final voiceConversationEnabledProvider =
    NotifierProvider<VoiceConversationEnabledController, bool>(VoiceConversationEnabledController.new);

class AssistantVoiceStateController extends Notifier<AssistantVoiceState> {
  @override
  AssistantVoiceState build() => AssistantVoiceState.idle;

  void setState(AssistantVoiceState s) => state = s;
}

final assistantVoiceStateProvider =
    NotifierProvider<AssistantVoiceStateController, AssistantVoiceState>(AssistantVoiceStateController.new);

class ChatController extends Notifier<ChatState> {
  StreamSubscription<ConversationEvent>? _sub;

  @override
  ChatState build() {
    ref.onDispose(() => _sub?.cancel());
    return const ChatState();
  }

  void _updateLast(ChatMessage Function(ChatMessage m) f) {
    final msgs = [...state.messages];
    msgs[msgs.length - 1] = f(msgs.last);
    state = ChatState(messages: msgs, sessionId: state.sessionId);
  }

  // Monotonic id of the current spoken answer. Any stop()/new speak() bumps it, so a late
  // completion of an older utterance can never change state or trigger more audio.
  int _speakToken = 0;

  // A voice turn is "open" from the moment the mic starts until its transcript is submitted once.
  bool _voiceTurnOpen = false;

  void _setVoice(AssistantVoiceState v) => ref.read(assistantVoiceStateProvider.notifier).setState(v);

  void _notice(VoiceNotice n) => ref.read(voiceNoticeProvider.notifier).set(n);

  /// Called when the microphone starts. Clears any previous voice error.
  void beginVoiceTurn() {
    _voiceTurnOpen = true;
    _notice(VoiceNotice.none);
    _setVoice(AssistantVoiceState.listening);
  }

  /// The mic was stopped or failed without a transcript.
  void endVoiceTurn({VoiceNotice notice = VoiceNotice.none}) {
    _voiceTurnOpen = false;
    if (notice == VoiceNotice.none) {
      if (!state.busy) _setVoice(AssistantVoiceState.idle);
    } else {
      _notice(notice);
      _setVoice(AssistantVoiceState.error);
    }
  }

  /// Submits a final transcript. Exactly once per voice turn; empty or duplicate calls are ignored.
  Future<bool> sendVoice(String text) async {
    final q = text.trim();
    if (!_voiceTurnOpen || q.isEmpty || state.busy) return false;
    _voiceTurnOpen = false;
    await send(q, isVoiceInput: true);
    return true;
  }

  Future<void> stopSpeaking() async {
    _speakToken++; // invalidates any in-flight utterance
    await ref.read(speakerProvider).stop();
    if (ref.read(assistantVoiceStateProvider) == AssistantVoiceState.speaking) {
      _setVoice(AssistantVoiceState.idle);
    }
  }

  /// Manual speaker button: speaks [text] through the same single-utterance path as auto-speak.
  Future<void> speakAnswer(String text) => _autoSpeak(text);

  Future<void> _autoSpeak(String text) async {
    // Never talk over the farmer: if the mic is open, the answer stays on screen only.
    if (ref.read(assistantVoiceStateProvider) == AssistantVoiceState.listening) return;
    final speaker = ref.read(speakerProvider);
    final isTamil = RegExp(r'[\u0B80-\u0BFF]').hasMatch(text);
    final tag = isTamil ? 'ta-IN' : 'en-IN';
    final spokenText = planSpokenResponse(text, isTamil: isTamil);

    final token = ++_speakToken;
    _setVoice(AssistantVoiceState.speaking);
    SpeakOutcome outcome;
    try {
      outcome = await speaker.speak(spokenText, languageTag: tag);
    } catch (_) {
      outcome = SpeakOutcome.failed;
    }
    if (token != _speakToken) return; // superseded or interrupted: leave state to whoever did that
    switch (outcome) {
      case SpeakOutcome.spoken:
        _setVoice(AssistantVoiceState.idle);
      case SpeakOutcome.voiceMissing:
        _notice(isTamil ? VoiceNotice.ttsVoiceMissingTamil : VoiceNotice.ttsVoiceMissingEnglish);
        _setVoice(AssistantVoiceState.error);
      case SpeakOutcome.failed:
        _notice(VoiceNotice.ttsFailed);
        _setVoice(AssistantVoiceState.error);
    }
  }

  Future<void> send(
    String question, {
    bool isVoiceInput = false,
    Map<String, dynamic>? diseaseContext,
  }) async {
    final q = question.trim();
    if (q.isEmpty || state.busy) return;

    // Interruption handling: stop current speech immediately
    await stopSpeaking();
    if (!isVoiceInput) _notice(VoiceNotice.none);

    final voiceEnabled = ref.read(voiceConversationEnabledProvider);
    if (isVoiceInput || voiceEnabled) {
      ref.read(assistantVoiceStateProvider.notifier).setState(AssistantVoiceState.thinking);
    }

    state = ChatState(
      sessionId: state.sessionId,
      messages: [
        ...state.messages,
        ChatMessage(role: ChatRole.user, text: q),
        ChatMessage(role: ChatRole.assistant, text: '', pending: true, question: q),
      ],
    );
    await _run(q, isVoiceInput: isVoiceInput, diseaseContext: diseaseContext);
  }

  /// Re-asks the question of a failed assistant message (the last one).
  Future<void> retry() async {
    if (state.messages.isEmpty || state.busy) return;
    final last = state.messages.last;
    if (!last.isError || last.question == null) return;
    await stopSpeaking();
    final msgs = [...state.messages]..removeLast();
    state = ChatState(
      sessionId: state.sessionId,
      messages: [...msgs, ChatMessage(role: ChatRole.assistant, text: '', pending: true, question: last.question)],
    );
    await _run(last.question!);
  }

  Future<void> _run(
    String q, {
    bool isVoiceInput = false,
    Map<String, dynamic>? diseaseContext,
  }) async {
    // Language adaptation: detect script from query if present, otherwise follow locale
    final hasTamil = RegExp(r'[\u0B80-\u0BFF]').hasMatch(q);
    final hasEnglish = RegExp(r'[a-zA-Z]').hasMatch(q);
    final String language;
    if (hasTamil) {
      language = 'Tamil';
    } else if (hasEnglish && !hasTamil) {
      language = 'English';
    } else {
      language = ref.read(localeProvider).languageCode == AppLocales.english.languageCode ? 'English' : 'Tamil';
    }

    final farmId = ref.read(selectedFarmProvider).value?.farmId;
    final done = Completer<void>();
    var completed = false;
    var streamed = '';
    List<ChatSource>? sources;

    void fail(ApiFailure f) {
      if (done.isCompleted) return;
      ref.read(assistantVoiceStateProvider.notifier).setState(AssistantVoiceState.idle);
      _updateLast((m) => ChatMessage(
            role: ChatRole.assistant,
            text: '',
            failure: f,
            question: m.question,
          ));
      done.complete();
    }

    try {
      final events = await ref.read(assistantRepositoryProvider).ask(
            question: q,
            language: language,
            sessionId: state.sessionId,
            farmId: farmId,
            diseaseContext: diseaseContext,
          );
      await _sub?.cancel();
      _sub = events.listen(
        (e) {
          if (done.isCompleted) return;
          if (e.sessionId != null && e.sessionId != state.sessionId) {
            state = ChatState(messages: state.messages, sessionId: e.sessionId);
          }
          switch (e.type) {
            case 'sources':
              sources = ChatSource.listFrom(e.data);
            case 'token':
              final t = e.data['token'] ?? e.data['text'];
              if (t is String) {
                streamed += t;
                _updateLast((m) => m.copyWith(text: streamed, stage: 'token'));
              }
            case 'completed':
              completed = true;
              final answer = e.data['answer'];
              final rawSpoken = e.data['spoken_text'];
              final text = answer is String && answer.trim().isNotEmpty ? answer : streamed;
              final spoken = rawSpoken is String && rawSpoken.trim().isNotEmpty ? rawSpoken.trim() : null;
              if (text.trim().isEmpty) {
                fail(const ApiFailure(kind: ApiFailureKind.error, code: 'empty_answer'));
                return;
              }
              _updateLast((m) => ChatMessage(
                    role: ChatRole.assistant,
                    text: text,
                    spokenText: spoken,
                    sources: sources,
                    isFallback: e.data['is_fallback'] is bool ? e.data['is_fallback'] as bool : null,
                    grounded: e.data['grounded'] is bool ? e.data['grounded'] as bool : null,
                    question: m.question,
                  ));
              done.complete();

              // Auto voice response when voice mode is enabled or query was voice input
              final voiceEnabled = ref.read(voiceConversationEnabledProvider);
              if (isVoiceInput || voiceEnabled) {
                _autoSpeak(spoken ?? text);
              } else {
                ref.read(assistantVoiceStateProvider.notifier).setState(AssistantVoiceState.idle);
              }
            case 'error':
              final code = e.data['code'];
              fail(ApiFailure(kind: ApiFailureKind.error, code: code is String ? code : 'assistant_error'));
            default:
              if (progressEvents.contains(e.type)) {
                _updateLast((m) => m.copyWith(stage: e.type));
              }
          }
        },
        onError: (Object err) =>
            fail(err is ApiFailure ? err : const ApiFailure(kind: ApiFailureKind.unavailable, code: ApiFailure.networkCode)),
        onDone: () {
          if (!completed) fail(const ApiFailure(kind: ApiFailureKind.error, code: 'stream_ended'));
        },
        cancelOnError: true,
      );
    } on ApiFailure catch (f) {
      fail(f);
    } catch (_) {
      fail(const ApiFailure(kind: ApiFailureKind.unavailable, code: ApiFailure.networkCode));
    }
    return done.future;
  }

  void clear() {
    _sub?.cancel();
    stopSpeaking();
    state = const ChatState();
  }
}

final chatProvider = NotifierProvider<ChatController, ChatState>(ChatController.new);
