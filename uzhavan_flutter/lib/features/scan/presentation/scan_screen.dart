import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:go_router/go_router.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/localization/locale_controller.dart';
import '../../../core/networking/api_failure.dart';
import '../../../core/routing/routes.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../shared/utils/failure_text.dart';
import '../../../shared/utils/formatters.dart';
import '../../../shared/utils/links.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/data_state_view.dart';
import '../../../shared/widgets/ui_kit.dart';
import '../../../shared/widgets/option_picker_field.dart';
import '../../../shared/widgets/source_line.dart';
import '../../assistant/presentation/chat_controller.dart';
import '../../meta/presentation/meta_providers.dart';
import 'scan_controller.dart';

/// Crops offered for scanning. Paddy is excluded for now (the paddy model
/// is not part of this release).
const scanExcludedCrops = {'paddy'};

final scanCropOptionsProvider = Provider<AsyncValue<List<PickerOption>>>(
  (ref) => ref.watch(cropOptionsProvider).whenData(
        (list) => list.where((o) => !scanExcludedCrops.contains(o.id)).toList(),
      ),
);

class ScanScreen extends ConsumerWidget {
  const ScanScreen({super.key});

  Future<void> _pick(BuildContext context, WidgetRef ref, PickSource source) async {
    final l = context.l10n;
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.read(scanProvider.notifier).pick(source);
    } on PickDenied {
      messenger.showSnackBar(SnackBar(
        content: Text(source == PickSource.camera ? l.cameraPermissionDenied : l.galleryPermissionDenied),
      ));
    } catch (_) {
      messenger.showSnackBar(SnackBar(content: Text(l.scanPickFailed)));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final c = context.colors;
    final s = ref.watch(scanProvider);
    final uploading = s.phase == ScanPhase.uploading;
    return AppScaffold(
      title: l.featureScan,
      automaticallyImplyLeading: false,
      body: ListView(
        padding: AppSpace.screen,
        children: [
          // Always shown: the disease model is not approved, so this screen must never read
          // as a working diagnosis tool. The API's 503 safety gate is unchanged.
          NoticeBanner(
            key: const Key('scan-validation-notice'),
            tone: Tone.caution,
            icon: Icons.science_outlined,
            title: l.scanValidationTitle,
            text: l.scanValidationBody,
          ),
          const SizedBox(height: AppSpace.sm),
          Align(
            alignment: AlignmentDirectional.centerStart,
            child: StatusBadge(label: l.scanValidationBadge, tone: Tone.caution, icon: Icons.hourglass_top_rounded),
          ),
          const SizedBox(height: AppSpace.xl),
          Text(l.scanHowTitle, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: AppSpace.xs),
          Text(l.scanHowBody, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: c.mutedForeground)),
          const SizedBox(height: AppSpace.lg),
          OptionPickerField(
            label: l.scanCrop,
            options: ref.watch(scanCropOptionsProvider),
            selectedId: s.cropId,
            searchable: true,
            unavailableText: l.optionsUnavailable,
            onRetry: () => ref.invalidate(cropsProvider),
            onChanged: uploading ? (_) {} : (id) => ref.read(scanProvider.notifier).selectCrop(id),
          ),
          Padding(
            padding: const EdgeInsets.only(top: 4, left: 4),
            child: Text(l.scanPaddyExcluded, style: Theme.of(context).textTheme.bodySmall),
          ),
          const SizedBox(height: 16),
          if (s.imagePath == null)
            Row(children: [
              Expanded(
                child: FilledButton.icon(
                  key: const Key('scan-camera'),
                  onPressed: () => _pick(context, ref, PickSource.camera),
                  icon: const Icon(Icons.photo_camera_outlined),
                  label: Text(l.scanCamera),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  key: const Key('scan-gallery'),
                  onPressed: () => _pick(context, ref, PickSource.gallery),
                  icon: const Icon(Icons.photo_library_outlined),
                  label: Text(l.scanGallery),
                ),
              ),
            ])
          else ...[
            ClipRRect(
              borderRadius: BorderRadius.circular(20),
              child: AspectRatio(
                aspectRatio: 4 / 3,
                child: Image.file(
                  File(s.imagePath!),
                  key: const Key('scan-preview'),
                  fit: BoxFit.cover,
                  errorBuilder: (_, _, _) => ColoredBox(
                    color: c.muted,
                    child: Center(child: Icon(Icons.broken_image_outlined, color: c.mutedForeground)),
                  ),
                ),
              ),
            ),
            Text(l.scanYourPhoto, style: TextStyle(color: c.mutedForeground, fontSize: 12)),
            const SizedBox(height: 8),
            Row(children: [
              Expanded(
                child: OutlinedButton.icon(
                  key: const Key('scan-retake'),
                  onPressed: uploading ? null : () => _pick(context, ref, PickSource.camera),
                  icon: const Icon(Icons.replay),
                  label: Text(l.scanRetake),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  key: const Key('scan-remove'),
                  onPressed: uploading ? null : () => ref.read(scanProvider.notifier).removeImage(),
                  icon: const Icon(Icons.delete_outline),
                  label: Text(l.scanRemove),
                ),
              ),
            ]),
            const SizedBox(height: 12),
            if (uploading) ...[
              LinearProgressIndicator(key: const Key('scan-progress'), value: s.progress),
              const SizedBox(height: 4),
              Text(
                s.progress == null ? l.scanUploading : l.scanUploadingPct((s.progress! * 100).round()),
                style: TextStyle(color: c.mutedForeground),
              ),
            ] else
              FilledButton.icon(
                key: const Key('scan-submit'),
                onPressed: s.canSubmit ? () => ref.read(scanProvider.notifier).submit() : null,
                icon: const Icon(Icons.upload),
                label: Text(s.cropId == null ? l.scanPickCropFirst : l.scanSubmit),
              ),
          ],
          const SizedBox(height: 16),
          ScanOutcome(state: s),
        ],
      ),
    );
  }
}

/// UNAVAILABLE / UNSURE / diagnosis / error. A diagnosis appears only for a
/// 200 response with `status: ok` and a top prediction.
class ScanOutcome extends ConsumerWidget {
  const ScanOutcome({super.key, required this.state});
  final ScanState state;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final c = context.colors;
    void retry() => ref.read(scanProvider.notifier).submit();
    if (state.phase == ScanPhase.failed) {
      final f = state.failure!;
      if (f.code == 'model_unavailable') {
        return DataStateCard(
          key: const Key('scan-model-unavailable'),
          padding: EdgeInsets.zero,
          status: DataStatus.unavailable,
          icon: Icons.science_outlined,
          message: l.scanModelUnavailable,
        );
      }
      final msg = failureText(l, Localizations.localeOf(context), f);
      return DataStateCard(
        key: const Key('scan-failed'),
        padding: EdgeInsets.zero,
        status: f.kind == ApiFailureKind.unavailable ? DataStatus.unavailable : DataStatus.error,
        message: msg,
        onRetry: retry,
      );
    }
    final env = state.result;
    if (state.phase != ScanPhase.done || env == null) return const SizedBox.shrink();
    final r = env.data;
    if (r.isDemoResult) {
      String titleCase(String s) => s.replaceAll('_', ' ').split(' ').map((w) => w.isNotEmpty ? '${w[0].toUpperCase()}${w.substring(1)}' : '').join(' ');
      final rawDisease = r.predictedClass ?? r.top?.classId ?? 'Unknown';
      final diseaseName = titleCase(rawDisease);
      final confPct = r.confidence != null ? (r.confidence! * 100).toStringAsFixed(1) : (r.top?.probability != null ? (r.top!.probability! * 100).toStringAsFixed(1) : 'N/A');
      final isLowConfidence = r.confidence != null && r.confidence! < 0.70;

      return InfoCard(
        key: const Key('scan-demo-result'),
        title: 'M4 v1 RESEARCH DEMO',
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
          decoration: BoxDecoration(
            color: c.warning.withValues(alpha: 0.15),
            border: Border.all(color: c.warning, width: 1.2),
            borderRadius: BorderRadius.circular(6),
          ),
          child: Text(
            'NOT PRODUCTION CERTIFIED',
            style: TextStyle(color: c.warning, fontSize: 10, fontWeight: FontWeight.w800),
          ),
        ),
        children: [
          const SizedBox(height: 6),
          Text(
            diseaseName,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold, color: c.foreground),
          ),
          const SizedBox(height: 8),
          KV('Crop', (r.crop ?? r.cropId ?? 'groundnut').toUpperCase()),
          KV('Confidence', '$confPct %'),
          KV('Model', r.modelArchitecture ?? 'EfficientNetV2-S'),
          KV('Experiment', r.experimentId ?? 'UZ-M4-v1.0-a898475e-s1'),
          if (r.latencyMs != null) KV('Inference Latency', '${r.latencyMs!.toStringAsFixed(1)} ms'),
          const SizedBox(height: 12),
          if (isLowConfidence)
            Container(
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: c.warning.withValues(alpha: 0.12),
                border: Border.all(color: c.warning.withValues(alpha: 0.6)),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(Icons.warning_amber_rounded, size: 18, color: c.warning),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Low-confidence research prediction',
                      style: TextStyle(color: c.warning, fontSize: 12, fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ),
          if (r.top3.isNotEmpty) ...[
            const Text('Top probabilities', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
            const SizedBox(height: 6),
            for (final item in r.top3)
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          titleCase(item.className),
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
                        ),
                        Text(
                          '${(item.probability * 100).toStringAsFixed(1)} %',
                          style: TextStyle(fontSize: 12, color: c.mutedForeground, fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                    const SizedBox(height: 3),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: item.probability.clamp(0.0, 1.0),
                        minHeight: 6,
                        backgroundColor: c.muted,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          item == r.top3.first ? c.primary : c.mutedForeground.withValues(alpha: 0.5),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
          ],
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            child: FilledButton.tonalIcon(
              key: const Key('scan-ask-assistant'),
              onPressed: () {
                final isTamil = ref.read(localeProvider).languageCode == AppLocales.tamil.languageCode;
                final q = isTamil
                    ? 'இந்த இலைக்கு என்ன நோய் என்று மாடல் சொல்கிறது?'
                    : 'What disease did the model detect on this leaf?';
                final diseaseContext = {
                  'crop': r.crop ?? 'banana',
                  'predicted_class': r.predictedClass ?? r.top?.classId,
                  'confidence': r.confidence ?? r.top?.probability ?? 0.9,
                  'model': r.modelArchitecture ?? 'EfficientNetV2-S',
                  'model_version': r.modelVersion,
                  'experiment_id': r.experimentId,
                  'demo_mode': true,
                  'production_certified': false,
                };
                ref.read(chatProvider.notifier).send(q, diseaseContext: diseaseContext);
                context.go(Routes.assistant);
              },
              icon: const Icon(Icons.support_agent_outlined),
              label: Text(
                ref.read(localeProvider).languageCode == AppLocales.tamil.languageCode
                    ? 'உதவியாளரிடம் இந்த முடிவு பற்றி கேட்கவும்'
                    : 'Ask Assistant about this result',
              ),
            ),
          ),
          const SizedBox(height: 12),
          SourceLine(meta: env.meta),
        ],
      );
    }

    if (!r.isConfident) {
      return DataStateCard(
        key: const Key('scan-unsure'),
        status: DataStatus.unsure,
        message: l.scanUnsure,
      );
    }
    final top = r.top!;
    final prob = top.probability == null ? null : Fmt.num(top.probability! * 100, digits: 0);
    return InfoCard(
      key: const Key('scan-result'),
      title: l.scanResultTitle,
      children: [
        Text(top.label == null ? top.classId : context.bi(top.label!),
            style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
        KV(l.scanProbability, prob == null ? null : '$prob %'),
        KV(l.scanModelVersion, r.modelVersion),
        KV(l.scanInferredAt, Fmt.time(r.inferredAt)),
        const SizedBox(height: 8),
        Text(l.scanGuidance, style: const TextStyle(fontWeight: FontWeight.w700)),
        if (r.guidance.isEmpty)
          Text(l.notAvailable, style: TextStyle(color: c.mutedForeground, fontStyle: FontStyle.italic)),
        for (final g in r.guidance)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('• ${context.bi(g.text)}'),
                if (g.sourceUrl != null)
                  LinkText(label: l.sourceLabel(g.source ?? g.sourceUrl!), url: g.sourceUrl)
                else
                  Text(l.sourceLabel(g.source ?? l.notAvailable),
                      style: TextStyle(color: c.mutedForeground, fontSize: 12)),
              ],
            ),
          ),
        const SizedBox(height: 8),
        Text(l.scanConfirmWithOfficer, style: TextStyle(color: c.warning, fontSize: 13)),
        SourceLine(meta: env.meta),
      ],
    );
  }
}
