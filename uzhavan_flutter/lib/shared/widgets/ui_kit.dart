import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_tokens.dart';

/// Semantic tone for badges, notices and icon tiles.
enum Tone { neutral, brand, positive, caution, critical, info }

extension ToneColors on Tone {
  /// (foreground/ink, soft background, border)
  (Color, Color, Color) resolve(AppColors c) => switch (this) {
        Tone.neutral => (c.mutedForeground, c.muted, c.border),
        Tone.brand => (c.secondary, c.primarySoft, c.secondary.withValues(alpha: 0.25)),
        Tone.positive => (c.success, c.success.withValues(alpha: 0.10), c.success.withValues(alpha: 0.30)),
        Tone.caution => (c.warning, c.warning.withValues(alpha: 0.10), c.warning.withValues(alpha: 0.35)),
        Tone.critical => (c.danger, c.danger.withValues(alpha: 0.08), c.danger.withValues(alpha: 0.35)),
        Tone.info => (c.info, c.info.withValues(alpha: 0.08), c.info.withValues(alpha: 0.30)),
      };
}

/// The standard raised surface: white card, hairline border, one soft shadow. Tappable cards
/// get ink feedback clipped to the card's radius.
class AppCard extends StatelessWidget {
  const AppCard({
    super.key,
    required this.child,
    this.onTap,
    this.padding = const EdgeInsets.all(AppSpace.lg),
    this.color,
    this.borderColor,
    this.raised = true,
    this.semanticLabel,
  });

  final Widget child;
  final VoidCallback? onTap;
  final EdgeInsetsGeometry padding;
  final Color? color;
  final Color? borderColor;
  final bool raised;
  final String? semanticLabel;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final radius = AppRadius.card;
    final content = Padding(padding: padding, child: child);
    return Semantics(
      container: true,
      button: onTap != null,
      label: semanticLabel,
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: color ?? c.card,
          borderRadius: radius,
          border: Border.all(color: borderColor ?? c.border, width: borderColor == null ? 1 : 1.4),
          boxShadow: raised ? AppShadows.card(c) : null,
        ),
        child: Material(
          type: MaterialType.transparency,
          borderRadius: radius,
          clipBehavior: Clip.antiAlias,
          child: onTap == null ? content : InkWell(onTap: onTap, child: content),
        ),
      ),
    );
  }
}

/// Section heading with an optional trailing action ("See all").
class SectionHeader extends StatelessWidget {
  const SectionHeader(this.title, {super.key, this.actionLabel, this.onAction, this.padding});
  final String title;
  final String? actionLabel;
  final VoidCallback? onAction;
  final EdgeInsetsGeometry? padding;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: padding ?? const EdgeInsets.only(bottom: AppSpace.sm),
      child: Row(
        children: [
          Expanded(
            child: Semantics(
              header: true,
              child: Text(title, style: Theme.of(context).textTheme.titleLarge),
            ),
          ),
          if (onAction != null && actionLabel != null)
            TextButton(
              onPressed: onAction,
              style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
              child: Text(actionLabel!),
            ),
        ],
      ),
    );
  }
}

/// A small pill label ("Forecast", "Snapshot", "Under validation").
class StatusBadge extends StatelessWidget {
  const StatusBadge({super.key, required this.label, this.tone = Tone.neutral, this.icon});
  final String label;
  final Tone tone;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final (ink, bg, border) = tone.resolve(context.colors);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: bg, borderRadius: AppRadius.chip, border: Border.all(color: border)),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[Icon(icon, size: 14, color: ink), const SizedBox(width: 4)],
          Flexible(
            child: Text(
              label,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(color: ink, fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

/// A rounded square holding an icon; the consistent leading element for tiles and shortcuts.
class IconTile extends StatelessWidget {
  const IconTile(this.icon, {super.key, this.tone = Tone.brand, this.size = 44});
  final IconData icon;
  final Tone tone;
  final double size;

  @override
  Widget build(BuildContext context) {
    final (ink, bg, _) = tone.resolve(context.colors);
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(size * 0.32)),
      child: Icon(icon, color: ink, size: size * 0.52),
    );
  }
}

/// An inline notice: icon, message, optional action. Used for safety and status information.
class NoticeBanner extends StatelessWidget {
  const NoticeBanner({
    super.key,
    required this.text,
    this.title,
    this.tone = Tone.info,
    this.icon,
    this.trailing,
  });

  final String text;
  final String? title;
  final Tone tone;
  final IconData? icon;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    final (ink, bg, border) = tone.resolve(context.colors);
    final t = Theme.of(context).textTheme;
    final defaultIcon = switch (tone) {
      Tone.caution => Icons.warning_amber_rounded,
      Tone.critical => Icons.error_outline_rounded,
      Tone.positive => Icons.check_circle_outline_rounded,
      _ => Icons.info_outline_rounded,
    };
    return Container(
      padding: const EdgeInsets.fromLTRB(AppSpace.md, AppSpace.md, AppSpace.sm, AppSpace.md),
      decoration: BoxDecoration(color: bg, borderRadius: AppRadius.control, border: Border.all(color: border)),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(padding: const EdgeInsets.only(top: 1), child: Icon(icon ?? defaultIcon, size: 20, color: ink)),
          const SizedBox(width: AppSpace.sm + 2),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (title != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 2),
                    child: Text(title!, style: t.titleSmall),
                  ),
                Text(text, style: t.bodyMedium?.copyWith(height: 1.45)),
              ],
            ),
          ),
          ?trailing,
        ],
      ),
    );
  }
}

/// A calm placeholder block shown while data loads (no shimmer package, no heavy animation).
class Skeleton extends StatefulWidget {
  const Skeleton({super.key, this.height = 16, this.width, this.radius = AppRadius.sm});
  final double height;
  final double? width;
  final double radius;

  @override
  State<Skeleton> createState() => _SkeletonState();
}

class _SkeletonState extends State<Skeleton> with SingleTickerProviderStateMixin {
  late final AnimationController _a =
      AnimationController(vsync: this, duration: const Duration(milliseconds: 900))..repeat(reverse: true);

  @override
  void dispose() {
    _a.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return FadeTransition(
      opacity: Tween<double>(begin: 0.55, end: 1).animate(_a),
      child: Container(
        height: widget.height,
        width: widget.width,
        decoration: BoxDecoration(color: c.muted, borderRadius: BorderRadius.circular(widget.radius)),
      ),
    );
  }
}

/// A card-shaped loading placeholder: a title line and a few body lines.
class SkeletonCard extends StatelessWidget {
  const SkeletonCard({super.key, this.lines = 3});
  final int lines;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      raised: false,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Skeleton(height: 18, width: 140),
          for (var i = 0; i < lines; i++) ...[
            const SizedBox(height: AppSpace.md),
            Skeleton(height: 14, width: i.isEven ? null : 200),
          ],
        ],
      ),
    );
  }
}
