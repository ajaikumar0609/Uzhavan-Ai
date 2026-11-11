import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/bilingual_text.dart';
import '../../../core/localization/l10n.dart';
import '../../../core/networking/api_failure.dart';
import '../../../core/routing/routes.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/utils/area_units.dart';
import '../../../shared/utils/failure_text.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/data_state_view.dart';
import '../../meta/domain/meta_models.dart';
import '../../meta/presentation/meta_providers.dart';
import '../domain/farm.dart';
import 'farms_controller.dart';

class FarmListScreen extends ConsumerWidget {
  const FarmListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final farms = ref.watch(farmsProvider);
    final count = farms.value?.length ?? 0;
    final canAdd = farms.hasValue && !farms.hasError && count < maxFarms;
    return AppScaffold(
      title: l.featureFarms,
      floatingActionButton: canAdd
          ? FloatingActionButton.extended(
              onPressed: () => context.push(Routes.farmNew),
              icon: const Icon(Icons.add),
              label: Text(l.farmAdd),
            )
          : null,
      body: DataStateView(
        value: farms,
        unavailableText: l.farmsUnavailable,
        emptyText: l.farmsEmpty,
        isEmpty: (f) => f.isEmpty,
        onRetry: () => ref.invalidate(farmsProvider),
        builder: (context, list) => ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
          children: [
            for (final f in list) ...[
              _FarmCard(farm: f),
              const SizedBox(height: 12),
            ],
            if (list.length >= maxFarms)
              Text(l.farmLimitReached, style: TextStyle(color: context.colors.mutedForeground)),
          ],
        ),
      ),
    );
  }
}

class _FarmCard extends ConsumerWidget {
  const _FarmCard({required this.farm});
  final Farm farm;

  Future<void> _delete(BuildContext context, WidgetRef ref) async {
    final l = context.l10n;
    final messenger = ScaffoldMessenger.of(context);
    final locale = Localizations.localeOf(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        content: Text(l.farmDeleteConfirm(farm.name)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(l.cancel)),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: Text(l.delete)),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(farmsProvider.notifier).delete(farm.farmId);
      messenger.showSnackBar(SnackBar(content: Text(l.farmDeleted)));
    } on ApiFailure catch (f) {
      messenger.showSnackBar(SnackBar(content: Text(failureText(l, locale, f))));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final c = context.colors;
    final locale = Localizations.localeOf(context);
    final districts = ref.watch(districtsProvider).value;
    final crops = ref.watch(cropsProvider).value;
    final enums = ref.watch(enumsProvider).value;

    String label(BilingualText? t, String? id) =>
        t != null ? context.bi(t) : (id ?? l.notSet);
    final district = districts?.where((d) => d.id == farm.districtId).firstOrNull;
    final area = farm.areaHa;

    Widget row(IconData icon, String title, String? value) {
      final missing = value == null;
      return Padding(
        padding: const EdgeInsets.only(top: 6),
        child: Row(
          children: [
            Icon(icon, size: 18, color: c.mutedForeground),
            const SizedBox(width: 8),
            Text(title, style: TextStyle(color: c.mutedForeground)),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                value ?? l.notSet,
                style: TextStyle(fontStyle: missing ? FontStyle.italic : null),
              ),
            ),
          ],
        ),
      );
    }

    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(24),
        onTap: () => context.push(Routes.farmEdit(farm.farmId)),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 4, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(farm.name, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                  ),
                  PopupMenuButton<String>(
                    onSelected: (v) => v == 'edit'
                        ? context.push(Routes.farmEdit(farm.farmId))
                        : _delete(context, ref),
                    itemBuilder: (_) => [
                      PopupMenuItem(value: 'edit', child: Text(l.edit)),
                      PopupMenuItem(value: 'delete', child: Text(l.delete)),
                    ],
                  ),
                ],
              ),
              row(Icons.map_outlined, l.profileDistrict,
                  district == null ? farm.districtId : context.bi(district.name)),
              row(Icons.home_work_outlined, l.profileVillage, farm.village),
              row(Icons.straighten, l.farmArea,
                  area == null ? null : l.farmAreaValue(AreaUnits.formatAcres(area, locale: locale.toString()))),
              row(Icons.grass, l.farmCrop,
                  farm.cropId == null ? null : label(labelFor(crops, farm.cropId), farm.cropId)),
              row(Icons.timeline, l.farmStage,
                  farm.cropStageId == null ? null : label(labelFor(enums?.cropStages, farm.cropStageId), farm.cropStageId)),
              row(Icons.calendar_month_outlined, l.farmSeason,
                  farm.seasonId == null ? null : label(labelFor(enums?.seasons, farm.seasonId), farm.seasonId)),
              row(Icons.water_drop_outlined, l.farmIrrigation,
                  farm.irrigationTypeId == null
                      ? null
                      : label(labelFor(enums?.irrigationTypes, farm.irrigationTypeId), farm.irrigationTypeId)),
            ],
          ),
        ),
      ),
    );
  }
}
