import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/core/networking/api_client.dart';
import 'package:uzhavan/core/networking/api_failure.dart';
import 'package:uzhavan/core/storage/token_store.dart';
import 'package:uzhavan/features/farm/presentation/selected_farm.dart';
import 'package:uzhavan/features/market/data/market_repository.dart';
import 'package:uzhavan/features/market/domain/market_models.dart';
import 'package:uzhavan/features/weather/data/weather_repository.dart';

import '../helpers/scripted_adapter.dart';

Map<String, Object?> meta({String kind = 'current', List<Object?> notes = const []}) => {
      'source': 'Open-Meteo',
      'source_url': 'https://open-meteo.com',
      'kind': kind,
      'retrieved_at': '2026-09-25T10:30:00Z',
      'observed_at': '2026-09-25T10:15:00Z',
      'location': {'name': 'Thanjavur', 'lat': 10.787, 'lon': 79.138},
      'notes': notes,
      'future_field': 1,
    };

void main() {
  late ScriptedAdapter adapter;
  late ApiClient api;

  setUp(() {
    adapter = ScriptedAdapter((_) async => jsonBody(200, {}));
    api = ApiClient(
      baseUrl: 'http://test.local',
      tokenStore: MemoryTokenStore(const AuthTokens(accessToken: 'a', refreshToken: 'r')),
      adapter: adapter,
    );
  });

  group('WeatherRepository', () {
    const farmLoc = DataLocation(farmId: 'f1');
    const districtLoc = DataLocation(districtId: 'thanjavur');

    test('current: envelope + meta kept, nulls stay null, extra fields ignored', () async {
      adapter.handler = (_) async => jsonBody(200, {
            'data': {
              'temperature_c': 31.2,
              'apparent_temperature_c': null,
              'humidity_pct': 70,
              'precipitation_mm': 0,
              'wind_speed_kmph': 12.5,
              'wind_direction_deg': null,
              'weather_code': 2,
              'condition': {'en': 'Partly cloudy', 'ta': null},
              'is_day': true,
              'unknown': 'x',
            },
            'meta': meta(),
          });
      final env = await WeatherRepository(api).current(farmLoc);
      expect(env.data.temperatureC, 31.2);
      expect(env.data.apparentTemperatureC, isNull);
      expect(env.data.windDirectionDeg, isNull);
      expect(env.meta.source, 'Open-Meteo');
      expect(env.meta.kind, 'current');
      expect(env.meta.location?.name, 'Thanjavur');
      expect(env.meta.retrievedAt, DateTime.utc(2026, 9, 25, 10, 30));
      expect(adapter.requests.single.path, '/api/weather/current');
      expect(adapter.requests.single.queryParameters, {'farm_id': 'f1'});
    });

    test('forecast: daily list, district location, days=7', () async {
      adapter.handler = (_) async => jsonBody(200, {
            'data': {
              'daily': [
                {
                  'date': '2026-09-25',
                  'temp_max_c': 33,
                  'temp_min_c': 24,
                  'precipitation_mm': 1.2,
                  'precipitation_probability_pct': null,
                  'wind_max_kmph': 20,
                  'weather_code': 61,
                  'condition': {'en': 'Rain', 'ta': 'மழை'},
                },
              ],
            },
            'meta': meta(kind: 'forecast'),
          });
      final env = await WeatherRepository(api).forecast(districtLoc);
      expect(env.data.single.date, DateTime(2026, 9, 25));
      expect(env.data.single.precipitationProbabilityPct, isNull);
      expect(env.meta.kind, 'forecast');
      expect(adapter.requests.single.queryParameters, {'district_id': 'thanjavur', 'days': 7});
    });

    test('advisories: empty list is valid; notes parsed; rule source kept', () async {
      adapter.handler = (_) async => jsonBody(200, {
            'data': [
              {
                'rule_id': 'heavy_rain',
                'severity': 'caution',
                'text': {'en': 'x', 'ta': null},
                'evidence': {'precipitation_mm': 70},
                'rule_source': 'TNAU Agritech Portal',
              },
            ],
            'meta': meta(notes: [
              {'en': 'Official IMD warnings not integrated', 'ta': null},
            ]),
          });
      final env = await WeatherRepository(api).advisories(farmLoc);
      expect(env.data.single.ruleSource, 'TNAU Agritech Portal');
      expect(env.data.single.severity, 'caution');
      expect(env.meta.notes.single.en, 'Official IMD warnings not integrated');

      adapter.handler = (_) async => jsonBody(200, {'data': [], 'meta': meta()});
      expect((await WeatherRepository(api).advisories(farmLoc)).data, isEmpty);
    });

    test('503 service_unavailable → unavailable', () async {
      adapter.handler = (_) async => jsonBody(503, errorDetail('service_unavailable'));
      await expectLater(
        WeatherRepository(api).current(farmLoc),
        throwsA(isA<ApiFailure>()
            .having((f) => f.kind, 'kind', ApiFailureKind.unavailable)
            .having((f) => f.code, 'code', 'service_unavailable')),
      );
    });

    test('500 → error; body without envelope → malformed_response', () async {
      adapter.handler = (_) async => jsonBody(500, {'detail': 'boom'});
      await expectLater(WeatherRepository(api).forecast(farmLoc),
          throwsA(isA<ApiFailure>().having((f) => f.kind, 'kind', ApiFailureKind.error)));
      adapter.handler = (_) async => jsonBody(200, {'temperature_c': 1});
      await expectLater(WeatherRepository(api).current(farmLoc),
          throwsA(isA<ApiFailure>().having((f) => f.code, 'code', 'malformed_response')));
    });
  });

  group('MarketRepository', () {
    test('commodities keep the coconut unit_note', () async {
      adapter.handler = (_) async => jsonBody(200, {
            'data': [
              {'id': 'paddy', 'name': {'en': 'Paddy', 'ta': 'நெல்'}, 'unit': 'Rs/quintal', 'unit_note': null},
              {
                'id': 'coconut',
                'name': {'en': 'Coconut', 'ta': null},
                'unit': 'Rs/quintal',
                'unit_note': 'unit unverified (per quintal vs per 1000 nuts)',
              },
            ],
          });
      final env = await MarketRepository(api).commodities();
      expect(env.data.first.unitNote, isNull);
      expect(env.data.last.unitNote?.en, contains('unit unverified'));
    });

    test('latest: query params, nulls kept, stale flag', () async {
      adapter.handler = (_) async => jsonBody(200, {
            'data': [
              {
                'commodity': 'paddy',
                'commodity_name': {'en': 'Paddy', 'ta': 'நெல்'},
                'variety': null,
                'market': 'Test market',
                'district_id': 'thanjavur',
                'modal_price': 2100.5,
                'min_price': null,
                'max_price': null,
                'unit': 'Rs/quintal',
                'arrivals_tonnes': null,
                'observed_on': '2026-09-01',
                'stale': true,
              },
            ],
            'meta': {'source': 'Agmarknet', 'kind': 'latest_observed'},
          });
      final env = await MarketRepository(api)
          .latest(const LatestQuery(commodity: 'paddy', districtId: 'thanjavur'));
      final o = env.data.single;
      expect(o.modalPrice, 2100.5);
      expect(o.minPrice, isNull);
      expect(o.serverStale, isTrue);
      expect(o.observedOn, DateTime(2026, 9, 1));
      expect(env.meta.kind, 'latest_observed');
      expect(adapter.requests.single.queryParameters,
          {'commodity': 'paddy', 'district_id': 'thanjavur', 'limit': 20});
    });

    test('trend: points sorted, rows without price dropped', () async {
      adapter.handler = (_) async => jsonBody(200, {
            'data': {
              'points': [
                {'date': '2026-09-20', 'modal_price': 2000},
                {'date': '2026-09-10', 'modal_price': 1900},
                {'date': '2026-09-15', 'modal_price': null},
              ],
            },
            'meta': {'kind': 'historical'},
          });
      final env = await MarketRepository(api)
          .trend(const TrendQuery(commodity: 'paddy', market: 'Test market'));
      expect(env.data.map((p) => p.modalPrice), [1900, 2000]);
      expect(adapter.requests.single.queryParameters,
          {'commodity': 'paddy', 'market': 'Test market', 'days': 90});
    });

    test('404 → unavailable, 422 → validation', () async {
      adapter.handler = (_) async => jsonBody(404, errorDetail('not_found'));
      await expectLater(MarketRepository(api).commodities(),
          throwsA(isA<ApiFailure>().having((f) => f.kind, 'kind', ApiFailureKind.unavailable)));
      adapter.handler = (_) async => jsonBody(422, {'detail': []});
      await expectLater(MarketRepository(api).latest(const LatestQuery()),
          throwsA(isA<ApiFailure>().having((f) => f.kind, 'kind', ApiFailureKind.validation)));
    });
  });

  group('market stale logic', () {
    final now = DateTime(2026, 9, 25, 9);
    test('server flag wins', () {
      expect(isMarketStale(DateTime(2026, 9, 24), serverStale: true, now: now), isTrue);
    });
    test('7 days old is fresh, 8 days is stale', () {
      expect(isMarketStale(DateTime(2026, 9, 18), now: now), isFalse);
      expect(isMarketStale(DateTime(2026, 9, 17), now: now), isTrue);
    });
    test('yesterday is fresh; unknown date is stale', () {
      expect(isMarketStale(DateTime(2026, 9, 24), now: now), isFalse);
      expect(isMarketStale(null, now: now), isTrue);
    });
  });
}
