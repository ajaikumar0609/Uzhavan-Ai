import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/auth_repository.dart';

/// The phone number an OTP was sent to, and the server's timers.
@immutable
class OtpFlow {
  const OtpFlow({
    required this.phone,
    required this.resendAfter,
    required this.expiresIn,
    required this.attempt,
  });

  final String phone;
  final Duration resendAfter;
  final Duration expiresIn;

  /// Increments on every successful send (restarts the resend countdown).
  final int attempt;
}

class OtpFlowController extends Notifier<OtpFlow?> {
  @override
  OtpFlow? build() => null;

  /// Sends (or resends) the OTP. Throws `ApiFailure`.
  Future<void> send(String phone) async {
    final sent = await ref.read(authRepositoryProvider).sendOtp(phone);
    state = OtpFlow(
      phone: phone,
      resendAfter: sent.resendAfter,
      expiresIn: sent.expiresIn,
      attempt: (state?.attempt ?? 0) + 1,
    );
  }

  void reset() => state = null;
}

final otpFlowProvider = NotifierProvider<OtpFlowController, OtpFlow?>(OtpFlowController.new);
