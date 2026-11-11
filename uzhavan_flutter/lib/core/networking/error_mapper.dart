import 'package:dio/dio.dart';

import '../localization/bilingual_text.dart';
import 'api_failure.dart';

/// Maps a Dio error to an [ApiFailure] per API contract §0:
/// network failure / 404 / 501 / 503 → unavailable, other 5xx → error,
/// 401 → unauthenticated, 429 → rateLimited, other 4xx → validation.
ApiFailure mapDioException(DioException e) {
  final response = e.response;
  if (response == null) {
    switch (e.type) {
      case DioExceptionType.cancel:
        return const ApiFailure(kind: ApiFailureKind.error, code: 'cancelled');
      case DioExceptionType.badCertificate:
        return const ApiFailure(kind: ApiFailureKind.error, code: 'bad_certificate');
      case DioExceptionType.transformTimeout:
        return const ApiFailure(kind: ApiFailureKind.error, code: 'malformed_response');
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.connectionError:
      case DioExceptionType.unknown:
      case DioExceptionType.badResponse:
        return const ApiFailure(
          kind: ApiFailureKind.unavailable,
          code: ApiFailure.networkCode,
        );
    }
  }
  return mapResponse(response.statusCode ?? 0, response.data, response.headers);
}

ApiFailure mapResponse(int status, Object? body, Headers headers) {
  final detail = body is Map ? body['detail'] : null;
  String? code;
  BilingualText? message;
  if (detail is Map) {
    final c = detail['code'];
    if (c is String && c.isNotEmpty) code = c;
    message = BilingualText.tryParse(detail['message']);
  }

  final ApiFailureKind kind;
  String fallbackCode;
  Duration? retryAfter;
  switch (status) {
    case 401:
      kind = ApiFailureKind.unauthenticated;
      fallbackCode = 'unauthenticated';
    case 404:
      kind = ApiFailureKind.unavailable;
      fallbackCode = 'not_found';
    case 501:
      kind = ApiFailureKind.unavailable;
      fallbackCode = 'not_implemented';
    case 503:
      kind = ApiFailureKind.unavailable;
      fallbackCode = 'service_unavailable';
    case 429:
      kind = ApiFailureKind.rateLimited;
      fallbackCode = 'rate_limited';
      retryAfter = parseRetryAfter(headers.value('retry-after'));
    case 422:
      kind = ApiFailureKind.validation;
      fallbackCode = 'validation_error';
    default:
      if (status >= 400 && status < 500) {
        kind = ApiFailureKind.validation;
        fallbackCode = 'bad_request';
      } else {
        kind = ApiFailureKind.error;
        fallbackCode = 'server_error';
      }
  }
  return ApiFailure(
    kind: kind,
    code: code ?? fallbackCode,
    message: message,
    statusCode: status,
    retryAfter: retryAfter,
  );
}

/// `Retry-After` as delta-seconds or an HTTP date.
Duration? parseRetryAfter(String? value, {DateTime? now}) {
  if (value == null || value.trim().isEmpty) return null;
  final seconds = int.tryParse(value.trim());
  if (seconds != null) return seconds < 0 ? Duration.zero : Duration(seconds: seconds);
  try {
    final date = HttpDateParser.parse(value.trim());
    final diff = date.difference((now ?? DateTime.now()).toUtc());
    return diff.isNegative ? Duration.zero : diff;
  } on FormatException {
    return null;
  }
}

/// Minimal RFC 7231 IMF-fixdate parser (`Wed, 21 Oct 2015 07:28:00 GMT`).
class HttpDateParser {
  static const _months = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
  };

  static DateTime parse(String s) {
    final m = RegExp(r'^\w{3}, (\d{2}) (\w{3}) (\d{4}) (\d{2}):(\d{2}):(\d{2}) GMT$')
        .firstMatch(s);
    final month = m == null ? null : _months[m.group(2)];
    if (m == null || month == null) throw const FormatException('Bad HTTP date');
    return DateTime.utc(int.parse(m.group(3)!), month, int.parse(m.group(1)!),
        int.parse(m.group(4)!), int.parse(m.group(5)!), int.parse(m.group(6)!));
  }
}
