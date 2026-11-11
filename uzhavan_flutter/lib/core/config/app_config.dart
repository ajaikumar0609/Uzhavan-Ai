import 'package:flutter/foundation.dart';

/// Why the configured API address cannot be used.
enum ConfigErrorKind { invalidUrl, insecureInRelease }

/// Thrown by [AppConfig.resolve] when the app must not start.
class ConfigError implements Exception {
  const ConfigError(this.kind, this.url);
  final ConfigErrorKind kind;
  final String url;

  @override
  String toString() => 'ConfigError(${kind.name}, $url)';
}

/// Build-time configuration.
///
/// `API_BASE_URL` comes from `--dart-define`. Without it, the Android
/// emulator uses `http://10.0.2.2:8000` (the host loopback) and every other
/// target uses `http://127.0.0.1:8000`. A release build refuses a non-https
/// address unless `ALLOW_INSECURE_API=true` is defined.
@immutable
class AppConfig {
  const AppConfig({required this.apiBaseUrl, required this.isRelease});

  static const String androidEmulatorDefault = 'http://10.0.2.2:8000';
  static const String localDefault = 'http://127.0.0.1:8000';

  static const String _definedUrl = String.fromEnvironment('API_BASE_URL');
  static const bool _allowInsecure = bool.fromEnvironment('ALLOW_INSECURE_API');

  /// Base URL without a trailing slash, e.g. `https://api.example.org`.
  final String apiBaseUrl;
  final bool isRelease;

  /// Resolves the configuration of the running build.
  static AppConfig fromEnvironment() => resolve(
        definedUrl: _definedUrl,
        isAndroid: !kIsWeb && defaultTargetPlatform == TargetPlatform.android,
        isRelease: kReleaseMode,
        allowInsecure: _allowInsecure,
      );

  /// Pure resolution logic (unit-tested). Throws [ConfigError].
  static AppConfig resolve({
    required String definedUrl,
    required bool isAndroid,
    required bool isRelease,
    required bool allowInsecure,
  }) {
    final raw = definedUrl.trim().isNotEmpty
        ? definedUrl.trim()
        : (isAndroid ? androidEmulatorDefault : localDefault);
    final uri = Uri.tryParse(raw);
    if (uri == null ||
        !(uri.scheme == 'http' || uri.scheme == 'https') ||
        uri.host.isEmpty) {
      throw ConfigError(ConfigErrorKind.invalidUrl, raw);
    }
    if (isRelease && uri.scheme != 'https' && !allowInsecure) {
      throw ConfigError(ConfigErrorKind.insecureInRelease, raw);
    }
    var normalized = uri.toString();
    while (normalized.endsWith('/')) {
      normalized = normalized.substring(0, normalized.length - 1);
    }
    return AppConfig(apiBaseUrl: normalized, isRelease: isRelease);
  }
}
