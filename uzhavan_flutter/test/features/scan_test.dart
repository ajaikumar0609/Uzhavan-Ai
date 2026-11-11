import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/core/networking/api_client.dart';
import 'package:uzhavan/core/networking/api_failure.dart';
import 'package:uzhavan/core/storage/token_store.dart';
import 'package:uzhavan/features/scan/data/scan_repository.dart';
import 'package:uzhavan/features/scan/presentation/scan_controller.dart';
import 'package:uzhavan/features/scan/presentation/scan_screen.dart';

import '../helpers/scripted_adapter.dart';
import '../helpers/test_app.dart';

ApiClient makeApi(ScriptedAdapter adapter) => ApiClient(
      baseUrl: 'http://test.local',
      tokenStore: MemoryTokenStore(const AuthTokens(accessToken: 'a', refreshToken: 'r')),
      adapter: adapter,
    );

MultipartFile part() => MultipartFile.fromBytes([1, 2, 3], filename: 'leaf.jpg', contentType: imageMediaType('leaf.jpg'));

final modelUnavailable = errorDetail('model_unavailable', en: 'The disease model is not yet approved for use.');

Map<String, Object?> okBody(String status, {bool withTop = true}) => {
      'data': {
        'status': status,
        'crop_id': 'tomato',
        'top': withTop
            ? {'class_id': 'early_blight', 'label': {'en': 'Early blight', 'ta': null}, 'probability': 0.91}
            : null,
        'predictions': [],
        'model_version': 'm4-test',
        'inferred_at': '2026-09-25T10:30:00Z',
        'production_eligible': true,
        'guidance': [
          {'text': {'en': 'Remove infected leaves', 'ta': null}, 'source': 'TNAU', 'source_url': 'https://agritech.tnau.ac.in'},
        ],
      },
      'meta': {'source': 'UZHAVAN M4'},
    };

class FakePicker implements ImageSourcePicker {
  FakePicker({this.deny = false});
  final bool deny;
  @override
  Future<String?> pick(PickSource source) async {
    if (deny) throw const PickDenied();
    return '/tmp/leaf.jpg';
  }
}

void main() {
  group('ScanRepository', () {
    test('multipart with image (jpeg) + crop_id; 503 model_unavailable → unavailable', () async {
      final adapter = ScriptedAdapter((_) async => jsonBody(503, modelUnavailable));
      await expectLater(
        ScanRepository(makeApi(adapter)).scan(image: part(), cropId: 'tomato'),
        throwsA(isA<ApiFailure>()
            .having((f) => f.kind, 'kind', ApiFailureKind.unavailable)
            .having((f) => f.code, 'code', 'model_unavailable')),
      );
      final req = adapter.requests.single;
      expect(req.path, '/api/disease/scan');
      final form = req.data as FormData;
      expect(Map.fromEntries(form.fields), {'crop_id': 'tomato'});
      expect(form.files.single.key, 'image');
      expect(form.files.single.value.contentType.toString(), 'image/jpeg');
    });

    test('future 200 parses; 413 → validation with code', () async {
      final adapter = ScriptedAdapter((_) async => jsonBody(200, okBody('ok')));
      final env = await ScanRepository(makeApi(adapter)).scan(image: part(), cropId: 'tomato');
      expect(env.data.isConfident, isTrue);
      expect(env.data.top!.probability, 0.91);
      expect(env.data.guidance.single.sourceUrl, 'https://agritech.tnau.ac.in');

      adapter.handler = (_) async => jsonBody(413, errorDetail('file_too_large'));
      await expectLater(ScanRepository(makeApi(adapter)).scan(image: part()),
          throwsA(isA<ApiFailure>().having((f) => f.code, 'code', 'file_too_large')));
      adapter.handler = (_) async => jsonBody(415, errorDetail('unsupported_media_type'));
      await expectLater(ScanRepository(makeApi(adapter)).scan(image: part()),
          throwsA(isA<ApiFailure>().having((f) => f.kind, 'kind', ApiFailureKind.validation)));
    });

    test('media type by extension', () {
      expect(imageMediaType('a.PNG').toString(), 'image/png');
      expect(imageMediaType('a.webp').toString(), 'image/webp');
      expect(imageMediaType('a.jpg').toString(), 'image/jpeg');
    });
  });

  group('scan flow', () {
    Future<ProviderContainer> container(ScriptedAdapter adapter, {bool deny = false}) async {
      final c = await makeContainer(prefs: {'app.language': 'en'}, overrides: [
        scanRepositoryProvider.overrideWithValue(ScanRepository(makeApi(adapter))),
        imagePickerProvider.overrideWithValue(FakePicker(deny: deny)),
        imagePartBuilderProvider.overrideWithValue((_) async => part()),
      ]);
      addTearDown(c.dispose);
      return c;
    }

    Future<void> showOutcome(WidgetTester tester, ProviderContainer c) async {
      await tester.pumpWidget(UncontrolledProviderScope(
        container: c,
        child: TestApp(
          home: Scaffold(
            body: Consumer(builder: (context, ref, _) => ScanOutcome(state: ref.watch(scanProvider))),
          ),
        ),
      ));
      await tester.pumpAndSettle();
    }

    testWidgets('503 → UNAVAILABLE "validated disease model unavailable", no diagnosis', (tester) async {
      final adapter = ScriptedAdapter((_) async => jsonBody(503, modelUnavailable));
      final c = await container(adapter);
      final ctl = c.read(scanProvider.notifier);
      ctl.selectCrop('tomato');
      await ctl.pick(PickSource.camera);
      expect(c.read(scanProvider).canSubmit, isTrue);
      await tester.runAsync(ctl.submit);
      expect(c.read(scanProvider).result, isNull);
      await showOutcome(tester, c);
      expect(find.byKey(const Key('scan-model-unavailable')), findsOneWidget);
      expect(find.textContaining('Validated disease model unavailable'), findsOneWidget);
      expect(find.byKey(const Key('scan-result')), findsNothing);
      expect(find.textContaining('not yet approved'), findsNothing); // server text not shown
    });

    testWidgets('200 unsure → UNSURE (consult an officer), no label', (tester) async {
      final adapter = ScriptedAdapter((_) async => jsonBody(200, okBody('unsure')));
      final c = await container(adapter);
      final ctl = c.read(scanProvider.notifier)..selectCrop('tomato');
      await ctl.pick(PickSource.gallery);
      await tester.runAsync(ctl.submit);
      await showOutcome(tester, c);
      expect(find.byKey(const Key('scan-unsure')), findsOneWidget);
      expect(find.text('Early blight'), findsNothing);
    });

    testWidgets('200 ok without top → treated as unsure', (tester) async {
      final adapter = ScriptedAdapter((_) async => jsonBody(200, okBody('ok', withTop: false)));
      final c = await container(adapter);
      final ctl = c.read(scanProvider.notifier)..selectCrop('tomato');
      await ctl.pick(PickSource.gallery);
      await tester.runAsync(ctl.submit);
      await showOutcome(tester, c);
      expect(find.byKey(const Key('scan-unsure')), findsOneWidget);
    });

    testWidgets('200 ok → label, probability, model version, guidance with source', (tester) async {
      final adapter = ScriptedAdapter((_) async => jsonBody(200, okBody('ok')));
      final c = await container(adapter);
      final ctl = c.read(scanProvider.notifier)..selectCrop('tomato');
      await ctl.pick(PickSource.camera);
      await tester.runAsync(ctl.submit);
      await showOutcome(tester, c);
      expect(find.byKey(const Key('scan-result')), findsOneWidget);
      expect(find.text('Early blight'), findsOneWidget);
      expect(find.text('91 %'), findsOneWidget);
      expect(find.text('m4-test'), findsOneWidget);
      expect(find.text('• Remove infected leaves'), findsOneWidget);
    });

    testWidgets('200 demo_result → M4 v1 RESEARCH DEMO with NOT PRODUCTION CERTIFIED badge', (tester) async {
      final demoPayload = {
        'status': 'demo_result',
        'crop': 'groundnut',
        'predicted_class': 'rust',
        'confidence': 0.626,
        'top3': [
          {'class': 'rust', 'probability': 0.626},
          {'class': 'late_leaf_spot', 'probability': 0.1533},
          {'class': 'nutrient_deficiency', 'probability': 0.0976},
        ],
        'model_architecture': 'EfficientNetV2-S',
        'model_version': 'v1.0',
        'experiment_id': 'UZ-M4-v1.0-a898475e-s1',
        'demo_mode': true,
        'production_certified': false,
        'inference_timestamp': '2026-09-26T06:28:19Z',
        'latency_ms': 35.6,
        'data': {
          'status': 'demo_result',
          'crop': 'groundnut',
          'predicted_class': 'rust',
          'confidence': 0.626,
          'top3': [
            {'class': 'rust', 'probability': 0.626},
            {'class': 'late_leaf_spot', 'probability': 0.1533},
            {'class': 'nutrient_deficiency', 'probability': 0.0976},
          ],
          'model_architecture': 'EfficientNetV2-S',
          'model_version': 'v1.0',
          'experiment_id': 'UZ-M4-v1.0-a898475e-s1',
          'demo_mode': true,
          'production_certified': false,
          'inference_timestamp': '2026-09-26T06:28:19Z',
          'latency_ms': 35.6,
        },
        'meta': {'source': 'UZHAVAN M4 v1 Research Checkpoint'},
      };
      final adapter = ScriptedAdapter((_) async => jsonBody(200, demoPayload));
      final c = await container(adapter);
      final ctl = c.read(scanProvider.notifier)..selectCrop('groundnut');
      await ctl.pick(PickSource.camera);
      await tester.runAsync(ctl.submit);
      await showOutcome(tester, c);

      expect(find.byKey(const Key('scan-demo-result')), findsOneWidget);
      expect(find.text('M4 v1 RESEARCH DEMO'), findsOneWidget);
      expect(find.text('NOT PRODUCTION CERTIFIED'), findsOneWidget);
      expect(find.text('Rust'), findsNWidgets(2));
      expect(find.text('62.6 %'), findsNWidgets(2));
      expect(find.text('Low-confidence research prediction'), findsOneWidget);
      expect(find.text('EfficientNetV2-S'), findsOneWidget);
      expect(find.text('UZ-M4-v1.0-a898475e-s1'), findsOneWidget);
      expect(find.text('35.6 ms'), findsOneWidget);
      expect(find.text('Top probabilities'), findsOneWidget);
    });

    test('camera denied → PickDenied; remove clears the image', () async {
      final c = await container(ScriptedAdapter((_) async => jsonBody(200, {})), deny: true);
      await expectLater(c.read(scanProvider.notifier).pick(PickSource.camera), throwsA(isA<PickDenied>()));
      expect(c.read(scanProvider).imagePath, isNull);
    });

    test('paddy is excluded from the scan crop list', () {
      expect(scanExcludedCrops, contains('paddy'));
    });
  });
}

