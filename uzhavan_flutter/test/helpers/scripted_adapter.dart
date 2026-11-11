import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

typedef Handler = Future<ResponseBody> Function(RequestOptions options);

/// A Dio adapter that answers from a test script and records requests.
class ScriptedAdapter implements HttpClientAdapter {
  ScriptedAdapter(this.handler);

  Handler handler;
  final List<RequestOptions> requests = [];

  int countPath(String path) => requests.where((r) => r.path == path).length;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) {
    requests.add(options);
    return handler(options);
  }

  @override
  void close({bool force = false}) {}
}

ResponseBody jsonBody(int status, Object? body, {Map<String, List<String>> headers = const {}}) =>
    ResponseBody.fromString(
      body == null ? '' : jsonEncode(body),
      status,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
        ...headers,
      },
    );

Map<String, Object?> errorDetail(String code, {String en = 'x', String? ta}) => {
      'detail': {
        'code': code,
        'message': {'en': en, 'ta': ta},
      },
    };
