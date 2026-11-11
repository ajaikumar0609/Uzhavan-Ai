import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/core/networking/api_client.dart';
import 'package:uzhavan/core/networking/api_failure.dart';
import 'package:uzhavan/core/storage/token_store.dart';
import 'package:uzhavan/features/schemes/data/scheme_repository.dart';
import 'package:uzhavan/features/schemes/domain/scheme_models.dart';
import 'package:uzhavan/features/schemes/presentation/scheme_detail_screen.dart';

import '../helpers/scripted_adapter.dart';
import '../helpers/test_app.dart';

ApiClient makeApi(ScriptedAdapter adapter) => ApiClient(
      baseUrl: 'http://test.local',
      tokenStore: MemoryTokenStore(const AuthTokens(accessToken: 'a', refreshToken: 'r')),
      adapter: adapter,
    );

Map<String, Object?> elig(String status) => {
      'data': {
        'status': status,
        'reasons': [
          {'en': 'Reason A', 'ta': null},
        ],
        'missing_fields': status == 'more_information_required' ? ['area_ha'] : [],
        'criteria_source_url': 'https://example.gov.in/rules',
      },
      'meta': {'source': 'scheme rules'},
    };

void main() {
  group('SchemeRepository', () {
    test('list sends q/level/crop_id and parses items tolerantly', () async {
      final adapter = ScriptedAdapter((_) async => jsonBody(200, {
            'data': [
              {
                'scheme_id': 's1',
                'name': {'en': 'Scheme One', 'ta': null},
                'authority': 'Dept',
                'level': 'central',
                'active': null,
                'crops': null,
                'official_url': 'https://example.gov.in',
                'extra': true,
              },
            ],
            'meta': {'source': 'Government portals', 'kind': 'reference'},
          }));
      final env = await SchemeRepository(makeApi(adapter))
          .list(const SchemeQuery(q: ' pm ', level: 'central', cropId: 'paddy'));
      expect(env.data.single.schemeId, 's1');
      expect(env.data.single.active, isNull);
      expect(env.data.single.authority?.en, 'Dept');
      expect(adapter.requests.single.queryParameters, {'q': 'pm', 'level': 'central', 'crop_id': 'paddy'});
    });

    test('detail keeps nulls (application_method hidden when null)', () async {
      final adapter = ScriptedAdapter((_) async => jsonBody(200, {
            'data': {
              'scheme_id': 's1',
              'name': {'en': 'Scheme One', 'ta': 'திட்டம்'},
              'level': 'state',
              'description': 'Desc',
              'eligibility_text': null,
              'benefits': {'en': 'B', 'ta': null},
              'application_method': null,
              'required_documents': ['Aadhaar', 'Land record'],
              'official_url': 'https://example.gov.in',
              'source_documents': [
                {'title': 'Guidelines', 'url': 'https://example.gov.in/g.pdf'},
              ],
              'date_checked': '2026-09-01',
              'last_updated_on_source': null,
            },
          }));
      final env = await SchemeRepository(makeApi(adapter)).detail('s1');
      final d = env.data;
      expect(d.description?.en, 'Desc');
      expect(d.eligibilityText, isNull);
      expect(d.applicationMethod, isNull);
      expect(d.requiredDocuments!.map((e) => e.en), ['Aadhaar', 'Land record']);
      expect(d.sourceDocuments.single.url, 'https://example.gov.in/g.pdf');
      expect(d.dateChecked, DateTime(2026, 9, 1));
    });

    test('eligibility parses the 4 statuses; unknown → unrecognized', () async {
      for (final s in EligibilityStatus.values.where((s) => s.wire.isNotEmpty)) {
        expect(EligibilityResult.fromJson(elig(s.wire)['data']).status, s);
      }
      expect(EligibilityResult.fromJson({'status': 'probably'}).status, EligibilityStatus.unrecognized);
    });

    test('503 → unavailable; 401 without refresh → unauthenticated', () async {
      final adapter = ScriptedAdapter((_) async => jsonBody(503, errorDetail('service_unavailable')));
      await expectLater(SchemeRepository(makeApi(adapter)).eligibility('s1', farmId: 'f1'),
          throwsA(isA<ApiFailure>().having((f) => f.kind, 'kind', ApiFailureKind.unavailable)));
      adapter.handler = (_) async => jsonBody(401, errorDetail('unauthenticated'));
      await expectLater(SchemeRepository(makeApi(adapter)).eligibility('s1', farmId: 'f1'),
          throwsA(isA<ApiFailure>().having((f) => f.kind, 'kind', ApiFailureKind.unauthenticated)));
    });
  });

  group('EligibilityCard renders exactly the returned status', () {
    const labels = {
      'eligible_known_criteria': 'You meet the known criteria',
      'not_eligible_known_criteria': 'You do not meet the known criteria',
      'more_information_required': 'More information required',
      'cannot_determine': 'Cannot determine',
    };

    for (final entry in labels.entries) {
      testWidgets(entry.key, (tester) async {
        final adapter = ScriptedAdapter((_) async => jsonBody(200, elig(entry.key)));
        final c = await makeContainer(
          prefs: {'app.language': 'en'},
          overrides: [schemeRepositoryProvider.overrideWithValue(SchemeRepository(makeApi(adapter)))],
        );
        addTearDown(c.dispose);
        await tester.pumpWidget(UncontrolledProviderScope(
          container: c,
          child: const TestApp(home: Scaffold(body: SingleChildScrollView(child: EligibilityCard(schemeId: 's1')))),
        ));
        await tester.pumpAndSettle();
        expect(find.text(entry.value), findsOneWidget);
        for (final other in labels.values.where((v) => v != entry.value)) {
          expect(find.text(other), findsNothing);
        }
        expect(find.text('• Reason A'), findsOneWidget);
        expect(find.text('Criteria source'), findsOneWidget);
        if (entry.key == 'more_information_required') {
          expect(find.text('Land size (acres)'), findsOneWidget);
        }
      });
    }

    testWidgets('an unknown status shows no status label', (tester) async {
      final adapter = ScriptedAdapter((_) async => jsonBody(200, elig('maybe')));
      final c = await makeContainer(
        prefs: {'app.language': 'en'},
        overrides: [schemeRepositoryProvider.overrideWithValue(SchemeRepository(makeApi(adapter)))],
      );
      addTearDown(c.dispose);
      await tester.pumpWidget(UncontrolledProviderScope(
        container: c,
        child: const TestApp(home: Scaffold(body: SingleChildScrollView(child: EligibilityCard(schemeId: 's1')))),
      ));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('elig-unrecognized')), findsOneWidget);
      for (final v in labels.values) {
        expect(find.text(v), findsNothing);
      }
    });

    testWidgets('503 → unavailable state with retry, no status', (tester) async {
      final adapter = ScriptedAdapter((_) async => jsonBody(503, errorDetail('service_unavailable')));
      final c = await makeContainer(
        prefs: {'app.language': 'en'},
        overrides: [schemeRepositoryProvider.overrideWithValue(SchemeRepository(makeApi(adapter)))],
      );
      addTearDown(c.dispose);
      await tester.pumpWidget(UncontrolledProviderScope(
        container: c,
        child: const TestApp(home: Scaffold(body: SingleChildScrollView(child: EligibilityCard(schemeId: 's1')))),
      ));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('data-state-unavailable')), findsOneWidget);
      expect(find.text('Retry'), findsOneWidget);
    });
  });
}
