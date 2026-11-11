import 'package:flutter/widgets.dart';

import '../../core/localization/generated/app_localizations.dart';
import '../../core/networking/api_failure.dart';

/// Server error codes (contract M-06, backend as deployed 2026-09-25) that
/// have a dedicated ARB string. The server's `detail.message.ta` is always
/// null, so errors are localized by code; `message.en` is only a last resort.
const localizedErrorCodes = <String>{
  'invalid_phone', 'rate_limited', 'otp_incorrect', 'otp_attempts_exceeded',
  'otp_expired', 'otp_not_found', 'otp_delivery_not_configured',
  'service_unavailable', 'unauthenticated', 'not_found', 'invalid_name',
  'invalid_district', 'invalid_language', 'invalid_village', 'invalid_location',
  'location_outside_tamil_nadu', 'invalid_area', 'invalid_boundary',
  'invalid_crop', 'invalid_crop_stage', 'invalid_season',
  'invalid_irrigation_type', 'farm_limit_reached', ApiFailure.networkCode,
  // Wave B (live backend 2026-09-26)
  'value_out_of_range', 'unsupported_media_type', 'file_too_large',
  'image_too_large', 'empty_image', 'model_unavailable',
};

/// One localized sentence for a failed request: the ARB string for a known
/// code; otherwise a generic text by kind; the server's English message only
/// for unknown validation codes (the most specific thing available).
String failureText(AppLocalizations l, Locale locale, Object error) {
  if (error is! ApiFailure) return l.stateError;
  switch (error.code) {
    case 'otp_incorrect':
      return l.errOtpIncorrect;
    case 'otp_expired':
      return l.errOtpExpired;
    case 'otp_attempts_exceeded':
      return l.errOtpAttemptsExceeded;
    case 'otp_not_found':
      return l.errOtpNotFound;
    case 'otp_delivery_not_configured':
      return l.errOtpDeliveryNotConfigured;
    case 'invalid_phone':
      return l.phoneInvalid;
    case ApiFailure.networkCode:
      return l.errServerUnreachable;
    case 'rate_limited':
      return rateLimitText(l, error.retryAfter);
    case 'service_unavailable':
      return l.stateUnavailable;
    case 'unauthenticated':
      return l.errSessionExpired;
    case 'not_found':
      return l.errNotFound;
    case 'invalid_name':
      return l.nameInvalid;
    case 'invalid_district':
      return l.errInvalidDistrict;
    case 'invalid_language':
      return l.errInvalidLanguage;
    case 'invalid_village':
      return l.errInvalidVillage;
    case 'invalid_location':
      return l.errInvalidLocation;
    case 'location_outside_tamil_nadu':
      return l.errLocationOutsideTn;
    case 'invalid_area':
      return l.farmAreaInvalid;
    case 'invalid_boundary':
      return l.errInvalidBoundary;
    case 'invalid_crop':
      return l.errInvalidCrop;
    case 'invalid_crop_stage':
      return l.errInvalidCropStage;
    case 'invalid_season':
      return l.errInvalidSeason;
    case 'invalid_irrigation_type':
      return l.errInvalidIrrigationType;
    case 'farm_limit_reached':
      return l.farmLimitReached;
    case 'value_out_of_range':
      return l.errValueOutOfRange;
    case 'unsupported_media_type':
    case 'empty_image':
      return l.scanUnsupportedImage;
    case 'file_too_large':
    case 'image_too_large':
      return l.scanImageTooLarge;
    case 'model_unavailable':
      return l.scanModelUnavailable;
  }
  switch (error.kind) {
    case ApiFailureKind.rateLimited:
      return rateLimitText(l, error.retryAfter);
    case ApiFailureKind.unauthenticated:
      return l.errSessionExpired;
    case ApiFailureKind.unavailable:
      return l.stateUnavailable;
    case ApiFailureKind.error:
      return l.stateError;
    case ApiFailureKind.validation:
      // Unknown code: the server text (English unless it ever sends Tamil)
      // is more useful than a generic line. Last resort only.
      final server = error.message;
      if (server != null && server.en.trim().isNotEmpty) return server.resolve(locale);
      return l.errValidation;
  }
}

String rateLimitText(AppLocalizations l, Duration? retryAfter) {
  if (retryAfter == null || retryAfter <= Duration.zero) return l.errRateLimited;
  final s = retryAfter.inSeconds;
  if (s < 60) return l.errRateLimitedSeconds(s);
  return l.errRateLimitedMinutes((s / 60).ceil());
}
