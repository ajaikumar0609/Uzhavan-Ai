import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/localization/bilingual_text.dart';
import '../../../core/localization/l10n.dart';
import '../../../core/networking/envelope.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../shared/utils/formatters.dart';
import '../../../shared/widgets/data_state_view.dart';
import '../../../shared/widgets/source_line.dart';
import '../../../shared/widgets/ui_kit.dart';
import '../data/market_repository.dart';
import '../domain/market_models.dart';

/// One observed price row: modal price, min–max (if present), market, date,
/// stale chip and the commodity's unit note. No advice.
class MarketObservationTile extends StatelessWidget {
  const MarketObservationTile({
    super.key,
    required this.obs,
    required this.meta,
    this.unitNote,
    this.onTap,
  });

  final MarketObservation obs;
  final ApiMeta meta;
  final BilingualText? unitNote;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final c = context.colors;
    final modal = Fmt.num(obs.modalPrice, digits: 2);
    final min = Fmt.num(obs.minPrice, digits: 2);
    final max = Fmt.num(obs.maxPrice, digits: 2);
    final unit = obs.unit ?? l.unitRsPerQuintal;
    final note = obs.unitNote ?? unitNote;
    final t = Theme.of(context).textTheme;
    return AppCard(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(context.bi(obs.commodityName), style: t.titleMedium?.copyWith(fontSize: 17, fontWeight: FontWeight.w700)),
                    if (obs.variety != null) Text(obs.variety!, style: t.bodySmall),
                  ],
                ),
              ),
              const SizedBox(width: AppSpace.md),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(modal == null ? l.notAvailable : '₹ $modal',
                      key: const Key('modal-price'), style: t.headlineSmall?.copyWith(color: c.primary)),
                  // The unit is always shown next to the price: rupees per quintal, never per kg.
                  Text(unit, style: t.labelSmall),
                ],
              ),
            ],
          ),
          if (min != null || max != null)
            Padding(
              padding: const EdgeInsets.only(top: AppSpace.xs),
              child: Text(l.marketMinMax(min ?? l.notAvailable, max ?? l.notAvailable), style: t.bodyMedium),
            ),
          const SizedBox(height: AppSpace.sm),
          Row(children: [
            Icon(Icons.storefront_outlined, size: 16, color: c.mutedForeground),
            const SizedBox(width: 6),
            Expanded(child: Text(obs.market, style: t.bodyMedium)),
          ]),
          if (note != null)
            Padding(
              padding: const EdgeInsets.only(top: AppSpace.sm),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.info_outline_rounded, size: 16, color: c.warning),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(l.unitNoteLabel(context.bi(note)), key: const Key('unit-note'), style: t.bodySmall),
                  ),
                ],
              ),
            ),
          Padding(
            padding: const EdgeInsets.only(top: AppSpace.md),
            child: Divider(color: c.border, height: 1),
          ),
          const SizedBox(height: AppSpace.sm),
          SourceLine(
            meta: meta,
            observedOn: obs.observedOn,
            stale: obs.isStale(),
          ),
          if (obs.observedOn == null) Text(l.observedOn(l.notAvailable), style: t.bodySmall),
        ],
      ),
    );
  }
}

/// Historical modal prices for one commodity at one market, one variety
/// at a time (the farmer picks the variety when several exist).
class MarketTrendCard extends ConsumerStatefulWidget {
  const MarketTrendCard({super.key, required this.query, required this.title});
  final TrendQuery query;
  final String title;

  @override
  ConsumerState<MarketTrendCard> createState() => _MarketTrendCardState();
}

class _MarketTrendCardState extends ConsumerState<MarketTrendCard> {
  String? _variety;

  @override
  void didUpdateWidget(MarketTrendCard old) {
    super.didUpdateWidget(old);
    if (old.query != widget.query) _variety = null;
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final c = context.colors;
    final query = widget.query;
    final value = ref.watch(marketTrendProvider(query));
    return DataStateView<Enveloped<List<TrendPoint>>>(
      value: value,
      unavailableText: l.marketUnavailable,
      padding: EdgeInsets.zero,
      isEmpty: (e) => e.data.isEmpty,
      emptyText: l.marketTrendEmpty,
      onRetry: () => ref.invalidate(marketTrendProvider(query)),
      builder: (context, env) {
        final byVariety = trendByVariety(env.data);
        final keys = byVariety.keys.toList()..sort();
        final selected = keys.contains(_variety) ? _variety! : keys.first;
        final pts = byVariety[selected]!;
        final first = pts.first.date;
        final spots = [
          for (final p in pts) FlSpot(p.date.difference(first).inDays.toDouble(), p.modalPrice),
        ];
        final lastX = spots.last.x;
        return InfoCard(
          key: const Key('market-trend'),
          title: widget.title,
          trailing: KindBadge(kind: env.meta.kind ?? 'historical'),
          children: [
            Text(l.marketTrendCaption(query.market, query.days), style: TextStyle(color: c.mutedForeground)),
            if (keys.length > 1) ...[
              const SizedBox(height: 8),
              Text(l.marketVariety, style: const TextStyle(fontWeight: FontWeight.w600)),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: [
                  for (final k in keys)
                    ChoiceChip(
                      key: Key('variety-$k'),
                      label: Text(k.isEmpty ? l.notAvailable : k),
                      selected: k == selected,
                      onSelected: (_) => setState(() => _variety = k),
                    ),
                ],
              ),
            ] else if (selected.isNotEmpty)
              Text(l.marketVarietyValue(selected), style: TextStyle(color: c.mutedForeground)),
            const SizedBox(height: 12),
            SizedBox(
              height: 220,
              child: LineChart(
                LineChartData(
                  gridData: const FlGridData(show: true, drawVerticalLine: false),
                  borderData: FlBorderData(show: false),
                  lineTouchData: LineTouchData(
                    touchTooltipData: LineTouchTooltipData(
                      getTooltipItems: (items) => [
                        for (final i in items)
                          LineTooltipItem(
                            '${Fmt.date(first.add(Duration(days: i.x.round())))}\n₹ ${Fmt.num(i.y, digits: 2)}',
                            const TextStyle(color: Colors.white, fontSize: 12),
                          ),
                      ],
                    ),
                  ),
                  titlesData: FlTitlesData(
                    topTitles: const AxisTitles(),
                    rightTitles: const AxisTitles(),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 52,
                        getTitlesWidget: (v, meta) => SideTitleWidget(
                          meta: meta,
                          child: Text(Fmt.num(v, digits: 0) ?? '', style: const TextStyle(fontSize: 10)),
                        ),
                      ),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 28,
                        interval: lastX <= 3 ? 1 : (lastX / 3).ceilToDouble(),
                        getTitlesWidget: (v, meta) {
                          final d = first.add(Duration(days: v.round()));
                          return SideTitleWidget(
                            meta: meta,
                            child: Text('${d.day}/${d.month}', style: const TextStyle(fontSize: 10)),
                          );
                        },
                      ),
                    ),
                  ),
                  lineBarsData: [
                    LineChartBarData(
                      spots: spots,
                      color: c.primary,
                      barWidth: 2.5,
                      dotData: FlDotData(show: spots.length <= 30),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(l.unitRsPerQuintal, style: TextStyle(color: c.mutedForeground, fontSize: 12)),
            SourceLine(meta: env.meta),
            NotesBlock(notes: env.meta.notes),
          ],
        );
      },
    );
  }
}
