import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/core/localization/bilingual_text.dart';

void main() {
  const ta = Locale('ta');
  const en = Locale('en');

  test('picks Tamil in the Tamil locale', () {
    final t = BilingualText.fromJson({'en': 'Paddy', 'ta': 'நெல்'});
    expect(t.resolve(ta), 'நெல்');
    expect(t.resolve(en), 'Paddy');
  });

  test('falls back to English only when ta is null or blank', () {
    expect(BilingualText.fromJson({'en': 'Coconut', 'ta': null}).resolve(ta), 'Coconut');
    expect(BilingualText.fromJson({'en': 'Coconut'}).resolve(ta), 'Coconut');
    expect(BilingualText.fromJson({'en': 'Coconut', 'ta': '  '}).resolve(ta), 'Coconut');
  });

  test('tryParse rejects non-objects', () {
    expect(BilingualText.tryParse('plain'), isNull);
    expect(BilingualText.tryParse(null), isNull);
    expect(BilingualText.tryParse({'x': 1}), isNull);
  });

  testWidgets('context.bi follows the widget locale', (tester) async {
    const text = BilingualText(en: 'Thanjavur', ta: 'தஞ்சாவூர்');
    for (final (locale, expected) in [(ta, 'தஞ்சாவூர்'), (en, 'Thanjavur')]) {
      await tester.pumpWidget(Localizations(
        locale: locale,
        delegates: const [DefaultWidgetsLocalizations.delegate],
        child: Builder(
          builder: (c) => Text(c.bi(text), textDirection: TextDirection.ltr),
        ),
      ));
      expect(find.text(expected), findsOneWidget);
    }
  });
}
