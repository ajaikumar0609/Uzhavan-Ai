import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uzhavan/core/config/app_config.dart';
import 'package:uzhavan/core/localization/generated/app_localizations.dart';
import 'package:uzhavan/core/localization/locale_controller.dart';
import 'package:uzhavan/core/networking/providers.dart';
import 'package:uzhavan/core/storage/preferences.dart';
import 'package:uzhavan/core/storage/token_store.dart';
import 'package:uzhavan/core/theme/app_theme.dart';

/// Builds a container with the platform-bound providers replaced.
Future<ProviderContainer> makeContainer({
  Map<String, Object> prefs = const {},
  List overrides = const [],
  TokenStore? tokenStore,
}) async {
  SharedPreferences.setMockInitialValues(prefs);
  final sp = await SharedPreferences.getInstance();
  return ProviderContainer(
    overrides: [
      sharedPreferencesProvider.overrideWithValue(sp),
      appConfigProvider.overrideWithValue(
        const AppConfig(apiBaseUrl: 'http://test.local', isRelease: false),
      ),
      tokenStoreProvider.overrideWithValue(tokenStore ?? MemoryTokenStore()),
      ...overrides,
    ],
    retry: (_, _) => null,
  );
}

/// A localized MaterialApp following the app's locale provider.
class TestApp extends ConsumerWidget {
  const TestApp({super.key, this.home, this.routerConfig});
  final Widget? home;
  final RouterConfig<Object>? routerConfig;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final locale = ref.watch(localeProvider);
    if (routerConfig != null) {
      return MaterialApp.router(
        theme: AppTheme.light(),
        locale: locale,
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        routerConfig: routerConfig,
      );
    }
    return MaterialApp(
      theme: AppTheme.light(),
      locale: locale,
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      home: home,
    );
  }
}
