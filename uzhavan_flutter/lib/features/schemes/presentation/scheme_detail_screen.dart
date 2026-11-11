import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/localization/bilingual_text.dart';
import '../../../core/localization/l10n.dart';
import '../../../core/networking/api_failure.dart';
import '../../../core/networking/envelope.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/utils/formatters.dart';
import '../../../shared/utils/links.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/data_state_view.dart';
import '../../../shared/widgets/source_line.dart';
import '../../farm/presentation/selected_farm.dart';
import '../data/scheme_repository.dart';
import '../domain/scheme_models.dart';
import 'schemes_screen.dart' show levelLabel;

class SchemeDetailScreen extends ConsumerWidget {
  const SchemeDetailScreen({super.key, required this.schemeId});
  final String schemeId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final value = ref.watch(schemeDetailProvider(schemeId));
    return AppScaffold(
      title: value.value == null ? l.featureSchemes : context.bi(value.value!.data.summary.name),
      body: DataStateView<Enveloped<SchemeDetail>>(
        value: value,
        unavailableText: l.schemesUnavailable,
        onRetry: () => ref.invalidate(schemeDetailProvider(schemeId)),
        builder: (context, env) {
          final s = env.data;
          return ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            children: [
              InfoCard(
                title: context.bi(s.summary.name),
                children: [
                  KV(l.schemeLevel, levelLabel(context, s.summary.level)),
                  KV(l.schemeStatus, switch (s.summary.active) {
                    true => l.schemeActiveOnSource,
                    false => l.schemeInactive,
                    null => l.schemeStatusNotStated,
                  }),
                  KV(l.schemeAuthority, s.summary.authority == null ? null : context.bi(s.summary.authority!)),
                  KV(l.schemeDateChecked, Fmt.date(s.dateChecked)),
                  if (s.lastUpdatedOnSource != null) KV(l.schemeLastUpdatedOnSource, Fmt.date(s.lastUpdatedOnSource)),
                  const SizedBox(height: 8),
                  if (s.summary.officialUrl != null)
                    FilledButton.tonalIcon(
                      key: const Key('official-link'),
                      onPressed: () => openExternalLink(context, s.summary.officialUrl),
                      icon: const Icon(Icons.open_in_new),
                      label: Text(l.schemeOfficialLink),
                    )
                  else
                    KV(l.schemeOfficialLink, null),
                ],
              ),
              const SizedBox(height: 12),
              _Section(title: l.schemeDescription, text: s.description),
              _Section(title: l.schemeEligibilityText, text: s.eligibilityText),
              _Section(title: l.schemeBenefits, text: s.benefits),
              if (s.applicationMethod != null) _Section(title: l.schemeHowToApply, text: s.applicationMethod),
              if (s.components != null && s.components!.isNotEmpty) ...[
                InfoCard(
                  key: const Key('scheme-components'),
                  title: l.schemeComponents,
                  children: [for (final c in s.components!) Text('• ${context.bi(c)}')],
                ),
                const SizedBox(height: 12),
              ],
              InfoCard(
                title: l.schemeDocuments,
                children: [
                  if (s.requiredDocuments == null || s.requiredDocuments!.isEmpty)
                    Text(l.notAvailable, style: TextStyle(color: context.colors.mutedForeground, fontStyle: FontStyle.italic))
                  else
                    for (final d in s.requiredDocuments!) Text('• ${context.bi(d)}'),
                ],
              ),
              const SizedBox(height: 12),
              EligibilityCard(schemeId: schemeId),
              const SizedBox(height: 12),
              if (s.sourceDocuments.isNotEmpty)
                InfoCard(
                  title: l.schemeSourceDocuments,
                  children: [
                    for (final d in s.sourceDocuments) LinkText(label: d.title, url: d.url),
                  ],
                ),
              const SizedBox(height: 8),
              SourceLine(meta: env.meta),
            ],
          );
        },
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.text});
  final String title;
  final BilingualText? text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: InfoCard(
          title: title,
          children: [
            Text(
              text == null ? context.l10n.notAvailable : context.bi(text!),
              style: text == null
                  ? TextStyle(color: context.colors.mutedForeground, fontStyle: FontStyle.italic)
                  : null,
            ),
          ],
        ),
      );
}

/// Calls the eligibility endpoint and shows exactly the status it returned
/// (one of 4), with reasons, missing fields and the criteria source link.
class EligibilityCard extends ConsumerWidget {
  const EligibilityCard({super.key, required this.schemeId});
  final String schemeId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final c = context.colors;
    final q = EligibilityQuery(schemeId, farmId: ref.watch(selectedFarmProvider).value?.farmId);
    final value = ref.watch(schemeEligibilityProvider(q));
    final err = value.error;
    if (!value.isLoading && err is ApiFailure && err.kind == ApiFailureKind.unauthenticated) {
      // No token → 401: ask the farmer to sign in again.
      return DataStateCard(
        key: const Key('elig-signin'),
        status: DataStatus.error,
        icon: Icons.lock_outline,
        message: l.eligibilitySignIn,
      );
    }
    return DataStateView<Enveloped<EligibilityResult>>(
      value: value,
      unavailableText: l.eligibilityUnavailable,
      onRetry: () => ref.invalidate(schemeEligibilityProvider(q)),
      builder: (context, env) {
        final r = env.data;
        final (String? label, IconData icon, Color color) = switch (r.status) {
          EligibilityStatus.meetsKnownCriteria => (l.eligMeetsKnown, Icons.check_circle_outline, c.success),
          EligibilityStatus.failsKnownCriteria => (l.eligFailsKnown, Icons.cancel_outlined, c.danger),
          EligibilityStatus.moreInformationRequired => (l.eligMoreInfo, Icons.help_outline, c.warning),
          EligibilityStatus.cannotDetermine => (l.eligCannotDetermine, Icons.remove_circle_outline, c.mutedForeground),
          EligibilityStatus.unrecognized => (null, Icons.info_outline, c.mutedForeground),
        };
        return InfoCard(
          key: const Key('eligibility-card'),
          title: l.eligibilityTitle,
          borderColor: color.withValues(alpha: 0.6),
          children: [
            if (label != null)
              Row(
                key: Key('elig-${r.status.name}'),
                children: [
                  Icon(icon, color: color),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(label, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                  ),
                ],
              )
            else
              Text(l.eligibilityNoResult, key: const Key('elig-unrecognized')),
            if (r.reasons.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(l.eligibilityReasons, style: TextStyle(color: c.mutedForeground)),
              for (final reason in r.reasons) Text('• ${context.bi(reason)}'),
            ],
            if (r.missingFields.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(l.eligibilityMissing, style: TextStyle(color: c.mutedForeground)),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: [for (final f in r.missingFields) Chip(label: Text(_fieldLabel(context, f)))],
              ),
            ],
            const SizedBox(height: 8),
            if (r.criteriaSourceUrl != null)
              LinkText(label: l.eligibilityCriteriaSource, url: r.criteriaSourceUrl)
            else
              KV(l.eligibilityCriteriaSource, null),
            Text(l.eligibilityDisclaimer, style: TextStyle(color: c.mutedForeground, fontSize: 12)),
          ],
        );
      },
    );
  }

  static String _fieldLabel(BuildContext context, String field) {
    final l = context.l10n;
    return switch (field) {
      'district_id' || 'district' => l.profileDistrict,
      'crop_id' || 'crop' => l.farmCrop,
      'area_ha' || 'land_area' || 'area' => l.farmArea,
      'name' => l.profileName,
      'village' => l.profileVillage,
      _ => field,
    };
  }
}
