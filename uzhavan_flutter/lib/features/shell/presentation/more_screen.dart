import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/routing/routes.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/ui_kit.dart';

/// The hub for everything that is not a bottom tab, grouped by purpose.
class MoreScreen extends StatelessWidget {
  const MoreScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    return AppScaffold(
      title: l.navMore,
      automaticallyImplyLeading: false,
      body: ListView(
        padding: AppSpace.screen,
        children: [
          _Group(title: l.moreInfoSection, items: [
            _Item(Icons.wb_sunny_outlined, l.featureWeather, l.moreWeatherSub, Routes.weather),
            _Item(Icons.account_balance_outlined, l.featureSchemes, l.moreSchemesSub, Routes.schemes),
            _Item(Icons.terrain_outlined, l.featureSoil, l.moreSoilSub, Routes.soil),
            _Item(Icons.satellite_alt_outlined, l.featureSatellite, l.moreSatelliteSub, Routes.satellite),
          ]),
          const SizedBox(height: AppSpace.xl),
          _Group(title: l.moreRecordsSection, items: [
            _Item(Icons.agriculture_outlined, l.featureFarms, l.moreFarmsSub, Routes.farms),
            _Item(Icons.menu_book_outlined, l.featureDiary, l.moreDiarySub, Routes.diary),
          ]),
          const SizedBox(height: AppSpace.xl),
          _Group(title: l.moreAccountSection, items: [
            _Item(Icons.person_outline_rounded, l.featureProfile, l.moreProfileSub, Routes.profile),
            _Item(Icons.tune_rounded, l.featureSettings, l.moreSettingsSub, Routes.settings),
          ]),
        ],
      ),
    );
  }
}

class _Item {
  const _Item(this.icon, this.title, this.subtitle, this.route);
  final IconData icon;
  final String title;
  final String subtitle;
  final String route;
}

class _Group extends StatelessWidget {
  const _Group({required this.title, required this.items});
  final String title;
  final List<_Item> items;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final t = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: AppSpace.xs, bottom: AppSpace.sm),
          child: Semantics(
            header: true,
            child: Text(title.toUpperCase(),
                style: t.labelSmall?.copyWith(letterSpacing: 0.8, color: c.mutedForeground)),
          ),
        ),
        AppCard(
          padding: EdgeInsets.zero,
          child: Column(
            children: [
              for (var i = 0; i < items.length; i++) ...[
                if (i > 0) Divider(indent: 72, color: c.border),
                InkWell(
                  onTap: () => context.go(items[i].route),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: AppSpace.lg, vertical: AppSpace.md),
                    child: Row(
                      children: [
                        IconTile(items[i].icon, size: 40),
                        const SizedBox(width: AppSpace.lg),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(items[i].title, style: t.titleMedium),
                              const SizedBox(height: 2),
                              Text(items[i].subtitle, style: t.bodySmall),
                            ],
                          ),
                        ),
                        Icon(Icons.chevron_right_rounded, color: c.mutedForeground),
                      ],
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }
}
