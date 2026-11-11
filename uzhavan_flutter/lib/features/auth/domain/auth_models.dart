import '../../../core/networking/api_client.dart';
import '../../../core/storage/token_store.dart';

/// `POST /api/auth/send-otp` → 200.
class OtpSent {
  const OtpSent({required this.expiresIn, required this.resendAfter});

  final Duration expiresIn;
  final Duration resendAfter;

  factory OtpSent.fromJson(Object? json) {
    final m = asJsonMap(json);
    return OtpSent(
      expiresIn: Duration(seconds: (m['expires_in'] as num?)?.toInt() ?? 0),
      resendAfter: Duration(seconds: (m['resend_after'] as num?)?.toInt() ?? 0),
    );
  }
}

/// `POST /api/auth/verify-otp` → 200.
class VerifyResult {
  const VerifyResult({
    required this.tokens,
    required this.isNewFarmer,
    required this.profileComplete,
  });

  final AuthTokens tokens;
  final bool isNewFarmer;
  final bool profileComplete;

  factory VerifyResult.fromJson(Object? json) {
    final m = asJsonMap(json);
    return VerifyResult(
      tokens: AuthTokens(
        accessToken: m['access_token'] as String,
        refreshToken: m['refresh_token'] as String,
      ),
      isNewFarmer: m['is_new_farmer'] == true,
      profileComplete: m['profile_complete'] == true,
    );
  }
}
