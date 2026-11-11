import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../storage/preferences.dart';

/// Supported app languages. Tamil is the default.
abstract final class AppLocales {
  static const tamil = Locale('ta');
  static const english = Locale('en');
  static const supported = [tamil, english];

  static Locale fromCode(String? code) => code == 'en' ? english : tamil;
}

/// The app language: switches instantly and is persisted.
class LocaleController extends Notifier<Locale> {
  @override
  Locale build() {
    final prefs = ref.watch(sharedPreferencesProvider);
    return AppLocales.fromCode(prefs.getString(PrefKeys.language));
  }

  Future<void> setLocale(Locale locale) async {
    final next = AppLocales.fromCode(locale.languageCode);
    state = next;
    await ref.read(sharedPreferencesProvider).setString(PrefKeys.language, next.languageCode);
  }

  Future<void> toggle() => setLocale(
        state.languageCode == AppLocales.tamil.languageCode
            ? AppLocales.english
            : AppLocales.tamil,
      );
}

final localeProvider = NotifierProvider<LocaleController, Locale>(LocaleController.new);
