// Local Android voice: on-device STT only, local TTS only, a state machine with no duplicate /
// overlapping / empty submissions, and explicit offline-unavailable handling (no cloud fallback).
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/features/assistant/data/assistant_repository.dart';
import 'package:uzhavan/features/assistant/data/voice_services.dart';
import 'package:uzhavan/features/assistant/presentation/assistant_screen.dart';
import 'package:uzhavan/features/assistant/presentation/chat_controller.dart';

import '../helpers/scripted_adapter.dart';
import '../helpers/test_app.dart';
import 'assistant_test.dart' show FakeSpeaker, FakeVoice, ev, makeApi, sseBody;

final _answerTa = [
  ev('session_started', {}),
  ev('completed', {'answer': 'நைட்ரஜன் குறைபாடு இருக்கலாம்', 'is_fallback': false, 'grounded': true}),
].join();
final _answerEn = [
  ev('session_started', {}),
  ev('completed', {'answer': 'Nitrogen deficiency is likely.', 'is_fallback': false}),
].join();

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  group('Voice loop (screen + controller)', () {
    Future<(ProviderContainer, FakeVoice, FakeSpeaker, ScriptedAdapter)> pump(
      WidgetTester tester, {
      VoiceInitResult init = VoiceInitResult.ready,
      String lang = 'ta',
      String body = '',
    }) async {
      final adapter = ScriptedAdapter((_) async => sseBody(body.isEmpty ? _answerTa : body));
      final voice = FakeVoice(init);
      final speaker = FakeSpeaker();
      final c = await makeContainer(
        prefs: {'app.language': lang},
        overrides: [
          assistantRepositoryProvider.overrideWithValue(AssistantRepository(makeApi(adapter))),
          voiceInputProvider.overrideWithValue(voice),
          speakerProvider.overrideWithValue(speaker),
        ],
      );
      addTearDown(c.dispose);
      await tester.pumpWidget(UncontrolledProviderScope(container: c, child: const TestApp(home: AssistantScreen())));
      await tester.pumpAndSettle();
      return (c, voice, speaker, adapter);
    }

    testWidgets('speak → final transcript auto-submits (no Send tap) → Tamil TTS → idle', (tester) async {
      final (c, voice, speaker, adapter) = await pump(tester);
      await tester.tap(find.byKey(const Key('mic-button')));
      await tester.pump();
      expect(voice.initLocale, 'ta-IN');
      expect(voice.startLocale, 'ta-IN');
      expect(c.read(assistantVoiceStateProvider), AssistantVoiceState.listening);

      voice.say('நெல் இலை மஞ்சளாக இருக்கு', isFinal: false); // partials never submit
      await tester.pump();
      expect(adapter.requests, isEmpty);

      voice.say('நெல் இலை மஞ்சளாக இருக்கு');
      voice.finish();
      await tester.pumpAndSettle();

      expect(adapter.countPath('/conversation'), 1);
      expect(find.text('நைட்ரஜன் குறைபாடு இருக்கலாம்'), findsOneWidget);
      expect(speaker.spoken.single, startsWith('ta-IN:'));
      expect(c.read(assistantVoiceStateProvider), AssistantVoiceState.idle);
      expect(c.read(voiceNoticeProvider), VoiceNotice.none);
    });

    testWidgets('English preference: en-IN recognition and en-IN speech', (tester) async {
      final (c, voice, speaker, _) = await pump(tester, lang: 'en', body: _answerEn);
      await tester.tap(find.byKey(const Key('mic-button')));
      await tester.pump();
      expect(voice.startLocale, 'en-IN');
      voice.say('why are my rice leaves yellow');
      voice.finish();
      await tester.pumpAndSettle();
      expect(speaker.spoken.single, startsWith('en-IN:'));
      expect(c.read(assistantVoiceStateProvider), AssistantVoiceState.idle);
    });

    testWidgets('duplicate final results and empty transcripts never double-submit', (tester) async {
      final (c, voice, _, adapter) = await pump(tester);
      await tester.tap(find.byKey(const Key('mic-button')));
      await tester.pump();
      voice.say('   '); // empty/whitespace final
      await tester.pump();
      expect(adapter.requests, isEmpty);

      voice.say('நெல் நோய்');
      voice.say('நெல் நோய்'); // duplicate final
      voice.finish();
      voice.finish();
      await tester.pumpAndSettle();
      expect(adapter.countPath('/conversation'), 1);
      expect(c.read(chatProvider).messages.where((m) => m.role == ChatRole.user).length, 1);
    });

    testWidgets('silence (done without transcript) returns to idle, nothing sent', (tester) async {
      final (c, voice, _, adapter) = await pump(tester);
      await tester.tap(find.byKey(const Key('mic-button')));
      await tester.pump();
      voice.finish();
      await tester.pumpAndSettle();
      expect(adapter.requests, isEmpty);
      expect(c.read(assistantVoiceStateProvider), AssistantVoiceState.idle);
    });

    test('multi-turn: voice turns share one session, both are spoken, context is preserved', () async {
      final adapter = ScriptedAdapter((_) async => sseBody(_answerTa));
      final speaker = FakeSpeaker();
      final c = await makeContainer(prefs: {'app.language': 'ta'}, overrides: [
        assistantRepositoryProvider.overrideWithValue(AssistantRepository(makeApi(adapter))),
        voiceInputProvider.overrideWithValue(FakeVoice(VoiceInitResult.ready)),
        speakerProvider.overrideWithValue(speaker),
      ]);
      addTearDown(c.dispose);
      final chat = c.read(chatProvider.notifier);
      for (final q in ['முதல் கேள்வி', 'இரண்டாவது கேள்வி']) {
        chat.beginVoiceTurn();
        expect(await chat.sendVoice(q), isTrue);
        expect(await chat.sendVoice(q), isFalse); // the same turn can never be submitted twice
      }
      await Future<void>.delayed(const Duration(milliseconds: 50));
      expect(adapter.countPath('/conversation'), 2);
      expect(adapter.requests.first.data.toString(), isNot(contains('session_id')));
      expect(adapter.requests.last.data.toString(), contains('session_id: s1')); // context carried over
      expect(c.read(chatProvider).messages.length, 4);
      expect(speaker.spoken.length, 2);
      expect(c.read(assistantVoiceStateProvider), AssistantVoiceState.idle);
    });

    test('sendVoice without an open voice turn, or with empty text, is ignored', () async {
      final adapter = ScriptedAdapter((_) async => sseBody(_answerTa));
      final c = await makeContainer(prefs: {'app.language': 'ta'}, overrides: [
        assistantRepositoryProvider.overrideWithValue(AssistantRepository(makeApi(adapter))),
        voiceInputProvider.overrideWithValue(FakeVoice(VoiceInitResult.ready)),
        speakerProvider.overrideWithValue(FakeSpeaker()),
      ]);
      addTearDown(c.dispose);
      final chat = c.read(chatProvider.notifier);
      expect(await chat.sendVoice('late result after cancel'), isFalse);
      chat.beginVoiceTurn();
      expect(await chat.sendVoice('   '), isFalse);
      expect(adapter.requests, isEmpty);
    });

    testWidgets('offline recognition unavailable → explicit notice, NO audio started, typing still works', (tester) async {
      final (c, voice, _, adapter) = await pump(tester, init: VoiceInitResult.offlineUnavailable);
      await tester.tap(find.byKey(const Key('mic-button')));
      await tester.pumpAndSettle();
      expect(voice.startCalls, 0); // recognizer never started => nothing captured/uploaded
      expect(find.byKey(const Key('voice-notice')), findsOneWidget);
      expect(find.textContaining('nothing was recorded or uploaded'), findsNothing); // Tamil UI
      expect(c.read(voiceNoticeProvider), VoiceNotice.offlineUnavailable);
      expect(c.read(assistantVoiceStateProvider), AssistantVoiceState.error);

      // text fallback
      await tester.enterText(find.byKey(const Key('chat-input')), 'நெல் நோய்');
      await tester.tap(find.byKey(const Key('send-button')));
      await tester.pumpAndSettle();
      expect(adapter.countPath('/conversation'), 1);
      expect(c.read(voiceNoticeProvider), VoiceNotice.none); // cleared by the next action
    });

    testWidgets('offline notice text in English', (tester) async {
      await pump(tester, init: VoiceInitResult.offlineUnavailable, lang: 'en');
      await tester.tap(find.byKey(const Key('mic-button')));
      await tester.pumpAndSettle();
      expect(find.textContaining("Offline voice recognition isn't available"), findsOneWidget);
      expect(find.textContaining('nothing was recorded or uploaded'), findsOneWidget);
    });

    testWidgets('offline language pack missing → install instructions, no audio', (tester) async {
      final (c, voice, _, _) = await pump(tester, init: VoiceInitResult.offlineLanguageMissing, lang: 'en');
      await tester.tap(find.byKey(const Key('mic-button')));
      await tester.pumpAndSettle();
      expect(voice.startCalls, 0);
      expect(find.textContaining('offline speech pack'), findsOneWidget);
      expect(c.read(voiceNoticeProvider), VoiceNotice.offlineLanguageMissing);
    });

    testWidgets('native recognizer refusing at start (offline_unavailable) shows the notice', (tester) async {
      final (c, voice, _, adapter) = await pump(tester);
      await tester.tap(find.byKey(const Key('mic-button')));
      await tester.pump();
      voice.fail('offline_unavailable');
      voice.finish();
      await tester.pumpAndSettle();
      expect(c.read(voiceNoticeProvider), VoiceNotice.offlineUnavailable);
      expect(adapter.requests, isEmpty);
    });

    testWidgets('missing offline Tamil TTS voice → clear install notice, nothing spoken', (tester) async {
      final (c, voice, speaker, _) = await pump(tester, lang: 'en');
      speaker.outcome = SpeakOutcome.voiceMissing;
      await tester.tap(find.byKey(const Key('mic-button')));
      await tester.pump();
      voice.say('நெல் இலை மஞ்சள்');
      voice.finish();
      await tester.pumpAndSettle();
      expect(c.read(voiceNoticeProvider), VoiceNotice.ttsVoiceMissingTamil);
      expect(c.read(assistantVoiceStateProvider), AssistantVoiceState.error);
      expect(find.textContaining('No offline Tamil voice is installed'), findsOneWidget);
      expect(find.textContaining('Install voice data > Tamil'), findsOneWidget);
      // the written answer is still shown
      expect(find.text('நைட்ரஜன் குறைபாடு இருக்கலாம்'), findsOneWidget);
    });

    testWidgets('dismissing the notice clears the error state', (tester) async {
      final (c, _, _, _) = await pump(tester, init: VoiceInitResult.offlineUnavailable);
      await tester.tap(find.byKey(const Key('mic-button')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('voice-notice-dismiss')));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('voice-notice')), findsNothing);
      expect(c.read(assistantVoiceStateProvider), AssistantVoiceState.idle);
    });

    testWidgets('mic tapped during TTS: speech stopped first, then listening; stale completion is ignored', (tester) async {
      final (c, voice, speaker, _) = await pump(tester);
      speaker.hold = Completer<void>();
      c.read(voiceConversationEnabledProvider.notifier).setEnabled(true);
      await tester.enterText(find.byKey(const Key('chat-input')), 'நெல் நோய்');
      await tester.tap(find.byKey(const Key('send-button')));
      await tester.pump(const Duration(milliseconds: 50));
      await tester.pump(const Duration(milliseconds: 50));
      expect(c.read(assistantVoiceStateProvider), AssistantVoiceState.speaking);

      await tester.tap(find.byKey(const Key('mic-button')));
      await tester.pump();
      // order: speak, stop (interrupt) ... then the mic started
      expect(speaker.events.lastIndexOf('stop'), greaterThan(speaker.events.indexOf('speak')));
      expect(voice.startCalls, 1);
      expect(c.read(assistantVoiceStateProvider), AssistantVoiceState.listening);

      speaker.hold!.complete(); // the old utterance "finishes" late
      await tester.pump();
      expect(c.read(assistantVoiceStateProvider), AssistantVoiceState.listening); // not clobbered
    });

    testWidgets('stop button interrupts speech immediately; late completion cannot restart it', (tester) async {
      final (c, _, speaker, _) = await pump(tester);
      speaker.hold = Completer<void>();
      c.read(voiceConversationEnabledProvider.notifier).setEnabled(true);
      await tester.enterText(find.byKey(const Key('chat-input')), 'நெல் நோய்');
      await tester.tap(find.byKey(const Key('send-button')));
      await tester.pump(const Duration(milliseconds: 100));
      await tester.pump(const Duration(milliseconds: 100));
      expect(find.byKey(const Key('stop-speaking-button')), findsOneWidget);

      await tester.tap(find.byKey(const Key('stop-speaking-button')));
      await tester.pump();
      expect(speaker.events.last, 'stop');
      expect(c.read(assistantVoiceStateProvider), AssistantVoiceState.idle);
      speaker.hold!.complete();
      await tester.pump();
      expect(c.read(assistantVoiceStateProvider), AssistantVoiceState.idle);
      expect(speaker.spoken.length, 1); // no repeated TTS
    });

    testWidgets('manual speaker button remains available and uses the same single-utterance path', (tester) async {
      final (_, _, speaker, _) = await pump(tester);
      await tester.enterText(find.byKey(const Key('chat-input')), 'நெல் நோய்');
      await tester.tap(find.byKey(const Key('send-button')));
      await tester.pumpAndSettle();
      expect(speaker.spoken, isEmpty); // typed question without voice mode: not auto-spoken
      await tester.tap(find.byKey(const Key('speak-button')));
      await tester.pumpAndSettle();
      expect(speaker.spoken.single, startsWith('ta-IN:'));
      expect(speaker.events.first, 'stop'); // previous audio is always cut before a new utterance? (controller stop)
    });

    testWidgets('backgrounding the app cancels the mic and stops speech', (tester) async {
      final (c, voice, speaker, _) = await pump(tester);
      await tester.tap(find.byKey(const Key('mic-button')));
      await tester.pump();
      expect(c.read(assistantVoiceStateProvider), AssistantVoiceState.listening);

      for (final st in [AppLifecycleState.inactive, AppLifecycleState.hidden, AppLifecycleState.paused]) {
        tester.binding.handleAppLifecycleStateChanged(st);
      }
      await tester.pump();
      expect(voice.cancelCalls, greaterThan(0));
      expect(speaker.events, contains('stop'));
      expect(c.read(assistantVoiceStateProvider), AssistantVoiceState.idle);
      for (final st in [AppLifecycleState.hidden, AppLifecycleState.inactive, AppLifecycleState.resumed]) {
        tester.binding.handleAppLifecycleStateChanged(st);
      }
    });

    testWidgets('the app never calls the backend /voice endpoints', (tester) async {
      final (_, voice, _, adapter) = await pump(tester);
      await tester.tap(find.byKey(const Key('mic-button')));
      await tester.pump();
      voice.say('நெல் நோய்');
      voice.finish();
      await tester.pumpAndSettle();
      expect(adapter.requests.where((r) => r.path.contains('/voice')), isEmpty);
    });
  });

  group('NativeLocalVoiceInput (platform-channel contract)', () {
    const channel = MethodChannel('ai.uzhavan/local_stt');
    final calls = <String>[];
    late Map<String, Object?> availability;
    bool permission = true;
    bool startResult = true;

    setUp(() {
      calls.clear();
      availability = {'state': 'ready'};
      permission = true;
      startResult = true;
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(channel, (call) async {
        calls.add(call.method);
        switch (call.method) {
          case 'hasPermission':
            return permission;
          case 'requestPermission':
            return permission;
          case 'availability':
            return availability;
          case 'start':
            return startResult;
          default:
            return null;
        }
      });
    });
    tearDown(() => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(channel, null));

    // Delivers a native event to Dart, as Kotlin's channel.invokeMethod("event", ...) does.
    Future<void> native(Map<String, Object?> e) async {
      await TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.handlePlatformMessage(
        channel.name,
        channel.codec.encodeMethodCall(MethodCall('event', e)),
        (_) {},
      );
    }

    test('availability states map to the right results', () async {
      final v = NativeLocalVoiceInput(channel: channel);
      for (final (state, expected) in [
        ('ready', VoiceInitResult.ready),
        ('ready_unverified', VoiceInitResult.ready),
        ('language_missing', VoiceInitResult.offlineLanguageMissing),
        ('language_unsupported', VoiceInitResult.offlineLanguageMissing),
        ('unsupported_api', VoiceInitResult.offlineUnavailable),
        ('no_on_device_service', VoiceInitResult.offlineUnavailable),
      ]) {
        availability = {'state': state};
        expect(await v.init(localeId: 'ta-IN'), expected, reason: state);
      }
    });

    test('permission denied → no availability probe, no recognizer', () async {
      permission = false;
      final v = NativeLocalVoiceInput(channel: channel);
      expect(await v.init(localeId: 'ta-IN'), VoiceInitResult.permissionDenied);
      expect(calls, isNot(contains('availability')));
      expect(calls, isNot(contains('start')));
    });

    test('partials do not submit; the final result is delivered exactly once', () async {
      final v = NativeLocalVoiceInput(channel: channel);
      final results = <(String, bool)>[];
      var done = 0;
      await v.start(localeId: 'ta-IN', onResult: (t, f) => results.add((t, f)), onDone: () => done++);
      await native({'type': 'partial', 'text': 'நெல்'});
      await native({'type': 'final', 'text': 'நெல் இலை'});
      await native({'type': 'final', 'text': 'நெல் இலை'}); // duplicate
      expect(results.where((r) => r.$2).length, 1);
      expect(results.last, ('நெல் இலை', true));
      expect(done, 1);
    });

    test('no_speech ends quietly without a result or error', () async {
      final v = NativeLocalVoiceInput(channel: channel);
      final results = <String>[];
      final errors = <String>[];
      var done = 0;
      await v.start(
          localeId: 'ta-IN', onResult: (t, f) => results.add(t), onDone: () => done++, onError: errors.add);
      await native({'type': 'error', 'code': 'no_speech'});
      expect(results, isEmpty);
      expect(errors, isEmpty);
      expect(done, 1);
    });

    test('offline_unavailable from native is surfaced as an error, never retried online', () async {
      startResult = false;
      final v = NativeLocalVoiceInput(channel: channel);
      final errors = <String>[];
      var done = 0;
      await v.start(localeId: 'ta-IN', onResult: (_, _) {}, onDone: () => done++, onError: errors.add);
      await native({'type': 'error', 'code': 'offline_unavailable'});
      expect(errors, ['offline_unavailable']);
      expect(done, 1);
      expect(calls.where((c) => c == 'start').length, 1); // exactly one attempt, no fallback attempt
    });

    test('cancel delivers nothing', () async {
      final v = NativeLocalVoiceInput(channel: channel);
      final results = <String>[];
      await v.start(localeId: 'ta-IN', onResult: (t, f) => results.add(t), onDone: () {});
      await v.cancel();
      await native({'type': 'final', 'text': 'late'});
      expect(results, isEmpty);
    });

    test('only the documented on-device channel methods are ever invoked', () async {
      final v = NativeLocalVoiceInput(channel: channel);
      await v.init(localeId: 'ta-IN');
      await v.start(localeId: 'ta-IN', onResult: (_, _) {}, onDone: () {});
      await v.stop();
      await v.cancel();
      expect(calls.toSet().difference({'hasPermission', 'requestPermission', 'availability', 'start', 'stop', 'cancel'}), isEmpty);
    });
  });

  group('DeviceSpeaker (local, installed, non-network voices only)', () {
    const ttsChannel = MethodChannel('flutter_tts');
    final calls = <(String, Object?)>[];
    Set<String> installed = {};
    List<Map<String, String>> voices = [];

    setUp(() {
      calls.clear();
      installed = {};
      voices = [];
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(ttsChannel, (call) async {
        calls.add((call.method, call.arguments));
        switch (call.method) {
          case 'isLanguageInstalled':
            return installed.contains(call.arguments);
          case 'getVoices':
            return voices;
          case 'speak':
            return 1;
          default:
            return 1;
        }
      });
    });
    tearDown(() => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(ttsChannel, null));

    int count(String m) => calls.where((c) => c.$1 == m).length;

    // Delivers a native callback to flutter_tts, as the Android plugin does.
    Future<void> nativeTts(String method, [Object? arg]) async {
      await TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.handlePlatformMessage(
        ttsChannel.name,
        ttsChannel.codec.encodeMethodCall(MethodCall(method, arg)),
        (_) {},
      );
    }

    void givenInstalledEnglish() {
      installed = {'en-IN'};
      voices = [
        {'name': 'en-in-local', 'locale': 'en-IN', 'network_required': '0', 'features': ''},
      ];
    }


    test('Tamil voice not installed → voiceMissing and NOTHING is spoken', () async {
      final out = await DeviceSpeaker().speak('வணக்கம்', languageTag: 'ta-IN');
      expect(out, SpeakOutcome.voiceMissing);
      expect(count('speak'), 0);
    });

    test('installed Tamil: picks the local (network_required=0) voice, never the network one', () async {
      installed = {'ta-IN'};
      voices = [
        {'name': 'ta-in-x-network', 'locale': 'ta-IN', 'network_required': '1', 'features': ''},
        {'name': 'ta-in-x-local', 'locale': 'ta-IN', 'network_required': '0', 'features': 'embeddedTts'},
      ];
      final f = DeviceSpeaker().speak('வணக்கம்', languageTag: 'ta-IN');
      await Future<void>.delayed(const Duration(milliseconds: 20));
      await nativeTts('speak.onComplete');
      expect(await f, SpeakOutcome.spoken);
      final setVoice = calls.firstWhere((c) => c.$1 == 'setVoice').$2 as Map;
      expect(setVoice['name'], 'ta-in-x-local');
      expect(count('speak'), 1);
    });

    test('a Tamil voice flagged notInstalled is not used', () async {
      installed = {'ta-IN'};
      voices = [
        {'name': 'ta-in-x-local', 'locale': 'ta-IN', 'network_required': '0', 'features': 'notInstalled'},
      ];
      final f = DeviceSpeaker().speak('வணக்கம்', languageTag: 'ta-IN');
      await Future<void>.delayed(const Duration(milliseconds: 20));
      await nativeTts('speak.onComplete');
      await f;
      expect(calls.where((c) => c.$1 == 'setVoice'), isEmpty);
    });

    test('engine error ends the utterance as FAILED (regression: app stuck in SPEAKING on a real phone)', () async {
      givenInstalledEnglish();
      final f = DeviceSpeaker().speak('hello', languageTag: 'en-IN');
      await Future<void>.delayed(const Duration(milliseconds: 20));
      await nativeTts('speak.onError', 'Error from TextToSpeech (speak)');
      expect(await f.timeout(const Duration(seconds: 2)), SpeakOutcome.failed);
    });

    test('normal completion ends the utterance as spoken', () async {
      givenInstalledEnglish();
      final f = DeviceSpeaker().speak('hello', languageTag: 'en-IN');
      await Future<void>.delayed(const Duration(milliseconds: 20));
      await nativeTts('speak.onComplete');
      expect(await f.timeout(const Duration(seconds: 2)), SpeakOutcome.spoken);
    });

    test('stop() resolves the pending speak() immediately (interruption)', () async {
      givenInstalledEnglish();
      final s = DeviceSpeaker();
      final f = s.speak('a long answer', languageTag: 'en-IN');
      await Future<void>.delayed(const Duration(milliseconds: 20));
      await s.stop();
      expect(await f.timeout(const Duration(seconds: 2)), SpeakOutcome.spoken);
    });

    test('a new speak() resolves the previous one first (no two live utterances)', () async {
      givenInstalledEnglish();
      final s = DeviceSpeaker();
      final first = s.speak('one', languageTag: 'en-IN');
      await Future<void>.delayed(const Duration(milliseconds: 20));
      final second = s.speak('two', languageTag: 'en-IN');
      expect(await first.timeout(const Duration(seconds: 2)), SpeakOutcome.spoken);
      await Future<void>.delayed(const Duration(milliseconds: 20));
      await nativeTts('speak.onComplete');
      expect(await second.timeout(const Duration(seconds: 2)), SpeakOutcome.spoken);
    });

    test('English uses an English local voice; each speak() cuts previous audio first', () async {
      installed = {'en-IN'};
      voices = [
        {'name': 'en-in-local', 'locale': 'en-IN', 'network_required': '0', 'features': ''},
      ];
      final s = DeviceSpeaker();
      final a = s.speak('hello', languageTag: 'en-IN');
      await Future<void>.delayed(const Duration(milliseconds: 20));
      await nativeTts('speak.onComplete');
      await a;
      final b = s.speak('again', languageTag: 'en-IN');
      await Future<void>.delayed(const Duration(milliseconds: 20));
      await nativeTts('speak.onComplete');
      await b;
      final order = calls.map((c) => c.$1).toList();
      for (var i = 0; i < order.length; i++) {
        if (order[i] == 'speak') expect(order.sublist(0, i), contains('stop'));
      }
      expect(count('speak'), 2);
    });
  });
}
