import '../../../core/localization/bilingual_text.dart';
import '../../../core/networking/api_client.dart';
import '../../../core/networking/envelope.dart';

class ScanPrediction {
  const ScanPrediction({required this.classId, this.label, this.probability});
  final String classId;
  final BilingualText? label;
  final double? probability;

  static ScanPrediction? tryParse(Object? json) {
    if (json is! Map) return null;
    final m = json.cast<String, Object?>();
    return ScanPrediction(
      classId: jsonString(m, 'class_id') ?? '',
      label: parseBilingualLoose(m['label']),
      probability: jsonDouble(m, 'probability'),
    );
  }
}

class ScanGuidance {
  const ScanGuidance({required this.text, this.source, this.sourceUrl});
  final BilingualText text;
  final String? source;
  final String? sourceUrl;
}

class ScanTop3Item {
  const ScanTop3Item({required this.className, required this.probability});
  final String className;
  final double probability;

  static ScanTop3Item? tryParse(Object? json) {
    if (json is! Map) return null;
    final m = json.cast<String, Object?>();
    final c = jsonString(m, 'class') ?? '';
    final p = jsonDouble(m, 'probability') ?? 0.0;
    return ScanTop3Item(className: c, probability: p);
  }
}

/// Contract §10 future 200 body. Only ever built from a 200 response.
class ScanResult {
  const ScanResult({
    required this.status,
    this.cropId,
    this.top,
    this.predictions = const [],
    this.modelVersion,
    this.inferredAt,
    this.productionApproved,
    this.guidance = const [],
    this.isDemo = false,
    this.crop,
    this.predictedClass,
    this.confidence,
    this.top3 = const [],
    this.modelArchitecture,
    this.experimentId,
    this.latencyMs,
  });

  /// `ok` | `unsure` | `demo_result`
  final String status;
  final String? cropId;
  final ScanPrediction? top;
  final List<ScanPrediction> predictions;
  final String? modelVersion;
  final DateTime? inferredAt;
  final bool? productionApproved;
  final List<ScanGuidance> guidance;

  // M4 Demo Mode fields
  final bool isDemo;
  final String? crop;
  final String? predictedClass;
  final double? confidence;
  final List<ScanTop3Item> top3;
  final String? modelArchitecture;
  final String? experimentId;
  final double? latencyMs;

  bool get isDemoResult => status == 'demo_result' || isDemo;

  /// A diagnosis is shown only for `status: ok` with a top prediction from a
  /// model not flagged `production_eligible: false`.
  bool get isConfident => isDemoResult || (status == 'ok' && top != null && productionApproved != false);

  factory ScanResult.fromJson(Object? json) {
    final m = asJsonMap(json);
    final pe = m['production_eligible'];
    final isDemo = m['demo_mode'] == true || m['status'] == 'demo_result';
    return ScanResult(
      status: jsonString(m, 'status') ?? 'unsure',
      cropId: jsonString(m, 'crop_id') ?? jsonString(m, 'crop'),
      top: ScanPrediction.tryParse(m['top']),
      predictions: jsonListOrEmpty(m['predictions']).map(ScanPrediction.tryParse).whereType<ScanPrediction>().toList(),
      modelVersion: jsonString(m, 'model_version'),
      inferredAt: parseDateTime(m['inferred_at']) ?? parseDateTime(m['inference_timestamp']),
      productionApproved: pe is bool ? pe : (isDemo ? false : null),
      isDemo: isDemo,
      crop: jsonString(m, 'crop'),
      predictedClass: jsonString(m, 'predicted_class'),
      confidence: jsonDouble(m, 'confidence'),
      top3: jsonListOrEmpty(m['top3']).map(ScanTop3Item.tryParse).whereType<ScanTop3Item>().toList(),
      modelArchitecture: jsonString(m, 'model_architecture'),
      experimentId: jsonString(m, 'experiment_id'),
      latencyMs: jsonDouble(m, 'latency_ms'),
      guidance: [
        for (final g in jsonListOrEmpty(m['guidance']))
          if (g is Map && parseBilingualLoose(g['text']) != null)
            ScanGuidance(
              text: parseBilingualLoose(g['text'])!,
              source: jsonString(g.cast(), 'source'),
              sourceUrl: jsonString(g.cast(), 'source_url'),
            ),
      ],
    );
  }
}

