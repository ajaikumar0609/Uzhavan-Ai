import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/networking/api_failure.dart';
import '../../../core/routing/routes.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../shared/widgets/brand.dart';
import '../../../shared/widgets/error_banner.dart';
import '../../../shared/utils/failure_text.dart';
import '../../../shared/utils/validators.dart';
import '../../../shared/widgets/app_scaffold.dart';
import 'otp_flow_controller.dart';
import 'session_controller.dart';

class PhoneScreen extends ConsumerStatefulWidget {
  const PhoneScreen({super.key});

  static const phoneFieldKey = Key('phone-field');
  static const sendButtonKey = Key('send-otp');

  @override
  ConsumerState<PhoneScreen> createState() => _PhoneScreenState();
}

class _PhoneScreenState extends ConsumerState<PhoneScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phone = TextEditingController();
  bool _sending = false;
  ApiFailure? _failure;

  @override
  void initState() {
    super.initState();
    final flow = ref.read(otpFlowProvider);
    if (flow != null) _phone.text = flow.phone;
  }

  @override
  void dispose() {
    _phone.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _failure = null);
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() => _sending = true);
    try {
      await ref.read(otpFlowProvider.notifier).send(_phone.text.trim());
      if (mounted) context.go(Routes.otp);
    } on ApiFailure catch (f) {
      if (mounted) setState(() => _failure = f);
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final expired = ref.watch(sessionProvider.select((s) => s.expired));
    final failure = _failure;
    return AppScaffold(
      title: l.loginTitle,
      automaticallyImplyLeading: false,
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(AppSpace.xxl, AppSpace.lg, AppSpace.xxl, AppSpace.xxxl),
          children: [
            const BrandHeader(),
            const SizedBox(height: AppSpace.xxxl),
            Text(l.loginSubtitle, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: AppSpace.xs),
            Text(l.loginPhoneHelp, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: context.colors.mutedForeground)),
            if (expired) ...[
              const SizedBox(height: AppSpace.md),
              ErrorBanner(text: l.errSessionExpired),
            ],
            const SizedBox(height: AppSpace.xl),
            TextFormField(
              key: PhoneScreen.phoneFieldKey,
              controller: _phone,
              keyboardType: TextInputType.phone,
              autofillHints: const [AutofillHints.telephoneNumberNational],
              inputFormatters: [
                FilteringTextInputFormatter.digitsOnly,
                LengthLimitingTextInputFormatter(10),
              ],
              decoration: InputDecoration(
                labelText: l.phoneLabel,
                hintText: l.phoneHint,
                prefixText: '${l.phonePrefix} ',
                prefixIcon: const Icon(Icons.phone_iphone_rounded),
              ),
              validator: (v) => Validators.isValidPhone(v ?? '') ? null : l.phoneInvalid,
              onFieldSubmitted: (_) => _submit(),
            ),
            if (failure != null) ...[
              const SizedBox(height: 12),
              ErrorBanner(
                key: const Key('phone-error'),
                text: failureText(l, Localizations.localeOf(context), failure),
              ),
            ],
            const SizedBox(height: 24),
            FilledButton(
              key: PhoneScreen.sendButtonKey,
              onPressed: _sending ? null : _submit,
              child: _sending
                  ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2))
                  : Text(l.sendOtp),
            ),
          ],
        ),
      ),
    );
  }
}
