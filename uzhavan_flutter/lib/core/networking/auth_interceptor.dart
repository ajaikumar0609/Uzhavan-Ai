import 'package:dio/dio.dart';

import '../storage/token_store.dart';
import 'token_refresher.dart';

/// Request `extra` keys understood by [AuthInterceptor].
abstract final class AuthExtra {
  /// Set to false for public endpoints (no bearer token, no refresh).
  static const auth = 'auth';
  static const retried = 'auth_retried';
}

/// Adds the bearer token and, on 401, refreshes once and retries.
class AuthInterceptor extends Interceptor {
  AuthInterceptor({
    required Dio dio,
    required TokenStore store,
    required TokenRefresher refresher,
    required void Function() onSessionExpired,
  })  : _dio = dio,
        _store = store,
        _refresher = refresher,
        _onSessionExpired = onSessionExpired;

  final Dio _dio;
  final TokenStore _store;
  final TokenRefresher _refresher;
  final void Function() _onSessionExpired;

  static String bearer(String token) => 'Bearer $token';

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    if (options.extra[AuthExtra.auth] != false) {
      final tokens = await _store.read();
      if (tokens != null) {
        options.headers['Authorization'] = bearer(tokens.accessToken);
      }
    }
    handler.next(options);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    final req = err.requestOptions;
    final sent = req.headers['Authorization'];
    if (err.response?.statusCode != 401 ||
        req.extra[AuthExtra.auth] == false ||
        req.extra[AuthExtra.retried] == true ||
        sent is! String) {
      return handler.next(err);
    }

    String? newAccess;
    final current = await _store.read();
    if (current != null && bearer(current.accessToken) != sent) {
      // Another request already rotated the tokens: just retry.
      newAccess = current.accessToken;
    } else {
      try {
        newAccess = await _refresher.refresh();
      } on DioException catch (refreshError) {
        // Transient refresh failure: keep the session, surface the cause.
        return handler.next(refreshError);
      }
      if (newAccess == null) {
        _onSessionExpired();
        return handler.next(err);
      }
    }

    final retry = req.copyWith(
      headers: {...req.headers, 'Authorization': bearer(newAccess)},
      extra: {...req.extra, AuthExtra.retried: true},
    );
    try {
      handler.resolve(await _dio.fetch<Object?>(retry));
    } on DioException catch (e) {
      handler.next(e);
    }
  }
}
