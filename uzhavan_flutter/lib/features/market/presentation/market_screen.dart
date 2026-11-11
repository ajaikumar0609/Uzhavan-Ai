import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/networking/envelope.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/data_state_view.dart';
import '../../../shared/widgets/option_picker_field.dart';
import '../../../shared/widgets/source_line.dart';
import '../../../shared/widgets/ui_kit.dart';
import '../../meta/presentation/meta_providers.dart';
import '../../profile/presentation/profile_controller.dart';
import '../data/market_repository.dart';
import '../domain/market_models.dart';
import 'market_widgets.dart';

/// Contract §5: latest observed prices + a historical trend. No advice.
class MarketScreen extends ConsumerStatefulWidget {
  const MarketScreen({super.key});

  @override
  ConsumerState<MarketScreen> createState() => _MarketScreenState();
}

class _MarketScreenState extends ConsumerState<MarketScreen> {
  String? _commodity;
  String? _district;
  bool _districtTouched = false;
  TrendQuery? _trend;
  String? _trendTitle;

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final profileDistrict = ref.watch(profileProvider).value?.districtId;
    final district = _districtTouched ? _district : profileDistrict;
    final commodities = ref.watch(commoditiesProvider);
    final commodityList = commodities.value?.data ?? const <Commodity>[];
    final query = LatestQuery(commodity: _commodity, districtId: district);
    final latest = ref.watch(marketLatestProvider(query));

    return AppScaffold(
      title: l.featureMarket,
      automaticallyImplyLeading: false,
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(commoditiesProvider);
          ref.invalidate(marketLatestProvider(query));
        },
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
          children: [
            _CommodityChips(
              value: commodities,
              selected: _commodity,
              onSelected: (id) => setState(() {
                _commodity = id;
                _trend = null;
              }),
              onRetry: () => ref.invalidate(commoditiesProvider),
            ),
            const SizedBox(height: 8),
            OptionPickerField(
              label: l.marketDistrictFilter,
              options: ref.watch(districtOptionsProvider),
              selectedId: district,
              allowNone: true,
              searchable: true,
              unavailableText: l.districtsUnavailable,
              onRetry: () => ref.invalidate(districtsProvider),
              onChanged: (id) => setState(() {
                _district = id;
                _districtTouched = true;
              }),
            ),
            const SizedBox(height: 12),
            if (_trend != null) ...[
              Stack(
                children: [
                  MarketTrendCard(query: _trend!, title: _trendTitle ?? l.marketTrend),
                  PositionedDirectional(
                    top: 4,
                    end: 4,
                    child: IconButton(
                      tooltip: l.close,
                      icon: const Icon(Icons.close),
                      onPressed: () => setState(() => _trend = null),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
            ],
            Row(
              children: [
                Expanded(child: Text(l.marketLatestTitle, style: Theme.of(context).textTheme.titleLarge)),
                // Always visible: these are observed snapshots, not live prices.
                StatusBadge(
                  key: const Key('market-snapshot-badge'),
                  label: l.marketSnapshotBadge,
                  tone: Tone.caution,
                  icon: Icons.photo_camera_back_outlined,
                ),
              ],
            ),
            const SizedBox(height: 2),
            Text(l.marketTapForTrend, style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: AppSpace.sm),
            DataStateView<Enveloped<List<MarketObservation>>>(
              value: latest,
              unavailableText: l.marketUnavailable,
              padding: EdgeInsets.zero,
              isEmpty: (e) => e.data.isEmpty,
              emptyText: l.marketEmpty,
              onRetry: () => ref.invalidate(marketLatestProvider(query)),
              builder: (context, env) => Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  NotesBlock(notes: env.meta.notes),
                  const SizedBox(height: AppSpace.md),
                  for (final o in env.data) ...[
                    MarketObservationTile(
                      obs: o,
                      meta: env.meta,
                      unitNote: commodityList.where((c) => c.id == o.commodity).firstOrNull?.unitNote,
                      onTap: o.market.isEmpty || o.commodity.isEmpty
                          ? null
                          : () => setState(() {
                                _trend = TrendQuery(commodity: o.commodity, market: o.market);
                                _trendTitle = l.marketTrendTitle(context.bi(o.commodityName));
                              }),
                    ),
                    const SizedBox(height: AppSpace.md),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CommodityChips extends StatelessWidget {
  const _CommodityChips({
    required this.value,
    required this.selected,
    required this.onSelected,
    required this.onRetry,
  });

  final AsyncValue<Enveloped<List<Commodity>>> value;
  final String? selected;
  final ValueChanged<String?> onSelected;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    return DataStateView<Enveloped<List<Commodity>>>(
      value: value,
      unavailableText: l.marketUnavailable,
      padding: EdgeInsets.zero,
      loadingLines: 1,
      isEmpty: (e) => e.data.isEmpty,
      onRetry: onRetry,
      builder: (context, env) => SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            Padding(
              padding: const EdgeInsetsDirectional.only(end: 8),
              child: ChoiceChip(
                label: Text(l.allCommodities),
                selected: selected == null,
                onSelected: (_) => onSelected(null),
              ),
            ),
            for (final c in env.data)
              Padding(
                padding: const EdgeInsetsDirectional.only(end: 8),
                child: ChoiceChip(
                  key: Key('commodity-${c.id}'),
                  label: Text(context.bi(c.name)),
                  selected: selected == c.id,
                  onSelected: (_) => onSelected(c.id),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
