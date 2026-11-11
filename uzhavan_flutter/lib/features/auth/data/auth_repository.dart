import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/networking/api_client.dart';
import '../../../core/networking/providers.dart';
import '../domain/auth_models.dart';

class AuthRepository {
  AuthRepository(this._api);
  final ApiClient _api;

  Future<OtpSent> sendOtp(String phone) async => OtpSent.fromJson(
        await _api.post('/api/auth/send-otp', body: {'phone': phone}, auth: false),
      );

  Future<VerifyResult> verifyOtp(String phone, String otp) async => VerifyResult.fromJson(
        await _api.post('/api/auth/verify-otp', body: {'phone': phone, 'otp': otp}, auth: false),
      );

  /// Revokes the refresh token server-side (204).
  Future<void> logout(String refreshToken) async {
    await _api.post('/api/auth/logout', body: {'refresh_token': refreshToken});
  }
}

final authRepositoryProvider =
    Provider<AuthRepository>((ref) => AuthRepository(ref.watch(apiClientProvider)));
