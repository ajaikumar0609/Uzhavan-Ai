import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/core/localization/generated/app_localizations.dart';
import 'package:uzhavan/core/networking/api_client.dart';
import 'package:uzhavan/core/networking/api_failure.dart';
import 'package:uzhavan/core/networking/envelope.dart';
import 'package:uzhavan/core/storage/token_store.dart';
import 'package:uzhavan/features/diary/data/diary_repository.dart';
import 'package:uzhavan/features/diary/domain/diary_models.dart';
import 'package:uzhavan/features/farm/presentation/selected_farm.dart';
import 'package:uzhavan/features/satellite/data/satellite_repository.dart';
import 'package:uzhavan/features/satellite/presentation/satellite_screen.dart';
import 'package:uzhavan/features/soil/data/soil_repository.dart';
import 'package:uzhavan/features/soil/domain/soil_models.dart';
import 'package:uzhavan/features/soil/presentation/soil_screen.dart';
import 'package:uzhavan/features/soil/presentation/soil_test_form_screen.dart';

import '../helpers/scripted_adapter.dart';
import '../helpers/test_app.dart';

ApiClient makeApi(ScriptedAdapter adapter) => ApiClient(
      baseUrl: 'http://test.local',
      tokenStore: MemoryTokenStore(const AuthTokens(accessToken: 'a', refreshToken: 'r')),
      adapter: adapter,
    );

final soilBody = {
  'data': {
    'regional': {
      'soil_types': [
        {'name': {'en': 'Alluvial', 'ta': null}},
      ],
      'source': 'TN Agriculture Dept (Tamil Mannvalam)',
      'kind': 'reference',
    },
    'nutrient_status': null,
    'estimated': {
      'depth': '0-30cm',
      'values': {'ph': 7.9, 'soc_g_kg': null, 'clay_pct': 41.0},
      'source': 'ISRIC SoilGrids 2.0',
      'kind': 'estimated',
      'caveats': [
        {'en': '250 m model estimate', 'ta': null},
      ],
    },
    'measured': [
      {
        'test_id': 't1',
        'farm_id': 'f1',
        'sample_date': '2026-08-01',
        'lab_name': 'Soil lab',
        'ph': 6.4,
        'n_kg_ha': 210,
        'kind': 'measured',
      },
    ],
  },
  'meta': {'source': 'mixed', 'kind': 'reference'},
};

Future<void> pumpIn(WidgetTester tester, Widget child, {List overrides = const []}) async {
  final c = await makeContainer(prefs: {'app.language': 'en'}, overrides: overrides);
  addTearDown(c.dispose);
  await tester.pumpWidget(UncontrolledProviderScope(
    container: c,
    child: TestApp(home: Scaffold(body: SingleChildScrollView(child: child))),
  ));
  await tester.pumpAndSettle();
}

void main() {
  group('SoilRepository', () {
    test('parses the 3 sections independently; nulls kept', () async {
      final adapter = ScriptedAdapter((_) async => jsonBody(200, soilBody));
      final env = await SoilRepository(makeApi(adapter)).soil(const DataLocation(farmId: 'f1'));
      expect(env.data.regional!.soilTypes.single.en, 'Alluvial');
      expect(env.data.nutrientStatus, isNull);
      expect(env.data.estimated!.values['ph'], 7.9);
      expect(env.data.estimated!.values['soc_g_kg'], isNull);
      expect(env.data.estimated!.values['nitrogen'], isNull);
      expect(env.data.measured.single.values['n_kg_ha'], 210);
      expect(env.data.measured.single.values['ph'], 6.4);
      expect(adapter.requests.single.queryParameters, {'farm_id': 'f1'});
    });

    test('addTest posts every field (null when empty) and accepts a bare 201', () async {
      final adapter = ScriptedAdapter((_) async => jsonBody(201, (soilBody['data'] as Map)['measured'][0]));
      final t = await SoilRepository(makeApi(adapter)).addTest(SoilTestInput(
        farmId: 'f1',
        sampleDate: DateTime(2026, 8, 1),
        labName: '  ',
        values: const {'ph': 6.4},
      ));
      expect(t.testId, 't1');
      final sent = adapter.requests.single.data as Map;
      expect(sent['sample_date'], '2026-08-01');
      expect(sent['lab_name'], isNull);
      expect(sent['ph'], 6.4);
      expect(sent.containsKey('b_ppm'), isTrue);
      expect(sent['b_ppm'], isNull);
    });

    test('400 range error → validation; 503 → unavailable', () async {
      final adapter = ScriptedAdapter((_) async => jsonBody(400, errorDetail('invalid_soil_value')));
      await expectLater(
        SoilRepository(makeApi(adapter)).addTest(SoilTestInput(farmId: 'f1', sampleDate: DateTime(2026), values: const {})),
        throwsA(isA<ApiFailure>().having((f) => f.kind, 'kind', ApiFailureKind.validation)),
      );
      adapter.handler = (_) async => jsonBody(503, errorDetail('service_unavailable'));
      await expectLater(SoilRepository(makeApi(adapter)).soil(const DataLocation(districtId: 'x')),
          throwsA(isA<ApiFailure>().having((f) => f.kind, 'kind', ApiFailureKind.unavailable)));
    });

    test('form range validation', () async {
      final l = await AppLocalizations.delegate.load(const Locale('en'));
      const ph = SoilParam('ph', '', 0, 14);
      expect(validateSoilValue(l, ph, ''), isNull);
      expect(validateSoilValue(l, ph, '6.5'), isNull);
      expect(validateSoilValue(l, ph, '15'), isNotNull);
      expect(validateSoilValue(l, ph, 'abc'), isNotNull);
    });
  });

  testWidgets('soil sections never mix estimated and measured values', (tester) async {
    final env = parseEnvelope(soilBody, SoilData.fromJson);
    await pumpIn(tester, SoilSections(env: env, canAddTest: true));

    final estimated = find.byKey(const Key('soil-estimated'));
    final measured = find.byKey(const Key('soil-measured'));
    final regional = find.byKey(const Key('soil-regional'));
    expect(estimated, findsOneWidget);
    expect(measured, findsOneWidget);
    expect(regional, findsOneWidget);

    // Estimated pH 7.9 and clay only in the estimated card, with caveats.
    expect(find.descendant(of: estimated, matching: find.text('7.9')), findsOneWidget);
    expect(find.descendant(of: measured, matching: find.text('7.9')), findsNothing);
    expect(find.descendant(of: estimated, matching: find.byKey(const Key('soil-caveats'))), findsOneWidget);
    expect(find.descendant(of: estimated, matching: find.text('• 250 m model estimate')), findsOneWidget);
    // Measured pH 6.4 and N only in the measured card.
    expect(find.descendant(of: measured, matching: find.text('6.4')), findsOneWidget);
    expect(find.descendant(of: estimated, matching: find.text('6.4')), findsNothing);
    expect(find.descendant(of: measured, matching: find.text('210 kg/ha')), findsOneWidget);
    // Regional has no numbers from either.
    expect(find.descendant(of: regional, matching: find.text('7.9')), findsNothing);
    expect(find.descendant(of: regional, matching: find.text('6.4')), findsNothing);
    // Null estimated value → not available, never 0.
    expect(find.descendant(of: estimated, matching: find.text('Not available')), findsWidgets);
  });

  group('DiaryRepository', () {
    test('list is enveloped; question/scan kinds kept', () async {
      final adapter = ScriptedAdapter((_) async => jsonBody(200, {
            'data': [
              {
                'entry_id': 'e1',
                'farm_id': null,
                'kind': 'scan',
                'text': 'scan submitted',
                'amount_inr': null,
                'entry_date': '2026-09-25',
                'created_at': '2026-09-25T10:30:00Z',
                'ref': {'status': 'model_unavailable'},
              },
            ],
          }));
      final list = await DiaryRepository(makeApi(adapter)).list();
      expect(list.single.kind, 'scan');
      expect(list.single.amountInr, isNull);
      expect(adapter.requests.single.queryParameters, {'limit': 50});
    });

    test('add sends amount only for money kinds', () {
      final note = DiaryInput(kind: 'note', text: ' hi ', entryDate: DateTime(2026, 9, 25), amountInr: 5).toJson();
      expect(note, {'kind': 'note', 'text': 'hi', 'entry_date': '2026-09-25'});
      final exp = DiaryInput(kind: 'expense', text: 'urea', entryDate: DateTime(2026, 9, 25), farmId: 'f1', amountInr: 350)
          .toJson();
      expect(exp['amount_inr'], 350);
      expect(exp['farm_id'], 'f1');
    });

    test('401 → unauthenticated; network 503 → unavailable', () async {
      final adapter = ScriptedAdapter((_) async => jsonBody(401, errorDetail('unauthenticated')));
      await expectLater(DiaryRepository(makeApi(adapter)).list(),
          throwsA(isA<ApiFailure>().having((f) => f.kind, 'kind', ApiFailureKind.unauthenticated)));
      adapter.handler = (_) async => jsonBody(503, errorDetail('service_unavailable'));
      await expectLater(DiaryRepository(makeApi(adapter)).list(),
          throwsA(isA<ApiFailure>().having((f) => f.kind, 'kind', ApiFailureKind.unavailable)));
    });
  });

  group('Satellite', () {
    final body = {
      'data': {
        'available': false,
        'reason': 'under_validation',
        'gates': {
          'licence': false,
          'units': false,
          'geography_scope': 'Cauvery Delta only',
          'independent_evaluation': 'baseline only (val, 14 plots)',
        },
      },
      'meta': {'source': 'UZHAVAN model registry', 'kind': 'reference'},
    };

    test('repository parses status + gates', () async {
      final adapter = ScriptedAdapter((_) async => jsonBody(200, body));
      final env = await SatelliteRepository(makeApi(adapter)).status();
      expect(env.data.available, isFalse);
      expect(env.data.gates['geography_scope'], 'Cauvery Delta only');
    });

    testWidgets('under validation with the 4 gates, no predictions', (tester) async {
      final env = parseEnvelope(body, SatelliteStatus.fromJson);
      await pumpIn(tester, SatelliteStatusCard(env: env));
      expect(find.text('Satellite intelligence under validation'), findsOneWidget);
      expect(find.text('Data licence'), findsOneWidget);
      expect(find.text('Units verified'), findsOneWidget);
      expect(find.text('Geographic scope'), findsOneWidget);
      expect(find.text('Independent evaluation'), findsOneWidget);
      expect(find.text('Cauvery Delta only'), findsOneWidget);
      expect(find.text('Not passed yet'), findsNWidgets(2));
    });
  });
}
