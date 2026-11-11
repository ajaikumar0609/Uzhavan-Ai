import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/core/networking/api_client.dart';
import 'package:uzhavan/core/networking/providers.dart';
import 'package:uzhavan/core/storage/token_store.dart';
import 'package:uzhavan/features/farm/domain/farm.dart';
import 'package:uzhavan/features/farm/presentation/farms_controller.dart';
import 'package:uzhavan/features/home/presentation/home_screen.dart';
import 'package:uzhavan/features/profile/domain/farmer_profile.dart';
import 'package:uzhavan/features/profile/presentation/profile_controller.dart';

import '../helpers/scripted_adapter.dart';
import '../helpers/test_app.dart';

List<Farm> _farms = const [];

class FakeProfile extends ProfileController {
  @override
  Future<FarmerProfile> build() async => FarmerProfile.fromJson({
        'farmer_id': 'u1',
        'phone': '9876543210',
        'name': 'Test Farmer',
        'district_id': 'thanjavur',
        'preferred_language': 'en',
        'profile_complete': true,
      });
}

class FakeFarms extends FarmsController {
  @override
  Future<List<Farm>> build() async => _farms;
}

Future<ScriptedAdapter> pumpHome(WidgetTester tester) async {
  tester.view.physicalSize = const Size(1080, 9000);
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);
  final adapter = ScriptedAdapter((o) async {
    switch (o.path) {
      case '/api/weather/current':
        return jsonBody(200, {
          'data': {'temperature_c': 30.5, 'humidity_pct': null, 'condition': {'en': 'Clear', 'ta': null}},
          'meta': {'source': 'Open-Meteo', 'kind': 'current', 'retrieved_at': '2026-09-26T04:00:00Z'},
        });
      case '/api/weather/forecast':
        return jsonBody(200, {
          'data': {
            'daily': [
              {'date': '2026-09-26', 'temp_max_c': 34, 'temp_min_c': 25},
              {'date': '2026-09-27', 'temp_max_c': 35, 'temp_min_c': 26},
            ],
          },
          'meta': {'source': 'Open-Meteo', 'kind': 'forecast', 'observed_at': null},
        });
      case '/api/market/latest':
        return jsonBody(200, {
          'data': [
            for (var i = 0; i < 5; i++)
              {
                'commodity': 'banana',
                'commodity_name': {'en': 'Banana', 'ta': null},
                'market': 'Market $i',
                'modal_price': 1000 + i,
                'observed_on': '2026-09-24',
                'stale': false,
              },
          ],
          'meta': {'source': 'AGMARKNET', 'kind': 'latest_observed'},
        });
      case '/api/market/commodities':
        return jsonBody(200, {
          'data': [
            for (final id in ['banana', 'paddy', 'tomato']) {'id': id, 'name': {'en': id, 'ta': null}, 'unit': 'Rs/quintal'},
          ],
        });
      case '/api/diary':
        return jsonBody(200, {
          'data': [
            for (var i = 0; i < 5; i++)
              {'entry_id': 'e$i', 'kind': 'note', 'text': 'Entry $i', 'entry_date': '2026-09-2$i'},
          ],
        });
    }
    return jsonBody(404, errorDetail('not_found'));
  });
  final c = await makeContainer(prefs: {'app.language': 'en'}, overrides: [
    profileProvider.overrideWith(FakeProfile.new),
    farmsProvider.overrideWith(FakeFarms.new),
    apiClientProvider.overrideWithValue(ApiClient(
      baseUrl: 'http://test.local',
      tokenStore: MemoryTokenStore(const AuthTokens(accessToken: 'a', refreshToken: 'r')),
      adapter: adapter,
    )),
  ]);
  addTearDown(c.dispose);
  await tester.pumpWidget(UncontrolledProviderScope(container: c, child: const TestApp(home: HomeScreen())));
  await tester.pumpAndSettle();
  return adapter;
}

void main() {
  testWidgets('real data only: greeting, farm, weather, ≤3 prices, ≤3 diary entries', (tester) async {
    _farms = [
      Farm.fromJson({
        'farm_id': 'f1',
        'name': 'North field',
        'district_id': 'thanjavur',
        'area_ha': 1.011715,
        'crop_id': 'banana',
      }),
    ];
    final adapter = await pumpHome(tester);
    expect(find.text('Hello, Test Farmer'), findsOneWidget);
    expect(find.byKey(const Key('home-farm')), findsOneWidget);
    expect(find.text('North field'), findsOneWidget);
    expect(find.text('2.5 acres'), findsOneWidget);
    expect(find.text('30.5 °C'), findsOneWidget);
    // Today's forecast only on Home.
    expect(find.textContaining('Max 34 °C'), findsOneWidget);
    expect(find.textContaining('Max 35 °C'), findsNothing);
    expect(find.text('Market 0'), findsOneWidget);
    expect(find.text('Market 2'), findsOneWidget);
    expect(find.text('Market 3'), findsNothing);
    expect(find.text('Entry 2'), findsOneWidget);
    expect(find.text('Entry 3'), findsNothing);
    // Market query uses the farm crop + district.
    final market = adapter.requests.firstWhere((r) => r.path == '/api/market/latest');
    expect(market.queryParameters, {'commodity': 'banana', 'district_id': 'thanjavur', 'limit': 3});
    // No invented metrics.
    expect(find.textContaining('score'), findsNothing);
    expect(find.textContaining('task'), findsNothing);
    expect(find.byKey(const Key('home-add-farm')), findsNothing);
  });

  testWidgets('no farm → add-farm CTA; weather falls back to the profile district', (tester) async {
    _farms = const [];
    final adapter = await pumpHome(tester);
    expect(find.byKey(const Key('home-add-farm')), findsOneWidget);
    final weather = adapter.requests.firstWhere((r) => r.path == '/api/weather/current');
    expect(weather.queryParameters, {'district_id': 'thanjavur'});
  });

  testWidgets('farm crop without market data (chilli) → honest empty, no query, no error', (tester) async {
    _farms = [
      Farm.fromJson({'farm_id': 'f2', 'name': 'Chilli plot', 'district_id': 'thanjavur', 'crop_id': 'chilli'}),
    ];
    final adapter = await pumpHome(tester);
    expect(find.byKey(const Key('home-market-no-crop')), findsOneWidget);
    expect(find.text('No market data for this crop'), findsOneWidget);
    expect(adapter.requests.where((r) => r.path == '/api/market/latest'), isEmpty);
    expect(find.byKey(const ValueKey('data-state-error')), findsNothing);
  });
}
