import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/networking/api_failure.dart';
import '../../../core/routing/routes.dart';
import '../../../shared/utils/failure_text.dart';
import '../../../shared/utils/validators.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/error_banner.dart';
import 'otp_flow_controller.dart';
import 'session_controller.dart';

class OtpScreen extends ConsumerStatefulWidget {
  const OtpScreen({super.key});

  static const otpFieldKey = Key('otp-field');
  static const verifyButtonKey = Key('verify-otp');
  static const resendButtonKey = Key('resend-otp');

  @override
  ConsumerState<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends ConsumerState<OtpScreen> {
  final _otp = TextEditingController();
  Timer? _timer;
  int _secondsLeft = 0;
  int _attemptShown = -1;
  bool _busy = false;
  ApiFailure? _failure;

  @override
  void initState() {
    super.initState();
    _otp.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _timer?.cancel();
    _otp.dispose();
    super.dispose();
  }

  void _startCountdown(OtpFlow flow) {
    _attemptShown = flow.attempt;
    _timer?.cancel();
    _secondsLeft = flow.resendAfter.inSeconds;
    if (_secondsLeft <= 0) return;
    _timer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (!mounted) return t.cancel();
      setState(() => _secondsLeft = _secondsLeft > 0 ? _secondsLeft - 1 : 0);
      if (_secondsLeft == 0) t.cancel();
    });
  }

  Future<void> _verify(OtpFlow flow) async {
    if (!Validators.isValidOtp(_otp.text)) return;
    setState(() {
      _busy = true;
      _failure = null;
    });
    try {
      await ref.read(sessionProvider.notifier).signInWithOtp(flow.phone, _otp.text.trim());
      ref.read(otpFlowProvider.notifier).reset();
      // The router redirect moves on to onboarding or home.
    } on ApiFailure catch (f) {
      if (mounted) setState(() => _failure = f);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _resend(OtpFlow flow) async {
    setState(() {
      _busy = true;
      _failure = null;
    });
    try {
      await ref.read(otpFlowProvider.notifier).send(flow.phone);
      _otp.clear();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(context.l10n.otpResent)));
      }
    } on ApiFailure catch (f) {
      if (mounted) setState(() => _failure = f);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final flow = ref.watch(otpFlowProvider);
    if (flow == null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) context.go(Routes.login);
      });
      return const SizedBox.shrink();
    }
    if (flow.attempt != _attemptShown) _startCountdown(flow);

    final valid = Validators.isValidOtp(_otp.text);
    final failure = _failure;
    return AppScaffold(
      title: l.otpTitle,
      automaticallyImplyLeading: false,
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(l.otpSentTo(flow.phone), style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 24),
          TextField(
            key: OtpScreen.otpFieldKey,
            controller: _otp,
            keyboardType: TextInputType.number,
            autofillHints: const [AutofillHints.oneTimeCode],
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(letterSpacing: 8),
            inputFormatters: [
              FilteringTextInputFormatter.digitsOnly,
              LengthLimitingTextInputFormatter(6),
            ],
            decoration: InputDecoration(
              labelText: l.otpLabel,
              helperText: valid || _otp.text.isEmpty ? null : l.otpInvalid,
            ),
            onSubmitted: (_) => _verify(flow),
          ),
          if (failure != null) ...[
            const SizedBox(height: 12),
            ErrorBanner(
              key: const Key('otp-error'),
              text: failureText(l, Localizations.localeOf(context), failure),
            ),
          ],
          const SizedBox(height: 24),
          FilledButton(
            key: OtpScreen.verifyButtonKey,
            onPressed: valid && !_busy ? () => _verify(flow) : null,
            child: _busy
                ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2))
                : Text(l.verify),
          ),
          const SizedBox(height: 12),
          TextButton(
            key: OtpScreen.resendButtonKey,
            onPressed: _secondsLeft == 0 && !_busy ? () => _resend(flow) : null,
            child: Text(_secondsLeft > 0 ? l.resendIn(_secondsLeft) : l.resendOtp),
          ),
          TextButton(
            onPressed: _busy ? null : () => context.go(Routes.login),
            child: Text(l.changeNumber),
          ),
        ],
      ),
    );
  }
}
