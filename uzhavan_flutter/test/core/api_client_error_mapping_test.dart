import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/core/networking/api_client.dart';
import 'package:uzhavan/core/networking/api_failure.dart';
import 'package:uzhavan/core/networking/error_mapper.dart';
import 'package:uzhavan/core/storage/token_store.dart';

import '../helpers/scripted_adapter.dart';

void main() {
  late ScriptedAdapter adapter;
  late ApiClient api;

  setUp(() {
    adapter = ScriptedAdapter((_) async => jsonBody(200, {'data': []}));
    api = ApiClient(baseUrl: 'http://test.local', tokenStore: MemoryTokenStore(), adapter: adapter);
  });

  Future<ApiFailure> failureFor(Handler h) async {
    adapter.handler = h;
    try {
      await api.get('/api/anything');
    } on ApiFailure catch (f) {
      return f;
    }
    fail('expected ApiFailure');
  }

  test('success returns the decoded body', () async {
    adapter.handler = (_) async => jsonBody(200, {'data': [1, 2]});
    expect(unwrapData(await api.get('/x')), [1, 2]);
  });

  test('network failure → unavailable', () async {
    final f = await failureFor((o) async => throw const SocketException('refused'));
    expect(f.kind, ApiFailureKind.unavailable);
    expect(f.code, ApiFailure.networkCode);
  });

  test('connection timeout → unavailable', () async {
    final f = await failureFor((o) async => throw DioException.connectionTimeout(
        timeout: const Duration(seconds: 1), requestOptions: o));
    expect(f.kind, ApiFailureKind.unavailable);
  });

  test('404 → unavailable, keeping the server code', () async {
    final f = await failureFor((_) async => jsonBody(404, errorDetail('not_found')));
    expect(f.kind, ApiFailureKind.unavailable);
    expect(f.code, 'not_found');
    expect(f.statusCode, 404);
  });

  test('501 → unavailable', () async {
    final f = await failureFor((_) async => jsonBody(501, null));
    expect(f.kind, ApiFailureKind.unavailable);
  });

  test('503 → unavailable with the bilingual server message', () async {
    final f = await failureFor((_) async =>
        jsonBody(503, errorDetail('model_unavailable', en: 'Model unavailable', ta: 'மாதிரி இல்லை')));
    expect(f.kind, ApiFailureKind.unavailable);
    expect(f.code, 'model_unavailable');
    expect(f.message?.en, 'Model unavailable');
    expect(f.message?.ta, 'மாதிரி இல்லை');
  });

  test('500 → error, never exposing the body', () async {
    final f = await failureFor((_) async => ResponseBody.fromString('Traceback ...', 500));
    expect(f.kind, ApiFailureKind.error);
    expect(f.code, 'server_error');
    expect(f.message, isNull);
  });

  test('429 → rateLimited with Retry-After seconds', () async {
    final f = await failureFor((_) async => jsonBody(429, errorDetail('rate_limited'), headers: {
          'retry-after': ['120'],
        }));
    expect(f.kind, ApiFailureKind.rateLimited);
    expect(f.retryAfter, const Duration(seconds: 120));
  });

  test('400 / 410 / 422 → validation', () async {
    expect((await failureFor((_) async => jsonBody(400, errorDetail('otp_incorrect')))).kind,
        ApiFailureKind.validation);
    final expired = await failureFor((_) async => jsonBody(410, errorDetail('otp_expired')));
    expect(expired.kind, ApiFailureKind.validation);
    expect(expired.code, 'otp_expired');
    final pydantic = await failureFor((_) async => jsonBody(422, {
          'detail': [
            {'loc': ['body', 'name'], 'msg': 'too short'}
          ]
        }));
    expect(pydantic.kind, ApiFailureKind.validation);
    expect(pydantic.code, 'validation_error');
  });

  test('401 on a public endpoint → unauthenticated (no refresh attempted)', () async {
    adapter.handler = (_) async => jsonBody(401, errorDetail('unauthenticated'));
    await expectLater(
      api.post('/api/auth/verify-otp', body: {}, auth: false),
      throwsA(isA<ApiFailure>().having((f) => f.kind, 'kind', ApiFailureKind.unauthenticated)),
    );
    expect(adapter.countPath('/api/auth/refresh'), 0);
  });

  test('parseRetryAfter handles HTTP dates', () {
    final now = DateTime.utc(2026, 9, 25, 10, 0, 0);
    expect(parseRetryAfter('Fri, 25 Sep 2026 10:01:00 GMT', now: now), const Duration(minutes: 1));
    expect(parseRetryAfter('garbage'), isNull);
  });
}
