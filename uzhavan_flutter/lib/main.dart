import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app.dart';
import 'core/config/app_config.dart';
import 'core/config/config_error_app.dart';
import 'core/networking/providers.dart';
import 'core/storage/preferences.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Edge-to-edge: draw behind the system bars; screens use SafeArea / AppBar.
  await SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    systemNavigationBarColor: Colors.transparent,
    systemNavigationBarContrastEnforced: false,
  ));

  final prefs = await SharedPreferences.getInstance();
  final prefsOverride = sharedPreferencesProvider.overrideWithValue(prefs);

  final AppConfig config;
  try {
    config = AppConfig.fromEnvironment();
  } on ConfigError catch (e) {
    runApp(ProviderScope(overrides: [prefsOverride], child: ConfigErrorApp(error: e)));
    return;
  }

  runApp(ProviderScope(
    overrides: [prefsOverride, appConfigProvider.overrideWithValue(config)],
    // Failures are shown with a Retry button; no silent automatic retries.
    retry: (_, _) => null,
    child: const UzhavanApp(),
  ));
}
