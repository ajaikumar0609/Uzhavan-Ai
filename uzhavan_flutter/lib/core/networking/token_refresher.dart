import 'package:dio/dio.dart';

import '../storage/token_store.dart';

/// Rotates tokens through `POST /api/auth/refresh`.
///
/// Single-flight: concurrent callers share one in-flight refresh, so a burst
/// of 401s never sends the (single-use) refresh token twice.
class TokenRefresher {
  TokenRefresher({required Dio refreshDio, required TokenStore store})
      : _dio = refreshDio,
        _store = store;

  final Dio _dio;
  final TokenStore _store;
  Future<String?>? _inflight;

  static const path = '/api/auth/refresh';

  /// Returns the new access token, or null when the server rejected the
  /// refresh token (the session is over and tokens are cleared).
  /// Throws [DioException] on transient failures (network, 5xx); tokens are
  /// kept in that case.
  Future<String?> refresh() {
    final existing = _inflight;
    if (existing != null) return existing;
    final future = _doRefresh();
    _inflight = future;
    return future.whenComplete(() => _inflight = null);
  }

  Future<String?> _doRefresh() async {
    final tokens = await _store.read();
    if (tokens == null) return null;
    try {
      final res = await _dio.post<Object?>(
        path,
        data: {'refresh_token': tokens.refreshToken},
      );
      final body = res.data;
      final access = body is Map ? body['access_token'] : null;
      final refresh = body is Map ? body['refresh_token'] : null;
      if (access is! String || refresh is! String || access.isEmpty || refresh.isEmpty) {
        throw DioException.badResponse(
          statusCode: res.statusCode ?? 200,
          requestOptions: res.requestOptions,
          response: res,
        );
      }
      await _store.save(AuthTokens(accessToken: access, refreshToken: refresh));
      return access;
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      if (status != null && status >= 400 && status < 500 && status != 429) {
        // Revoked / reused / unknown refresh token: the session is over.
        await _store.clear();
        return null;
      }
      rethrow;
    }
  }
}
