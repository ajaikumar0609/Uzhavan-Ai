import 'package:flutter/material.dart';

import '../../core/localization/l10n.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_tokens.dart';

/// The UZHAVAN mark: a leaf on a forest tile. Drawn with an icon, no image asset to load.
class BrandMark extends StatelessWidget {
  const BrandMark({super.key, this.size = 64});
  final double size;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(color: c.primary, borderRadius: BorderRadius.circular(size * 0.3)),
      child: Icon(Icons.eco_rounded, color: c.accent, size: size * 0.56),
    );
  }
}

/// Mark, product name and tagline. Used on the splash and sign-in screens.
class BrandHeader extends StatelessWidget {
  const BrandHeader({super.key, this.centered = false});
  final bool centered;

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final c = context.colors;
    final t = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: centered ? CrossAxisAlignment.center : CrossAxisAlignment.start,
      children: [
        const BrandMark(),
        const SizedBox(height: AppSpace.lg),
        Text(l.appTitle, style: t.headlineMedium?.copyWith(color: c.primary, letterSpacing: 0.2)),
        const SizedBox(height: AppSpace.xs),
        Text(
          l.brandTagline,
          textAlign: centered ? TextAlign.center : TextAlign.start,
          style: t.bodyLarge?.copyWith(color: c.mutedForeground),
        ),
      ],
    );
  }
}
