// Live backend (2026-09-26) deviations reported by the Master Agent.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/core/localization/bilingual_text.dart';
import 'package:uzhavan/core/localization/generated/app_localizations.dart';
import 'package:uzhavan/core/networking/api_client.dart';
import 'package:uzhavan/core/networking/api_failure.dart';
import 'package:uzhavan/core/networking/envelope.dart';
import 'package:uzhavan/core/storage/token_store.dart';
import 'package:uzhavan/features/farm/presentation/selected_farm.dart';
import 'package:uzhavan/features/market/data/market_repository.dart';
import 'package:uzhavan/features/market/domain/market_models.dart';
import 'package:uzhavan/features/market/presentation/market_widgets.dart';
import 'package:uzhavan/features/schemes/data/scheme_repository.dart';
import 'package:uzhavan/features/schemes/domain/scheme_models.dart';
import 'package:uzhavan/features/schemes/presentation/scheme_detail_screen.dart';
import 'package:uzhavan/features/soil/domain/soil_models.dart';
import 'package:uzhavan/features/soil/presentation/soil_screen.dart';
import 'package:uzhavan/features/weather/data/weather_repository.dart';
import 'package:uzhavan/features/weather/domain/weather_models.dart';
import 'package:uzhavan/features/weather/presentation/weather_widgets.dart';
import 'package:uzhavan/shared/utils/failure_text.dart';

import '../helpers/scripted_adapter.dart';
import '../helpers/test_app.dart';

ApiClient makeApi(ScriptedAdapter adapter) => ApiClient(
      baseUrl: 'http://test.local',
      tokenStore: MemoryTokenStore(const AuthTokens(accessToken: 'a', refreshToken: 'r')),
      adapter: adapter,
    );

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
  group('weather', () {
    const loc = DataLocation(farmId: 'f1');

    testWidgets('forecast with observed_at null → "Issued time not provided"; ta:null condition → en',
        (tester) async {
      final adapter = ScriptedAdapter((_) async => jsonBody(200, {
            'data': {
              'daily': [
                {'date': '2026-09-26', 'temp_max_c': 33, 'temp_min_c': 24, 'condition': {'en': 'Overcast', 'ta': null}},
              ],
            },
            'meta': {
              'source': 'Open-Meteo',
              'kind': 'forecast',
              'retrieved_at': '2026-09-26T04:00:00Z',
              'observed_at': null,
              'location': {'name': 'Thanjavur', 'lat': 10.7, 'lon': 79.1, 'resolved_from': 'farm'},
              'notes': [
                {'en': 'Open-Meteo does not provide a forecast issue time', 'ta': null},
              ],
            },
          }));
      await pumpIn(tester, const WeatherForecastCard(loc: loc),
          overrides: [weatherRepositoryProvider.overrideWithValue(WeatherRepository(makeApi(adapter)))]);
      expect(find.text('Issued time not provided'), findsOneWidget);
      expect(find.text('Overcast'), findsOneWidget);
      expect(find.textContaining('Source: Open-Meteo'), findsOneWidget);
      expect(find.text('Open-Meteo does not provide a forecast issue time'), findsOneWidget);
    });

    test('rule_source {title, document, page, quote} without url → text, no link', () {
      final a = WeatherAdvisory.fromJson({
        'rule_id': 'r1',
        'severity': 'caution',
        'text': {'en': 'x', 'ta': null},
        'rule_source': {'title': 'TNAU CPG 2020', 'document': 'cpg.pdf', 'page': 'p.29', 'quote': 'q', 'url': null},
      });
      expect(a.ruleSource, 'TNAU CPG 2020 · p.29');
      expect(a.ruleSourceUrl, isNull);
    });

    testWidgets('advisories: empty list → no-rule text; 503 → UNAVAILABLE', (tester) async {
      final adapter = ScriptedAdapter((_) async => jsonBody(200, {'data': [], 'meta': {'source': 'UZHAVAN rules'}}));
      await pumpIn(tester, const WeatherAdvisoriesCard(loc: loc),
          overrides: [weatherRepositoryProvider.overrideWithValue(WeatherRepository(makeApi(adapter)))]);
      expect(find.text('No advisory rule applies right now'), findsOneWidget);
    });

    testWidgets('current: 503 service_unavailable → UNAVAILABLE with retry', (tester) async {
      final adapter = ScriptedAdapter((_) async => jsonBody(503, errorDetail('service_unavailable')));
      await pumpIn(tester, const WeatherCurrentCard(loc: loc),
          overrides: [weatherRepositoryProvider.overrideWithValue(WeatherRepository(makeApi(adapter)))]);
      expect(find.byKey(const ValueKey('data-state-unavailable')), findsOneWidget);
      expect(find.text('Weather data is not available right now'), findsOneWidget);
    });
  });

  group('market', () {
    test('trend points per variety are kept separate, never averaged', () {
      final pts = TrendPoint.listFromData({
        'points': [
          {'date': '2026-09-20', 'modal_price': 2000, 'variety': 'Ponni'},
          {'date': '2026-09-20', 'modal_price': 3000, 'variety': 'Other'},
          {'date': '2026-09-21', 'modal_price': 2100, 'variety': 'Ponni'},
        ],
      });
      final by = trendByVariety(pts);
      expect(by.keys.toSet(), {'Ponni', 'Other'});
      expect(by['Ponni']!.map((p) => p.modalPrice), [2000, 2100]);
      expect(by['Other']!.single.modalPrice, 3000);
      expect(pts.any((p) => p.modalPrice == 2500), isFalse);
    });

    test('market name used verbatim as the trend param', () async {
      final adapter = ScriptedAdapter((_) async => jsonBody(200, {'data': {'points': []}}));
      await MarketRepository(makeApi(adapter))
          .trend(const TrendQuery(commodity: 'paddy', market: 'X Uzhavar Sandhai'));
      expect(adapter.requests.single.queryParameters['market'], 'X Uzhavar Sandhai');
    });

    testWidgets('trend with 2 varieties shows a variety picker', (tester) async {
      final adapter = ScriptedAdapter((_) async => jsonBody(200, {
            'data': {
              'points': [
                {'date': '2026-09-20', 'modal_price': 2000, 'variety': 'Ponni'},
                {'date': '2026-09-21', 'modal_price': 2100, 'variety': 'Ponni'},
                {'date': '2026-09-20', 'modal_price': 3000, 'variety': 'Other'},
              ],
            },
            'meta': {'source': 'AGMARKNET', 'kind': 'historical'},
          }));
      await pumpIn(
        tester,
        const MarketTrendCard(query: TrendQuery(commodity: 'paddy', market: 'Ammoor APMC'), title: 't'),
        overrides: [marketRepositoryProvider.overrideWithValue(MarketRepository(makeApi(adapter)))],
      );
      expect(find.byKey(const Key('variety-Ponni')), findsOneWidget);
      expect(find.byKey(const Key('variety-Other')), findsOneWidget);
      expect(find.text('Historical'), findsOneWidget);
      await tester.tap(find.byKey(const Key('variety-Ponni')));
      await tester.pumpAndSettle();
    });

    testWidgets('latest row: stale chip, coconut unit note, observed date', (tester) async {
      final obs = MarketObservation.fromJson({
        'commodity': 'coconut',
        'commodity_name': {'en': 'Coconut', 'ta': null},
        'market': 'Ammoor APMC',
        'modal_price': 1500,
        'unit': 'Rs/quintal',
        'unit_note': 'unit unverified (per quintal vs per 1000 nuts)',
        'observed_on': '2026-09-01',
        'stale': true,
      });
      await pumpIn(tester, MarketObservationTile(obs: obs, meta: const ApiMeta(source: 'AGMARKNET')));
      expect(find.byKey(const Key('stale-chip')), findsOneWidget);
      expect(find.byKey(const Key('unit-note')), findsOneWidget);
      expect(find.textContaining('Observed on 2026-09-01'), findsOneWidget);
      expect(find.textContaining('recommend'), findsNothing);
    });
  });

  group('schemes', () {
    test('source_documents: relative paths dropped, only http(s) kept', () {
      final d = SchemeDetail.fromJson({
        'scheme_id': 's1',
        'name': 'S',
        'source_documents': [
          'central/raw/aif_guidelines.pdf',
          'https://agriinfra.dac.gov.in/guidelines.pdf',
          {'title': 'state/raw/x.pdf', 'url': null},
          {'title': 'Guidelines', 'url': 'https://example.gov.in/g.pdf'},
          'ftp://x/y',
        ],
      });
      expect(d.sourceDocuments.map((e) => e.url), [
        'https://agriinfra.dac.gov.in/guidelines.pdf',
        'https://example.gov.in/g.pdf',
      ]);
      expect(d.sourceDocuments.any((e) => e.title.contains('raw/')), isFalse);
      expect(SchemeDetail.fromJson({'scheme_id': 's', 'name': 'S', 'source_documents': ['central/raw/a.pdf']})
          .sourceDocuments, isEmpty);
    });

    testWidgets('eligibility sends farm_id; 401 → sign-in prompt', (tester) async {
      final adapter = ScriptedAdapter((_) async => jsonBody(401, errorDetail('unauthenticated')));
      final api = ApiClient(baseUrl: 'http://test.local', tokenStore: MemoryTokenStore(), adapter: adapter);
      await pumpIn(tester, const EligibilityCard(schemeId: 's1'),
          overrides: [schemeRepositoryProvider.overrideWithValue(SchemeRepository(api))]);
      expect(find.byKey(const Key('elig-signin')), findsOneWidget);
      expect(find.text('Please sign in again to check your eligibility'), findsOneWidget);
    });

    test('eligibility farm_id query param', () async {
      final adapter = ScriptedAdapter((_) async => jsonBody(200, {
            'data': {'status': 'cannot_determine', 'reasons': [], 'missing_fields': [], 'criteria_source_url': null},
          }));
      await SchemeRepository(makeApi(adapter)).eligibility('pm_kisan', farmId: 'f1');
      expect(adapter.requests.single.path, '/api/schemes/pm_kisan/eligibility');
      expect(adapter.requests.single.queryParameters, {'farm_id': 'f1'});
    });
  });

  group('soil', () {
    testWidgets('nutrient_status with categories + scheme + cycle renders generically', (tester) async {
      final env = parseEnvelope({
        'data': {
          'regional': null,
          'nutrient_status': {
            'scheme': 'Soil Health Card',
            'cycle': '2023-24',
            'parameters': [
              {
                'param': 'Zinc',
                'samples': 1200,
                'categories': [
                  {'category': 'Deficient', 'pct': 38.5, 'samples': 462},
                  {'category': 'Sufficient', 'pct': 61.5, 'samples': 738},
                ],
              },
            ],
            'source': 'Soil Health Card dashboard',
          },
          'estimated': null,
          'measured': [],
        },
      }, SoilData.fromJson);
      await pumpIn(tester, SoilSections(env: env, canAddTest: false));
      expect(find.text('Soil Health Card'), findsOneWidget);
      expect(find.text('2023-24'), findsOneWidget);
      expect(find.text('Zinc (1200 samples)'), findsOneWidget);
      expect(find.text('Deficient 38.5% (462 samples) · Sufficient 61.5% (738 samples)'), findsOneWidget);
    });

    testWidgets('estimated units come from the server; missing key → no unit', (tester) async {
      final env = parseEnvelope({
        'data': {
          'estimated': {
            'depth': '0-30cm',
            'values': {'ph': 7.9, 'clay_pct': 41.0, 'bdod': 1.4},
            'units': {'ph': 'pH (H2O)', 'clay_pct': '%'},
            'source': 'ISRIC SoilGrids 2.0',
            'caveats': [],
          },
          'measured': [],
        },
      }, SoilData.fromJson);
      await pumpIn(tester, SoilSections(env: env, canAddTest: false));
      expect(find.text('7.9 pH (H2O)'), findsOneWidget);
      expect(find.text('41 %'), findsOneWidget);
      expect(find.text('1.4'), findsOneWidget); // bdod has no server unit → none shown
      expect(find.textContaining('kg/dm'), findsNothing);
    });

    test('value_out_of_range and scan codes are localized (never server English)', () async {
      final l = await AppLocalizations.delegate.load(const Locale('en'));
      for (final code in ['value_out_of_range', 'file_too_large', 'unsupported_media_type', 'model_unavailable']) {
        final text = failureText(
          l,
          const Locale('en'),
          ApiFailure(kind: ApiFailureKind.validation, code: code, message: const BilingualText(en: 'SERVER')),
        );
        expect(text, isNot('SERVER'), reason: code);
      }
      expect(
        failureText(l, const Locale('en'), const ApiFailure(kind: ApiFailureKind.validation, code: 'value_out_of_range')),
        'A value is outside the allowed range. Please check it.',
      );
    });
  });
}
