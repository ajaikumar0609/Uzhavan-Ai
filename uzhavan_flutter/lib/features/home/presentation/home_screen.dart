import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/networking/envelope.dart';
import '../../../core/routing/routes.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../shared/utils/area_units.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/data_state_view.dart';
import '../../../shared/widgets/ui_kit.dart';
import '../../diary/data/diary_repository.dart';
import '../../diary/domain/diary_models.dart';
import '../../diary/presentation/diary_screen.dart';
import '../../farm/domain/farm.dart';
import '../../farm/presentation/farms_controller.dart';
import '../../farm/presentation/location_gate.dart';
import '../../farm/presentation/selected_farm.dart';
import '../../market/data/market_repository.dart';
import '../../market/domain/market_models.dart';
import '../../market/presentation/market_widgets.dart';
import '../../meta/domain/meta_models.dart';
import '../../meta/presentation/meta_providers.dart';
import '../../profile/presentation/profile_controller.dart';
import '../../weather/data/weather_repository.dart';
import '../../weather/presentation/weather_widgets.dart';

/// Dashboard from real data only: no scores, counts or invented metrics.
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final c = context.colors;
    final t = Theme.of(context).textTheme;
    final name = ref.watch(profileProvider).value?.name;
    final locale = Localizations.localeOf(context).toString();
    return AppScaffold(
      title: l.featureHome,
      automaticallyImplyLeading: false,
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(farmsProvider);
          ref.invalidate(profileProvider);
          ref.invalidate(diaryProvider);
          ref.invalidate(weatherCurrentProvider);
          ref.invalidate(weatherForecastProvider);
          ref.invalidate(marketLatestProvider);
        },
        child: ListView(
          // The dashboard is short; build it all so nothing pops in while scrolling.
          cacheExtent: 4000,
          padding: const EdgeInsets.fromLTRB(AppSpace.page, AppSpace.sm, AppSpace.page, AppSpace.xxxl),
          children: [
            Text(
              name == null ? l.homeGreetingNoName : l.homeGreeting(name),
              key: const Key('home-greeting'),
              style: t.headlineMedium,
            ),
            const SizedBox(height: 2),
            // Today's date from the device clock (not data, never invented).
            Text(DateFormat.MMMMEEEEd(locale).format(DateTime.now()), style: t.bodyMedium?.copyWith(color: c.mutedForeground)),
            const SizedBox(height: AppSpace.lg),
            const FarmPicker(),
            const _FarmSummary(),
            const SizedBox(height: AppSpace.md),
            const _AskCard(),
            const SizedBox(height: AppSpace.xxl),
            SectionHeader(l.featureWeather, actionLabel: l.homeSeeAll, onAction: () => context.go(Routes.weather)),
            LocationGate(
              builder: (context, loc) => Column(
                children: [
                  WeatherCurrentCard(loc: loc, compact: true),
                  const SizedBox(height: AppSpace.sm),
                  WeatherForecastCard(loc: loc, maxDays: 1),
                ],
              ),
            ),
            const SizedBox(height: AppSpace.xxl),
            SectionHeader(l.homeServices),
            const _Shortcuts(),
            const SizedBox(height: AppSpace.xxl),
            SectionHeader(l.homeMarketSnapshot, actionLabel: l.homeSeeAll, onAction: () => context.go(Routes.market)),
            const _MarketSnapshot(),
            const SizedBox(height: AppSpace.xxl),
            SectionHeader(l.homeRecentActivity, actionLabel: l.homeSeeAll, onAction: () => context.go(Routes.diary)),
            const _RecentActivity(),
          ],
        ),
      ),
    );
  }
}

/// The farm, shown prominently on a forest surface: name, then crop / stage / area.
class _FarmSummary extends ConsumerWidget {
  const _FarmSummary();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final c = context.colors;
    final t = Theme.of(context).textTheme;
    final crops = ref.watch(cropsProvider).value;
    final enums = ref.watch(enumsProvider).value;
    return DataStateView<Farm?>(
      value: ref.watch(selectedFarmProvider),
      unavailableText: l.farmsUnavailable,
      padding: EdgeInsets.zero,
      isEmpty: (f) => f == null,
      emptyText: l.homeNoFarm,
      emptyAction: FilledButton.tonal(
        key: const Key('home-add-farm'),
        style: FilledButton.styleFrom(minimumSize: const Size(0, 44)),
        onPressed: () => context.go(Routes.farmNew),
        child: Text(l.farmAdd),
      ),
      onRetry: () => ref.invalidate(farmsProvider),
      builder: (context, farm) {
        final f = farm!;
        String? label(List<RefItem>? items, String? id) {
          if (id == null) return null;
          final tx = labelFor(items, id);
          return tx == null ? id : context.bi(tx);
        }

        final area = f.areaHa;
        final on = c.primaryForeground;
        return AppCard(
          key: const Key('home-farm'),
          color: c.primary,
          borderColor: c.primary,
          padding: const EdgeInsets.fromLTRB(AppSpace.xl, AppSpace.lg, AppSpace.sm, AppSpace.xl),
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
                        const SizedBox(height: AppSpace.xs),
                        Text(l.homeFarmLabel.toUpperCase(),
                            style: t.labelSmall?.copyWith(color: on.withValues(alpha: 0.72), letterSpacing: 0.9)),
                        const SizedBox(height: 2),
                        Text(f.name, style: t.headlineSmall?.copyWith(color: on), maxLines: 2, overflow: TextOverflow.ellipsis),
                      ],
                    ),
                  ),
                  IconButton(
                    tooltip: l.edit,
                    icon: Icon(Icons.edit_outlined, color: on.withValues(alpha: 0.9)),
                    onPressed: () => context.go(Routes.farmEdit(f.farmId)),
                  ),
                ],
              ),
              const SizedBox(height: AppSpace.lg),
              Padding(
                padding: const EdgeInsets.only(right: AppSpace.md),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(child: _FarmStat(Icons.grass_rounded, l.farmCrop, label(crops, f.cropId))),
                    Expanded(child: _FarmStat(Icons.timelapse_rounded, l.farmStage, label(enums?.cropStages, f.cropStageId))),
                    Expanded(
                      child: _FarmStat(
                        Icons.straighten_rounded,
                        l.farmArea,
                        area == null
                            ? null
                            : l.farmAreaValue(AreaUnits.formatAcres(area, locale: Localizations.localeOf(context).toString())),
                      ),
                    ),
                  ],
                ),
              ),
              if (f.cropId == null)
                Padding(
                  padding: const EdgeInsets.only(top: AppSpace.md, right: AppSpace.md),
                  child: Text(l.homeSetCrop, style: t.bodySmall?.copyWith(color: on.withValues(alpha: 0.8))),
                ),
            ],
          ),
        );
      },
    );
  }
}

class _FarmStat extends StatelessWidget {
  const _FarmStat(this.icon, this.label, this.value);
  final IconData icon;
  final String label;
  final String? value;

  @override
  Widget build(BuildContext context) {
    final on = context.colors.primaryForeground;
    final t = Theme.of(context).textTheme;
    final missing = value == null;
    return Padding(
      padding: const EdgeInsets.only(right: AppSpace.sm),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: on.withValues(alpha: 0.72)),
          const SizedBox(height: 6),
          Text(label, style: t.bodySmall?.copyWith(color: on.withValues(alpha: 0.72)), maxLines: 2, overflow: TextOverflow.ellipsis),
          const SizedBox(height: 2),
          Text(
            value ?? context.l10n.notAvailable,
            style: t.titleSmall?.copyWith(
              color: on.withValues(alpha: missing ? 0.72 : 1),
              fontStyle: missing ? FontStyle.italic : null,
              fontWeight: missing ? FontWeight.w400 : FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

/// Entry point to the assistant: the app's main capability, one tap from Home.
class _AskCard extends StatelessWidget {
  const _AskCard();

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final c = context.colors;
    final t = Theme.of(context).textTheme;
    return AppCard(
      key: Key('shortcut-${Routes.assistant}'),
      onTap: () => context.go(Routes.assistant),
      semanticLabel: l.homeAskTitle,
      child: Row(
        children: [
          const IconTile(Icons.forum_rounded, size: 48),
          const SizedBox(width: AppSpace.lg),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l.homeAskTitle, style: t.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 2),
                Text(l.homeAskSubtitle, style: t.bodySmall),
              ],
            ),
          ),
          const SizedBox(width: AppSpace.sm),
          Icon(Icons.arrow_forward_rounded, color: c.secondary),
        ],
      ),
    );
  }
}

class _MarketSnapshot extends ConsumerWidget {
  const _MarketSnapshot();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final farm = ref.watch(selectedFarmProvider).value;
    final district = farm?.districtId ?? ref.watch(profileProvider).value?.districtId;
    final crop = farm?.cropId;
    if (district == null && crop == null) {
      return NoticeBanner(text: l.homeMarketNeedsFarm, tone: Tone.neutral);
    }
    // Crops with no market series (e.g. chilli, sugarcane) → honest empty,
    // not an error and not another crop's prices.
    final commoditiesValue = ref.watch(commoditiesProvider);
    if (crop != null && commoditiesValue.isLoading && !commoditiesValue.hasValue) {
      return const DataStateCard(status: DataStatus.loading, message: '', padding: EdgeInsets.zero, loadingLines: 2);
    }
    final commodities = commoditiesValue.hasError ? null : commoditiesValue.value?.data;
    if (crop != null && commodities != null && !commodities.any((c) => c.id == crop)) {
      return DataStateCard(
        key: const Key('home-market-no-crop'),
        padding: EdgeInsets.zero,
        status: DataStatus.empty,
        message: l.homeNoMarketForCrop,
      );
    }
    final q = LatestQuery(commodity: crop, districtId: district, limit: 3);
    return DataStateView<Enveloped<List<MarketObservation>>>(
      value: ref.watch(marketLatestProvider(q)),
      unavailableText: l.marketUnavailable,
      padding: EdgeInsets.zero,
      isEmpty: (e) => e.data.isEmpty,
      emptyText: crop == null ? l.marketEmpty : l.homeNoMarketForCrop,
      onRetry: () => ref.invalidate(marketLatestProvider(q)),
      builder: (context, env) => Column(
        children: [
          for (final o in env.data.take(3)) ...[
            MarketObservationTile(obs: o, meta: env.meta, onTap: () => context.go(Routes.market)),
            const SizedBox(height: 8),
          ],
        ],
      ),
    );
  }
}

class _RecentActivity extends ConsumerWidget {
  const _RecentActivity();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    return DataStateView<List<DiaryEntry>>(
      value: ref.watch(diaryProvider),
      unavailableText: l.diaryUnavailable,
      padding: EdgeInsets.zero,
      isEmpty: (e) => e.isEmpty,
      emptyText: l.diaryEmpty,
      onRetry: () => ref.invalidate(diaryProvider),
      builder: (context, entries) => Column(
        children: [
          for (final e in entries.take(3)) ...[DiaryEntryTile(entry: e), const SizedBox(height: 6)],
        ],
      ),
    );
  }
}

class _Shortcuts extends StatelessWidget {
  const _Shortcuts();

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final t = Theme.of(context).textTheme;
    final items = <(IconData, String, String)>[
      (Icons.wb_sunny_outlined, l.featureWeather, Routes.weather),
      (Icons.storefront_outlined, l.navMarket, Routes.market),
      (Icons.terrain_outlined, l.featureSoil, Routes.soil),
      (Icons.account_balance_outlined, l.featureSchemes, Routes.schemes),
      (Icons.center_focus_weak_rounded, l.navScan, Routes.scan),
      (Icons.menu_book_outlined, l.featureDiary, Routes.diary),
    ];
    // Three per row; tile height follows the text scale so large fonts and Tamil never clip.
    final scale = MediaQuery.textScalerOf(context).scale(1);
    return LayoutBuilder(
      builder: (context, box) {
        const gap = AppSpace.md;
        final w = (box.maxWidth - gap * 2) / 3;
        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: [
            for (final (icon, label, route) in items)
              SizedBox(
                width: w,
                child: AppCard(
                  key: Key('shortcut-$route'),
                  padding: const EdgeInsets.symmetric(horizontal: AppSpace.sm, vertical: AppSpace.lg),
                  onTap: () => context.go(route),
                  semanticLabel: label,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconTile(icon, size: 44),
                      const SizedBox(height: AppSpace.sm + 2),
                      SizedBox(
                        height: 36 * scale,
                        child: Center(
                          child: Text(label,
                              textAlign: TextAlign.center, maxLines: 2, overflow: TextOverflow.ellipsis, style: t.labelMedium),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        );
      },
    );
  }
}
