import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';

import '../storage/token_store.dart';
import 'api_failure.dart';
import 'auth_interceptor.dart';
import 'error_mapper.dart';
import 'token_refresher.dart';

/// The only HTTP entry point. Every method returns the decoded JSON body or
/// throws an [ApiFailure]; widgets never see Dio.
class ApiClient {
  ApiClient({
    required String baseUrl,
    required TokenStore tokenStore,
    void Function()? onSessionExpired,
    HttpClientAdapter? adapter,
  }) {
    BaseOptions options() => BaseOptions(
          baseUrl: baseUrl,
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 30),
          sendTimeout: const Duration(seconds: 30),
          contentType: Headers.jsonContentType,
          responseType: ResponseType.json,
          headers: {'Accept': 'application/json'},
        );
    final refreshDio = Dio(options());
    dio = Dio(options());
    if (adapter != null) {
      refreshDio.httpClientAdapter = adapter;
      dio.httpClientAdapter = adapter;
    }
    refresher = TokenRefresher(refreshDio: refreshDio, store: tokenStore);
    dio.interceptors.add(AuthInterceptor(
      dio: dio,
      store: tokenStore,
      refresher: refresher,
      onSessionExpired: onSessionExpired ?? () {},
    ));
  }

  late final Dio dio;
  late final TokenRefresher refresher;

  Options _opts(bool auth) => Options(extra: {AuthExtra.auth: auth});

  Future<Object?> get(String path, {Map<String, Object?>? query, bool auth = true}) =>
      _send(() => dio.get<Object?>(path, queryParameters: query, options: _opts(auth)));

  Future<Object?> post(String path, {Object? body, bool auth = true}) =>
      _send(() => dio.post<Object?>(path, data: body, options: _opts(auth)));

  Future<Object?> put(String path, {Object? body, bool auth = true}) =>
      _send(() => dio.put<Object?>(path, data: body, options: _opts(auth)));

  Future<Object?> delete(String path, {Object? body, bool auth = true}) =>
      _send(() => dio.delete<Object?>(path, data: body, options: _opts(auth)));

  /// Multipart upload with progress (`sent`, `total` bytes).
  Future<Object?> postMultipart(
    String path,
    FormData form, {
    bool auth = true,
    void Function(int sent, int total)? onSendProgress,
  }) =>
      _send(() => dio.post<Object?>(
            path,
            data: form,
            onSendProgress: onSendProgress,
            options: _opts(auth).copyWith(
              contentType: 'multipart/form-data',
              sendTimeout: const Duration(seconds: 120),
            ),
          ));

  /// POST that returns the raw response byte stream (SSE). A non-2xx
  /// response is read and mapped to an [ApiFailure] like any other call.
  Future<Stream<List<int>>> postStream(
    String path, {
    Object? body,
    bool auth = true,
    CancelToken? cancelToken,
  }) async {
    try {
      final res = await dio.post<ResponseBody>(
        path,
        data: body,
        cancelToken: cancelToken,
        options: _opts(auth).copyWith(
          responseType: ResponseType.stream,
          headers: {'Accept': 'text/event-stream'},
          receiveTimeout: const Duration(minutes: 3),
        ),
      );
      final data = res.data;
      if (data == null) {
        throw const ApiFailure(kind: ApiFailureKind.error, code: 'malformed_response');
      }
      return data.stream;
    } on DioException catch (e) {
      final response = e.response;
      final raw = response?.data;
      if (response != null && raw is ResponseBody) {
        Object? decoded;
        try {
          final text = await utf8.decodeStream(raw.stream);
          decoded = text.isEmpty ? null : jsonDecode(text);
        } catch (_) {
          decoded = null;
        }
        throw mapResponse(response.statusCode ?? 0, decoded, response.headers);
      }
      throw mapDioException(e);
    }
  }

  Future<Object?> _send(Future<Response<Object?>> Function() call) async {
    try {
      final res = await call();
      return res.data;
    } on DioException catch (e) {
      throw mapDioException(e);
    }
  }
}

/// Extracts `data` from the contract's `{data, meta}` envelope.
Object? unwrapData(Object? body) {
  if (body is Map && body.containsKey('data')) return body['data'];
  throw const ApiFailure(kind: ApiFailureKind.error, code: 'malformed_response');
}

/// Casts a JSON value to a map or throws a malformed-response failure.
Map<String, Object?> asJsonMap(Object? v) {
  if (v is Map) return v.cast<String, Object?>();
  throw const ApiFailure(kind: ApiFailureKind.error, code: 'malformed_response');
}

List<Object?> asJsonList(Object? v) {
  if (v is List) return v.cast<Object?>();
  throw const ApiFailure(kind: ApiFailureKind.error, code: 'malformed_response');
}
