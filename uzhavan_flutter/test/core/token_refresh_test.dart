import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/core/networking/api_client.dart';
import 'package:uzhavan/core/networking/api_failure.dart';
import 'package:uzhavan/core/storage/token_store.dart';

import '../helpers/scripted_adapter.dart';

void main() {
  late MemoryTokenStore store;
  late ScriptedAdapter adapter;
  late ApiClient api;
  late int expiredCalls;

  const refreshPath = '/api/auth/refresh';

  setUp(() {
    store = MemoryTokenStore(const AuthTokens(accessToken: 'a1', refreshToken: 'r1'));
    expiredCalls = 0;
    adapter = ScriptedAdapter((_) async => jsonBody(200, {}));
    api = ApiClient(
      baseUrl: 'http://test.local',
      tokenStore: store,
      adapter: adapter,
      onSessionExpired: () => expiredCalls++,
    );
  });

  /// Server: valid access token is [valid]; refresh rotates r1→r2 / a2.
  Handler server({required String valid, Completer<void>? holdRefresh}) => (o) async {
        if (o.path == refreshPath) {
          await holdRefresh?.future;
          final data = o.data as Map;
          if (data['refresh_token'] == 'r1') {
            return jsonBody(200, {
              'access_token': 'a2',
              'refresh_token': 'r2',
              'token_type': 'bearer',
              'expires_in': 900,
            });
          }
          return jsonBody(401, {'detail': {'code': 'unauthenticated', 'message': {'en': 'x', 'ta': null}}});
        }
        if (o.headers['Authorization'] == 'Bearer $valid') {
          return jsonBody(200, {'data': {'ok': o.path}});
        }
        return jsonBody(401, {'detail': {'code': 'unauthenticated', 'message': {'en': 'x', 'ta': null}}});
      };

  test('sends the bearer token', () async {
    adapter.handler = server(valid: 'a1');
    await api.get('/api/farms');
    expect(adapter.requests.single.headers['Authorization'], 'Bearer a1');
  });

  test('401 → refresh → retry with the rotated tokens', () async {
    adapter.handler = server(valid: 'a2');
    final body = await api.get('/api/farms');
    expect(body, {'data': {'ok': '/api/farms'}});
    expect(adapter.countPath(refreshPath), 1);
    expect(store.tokens?.accessToken, 'a2');
    expect(store.tokens?.refreshToken, 'r2');
    final retried = adapter.requests.last;
    expect(retried.headers['Authorization'], 'Bearer a2');
    expect(expiredCalls, 0);
  });

  test('concurrent 401s share a single in-flight refresh', () async {
    final hold = Completer<void>();
    adapter.handler = server(valid: 'a2', holdRefresh: hold);
    final calls = [
      api.get('/api/farms'),
      api.get('/api/farmer/profile'),
      api.get('/api/diary'),
    ];
    // Let all three hit 401 and queue behind the same refresh.
    await Future<void>.delayed(const Duration(milliseconds: 20));
    hold.complete();
    final results = await Future.wait(calls);
    expect(results, hasLength(3));
    expect(adapter.countPath(refreshPath), 1, reason: 'refresh token is single-use');
    expect(store.tokens?.refreshToken, 'r2');
  });

  test('a 401 for an already-rotated token retries without refreshing again', () async {
    // The request went out with a1, but another call already rotated to a2.
    adapter.handler = (o) async {
      if (o.headers['Authorization'] == 'Bearer a1') {
        store.tokens = const AuthTokens(accessToken: 'a2', refreshToken: 'r2');
        return jsonBody(401, {});
      }
      return server(valid: 'a2')(o);
    };
    await api.get('/api/farms');
    expect(adapter.countPath(refreshPath), 0);
  });

  test('rejected refresh token → tokens cleared, session expired, unauthenticated', () async {
    store.tokens = const AuthTokens(accessToken: 'a1', refreshToken: 'revoked');
    adapter.handler = server(valid: 'never');
    await expectLater(
      api.get('/api/farms'),
      throwsA(isA<ApiFailure>().having((f) => f.kind, 'kind', ApiFailureKind.unauthenticated)),
    );
    expect(store.tokens, isNull);
    expect(expiredCalls, 1);
  });

  test('network failure during refresh keeps the session → unavailable', () async {
    adapter.handler = (o) async {
      if (o.path == refreshPath) throw DioException.connectionError(requestOptions: o, reason: 'down');
      return jsonBody(401, {});
    };
    await expectLater(
      api.get('/api/farms'),
      throwsA(isA<ApiFailure>().having((f) => f.kind, 'kind', ApiFailureKind.unavailable)),
    );
    expect(store.tokens?.refreshToken, 'r1');
    expect(expiredCalls, 0);
  });

  test('a retried request that 401s again does not loop', () async {
    adapter.handler = (o) async {
      if (o.path == refreshPath) {
        return jsonBody(200, {'access_token': 'a2', 'refresh_token': 'r2'});
      }
      return jsonBody(401, {});
    };
    await expectLater(api.get('/api/farms'), throwsA(isA<ApiFailure>()));
    expect(adapter.countPath(refreshPath), 1);
    expect(adapter.countPath('/api/farms'), 2);
  });
}
