import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/core/theme/app_theme.dart';
import 'package:uzhavan/features/shell/presentation/main_shell.dart';
import 'package:uzhavan/shared/widgets/app_scaffold.dart';

import '../helpers/test_app.dart';

void main() {
  testWidgets('F1: nav labels are single-line with ellipsis', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        bottomNavigationBar: NavigationBar(
          selectedIndex: 0,
          destinations: [
            MainShell.navDestination(Icons.home_outlined, Icons.home, 'முகப்பு'),
            MainShell.navDestination(Icons.chat_bubble_outline, null, 'உதவி உதவி உதவி உதவி உதவி'),
          ],
        ),
      ),
    ));
    final p = tester.renderObject<RenderParagraph>(find.text('உதவி உதவி உதவி உதவி உதவி'));
    expect(p.maxLines, 1);
    expect(p.overflow, TextOverflow.ellipsis);
    expect(p.softWrap, isFalse);
  });

  test('F2: Latin uses a sans family, Tamil falls back to Noto Sans Tamil', () {
    for (final t in [AppTheme.light(), AppTheme.dark()]) {
      final style = t.textTheme.bodyMedium!;
      expect(style.fontFamily, 'Roboto');
      expect(style.fontFamilyFallback, contains('NotoSansTamil'));
      expect(t.appBarTheme.titleTextStyle!.fontFamilyFallback, contains('NotoSansTamil'));
    }
  });

  testWidgets('F3: titles may use 2 lines; the switch label is intact', (tester) async {
    final c = await makeContainer();
    addTearDown(c.dispose);
    const title = 'தொலைபேசி சரிபார்ப்பு மிக நீண்ட தலைப்பு';
    await tester.pumpWidget(UncontrolledProviderScope(
      container: c,
      child: const TestApp(home: AppScaffold(title: title, body: SizedBox())),
    ));
    await tester.pumpAndSettle();
    expect(tester.renderObject<RenderParagraph>(find.text(title)).maxLines, 2);
    expect(find.text('தமிழ் → English'), findsOneWidget);
  });
}
