import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/networking/envelope.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/data_state_view.dart';
import '../../../shared/widgets/source_line.dart';
import '../data/satellite_repository.dart';

/// Contract §11: status and validation gates only. No imagery, no predictions.
class SatelliteScreen extends ConsumerWidget {
  const SatelliteScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    return AppScaffold(
      title: l.featureSatellite,
      body: DataStateView<Enveloped<SatelliteStatus>>(
        value: ref.watch(satelliteStatusProvider),
        unavailableText: l.satelliteUnavailable,
        onRetry: () => ref.invalidate(satelliteStatusProvider),
        builder: (context, env) => ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
          children: [SatelliteStatusCard(env: env)],
        ),
      ),
    );
  }
}

class SatelliteStatusCard extends StatelessWidget {
  const SatelliteStatusCard({super.key, required this.env});
  final Enveloped<SatelliteStatus> env;

  String _gateLabel(AppLocalizations l, String key) => switch (key) {
        'licence' || 'license' => l.gateLicence,
        'units' => l.gateUnits,
        'geography_scope' => l.gateGeography,
        'independent_evaluation' => l.gateEvaluation,
        _ => key,
      };

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final c = context.colors;
    final s = env.data;
    return InfoCard(
      key: const Key('satellite-status'),
      color: s.available ? null : c.warning.withValues(alpha: 0.06),
      borderColor: s.available ? null : c.warning,
      children: [
        Row(children: [
          Icon(s.available ? Icons.satellite_alt : Icons.hourglass_top, color: s.available ? c.success : c.warning),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              s.available ? l.satelliteAvailable : l.satelliteUnderValidation,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
          ),
        ]),
        if (!s.available) ...[
          const SizedBox(height: 8),
          Text(l.satelliteNoPredictions),
        ],
        const SizedBox(height: 12),
        Text(l.satelliteGates, style: const TextStyle(fontWeight: FontWeight.w600)),
        for (final g in s.gates.entries)
          ListTile(
            contentPadding: EdgeInsets.zero,
            dense: true,
            leading: Icon(
              g.value == true
                  ? Icons.check_circle_outline
                  : (g.value == false ? Icons.cancel_outlined : Icons.info_outline),
              color: g.value == true ? c.success : (g.value == false ? c.danger : c.info),
            ),
            title: Text(_gateLabel(l, g.key)),
            subtitle: Text(switch (g.value) {
              true => l.gatePassed,
              false => l.gateNotPassed,
              null => l.notAvailable,
              final v => '$v',
            }),
          ),
        const SizedBox(height: 8),
        SourceLine(meta: env.meta),
        NotesBlock(notes: env.meta.notes),
      ],
    );
  }
}
