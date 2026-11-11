import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/core/networking/api_client.dart';
import 'package:uzhavan/core/networking/api_failure.dart';
import 'package:uzhavan/core/storage/token_store.dart';
import 'package:uzhavan/features/assistant/data/assistant_repository.dart';
import 'package:uzhavan/features/assistant/data/sse_parser.dart';
import 'package:uzhavan/features/assistant/data/voice_services.dart';
import 'package:uzhavan/features/assistant/presentation/assistant_screen.dart';
import 'package:uzhavan/features/assistant/presentation/chat_controller.dart';

import '../helpers/scripted_adapter.dart';
import '../helpers/test_app.dart';

String ev(String type, Map<String, Object?> data) =>
    'event: $type\ndata: ${jsonEncode({'event': type, 'session_id': 's1', 'conversation_id': 'c1', 'timestamp': 't', 'data': data})}\n\n';

Stream<List<int>> chunked(String text, int size) async* {
  final bytes = utf8.encode(text);
  for (var i = 0; i < bytes.length; i += size) {
    yield bytes.sublist(i, i + size > bytes.length ? bytes.length : i + size);
  }
}

ResponseBody sseBody(String text, {int chunk = 7, int status = 200}) => ResponseBody(
      chunked(text, chunk).map(Uint8List.fromList),
      status,
      headers: {
        Headers.contentTypeHeader: ['text/event-stream'],
      },
    );

ApiClient makeApi(ScriptedAdapter adapter) => ApiClient(
      baseUrl: 'http://test.local',
      tokenStore: MemoryTokenStore(const AuthTokens(accessToken: 'a', refreshToken: 'r')),
      adapter: adapter,
    );

final happyWithSources = [
  ev('session_started', {'turn': 1}),
  ev('intent_detected', {'intent': 'advisory'}),
  ': keepalive\n\n',
  ev('grounding', {'passed': true}),
  ev('sources', {
    'sources': [
      {'source': 'TNAU', 'title': 'Rice CPG', 'confidence': 0.9},
    ],
  }),
  ev('completed', {'answer': 'நாற்றங்கால் பதில்', 'is_fallback': false}),
].join();

final happyNoSources = [ev('session_started', {}), ev('completed', {'answer': 'General answer', 'is_fallback': true})].join();

/// Scriptable on-device recognizer: tests drive transcripts with [say] / [finish].
class FakeVoice implements VoiceInput {
  FakeVoice(this.result);
  VoiceInitResult result;
  int startCalls = 0, stopCalls = 0, cancelCalls = 0;
  String? initLocale, startLocale;
  void Function(String, bool)? _onResult;
  void Function()? _onDone;
  void Function(String)? _onError;

  @override
  Future<VoiceInitResult> init({required String localeId}) async {
    initLocale = localeId;
    return result;
  }

  @override
  Future<void> start({
    required String localeId,
    required void Function(String, bool) onResult,
    required void Function() onDone,
    void Function(String)? onError,
  }) async {
    startCalls++;
    startLocale = localeId;
    _onResult = onResult;
    _onDone = onDone;
    _onError = onError;
  }

  @override
  Future<void> stop() async => stopCalls++;
  @override
  Future<void> cancel() async => cancelCalls++;

  void say(String text, {bool isFinal = true}) => _onResult?.call(text, isFinal);
  void finish() => _onDone?.call();
  void fail(String code) => _onError?.call(code);
}

/// Records call order; [hold] keeps an utterance "playing" until completed.
class FakeSpeaker implements Speaker {
  final spoken = <String>[];
  final events = <String>[];
  SpeakOutcome outcome = SpeakOutcome.spoken;
  Completer<void>? hold;

  @override
  Future<SpeakOutcome> speak(String text, {required String languageTag}) async {
    events.add('speak');
    spoken.add('$languageTag:$text');
    final h = hold;
    if (h != null) await h.future;
    return outcome;
  }

  @override
  Future<void> stop() async => events.add('stop');
}

void main() {
  group('SSE parser', () {
    test('handles 1-byte chunks (split lines and split UTF-8), CRLF, comments', () async {
      final text = happyWithSources.replaceAll('\n', '\r\n');
      final events = await parseSse(chunked(text, 1)).toList();
      expect(events.map((e) => e.type),
          ['session_started', 'intent_detected', 'grounding', 'sources', 'completed']);
      expect(events.last.data['answer'], 'நாற்றங்கால் பதில்');
      expect(events.first.sessionId, 's1');
    });

    test('multi-line data and a missing trailing blank line', () async {
      final text = 'data: {"event":"completed",\ndata: "data":{"answer":"x"}}';
      final events = await parseSse(chunked(text, 3)).toList();
      expect(events.single.type, 'completed');
      expect(events.single.data['answer'], 'x');
    });

    test('invalid JSON is skipped; event name falls back to the event: line', () async {
      final text = 'event: planning\ndata: not json\n\nevent: planning\ndata: {"data":{}}\n\n';
      final events = await parseSse(chunked(text, 5)).toList();
      expect(events.single.type, 'planning');
    });

    test('error event parsed with code', () async {
      final events = await parseSse(chunked(ev('error', {'code': 'graph_error', 'message': 'Traceback…'}), 4)).toList();
      expect(events.single.type, 'error');
      expect(events.single.data['code'], 'graph_error');
    });
  });

  group('ChatController', () {
    Future<ProviderContainer> container(ScriptedAdapter adapter, {String lang = 'ta'}) async {
      final c = await makeContainer(
        prefs: {'app.language': lang},
        overrides: [assistantRepositoryProvider.overrideWithValue(AssistantRepository(makeApi(adapter)))],
      );
      addTearDown(c.dispose);
      return c;
    }

    test('sends language from the locale; sources only when the event arrived', () async {
      final adapter = ScriptedAdapter((_) async => sseBody(happyWithSources));
      final c = await container(adapter);
      await c.read(chatProvider.notifier).send('கேள்வி');
      final msg = c.read(chatProvider).messages.last;
      expect(msg.text, 'நாற்றங்கால் பதில்');
      expect(msg.sources!.single.source, 'TNAU');
      expect(msg.isFinalAnswer, isTrue);
      final body = adapter.requests.single.data as Map;
      expect(body['language'], 'Tamil');
      expect(body['question'], 'கேள்வி');
      expect(body.containsKey('farm_id'), isFalse);
      expect(c.read(chatProvider).sessionId, 's1');

      adapter.handler = (_) async => sseBody(happyNoSources);
      await c.read(chatProvider.notifier).send('again');
      final second = c.read(chatProvider).messages.last;
      expect(second.sources, isNull);
      expect(second.isFallback, isTrue);
      expect((adapter.requests.last.data as Map)['session_id'], 's1');
    });

    test('English locale → language English', () async {
      final adapter = ScriptedAdapter((_) async => sseBody(happyNoSources));
      final c = await container(adapter, lang: 'en');
      await c.read(chatProvider.notifier).send('q');
      expect((adapter.requests.single.data as Map)['language'], 'English');
    });

    test('error event → error message (no answer), retry re-asks', () async {
      final adapter = ScriptedAdapter((_) async => sseBody([ev('session_started', {}), ev('error', {'code': 'graph_error', 'message': 'boom'})].join()));
      final c = await container(adapter);
      await c.read(chatProvider.notifier).send('q');
      final msg = c.read(chatProvider).messages.last;
      expect(msg.isError, isTrue);
      expect(msg.text, isEmpty);
      expect(msg.isFinalAnswer, isFalse);

      adapter.handler = (_) async => sseBody(happyNoSources);
      await c.read(chatProvider.notifier).retry();
      expect(c.read(chatProvider).messages.last.text, 'General answer');
      expect(c.read(chatProvider).messages.length, 2);
    });

    test('stream ending without completed → error', () async {
      final adapter = ScriptedAdapter((_) async => sseBody(ev('planning', {})));
      final c = await container(adapter);
      await c.read(chatProvider.notifier).send('q');
      expect(c.read(chatProvider).messages.last.failure?.code, 'stream_ended');
    });

    test('HTTP 429 on the stream request → rateLimited; network → unreachable', () async {
      final adapter = ScriptedAdapter((_) async => ResponseBody.fromString(
            jsonEncode(errorDetail('rate_limited')),
            429,
            headers: {Headers.contentTypeHeader: [Headers.jsonContentType], 'retry-after': ['30']},
          ));
      final c = await container(adapter);
      await c.read(chatProvider.notifier).send('q');
      final f = c.read(chatProvider).messages.last.failure!;
      expect(f.kind, ApiFailureKind.rateLimited);
      expect(f.retryAfter, const Duration(seconds: 30));

      adapter.handler = (o) async => throw DioException.connectionError(requestOptions: o, reason: 'refused');
      await c.read(chatProvider.notifier).retry();
      expect(c.read(chatProvider).messages.last.failure!.code, ApiFailure.networkCode);
    });
  });

  group('Assistant screen', () {
    Future<(ProviderContainer, FakeSpeaker)> pump(WidgetTester tester, ScriptedAdapter adapter,
        {VoiceInitResult voice = VoiceInitResult.ready}) async {
      final speaker = FakeSpeaker();
      final c = await makeContainer(
        prefs: {'app.language': 'en'},
        overrides: [
          assistantRepositoryProvider.overrideWithValue(AssistantRepository(makeApi(adapter))),
          voiceInputProvider.overrideWithValue(FakeVoice(voice)),
          speakerProvider.overrideWithValue(speaker),
        ],
      );
      addTearDown(c.dispose);
      await tester.pumpWidget(UncontrolledProviderScope(container: c, child: const TestApp(home: AssistantScreen())));
      await tester.pumpAndSettle();
      return (c, speaker);
    }

    testWidgets('suggestion → answer with sources and a speak button', (tester) async {
      final adapter = ScriptedAdapter((_) async => sseBody(happyWithSources));
      final (_, speaker) = await pump(tester, adapter);
      await tester.tap(find.text('How do I prepare a paddy nursery?'));
      await tester.pumpAndSettle();
      expect(find.text('நாற்றங்கால் பதில்'), findsOneWidget);
      expect(find.byKey(const Key('chat-sources')), findsOneWidget);
      expect(find.text('• TNAU: Rice CPG'), findsOneWidget);
      await tester.tap(find.byKey(const Key('speak-button')));
      await tester.pumpAndSettle();
      expect(speaker.spoken.single, startsWith('ta-IN:'));
    });

    testWidgets('no sources event → no citations list and en-IN speaker for English', (tester) async {
      final adapter = ScriptedAdapter((_) async => sseBody(happyNoSources));
      final (_, speaker) = await pump(tester, adapter);
      await tester.enterText(find.byKey(const Key('chat-input')), 'q');
      await tester.tap(find.byKey(const Key('send-button')));
      await tester.pumpAndSettle();
      expect(find.text('General answer'), findsOneWidget);
      await tester.tap(find.byKey(const Key('speak-button')));
      await tester.pumpAndSettle();
      expect(speaker.spoken.single, startsWith('en-IN:'));
      expect(find.byKey(const Key('chat-sources')), findsNothing);
      expect(find.byKey(const Key('speak-button')), findsOneWidget);
    });

    testWidgets('server unreachable → localized message, retry, no speak button, no raw error', (tester) async {
      final adapter = ScriptedAdapter((o) async => throw DioException.connectionError(requestOptions: o, reason: 'SocketException raw'));
      await pump(tester, adapter);
      await tester.enterText(find.byKey(const Key('chat-input')), 'q');
      await tester.tap(find.byKey(const Key('send-button')));
      await tester.pumpAndSettle();
      expect(find.text("Can't reach the UZHAVAN server"), findsOneWidget);
      expect(find.textContaining('SocketException'), findsNothing);
      expect(find.byKey(const Key('chat-retry')), findsOneWidget);
      expect(find.byKey(const Key('speak-button')), findsNothing);
    });

    testWidgets('error event text from the server is never shown', (tester) async {
      final adapter = ScriptedAdapter((_) async => sseBody(ev('error', {'code': 'graph_error', 'message': 'Traceback secret'})));
      await pump(tester, adapter);
      await tester.enterText(find.byKey(const Key('chat-input')), 'q');
      await tester.tap(find.byKey(const Key('send-button')));
      await tester.pumpAndSettle();
      expect(find.textContaining('Traceback'), findsNothing);
      expect(find.text('Could not get an answer. Please try again.'), findsOneWidget);
    });

    testWidgets('mic: permission denied and not available are handled', (tester) async {
      final adapter = ScriptedAdapter((_) async => sseBody(happyNoSources));
      await pump(tester, adapter, voice: VoiceInitResult.permissionDenied);
      await tester.tap(find.byKey(const Key('mic-button')));
      await tester.pump();
      expect(find.text('Microphone permission denied. Allow it in the phone settings.'), findsOneWidget);
    });

    test('planSpokenResponse cleans markdown, citations, and expands units', () {
      const raw = '## நெல் இலை மஞ்சள்\n'
          '* 18 மிமீ மழை வரும் வாய்ப்பு உள்ளது.\n'
          '* 50 kg உரம் இடவும் [TNAU].\n'
          'பின்வரும் பரிந்துரைகளை கடைப்பிடிக்கவும்: அச்சம் கொள்ளத் தேவையில்லை.';
      final spoken = planSpokenResponse(raw, isTamil: true);
      expect(spoken.contains('##'), isFalse);
      expect(spoken.contains('*'), isFalse);
      expect(spoken.contains('[TNAU]'), isFalse);
      expect(spoken.contains('18 மில்லிமீட்டர்'), isTrue);
      expect(spoken.contains('50 கிலோ'), isTrue);
      expect(spoken.contains('முதலில், '), isTrue);
      expect(spoken.contains('கவலைப்படாதீங்க'), isTrue);
      expect(spoken.contains('பின்வரும் பரிந்துரைகளை கடைப்பிடிக்கவும்'), isFalse);
    });

    testWidgets('voice conversation mode toggle auto-speaks response without manual speaker tap', (tester) async {
      final adapter = ScriptedAdapter((_) async => sseBody(happyWithSources));
      final (c, speaker) = await pump(tester, adapter);

      // Toggle voice mode ON
      await tester.tap(find.byKey(const Key('voice-mode-toggle')));
      await tester.pumpAndSettle();
      expect(c.read(voiceConversationEnabledProvider), isTrue);

      // Submit question
      await tester.enterText(find.byKey(const Key('chat-input')), 'என் நெல்லில் இலை மஞ்சளா இருக்கு');
      await tester.tap(find.byKey(const Key('send-button')));
      await tester.pumpAndSettle();

      // Verify answer is displayed
      expect(find.text('நாற்றங்கால் பதில்'), findsOneWidget);

      // Verify response was automatically spoken without tapping speaker icon!
      expect(speaker.spoken.isNotEmpty, isTrue);
      expect(speaker.spoken.last, contains('நாற்றங்கால் பதில்'));
    });

    testWidgets('interruption stops speaking when stop button tapped', (tester) async {
      final adapter = ScriptedAdapter((_) async => sseBody(happyWithSources));
      final (c, _) = await pump(tester, adapter);

      c.read(assistantVoiceStateProvider.notifier).setState(AssistantVoiceState.speaking);
      await tester.pump();
      expect(find.byKey(const Key('voice-state-banner')), findsOneWidget);

      // Tap stop button
      await tester.tap(find.byKey(const Key('stop-speaking-button')));
      await tester.pumpAndSettle();
      expect(c.read(assistantVoiceStateProvider), AssistantVoiceState.idle);
      expect(find.byKey(const Key('voice-state-banner')), findsNothing);
    });
  });
}
