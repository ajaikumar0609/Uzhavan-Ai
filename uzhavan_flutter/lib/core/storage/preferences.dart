import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Overridden in `main()` (and in tests) with a loaded instance.
final sharedPreferencesProvider = Provider<SharedPreferences>(
  (ref) => throw UnimplementedError('sharedPreferencesProvider not overridden'),
);

abstract final class PrefKeys {
  static const language = 'app.language';
  static const themeMode = 'app.theme_mode';
  static const selectedFarm = 'app.selected_farm';
}
