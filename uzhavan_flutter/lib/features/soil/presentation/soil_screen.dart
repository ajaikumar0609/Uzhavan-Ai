import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/networking/envelope.dart';
import '../../../core/routing/routes.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/utils/formatters.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/data_state_view.dart';
import '../../../shared/widgets/source_line.dart';
import '../../farm/presentation/location_gate.dart';
import '../../farm/presentation/selected_farm.dart';
import '../data/soil_repository.dart';
import '../domain/soil_models.dart';

/// Localized name for a soil parameter key (estimated or measured).
String soilParamLabel(AppLocalizations l, String key) => switch (key) {
      'ph' => l.soilPh,
      'soc_g_kg' => l.soilSoc,
      'clay_pct' => l.soilClay,
      'sand_pct' => l.soilSand,
      'silt_pct' => l.soilSilt,
      'cec' => l.soilCec,
      'bdod' => l.soilBdod,
      'nitrogen' => l.soilNitrogenEst,
      'ec_ds_m' => l.soilEc,
      'oc_pct' => l.soilOc,
      'n_kg_ha' => l.soilN,
      'p_kg_ha' => l.soilP,
      'k_kg_ha' => l.soilK,
      's_ppm' => l.soilS,
      'zn_ppm' => l.soilZn,
      'fe_ppm' => l.soilFe,
      'cu_ppm' => l.soilCu,
      'mn_ppm' => l.soilMn,
      'b_ppm' => l.soilB,
      _ => key,
    };

String? _withUnit(double? v, String unit, {int digits = 2}) {
  final s = Fmt.num(v, digits: digits);
  if (s == null) return null;
  return unit.isEmpty ? s : '$s $unit';
}

class SoilScreen extends ConsumerWidget {
  const SoilScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    return AppScaffold(
      title: l.featureSoil,
      body: LocationGate(
        builder: (context, loc) => RefreshIndicator(
          onRefresh: () async => ref.invalidate(soilProvider(loc)),
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            children: [
              const FarmPicker(),
              DataStateView<Enveloped<SoilData>>(
                value: ref.watch(soilProvider(loc)),
                unavailableText: l.soilUnavailable,
                onRetry: () => ref.invalidate(soilProvider(loc)),
                builder: (context, env) => SoilSections(env: env, canAddTest: loc.farmId != null),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// The three separated sections. Estimated and measured values never share
/// a card, a style or a list.
class SoilSections extends StatelessWidget {
  const SoilSections({super.key, required this.env, required this.canAddTest});
  final Enveloped<SoilData> env;
  final bool canAddTest;

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final c = context.colors;
    final d = env.data;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // 1. Regional information (reference)
        InfoCard(
          key: const Key('soil-regional'),
          title: l.soilRegionalTitle,
          trailing: const KindBadge(kind: 'reference'),
          children: [
            if (d.regional == null && d.nutrientStatus == null)
              Text(l.notAvailable, style: TextStyle(color: c.mutedForeground, fontStyle: FontStyle.italic)),
            if (d.regional != null) ...[
              Text(l.soilTypes, style: const TextStyle(fontWeight: FontWeight.w600)),
              if (d.regional!.soilTypes.isEmpty) Text(l.notAvailable),
              for (final t in d.regional!.soilTypes) Text('• ${context.bi(t)}'),
              SourceLine(meta: env.meta, sourceOverride: d.regional!.source),
            ],
            if (d.nutrientStatus != null) ...[
              const SizedBox(height: 12),
              Text(l.soilNutrientStatus, style: const TextStyle(fontWeight: FontWeight.w600)),
              if (d.nutrientStatus!.scheme != null) KV(l.soilSurvey, d.nutrientStatus!.scheme),
              if (d.nutrientStatus!.cycle != null) KV(l.soilCycle, d.nutrientStatus!.cycle),
              Text(l.soilNutrientStatusCaption, style: TextStyle(color: c.mutedForeground, fontSize: 12)),
              for (final p in d.nutrientStatus!.parameters)
                KV(
                  p.samples == null ? p.param : l.soilParamSamples(p.param, p.samples!),
                  p.categories.isEmpty
                      ? null
                      : p.categories
                          .map((cat) => [
                                '${_categoryLabel(context, cat)} ${Fmt.num(cat.pct) ?? l.notAvailable}%',
                                if (cat.samples != null) '(${l.soilSamplesCount(cat.samples!)})',
                              ].join(' '))
                          .join(' · '),
                ),
              SourceLine(meta: env.meta, sourceOverride: d.nutrientStatus!.source),
            ],
          ],
        ),
        const SizedBox(height: 16),
        // 2. Estimated (model) values: caveats first and prominent.
        InfoCard(
          key: const Key('soil-estimated'),
          title: l.soilEstimatedTitle,
          trailing: const KindBadge(kind: 'estimated'),
          color: c.warning.withValues(alpha: 0.06),
          borderColor: c.warning,
          children: [
            if (d.estimated == null)
              Text(l.notAvailable, style: TextStyle(color: c.mutedForeground, fontStyle: FontStyle.italic))
            else ...[
              Container(
                key: const Key('soil-caveats'),
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: c.warning.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(children: [
                      Icon(Icons.warning_amber_rounded, color: c.warning),
                      const SizedBox(width: 8),
                      Expanded(child: Text(l.soilEstimatedWarning, style: const TextStyle(fontWeight: FontWeight.w700))),
                    ]),
                    for (final cv in d.estimated!.caveats)
                      Padding(padding: const EdgeInsets.only(top: 4), child: Text('• ${context.bi(cv)}')),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              if (d.estimated!.depth != null) KV(l.soilDepth, d.estimated!.depth),
              for (final e in d.estimated!.values.entries)
                KV(soilParamLabel(l, e.key), _withUnit(e.value, d.estimated!.units[e.key] ?? '')),
              const SizedBox(height: 8),
              SourceLine(meta: env.meta, sourceOverride: d.estimated!.source),
            ],
          ],
        ),
        const SizedBox(height: 16),
        // 3. Your soil tests (measured).
        InfoCard(
          key: const Key('soil-measured'),
          title: l.soilMeasuredTitle,
          trailing: const KindBadge(kind: 'measured'),
          color: c.primarySoft,
          borderColor: c.primary,
          children: [
            if (d.measured.isEmpty)
              Text(l.soilNoTests, style: TextStyle(color: c.mutedForeground)),
            for (final t in d.measured) _SoilTestTile(test: t),
            const SizedBox(height: 8),
            if (canAddTest)
              FilledButton.icon(
                key: const Key('soil-add-test'),
                onPressed: () => context.push(Routes.soilTestNew),
                icon: const Icon(Icons.add),
                label: Text(l.soilAddTest),
              )
            else
              Text(l.soilAddTestNeedsFarm, style: TextStyle(color: c.mutedForeground)),
          ],
        ),
      ],
    );
  }
}

String _categoryLabel(BuildContext context, NutrientCategory cat) {
  final l = context.l10n;
  return switch (cat.key) {
    'low' => l.soilLow,
    'medium' => l.soilMedium,
    'high' => l.soilHigh,
    _ => cat.name == null ? l.notAvailable : context.bi(cat.name!),
  };
}

class _SoilTestTile extends StatelessWidget {
  const _SoilTestTile({required this.test});
  final SoilTest test;

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final entered = [for (final p in soilTestParams) if (test.values[p.key] != null) p];
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: context.colors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: context.colors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(l.soilSampleOn(Fmt.date(test.sampleDate) ?? l.notAvailable),
              style: const TextStyle(fontWeight: FontWeight.w700)),
          Text(l.soilLab(test.labName ?? l.notAvailable)),
          for (final p in entered) KV(soilParamLabel(l, p.key), _withUnit(test.values[p.key], p.unit)),
          Text(l.soilFarmerEntered, style: TextStyle(color: context.colors.mutedForeground, fontSize: 12)),
        ],
      ),
    );
  }
}
