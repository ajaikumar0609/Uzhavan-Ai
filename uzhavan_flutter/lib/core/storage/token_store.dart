import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Access + refresh token pair.
class AuthTokens {
  const AuthTokens({required this.accessToken, required this.refreshToken});
  final String accessToken;
  final String refreshToken;
}

/// Token persistence. Tokens only ever live in secure storage.
abstract class TokenStore {
  Future<AuthTokens?> read();
  Future<void> save(AuthTokens tokens);
  Future<void> clear();

  /// Last known `profile_complete`, used when the profile can't be fetched
  /// on start-up (e.g. offline).
  Future<bool?> readProfileComplete();
  Future<void> saveProfileComplete(bool value);
}

class SecureTokenStore implements TokenStore {
  SecureTokenStore([FlutterSecureStorage? storage])
      : _storage = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _storage;

  static const _kAccess = 'auth.access_token';
  static const _kRefresh = 'auth.refresh_token';
  static const _kProfileComplete = 'auth.profile_complete';

  @override
  Future<AuthTokens?> read() async {
    final access = await _storage.read(key: _kAccess);
    final refresh = await _storage.read(key: _kRefresh);
    if (access == null || refresh == null) return null;
    return AuthTokens(accessToken: access, refreshToken: refresh);
  }

  @override
  Future<void> save(AuthTokens tokens) async {
    await _storage.write(key: _kAccess, value: tokens.accessToken);
    await _storage.write(key: _kRefresh, value: tokens.refreshToken);
  }

  @override
  Future<void> clear() async {
    await _storage.delete(key: _kAccess);
    await _storage.delete(key: _kRefresh);
    await _storage.delete(key: _kProfileComplete);
  }

  @override
  Future<bool?> readProfileComplete() async {
    final v = await _storage.read(key: _kProfileComplete);
    return v == null ? null : v == 'true';
  }

  @override
  Future<void> saveProfileComplete(bool value) =>
      _storage.write(key: _kProfileComplete, value: value.toString());
}

/// In-memory store for tests.
class MemoryTokenStore implements TokenStore {
  MemoryTokenStore([this.tokens]);
  AuthTokens? tokens;
  bool? profileComplete;

  @override
  Future<AuthTokens?> read() async => tokens;
  @override
  Future<void> save(AuthTokens t) async => tokens = t;
  @override
  Future<void> clear() async {
    tokens = null;
    profileComplete = null;
  }

  @override
  Future<bool?> readProfileComplete() async => profileComplete;
  @override
  Future<void> saveProfileComplete(bool value) async => profileComplete = value;
}
