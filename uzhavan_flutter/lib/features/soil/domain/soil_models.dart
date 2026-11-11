import '../../../core/localization/bilingual_text.dart';
import '../../../core/networking/api_client.dart';
import '../../../core/networking/envelope.dart';

/// Contract §7 `regional` (reference).
class RegionalSoil {
  const RegionalSoil({required this.soilTypes, this.source});
  final List<BilingualText> soilTypes;
  final String? source;

  static RegionalSoil? tryParse(Object? json) {
    if (json is! Map) return null;
    final m = json.cast<String, Object?>();
    return RegionalSoil(
      soilTypes: [
        for (final t in jsonListOrEmpty(m['soil_types']))
          ?(t is Map ? parseBilingualLoose(t['name']) : parseBilingualLoose(t)),
      ],
      source: jsonString(m, 'source'),
    );
  }
}

/// One category share. [key] is `low|medium|high` for the contract shape;
/// live data may instead send named categories (e.g. Deficient/Sufficient).
class NutrientCategory {
  const NutrientCategory({this.key, this.name, this.pct, this.samples});
  final String? key;
  final BilingualText? name;
  final double? pct;
  final int? samples;
}

class NutrientParam {
  const NutrientParam({required this.param, required this.categories, this.samples});
  final String param;
  final List<NutrientCategory> categories;
  final int? samples;

  factory NutrientParam.fromJson(Map<String, Object?> m) {
    final cats = <NutrientCategory>[];
    final raw = m['categories'];
    if (raw is List) {
      for (final c in raw) {
        if (c is! Map) continue;
        final cm = c.cast<String, Object?>();
        // Live shape: {category, pct, samples}; `name` only as a fallback.
        cats.add(NutrientCategory(
          name: parseBilingualLoose(cm['category']) ?? parseBilingualLoose(cm['name']),
          pct: jsonDouble(cm, 'pct') ?? jsonDouble(cm, 'percent'),
          samples: jsonInt(cm, 'samples'),
        ));
      }
    } else {
      for (final k in const ['low', 'medium', 'high']) {
        if (m.containsKey('${k}_pct')) cats.add(NutrientCategory(key: k, pct: jsonDouble(m, '${k}_pct')));
      }
    }
    return NutrientParam(
      param: jsonString(m, 'param') ?? jsonString(m, 'name') ?? '',
      categories: cats,
      samples: jsonInt(m, 'samples'),
    );
  }
}

/// Contract §7 `nutrient_status` (Soil Health Card dashboard, reference).
class NutrientStatus {
  const NutrientStatus({this.cycle, this.scheme, required this.parameters, this.source});
  final String? cycle;

  /// The survey name (live backend).
  final String? scheme;
  final List<NutrientParam> parameters;
  final String? source;

  static NutrientStatus? tryParse(Object? json) {
    if (json is! Map) return null;
    final m = json.cast<String, Object?>();
    return NutrientStatus(
      cycle: jsonString(m, 'cycle'),
      scheme: jsonString(m, 'scheme'),
      source: jsonString(m, 'source'),
      parameters: [
        for (final p in jsonListOrEmpty(m['parameters']))
          if (p is Map) NutrientParam.fromJson(p.cast<String, Object?>()),
      ],
    );
  }
}

/// Contract §7 `estimated` (ISRIC SoilGrids model values, NOT measurements).
class EstimatedSoil {
  const EstimatedSoil({
    this.depth,
    required this.values,
    this.units = const {},
    this.source,
    this.caveats = const [],
  });
  final String? depth;

  /// Server-provided unit per value key (`data.estimated.units`).
  final Map<String, String> units;

  /// Keys in contract order; a missing value is null.
  final Map<String, double?> values;
  final String? source;
  final List<BilingualText> caveats;

  static const keys = ['ph', 'soc_g_kg', 'clay_pct', 'sand_pct', 'silt_pct', 'cec', 'bdod', 'nitrogen'];

  static EstimatedSoil? tryParse(Object? json) {
    if (json is! Map) return null;
    final m = json.cast<String, Object?>();
    final raw = m['values'] is Map ? (m['values'] as Map).cast<String, Object?>() : const <String, Object?>{};
    return EstimatedSoil(
      depth: jsonString(m, 'depth'),
      values: {for (final k in keys) k: jsonDouble(raw, k)},
      units: m['units'] is Map
          ? {
              for (final e in (m['units'] as Map).entries)
                if (e.value is String && (e.value as String).trim().isNotEmpty) '${e.key}': e.value as String,
            }
          : const {},
      source: jsonString(m, 'source'),
      caveats: jsonListOrEmpty(m['caveats']).map(parseBilingualLoose).whereType<BilingualText>().toList(),
    );
  }
}

/// A farmer-entered lab test (contract §7, `kind: measured`).
class SoilTest {
  const SoilTest({
    this.testId,
    this.farmId,
    this.sampleDate,
    this.labName,
    required this.values,
    this.createdAt,
  });

  final String? testId;
  final String? farmId;
  final DateTime? sampleDate;
  final String? labName;
  final Map<String, double?> values;
  final DateTime? createdAt;

  factory SoilTest.fromJson(Object? json) {
    final m = asJsonMap(json);
    return SoilTest(
      testId: jsonString(m, 'test_id') ?? jsonString(m, 'id'),
      farmId: jsonString(m, 'farm_id'),
      sampleDate: parseDate(m['sample_date']),
      labName: jsonString(m, 'lab_name'),
      values: {for (final p in soilTestParams) p.key: jsonDouble(m, p.key)},
      createdAt: parseDateTime(m['created_at']),
    );
  }
}

/// Contract §7 `data`. Each section is independently nullable.
class SoilData {
  const SoilData({this.regional, this.nutrientStatus, this.estimated, this.measured = const []});
  final RegionalSoil? regional;
  final NutrientStatus? nutrientStatus;
  final EstimatedSoil? estimated;
  final List<SoilTest> measured;

  factory SoilData.fromJson(Object? json) {
    final m = asJsonMap(json);
    return SoilData(
      regional: RegionalSoil.tryParse(m['regional']),
      nutrientStatus: NutrientStatus.tryParse(m['nutrient_status']),
      estimated: EstimatedSoil.tryParse(m['estimated']),
      measured: jsonListOrEmpty(m['measured']).map(SoilTest.fromJson).toList(),
    );
  }
}

/// A lab parameter: API key, unit and the form's accepted range.
class SoilParam {
  const SoilParam(this.key, this.unit, this.min, this.max);
  final String key;
  final String unit;
  final double min;
  final double max;
}

/// The POST /api/soil/tests fields. Ranges are plausibility guards (the
/// server validates too); they are not agronomic thresholds.
const soilTestParams = <SoilParam>[
  SoilParam('ph', '', 0, 14),
  SoilParam('ec_ds_m', 'dS/m', 0, 20),
  SoilParam('oc_pct', '%', 0, 10),
  SoilParam('n_kg_ha', 'kg/ha', 0, 2000),
  SoilParam('p_kg_ha', 'kg/ha', 0, 1000),
  SoilParam('k_kg_ha', 'kg/ha', 0, 3000),
  SoilParam('s_ppm', 'ppm', 0, 500),
  SoilParam('zn_ppm', 'ppm', 0, 100),
  SoilParam('fe_ppm', 'ppm', 0, 500),
  SoilParam('cu_ppm', 'ppm', 0, 100),
  SoilParam('mn_ppm', 'ppm', 0, 500),
  SoilParam('b_ppm', 'ppm', 0, 50),
];


class SoilTestInput {
  const SoilTestInput({
    required this.farmId,
    required this.sampleDate,
    this.labName,
    required this.values,
  });

  final String farmId;
  final DateTime sampleDate;
  final String? labName;
  final Map<String, double?> values;

  Map<String, Object?> toJson() => {
        'farm_id': farmId,
        'sample_date': dateOnly(sampleDate),
        'lab_name': (labName?.trim().isEmpty ?? true) ? null : labName!.trim(),
        for (final p in soilTestParams) p.key: values[p.key],
      };
}
