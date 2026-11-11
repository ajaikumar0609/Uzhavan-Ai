import 'package:flutter/material.dart';

import '../../core/localization/bilingual_text.dart';
import '../../core/localization/l10n.dart';
import '../../core/networking/envelope.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_tokens.dart';
import '../utils/formatters.dart';
import 'ui_kit.dart';

/// "Source: Open-Meteo · Updated 10:30" (or "Observed on 2026-09-24"),
/// plus an "old data" chip when the data is stale. Shown on every data card.
class SourceLine extends StatelessWidget {
  const SourceLine({
    super.key,
    required this.meta,
    this.observedOn,
    this.stale = false,
    this.sourceOverride,
  });

  final ApiMeta meta;

  /// Market rows: the observation date replaces "Updated".
  final DateTime? observedOn;
  final bool stale;

  /// A per-item source (e.g. a soil section's own `source`).
  final String? sourceOverride;

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final c = context.colors;
    final source = sourceOverride ?? meta.source;
    final parts = <String>[
      l.sourceLabel(source ?? l.notAvailable),
      if (observedOn != null)
        l.observedOn(Fmt.date(observedOn)!)
      else if (meta.retrievedAt != null)
        l.updatedAt(Fmt.time(meta.retrievedAt)!),
    ];
    final style = Theme.of(context).textTheme.bodySmall?.copyWith(color: c.mutedForeground);
    return Wrap(
      key: const Key('source-line'),
      spacing: 8,
      runSpacing: 4,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.verified_outlined, size: 14, color: c.mutedForeground),
            const SizedBox(width: 4),
            Flexible(child: Text(parts.join(' · '), style: style)),
          ],
        ),
        if (stale || meta.stale) const StaleChip(),
      ],
    );
  }
}

class StaleChip extends StatelessWidget {
  const StaleChip({super.key});

  @override
  Widget build(BuildContext context) => StatusBadge(
        key: const Key('stale-chip'),
        label: context.l10n.oldData,
        tone: Tone.caution,
        icon: Icons.history_rounded,
      );
}

/// The contract's `meta.kind`, as a small label.
class KindBadge extends StatelessWidget {
  const KindBadge({super.key, required this.kind});
  final String? kind;

  static String? label(BuildContext context, String? kind) {
    final l = context.l10n;
    return switch (kind) {
      'current' => l.kindCurrent,
      'forecast' => l.kindForecast,
      'historical' => l.kindHistorical,
      'latest_observed' => l.kindLatestObserved,
      'estimated' => l.kindEstimated,
      'measured' => l.kindMeasured,
      'reference' => l.kindReference,
      _ => null,
    };
  }

  /// Tone and icon make the nature of the data obvious at a glance: a forecast is not a
  /// measurement, and an observed snapshot is not a live price.
  static (Tone, IconData) style(String? kind) => switch (kind) {
        'current' => (Tone.brand, Icons.sensors_rounded),
        'forecast' => (Tone.info, Icons.timeline_rounded),
        'historical' => (Tone.neutral, Icons.history_rounded),
        'latest_observed' => (Tone.caution, Icons.photo_camera_back_outlined),
        'estimated' => (Tone.caution, Icons.calculate_outlined),
        'measured' => (Tone.positive, Icons.science_outlined),
        _ => (Tone.neutral, Icons.menu_book_outlined),
      };

  @override
  Widget build(BuildContext context) {
    final text = label(context, kind);
    if (text == null) return const SizedBox.shrink();
    final (tone, icon) = style(kind);
    return StatusBadge(label: text, tone: tone, icon: icon);
  }
}

/// `meta.notes` as info lines (e.g. "Official IMD warnings not integrated").
class NotesBlock extends StatelessWidget {
  const NotesBlock({super.key, required this.notes});
  final List<BilingualText> notes;

  @override
  Widget build(BuildContext context) {
    if (notes.isEmpty) return const SizedBox.shrink();
    final c = context.colors;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final n in notes)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.info_outline, size: 16, color: c.info),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(context.bi(n),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(color: c.mutedForeground)),
                ),
              ],
            ),
          ),
      ],
    );
  }
}

/// A padded card with an optional title row and trailing widget.
class InfoCard extends StatelessWidget {
  const InfoCard({
    super.key,
    this.title,
    this.trailing,
    required this.children,
    this.color,
    this.borderColor,
  });

  final String? title;
  final Widget? trailing;
  final List<Widget> children;
  final Color? color;
  final Color? borderColor;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      color: color,
      borderColor: borderColor,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (title != null || trailing != null)
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpace.sm),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  if (title != null)
                    Expanded(child: Text(title!, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontSize: 17, fontWeight: FontWeight.w700))),
                  if (title != null && trailing != null) const SizedBox(width: AppSpace.sm),
                  ?trailing,
                ],
              ),
            ),
          ...children,
        ],
      ),
    );
  }
}

/// `label: value`, with "not available" for null.
class KV extends StatelessWidget {
  const KV(this.label, this.value, {super.key});
  final String label;
  final String? value;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final t = Theme.of(context).textTheme;
    final missing = value == null;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(flex: 5, child: Text(label, style: t.bodyMedium?.copyWith(color: c.mutedForeground))),
          const SizedBox(width: AppSpace.md),
          Expanded(
            flex: 5,
            child: Text(
              value ?? context.l10n.notAvailable,
              style: t.bodyMedium?.copyWith(
                fontWeight: missing ? FontWeight.w400 : FontWeight.w600,
                fontStyle: missing ? FontStyle.italic : null,
                color: missing ? c.mutedForeground : c.foreground,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Server bilingual text, or "not available" for null.
String biOr(BuildContext context, BilingualText? t) =>
    t == null ? context.l10n.notAvailable : context.bi(t);
