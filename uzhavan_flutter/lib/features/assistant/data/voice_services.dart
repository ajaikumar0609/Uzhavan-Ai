import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_tts/flutter_tts.dart';

/// Result of preparing speech recognition. Everything except [ready] means NO audio is captured.
enum VoiceInitResult {
  ready,
  permissionDenied,

  /// Generic failure to start.
  notAvailable,

  /// No on-device recognizer on this phone (Android < 12 or no offline recognition service).
  /// The app never falls back to Android's default (possibly online) recognizer.
  offlineUnavailable,

  /// On-device recognition exists but the offline pack for the language is not installed.
  offlineLanguageMissing,
}

/// On-device speech recognition ONLY (zero-cloud policy). Overridable in tests.
abstract class VoiceInput {
  Future<VoiceInitResult> init({required String localeId});
  Future<void> start({
    required String localeId,
    required void Function(String text, bool isFinal) onResult,
    required void Function() onDone,
    void Function(String code)? onError,
  });

  /// Finish the current utterance (a final result follows).
  Future<void> stop();

  /// Abort immediately; no result is delivered.
  Future<void> cancel();
}

enum SpeakOutcome {
  /// Playback finished (or was interrupted by stop()).
  spoken,

  /// No installed, non-network voice for the language. Nothing was spoken.
  voiceMissing,
  failed,
}

/// On-device text-to-speech (Android TextToSpeech). Never uses the backend or a cloud voice.
abstract class Speaker {
  Future<SpeakOutcome> speak(String text, {required String languageTag});
  Future<void> stop();
}

/// Bridge to `LocalSpeechRecognizer.kt`, which calls ONLY
/// `SpeechRecognizer.createOnDeviceSpeechRecognizer` (never the default recognizer).
class NativeLocalVoiceInput implements VoiceInput {
  NativeLocalVoiceInput({MethodChannel? channel})
      : _ch = channel ?? const MethodChannel('ai.uzhavan/local_stt') {
    _ch.setMethodCallHandler(_onNative);
  }

  final MethodChannel _ch;
  void Function(String text, bool isFinal)? _onResult;
  void Function()? _onDone;
  void Function(String code)? _onError;
  Timer? _silenceTimer;
  Timer? _finalFallback;
  String _last = '';
  bool _finished = true; // true while no utterance is in progress (one-shot guard)

  static const silenceStop = Duration(milliseconds: 2500);
  static const finalWait = Duration(milliseconds: 1500);

  @override
  Future<VoiceInitResult> init({required String localeId}) async {
    try {
      var granted = await _ch.invokeMethod<bool>('hasPermission') ?? false;
      if (!granted) granted = await _ch.invokeMethod<bool>('requestPermission') ?? false;
      if (!granted) return VoiceInitResult.permissionDenied;
      final r = await _ch.invokeMapMethod<String, Object?>('availability', {'locale': localeId});
      final state = r?['state'];
      debugPrint('[VOICE_STATE] on_device_availability=$state locale=$localeId');
      return switch (state) {
        'ready' || 'ready_unverified' => VoiceInitResult.ready,
        'language_missing' || 'language_unsupported' => VoiceInitResult.offlineLanguageMissing,
        'unsupported_api' || 'no_on_device_service' => VoiceInitResult.offlineUnavailable,
        _ => VoiceInitResult.notAvailable,
      };
    } on MissingPluginException {
      return VoiceInitResult.notAvailable;
    } catch (e) {
      debugPrint('[VOICE_STATE] init_exception=${e.runtimeType}');
      return VoiceInitResult.notAvailable;
    }
  }

  @override
  Future<void> start({
    required String localeId,
    required void Function(String text, bool isFinal) onResult,
    required void Function() onDone,
    void Function(String code)? onError,
  }) async {
    _clearTimers();
    _onResult = onResult;
    _onDone = onDone;
    _onError = onError;
    _last = '';
    _finished = false;
    debugPrint('[STT_START] locale=$localeId engine=ON_DEVICE_ONLY');
    final started = await _ch.invokeMethod<bool>('start', {'locale': localeId}) ?? false;
    if (!started && !_finished) {
      // Native refused to start (no on-device recognizer; it never falls back to the default
      // one). Report it here: the matching native event would arrive after this future resolves.
      _finish(null, error: 'offline_unavailable');
    }
  }

  Future<dynamic> _onNative(MethodCall call) async {
    if (call.method != 'event' || _finished) return null;
    final e = Map<String, Object?>.from(call.arguments as Map);
    switch (e['type']) {
      case 'partial':
        final t = (e['text'] as String?) ?? '';
        _last = t;
        if (kDebugMode) debugPrint('[STT_PARTIAL] chars=${t.length}');
        _onResult?.call(t, false);
        _silenceTimer?.cancel();
        _silenceTimer = Timer(silenceStop, () {
          if (!_finished) stop();
        });
      case 'final':
        final t = ((e['text'] as String?) ?? '').trim();
        debugPrint('[STT_FINAL] chars=${t.length}');
        _finish(t.isNotEmpty ? t : _last.trim());
      case 'status':
        if (e['value'] == 'end_of_speech') _armFinalFallback();
      case 'error':
        final code = (e['code'] as String?) ?? 'error';
        debugPrint('[VOICE_STATE] stt_error=$code');
        if (code == 'no_speech') {
          _finish(_last.trim().isNotEmpty ? _last.trim() : null);
        } else {
          _finish(null, error: code);
        }
    }
    return null;
  }

  void _armFinalFallback() {
    _finalFallback?.cancel();
    _finalFallback = Timer(finalWait, () {
      if (!_finished) _finish(_last.trim().isNotEmpty ? _last.trim() : null);
    });
  }

  /// Ends the utterance exactly once. [text] non-null => delivered as the single final result.
  void _finish(String? text, {String? error}) {
    if (_finished) return;
    _finished = true;
    _clearTimers();
    if (error != null) _onError?.call(error);
    if (text != null && text.isNotEmpty) {
      debugPrint('[AUTO_SUBMIT] final transcript chars=${text.length}');
      _onResult?.call(text, true);
    }
    _onDone?.call();
  }

  void _clearTimers() {
    _silenceTimer?.cancel();
    _finalFallback?.cancel();
  }

  @override
  Future<void> stop() async {
    debugPrint('[STT_STOP] finishing utterance');
    _silenceTimer?.cancel();
    _armFinalFallback();
    try {
      await _ch.invokeMethod<void>('stop');
    } catch (_) {}
  }

  @override
  Future<void> cancel() async {
    final wasListening = !_finished;
    _finished = true;
    _clearTimers();
    try {
      await _ch.invokeMethod<void>('cancel');
    } catch (_) {}
    if (wasListening) debugPrint('[STT_CANCEL] aborted, no result delivered');
  }
}

class DeviceSpeaker implements Speaker {
  DeviceSpeaker({FlutterTts? tts}) : _tts = tts ?? FlutterTts();
  final FlutterTts _tts;
  bool _configured = false;

  // Resolves when the CURRENT utterance ends: spoken (completed or interrupted) or failed.
  // flutter_tts' own awaitSpeakCompletion never returns after an engine error, which left the
  // app stuck in SPEAKING (seen on a physical phone when Google TTS failed to synthesize Tamil).
  Completer<SpeakOutcome>? _pending;

  void _finish(SpeakOutcome o) {
    final p = _pending;
    _pending = null;
    if (p != null && !p.isCompleted) p.complete(o);
  }

  Future<void> _configure() async {
    if (_configured) return;
    try {
      debugPrint('[TTS_INIT] configuring FlutterTts');
      await _tts.setSpeechRate(0.5);
      await _tts.setVolume(1.0);
      await _tts.setPitch(1.0);
      await _tts.awaitSpeakCompletion(false);
      _tts.setCompletionHandler(() {
        debugPrint('[TTS_COMPLETE] speech playback completed');
        _finish(SpeakOutcome.spoken);
      });
      _tts.setCancelHandler(() {
        debugPrint('[TTS_CANCEL] speech cancelled');
        _finish(SpeakOutcome.spoken);
      });
      _tts.setErrorHandler((msg) {
        debugPrint('[TTS_ERROR] $msg');
        _finish(SpeakOutcome.failed);
      });
      _configured = true;
    } catch (e) {
      debugPrint('[TTS_INIT] config error: ${e.runtimeType}');
    }
  }

  /// Picks a voice that Android reports as installed and non-network for [tags], or null when
  /// none is listed (we then speak nothing).
  ///
  /// LIMIT (found on a physical phone): this is only what Android REPORTS. Google TTS lists
  /// `ta-in-x-tac-local` and `isLanguageInstalled` is true even before the voice pack is
  /// downloaded; the first request then dispatches to a `-server` voice (network). Android offers
  /// no API that tells an app the pack is really present (CHECK_TTS_DATA lists every language as
  /// available). Install the voice data while online first, and confirm in logcat that the
  /// dispatch line says `...-embedded`, not `...-server`.
  Future<String?> _selectLocalVoice(List<String> tags) async {
    for (final tag in tags) {
      bool installed;
      try {
        installed = (await _tts.isLanguageInstalled(tag)) == true;
      } catch (_) {
        installed = false;
      }
      if (!installed) continue;
      try {
        final voices = await _tts.getVoices;
        if (voices is List) {
          for (final v in voices) {
            if (v is! Map) continue;
            final locale = '${v['locale']}'.replaceAll('_', '-');
            final features = '${v['features'] ?? ''}';
            if (locale.toLowerCase() == tag.toLowerCase() &&
                '${v['network_required']}' == '0' &&
                !features.contains('notInstalled')) {
              await _tts.setVoice({'name': '${v['name']}', 'locale': '${v['locale']}'});
              debugPrint('[TTS_VOICE] local voice selected tag=$tag network_required=0');
              return tag;
            }
          }
        }
      } catch (e) {
        debugPrint('[TTS_VOICE] voice listing failed: ${e.runtimeType}');
      }
      await _tts.setLanguage(tag);
      return tag;
    }
    return null;
  }

  @override
  Future<SpeakOutcome> speak(String text, {required String languageTag}) async {
    try {
      await _configure();
      await _tts.stop(); // never overlap: any previous utterance is cut first
      final isTamil = languageTag.toLowerCase().startsWith('ta');
      final tags = isTamil ? ['ta-IN', 'ta'] : ['en-IN', 'en-US', 'en-GB', 'en'];
      final selected = await _selectLocalVoice(tags);
      debugPrint('[TTS_LANGUAGE] requested=$languageTag selected=$selected');
      if (selected == null) return SpeakOutcome.voiceMissing;
      final preview = text.length > 50 ? '${text.substring(0, 50)}...' : text;
      if (kDebugMode) debugPrint('[TTS_START] speaking ${text.length} chars: "$preview"');
      _finish(SpeakOutcome.spoken); // any stale utterance is over
      final done = _pending = Completer<SpeakOutcome>();
      final result = await _tts.speak(text);
      if (!(result == 1 || result == true)) {
        _finish(SpeakOutcome.failed);
        return SpeakOutcome.failed;
      }
      return done.future.timeout(const Duration(minutes: 4), onTimeout: () => SpeakOutcome.failed);
    } catch (e) {
      debugPrint('[TTS_ERROR] exception in speak: ${e.runtimeType}');
      return SpeakOutcome.failed;
    }
  }

  @override
  Future<void> stop() async {
    try {
      debugPrint('[TTS_STOP] stopping TTS');
      _finish(SpeakOutcome.spoken); // interrupted: the pending speak() returns now
      await _tts.stop();
    } catch (_) {}
  }
}

final voiceInputProvider = Provider<VoiceInput>((ref) {
  final v = NativeLocalVoiceInput();
  ref.onDispose(v.cancel);
  return v;
});
final speakerProvider = Provider<Speaker>((ref) {
  final s = DeviceSpeaker();
  ref.onDispose(s.stop);
  return s;
});

/// Cleans raw response into spoken-friendly Tamil or English (Contract §9 voice).
String planSpokenResponse(String text, {required bool isTamil}) {
  if (text.trim().isEmpty) return '';

  var s = text;

  // Convert bullets to spoken connectors first
  final lines = s.split('\n');
  final processed = <String>[];
  var bulletIdx = 0;
  final taConnectors = ['முதலில், ', 'அடுத்ததாக, ', 'மேலும், ', 'இறுதியாக, '];
  final enConnectors = ['First, ', 'Next, ', 'Also, ', 'Finally, '];

  for (final line in lines) {
    final trimmed = line.trim();
    final bulletMatch = RegExp(r'^[-*•]\s+(.*)$|^\d+[\.)]\s+(.*)$').firstMatch(trimmed);
    if (bulletMatch != null) {
      final itemText = (bulletMatch.group(1) ?? bulletMatch.group(2) ?? '').trim();
      if (itemText.isNotEmpty) {
        final connectors = isTamil ? taConnectors : enConnectors;
        final prefix = connectors[bulletIdx < connectors.length ? bulletIdx : connectors.length - 1];
        processed.add('$prefix$itemText');
        bulletIdx++;
      }
    } else {
      bulletIdx = 0;
      if (trimmed.isNotEmpty) {
        processed.add(trimmed);
      }
    }
  }
  s = processed.join(' ');

  // Strip code blocks and JSON
  s = s.replaceAll(RegExp(r'```[\s\S]*?```'), '');
  s = s.replaceAll(RegExp(r'`([^`]+)`'), r'$1');
  s = s.replaceAll(RegExp(r'\{[\s\S]*?\}'), '');

  // Strip markdown images and links: [title](url) -> title
  s = s.replaceAll(RegExp(r'!\[([^\]]*)\]\([^)]+\)'), '');
  s = s.replaceAll(RegExp(r'\[([^\]]+)\]\([^)]+\)'), r'$1');

  // Strip raw URLs
  s = s.replaceAll(RegExp(r'https?://\S+'), '');
  s = s.replaceAll(RegExp(r'www\.\S+'), '');

  // Strip headers (# Title)
  s = s.replaceAll(RegExp(r'^#{1,6}\s*', multiLine: true), '');

  // Strip bold and italics
  s = s.replaceAll(RegExp(r'\*\*([^*]+)\*\*'), r'$1');
  s = s.replaceAll(RegExp(r'\*([^*]+)\*'), r'$1');
  s = s.replaceAll(RegExp(r'__([^_]+)__'), r'$1');
  s = s.replaceAll(RegExp(r'_([^_]+)_'), r'$1');
  s = s.replaceAll(RegExp(r'~~([^~]+)~~'), r'$1');

  // Strip citation tags [TNAU], (confidence: 90%), etc.
  s = s.replaceAll(RegExp(r'\[(?:TNAU|IMD|CACP|RAG|Farm|Weather|Market|Disease)[^\]]*\]', caseSensitive: false), '');
  s = s.replaceAll(RegExp(r'\((?:confidence|ஆதாரம்)[^)]*\)', caseSensitive: false), '');
  s = s.replaceAll(RegExp(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', caseSensitive: false), '');

  // Units expansion & spoken Tamil replacements
  if (isTamil) {
    s = s.replaceAllMapped(RegExp(r'(\d+(?:\.\d+)?)\s*(?:மிமீ|mm)(?=[.,!?;:\s]|$)'), (m) => '${m[1]} மில்லிமீட்டர்');
    s = s.replaceAllMapped(RegExp(r'(\d+(?:\.\d+)?)\s*(?:ஹெக்டேர்|ha)(?=[.,!?;:\s]|$)'), (m) => '${m[1]} ஹெக்டேர்');
    s = s.replaceAllMapped(RegExp(r'(\d+(?:\.\d+)?)\s*(?:கிலோ|kg|கிகி)(?=[.,!?;:\s]|$)'), (m) => '${m[1]} கிலோ');
    s = s.replaceAllMapped(RegExp(r'(\d+(?:\.\d+)?)\s*(?:கிராம்|gm|g)(?=[.,!?;:\s]|$)'), (m) => '${m[1]} கிராம்');
    s = s.replaceAllMapped(RegExp(r'(\d+(?:\.\d+)?)\s*(?:லிட்டர்|litres?|l)(?=[.,!?;:\s]|$)'), (m) => '${m[1]} லிட்டர்');
    s = s.replaceAllMapped(RegExp(r'(\d+(?:\.\d+)?)\s*%'), (m) => '${m[1]} சதவீதம்');
    s = s.replaceAllMapped(RegExp(r'(?:₹|ரூ\.)\s*(\d+(?:,\d+)*(?:\.\d+)?)'), (m) => '${m[1]} ரூபாய்');
    s = s.replaceAll(RegExp(r'பின்வரும்\s+பரிந்துரைகளை\s+கடைப்பிடிக்கவும்[:.]?'), 'முதலில் இதை பாருங்க:');
    s = s.replaceAll(RegExp(r'அச்சம்\s+கொள்ளத்\s+தேவையில்லை'), 'கவலைப்படாதீங்க');
    s = s.replaceAll(RegExp(r'நிழற்படத்தை\s+சமர்ப்பிக்கவும்'), 'ஒரு புகைப்படம் அனுப்புங்க');
  } else {
    s = s.replaceAllMapped(RegExp(r'(\d+(?:\.\d+)?)\s*(?:mm|மிமீ)(?=[.,!?;:\s]|$)'), (m) => '${m[1]} millimeters');
    s = s.replaceAllMapped(RegExp(r'(\d+(?:\.\d+)?)\s*(?:ha|ஹெக்டேர்)(?=[.,!?;:\s]|$)'), (m) => '${m[1]} hectares');
    s = s.replaceAllMapped(RegExp(r'(\d+(?:\.\d+)?)\s*(?:kg|கிலோ)(?=[.,!?;:\s]|$)'), (m) => '${m[1]} kilograms');
    s = s.replaceAllMapped(RegExp(r'(\d+(?:\.\d+)?)\s*%'), (m) => '${m[1]} percent');
    s = s.replaceAllMapped(RegExp(r'(?:₹|Rs\.?)\s*(\d+(?:,\d+)*(?:\.\d+)?)'), (m) => '${m[1]} rupees');
  }

  // Collapse whitespaces
  s = s.replaceAll(RegExp(r'\s+'), ' ').trim();
  s = s.replaceAll(RegExp(r'^[ ,:;.-]+'), '').trim();

  if (s.isEmpty) {
    return isTamil ? 'மன்னிக்கவும், தகவலைப் பெற முடியவில்லை.' : 'Sorry, could not prepare the voice answer.';
  }
  return s;
}
