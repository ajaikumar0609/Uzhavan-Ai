import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/core/config/app_config.dart';

void main() {
  AppConfig resolve({
    String url = '',
    bool android = true,
    bool release = false,
    bool insecure = false,
  }) =>
      AppConfig.resolve(
        definedUrl: url,
        isAndroid: android,
        isRelease: release,
        allowInsecure: insecure,
      );

  group('AppConfig.resolve', () {
    test('defaults to the emulator host loopback on Android', () {
      expect(resolve().apiBaseUrl, 'http://10.0.2.2:8000');
    });

    test('defaults to 127.0.0.1 on other platforms', () {
      expect(resolve(android: false).apiBaseUrl, 'http://127.0.0.1:8000');
    });

    test('uses API_BASE_URL and strips trailing slashes', () {
      expect(resolve(url: 'https://api.uzhavan.ai/').apiBaseUrl, 'https://api.uzhavan.ai');
      expect(resolve(url: '  http://192.168.1.5:8000// ').apiBaseUrl, 'http://192.168.1.5:8000');
    });

    test('debug builds accept http', () {
      expect(resolve(url: 'http://10.0.2.2:8000').isRelease, isFalse);
    });

    test('release builds reject http', () {
      expect(
        () => resolve(url: 'http://api.example.org', release: true),
        throwsA(isA<ConfigError>().having((e) => e.kind, 'kind', ConfigErrorKind.insecureInRelease)),
      );
    });

    test('release builds reject the http default when no URL is defined', () {
      expect(() => resolve(release: true), throwsA(isA<ConfigError>()));
    });

    test('release builds accept https', () {
      final c = resolve(url: 'https://api.example.org', release: true);
      expect(c.apiBaseUrl, 'https://api.example.org');
      expect(c.isRelease, isTrue);
    });

    test('ALLOW_INSECURE_API=true lets a release build use http', () {
      expect(resolve(url: 'http://10.0.2.2:8000', release: true, insecure: true).apiBaseUrl,
          'http://10.0.2.2:8000');
    });

    test('invalid URLs are rejected', () {
      for (final bad in ['not a url', 'ftp://x.org', 'http://']) {
        expect(
          () => resolve(url: bad),
          throwsA(isA<ConfigError>().having((e) => e.kind, 'kind', ConfigErrorKind.invalidUrl)),
          reason: bad,
        );
      }
    });
  });
}
