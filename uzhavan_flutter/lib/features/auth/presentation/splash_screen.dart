import 'package:flutter/material.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../shared/widgets/brand.dart';

/// Shown only while the stored session is being restored.
class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(AppSpace.xxxl),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const BrandHeader(centered: true),
                const SizedBox(height: AppSpace.xxxl),
                Semantics(
                  label: l.loading,
                  child: const SizedBox(width: 28, height: 28, child: CircularProgressIndicator(strokeWidth: 2.5)),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
