import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/core/localization/bilingual_text.dart';
import 'package:uzhavan/core/localization/generated/app_localizations.dart';
import 'package:uzhavan/core/networking/api_client.dart';
import 'package:uzhavan/core/networking/api_failure.dart';
import 'package:uzhavan/core/storage/token_store.dart';
import 'package:uzhavan/features/farm/data/farm_repository.dart';
import 'package:uzhavan/features/farm/domain/farm.dart';
import 'package:uzhavan/features/meta/data/meta_repository.dart';
import 'package:uzhavan/features/profile/data/profile_repository.dart';
import 'package:uzhavan/features/profile/domain/farmer_profile.dart';
import 'package:uzhavan/shared/utils/failure_text.dart';

import '../helpers/scripted_adapter.dart';

Map<String, Object?> farmJson({String id = 'f1'}) => {
      'farm_id': id,
      'name': 'North field',
      'district_id': 'thanjavur',
      'village': null,
      'latitude': 10.78,
      'longitude': 79.13,
      'area_ha': 1.011715,
      'crop_id': 'paddy',
      'crop_stage_id': null,
      'season_id': 'kharif',
      'irrigation_type_id': null,
      'boundary_geojson': null,
      'created_at': '2026-09-25T10:30:00Z',
      'updated_at': '2026-09-25T10:30:00Z',
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

  group('FarmRepository (deployed shapes)', () {
    test('GET /api/farms is enveloped', () async {
      adapter.handler = (_) async => jsonBody(200, {
            'data': [farmJson()],
          });
      final farms = await FarmRepository(api).list();
      expect(farms.single.name, 'North field');
      expect(farms.single.areaHa, 1.011715);
    });

    test('POST returns the bare Farm (201) and sends hectares', () async {
      adapter.handler = (_) async => jsonBody(201, farmJson(id: 'f9'));
      final farm = await FarmRepository(api).create(const FarmInput(
        name: 'North field',
        districtId: 'thanjavur',
        areaAcres: 2.5,
      ));
      expect(farm.farmId, 'f9');
      final sent = adapter.requests.single.data as Map;
      expect(sent['area_ha'], closeTo(1.011715, 1e-9));
      expect(sent.containsKey('boundary_geojson'), isFalse);
    });

    test('PUT returns the bare Farm', () async {
      adapter.handler = (_) async => jsonBody(200, farmJson());
      final farm = await FarmRepository(api)
          .update('f1', const FarmInput(name: 'North field', districtId: 'thanjavur'));
      expect(farm.farmId, 'f1');
      expect(adapter.requests.single.method, 'PUT');
      expect(adapter.requests.single.path, '/api/farms/f1');
    });

    test('DELETE → 204', () async {
      adapter.handler = (_) async => jsonBody(204, null);
      await FarmRepository(api).delete('f1');
      expect(adapter.requests.single.method, 'DELETE');
    });

    test("another farmer's farm → 404 → unavailable/not_found", () async {
      adapter.handler = (_) async => jsonBody(404, errorDetail('not_found'));
      await expectLater(
        FarmRepository(api).delete('other'),
        throwsA(isA<ApiFailure>().having((f) => f.code, 'code', 'not_found')),
      );
    });

    test('farm_limit_reached (409) keeps its code', () async {
      adapter.handler = (_) async => jsonBody(409, errorDetail('farm_limit_reached'));
      await expectLater(
        FarmRepository(api).create(const FarmInput(name: 'x', districtId: 'thanjavur')),
        throwsA(isA<ApiFailure>()
            .having((f) => f.code, 'code', 'farm_limit_reached')
            .having((f) => f.kind, 'kind', ApiFailureKind.validation)),
      );
    });
  });

  group('ProfileRepository (deployed shapes)', () {
    final profile = {
      'farmer_id': 'u1',
      'phone': '9876543210',
      'name': null,
      'district_id': null,
      'village': null,
      'preferred_language': 'ta',
      'profile_complete': false,
      'created_at': '2026-09-25T10:30:00Z',
      'updated_at': '2026-09-25T10:30:00Z',
    };

    test('GET and PUT are enveloped', () async {
      adapter.handler = (o) async => jsonBody(200, {
            'data': o.method == 'PUT'
                ? {...profile, 'name': 'Test', 'district_id': 'thanjavur', 'profile_complete': true}
                : profile,
          });
      final repo = ProfileRepository(api);
      final p = await repo.fetch();
      expect(p.name, isNull);
      expect(p.profileComplete, isFalse);
      final saved = await repo.update(const ProfileUpdate(name: 'Test', districtId: 'thanjavur'));
      expect(saved.profileComplete, isTrue);
      expect(adapter.requests.last.data, {'name': 'Test', 'district_id': 'thanjavur'});
    });
  });

  test('meta enums with ta:null render English in Tamil mode', () async {
    adapter.handler = (_) async => jsonBody(200, {
          'data': {
            'crop_stages': [],
            'seasons': [
              {'id': 'kharif', 'name': {'en': 'Kharif', 'ta': null}},
              {'id': 'samba', 'name': {'en': 'Samba', 'ta': 'சம்பா'}},
            ],
            'irrigation_types': [],
            'diary_kinds': [
              {'id': 'scan', 'name': {'en': 'Scan', 'ta': null}},
            ],
          },
        });
    final enums = await MetaRepository(api).enums();
    expect(enums.seasons.first.name.resolve(const Locale('ta')), 'Kharif');
    expect(enums.seasons.last.name.resolve(const Locale('ta')), 'சம்பா');
    expect(enums.diaryKinds.single.name.resolve(const Locale('ta')), 'Scan');
  });

  group('failureText localizes every server code (message.ta is always null)', () {
    for (final lang in ['ta', 'en']) {
      test(lang, () async {
        final l = await AppLocalizations.delegate.load(Locale(lang));
        const serverEnglish = 'SERVER ENGLISH';
        for (final code in localizedErrorCodes) {
          final f = ApiFailure(
            kind: ApiFailureKind.validation,
            code: code,
            message: const BilingualText(en: serverEnglish),
          );
          final text = failureText(l, Locale(lang), f);
          expect(text, isNot(serverEnglish), reason: code);
          expect(text, isNot(l.errValidation), reason: '$code should have its own string');
        }
        // Unknown code: the server English is the last resort.
        final unknown = failureText(
          l,
          Locale(lang),
          const ApiFailure(
            kind: ApiFailureKind.validation,
            code: 'brand_new_code',
            message: BilingualText(en: 'SERVER ENGLISH'),
          ),
        );
        expect(unknown, serverEnglish);
      });
    }
  });
}
