import 'package:flutter/widgets.dart';

/// A server string in both languages: `{ "en": "...", "ta": "..." }`.
///
/// `ta` may be null when no verified Tamil translation exists; the client
/// then shows `en` (API contract §0).
@immutable
class BilingualText {
  const BilingualText({required this.en, this.ta});

  final String en;
  final String? ta;

  /// Parses `{en, ta}`. Returns null when [json] is not a usable object.
  static BilingualText? tryParse(Object? json) {
    if (json is Map) {
      final en = json['en'];
      final ta = json['ta'];
      if (en is String) {
        return BilingualText(en: en, ta: ta is String ? ta : null);
      }
      if (ta is String && ta.isNotEmpty) {
        // Defensive: Tamil only. Still show something real rather than nothing.
        return BilingualText(en: ta, ta: ta);
      }
    }
    return null;
  }

  factory BilingualText.fromJson(Object? json) =>
      tryParse(json) ?? const BilingualText(en: '');

  Map<String, Object?> toJson() => {'en': en, 'ta': ta};

  /// The single place that picks a language for server text.
  String resolve(Locale locale) {
    final tamil = ta;
    if (locale.languageCode == 'ta' && tamil != null && tamil.trim().isNotEmpty) {
      return tamil;
    }
    return en;
  }

  @override
  bool operator ==(Object other) =>
      other is BilingualText && other.en == en && other.ta == ta;

  @override
  int get hashCode => Object.hash(en, ta);
}

extension BilingualContext on BuildContext {
  /// Renders server bilingual text for the current app locale.
  String bi(BilingualText text) => text.resolve(Localizations.localeOf(this));
}
