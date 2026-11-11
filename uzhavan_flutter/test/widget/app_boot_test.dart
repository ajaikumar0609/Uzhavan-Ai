import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:uzhavan/app.dart';
import 'package:uzhavan/core/networking/api_failure.dart';
import 'package:uzhavan/core/storage/token_store.dart';
import 'package:uzhavan/features/meta/data/meta_repository.dart';
import 'package:uzhavan/features/profile/data/profile_repository.dart';
import 'package:uzhavan/features/profile/domain/farmer_profile.dart';

import '../helpers/test_app.dart';

class MockProfileRepository extends Mock implements ProfileRepository {}

class MockMetaRepository extends Mock implements MetaRepository {}

void main() {
  testWidgets('no stored session → login screen in Tamil', (tester) async {
    final c = await makeContainer();
    addTearDown(c.dispose);
    await tester.pumpWidget(UncontrolledProviderScope(container: c, child: const UzhavanApp()));
    await tester.pumpAndSettle();
    expect(find.text('உள்நுழைக'), findsOneWidget);
    expect(find.text('தமிழ் → English'), findsOneWidget);
  });

  testWidgets('stored session with incomplete profile → onboarding, no placeholder name',
      (tester) async {
    final profiles = MockProfileRepository();
    final meta = MockMetaRepository();
    when(profiles.fetch).thenAnswer((_) async => const FarmerProfile(
          farmerId: 'f1',
          phone: '9876543210',
          preferredLanguage: 'ta',
          profileComplete: false,
        ));
    when(meta.districts).thenThrow(
        const ApiFailure(kind: ApiFailureKind.unavailable, code: ApiFailure.networkCode));
    final c = await makeContainer(
      tokenStore: MemoryTokenStore(const AuthTokens(accessToken: 'a', refreshToken: 'r')),
      overrides: [
        profileRepositoryProvider.overrideWithValue(profiles),
        metaRepositoryProvider.overrideWithValue(meta),
      ],
    );
    addTearDown(c.dispose);
    await tester.pumpWidget(UncontrolledProviderScope(container: c, child: const UzhavanApp()));
    await tester.pumpAndSettle();
    expect(find.text('உங்கள் விவரங்கள்'), findsOneWidget); // onboarding title
    expect(find.text('மாவட்டப் பட்டியல் கிடைக்கவில்லை'), findsOneWidget); // honest unavailable
    final name = tester.widget<EditableText>(
        find.descendant(of: find.byKey(const Key('profile-name')), matching: find.byType(EditableText)));
    expect(name.controller.text, isEmpty);
  });

  testWidgets('offline start with a stored session keeps the user signed in', (tester) async {
    final profiles = MockProfileRepository();
    when(profiles.fetch).thenThrow(
        const ApiFailure(kind: ApiFailureKind.unavailable, code: ApiFailure.networkCode));
    final store = MemoryTokenStore(const AuthTokens(accessToken: 'a', refreshToken: 'r'))
      ..profileComplete = true;
    final c = await makeContainer(
      tokenStore: store,
      overrides: [profileRepositoryProvider.overrideWithValue(profiles)],
    );
    addTearDown(c.dispose);
    await tester.pumpWidget(UncontrolledProviderScope(container: c, child: const UzhavanApp()));
    await tester.pumpAndSettle();
    expect(find.byType(NavigationBar), findsOneWidget);
    expect(find.byKey(const Key('home-greeting')), findsOneWidget); // real dashboard, no placeholder data
    expect(store.tokens, isNotNull);
  });
}
