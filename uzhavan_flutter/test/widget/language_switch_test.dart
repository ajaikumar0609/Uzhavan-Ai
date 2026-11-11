import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/core/storage/preferences.dart';
import 'package:uzhavan/shared/widgets/app_scaffold.dart';
import 'package:uzhavan/shared/widgets/language_switch_button.dart';

import '../helpers/test_app.dart';

void main() {
  Widget app(ProviderContainer c) => UncontrolledProviderScope(
        container: c,
        child: TestApp(
          home: Builder(
            builder: (context) => AppScaffold(
              title: 'x',
              body: Text(Localizations.localeOf(context).languageCode, key: const Key('lang')),
            ),
          ),
        ),
      );

  testWidgets('defaults to Tamil and flips instantly to English, persisted', (tester) async {
    final c = await makeContainer();
    addTearDown(c.dispose);
    await tester.pumpWidget(app(c));
    await tester.pumpAndSettle();

    expect(find.text('தமிழ் → English'), findsOneWidget);
    expect(find.text('ta'), findsOneWidget);

    await tester.tap(find.byKey(LanguageSwitchButton.buttonKey));
    await tester.pumpAndSettle();

    expect(find.text('English → தமிழ்'), findsOneWidget);
    expect(find.text('தமிழ் → English'), findsNothing);
    expect(find.text('en'), findsOneWidget);
    expect(c.read(sharedPreferencesProvider).getString(PrefKeys.language), 'en');

    await tester.tap(find.byKey(LanguageSwitchButton.buttonKey));
    await tester.pumpAndSettle();
    expect(find.text('தமிழ் → English'), findsOneWidget);
    expect(c.read(sharedPreferencesProvider).getString(PrefKeys.language), 'ta');
  });

  testWidgets('restores the persisted language on start', (tester) async {
    final c = await makeContainer(prefs: {PrefKeys.language: 'en'});
    addTearDown(c.dispose);
    await tester.pumpWidget(app(c));
    await tester.pumpAndSettle();
    expect(find.text('English → தமிழ்'), findsOneWidget);
    expect(find.text('en'), findsOneWidget);
  });
}
