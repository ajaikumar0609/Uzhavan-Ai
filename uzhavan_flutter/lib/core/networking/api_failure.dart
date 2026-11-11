import 'package:flutter/foundation.dart';

import '../localization/bilingual_text.dart';

/// How the UI should treat a failed request (API contract §0).
enum ApiFailureKind {
  /// Network failure, 404, 501, 503: the service or data is not available.
  unavailable,

  /// 500 and other unexpected failures.
  error,

  /// 401 that could not be recovered by a token refresh.
  unauthenticated,

  /// 400 / 403 / 409 / 410 / 422: the request was rejected.
  validation,

  /// 429, with an optional `Retry-After`.
  rateLimited,
}

@immutable
class ApiFailure implements Exception {
  const ApiFailure({
    required this.kind,
    required this.code,
    this.message,
    this.statusCode,
    this.retryAfter,
  });

  final ApiFailureKind kind;

  /// Server `detail.code`, or a client code such as `network`.
  final String code;

  /// Server `detail.message` ({en, ta}), when provided.
  final BilingualText? message;
  final int? statusCode;
  final Duration? retryAfter;

  static const String networkCode = 'network';
  static const String unknownCode = 'unknown';

  @override
  String toString() =>
      'ApiFailure(${kind.name}, $code, status: $statusCode, retryAfter: $retryAfter)';
}
