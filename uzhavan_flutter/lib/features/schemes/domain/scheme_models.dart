import 'package:flutter/foundation.dart';

import '../../../core/localization/bilingual_text.dart';
import '../../../core/networking/api_client.dart';
import '../../../core/networking/envelope.dart';

/// Server text that may be `{en, ta}` or a plain string. Null stays null.
BilingualText? _bi(Map<String, Object?> m, String k) => parseBilingualLoose(m[k]);

/// A list of strings / `{en,ta}` / `{title|name, url}`; a single string is
/// one item. Null stays null (the UI hides or shows "not available").
List<BilingualText>? _biList(Object? v) {
  if (v == null) return null;
  if (v is String) return v.trim().isEmpty ? null : [BilingualText(en: v)];
  if (v is! List) return null;
  final out = <BilingualText>[];
  for (final e in v) {
    if (e is Map && e['en'] == null && e['ta'] == null) {
      final t = e['title'] ?? e['name'] ?? e['url'];
      if (t is String && t.trim().isNotEmpty) out.add(BilingualText(en: t));
      continue;
    }
    final t = parseBilingualLoose(e);
    if (t != null) out.add(t);
  }
  return out;
}

/// A source document: title + optional url.
@immutable
class SourceDoc {
  const SourceDoc({required this.title, this.url});
  final String title;
  final String? url;

  static bool _isWebUrl(String? u) {
    final uri = u == null ? null : Uri.tryParse(u.trim());
    return uri != null && (uri.scheme == 'http' || uri.scheme == 'https') && uri.host.isNotEmpty;
  }

  /// Only http(s) URLs are kept. The live backend sends internal relative
  /// file paths (e.g. `central/raw/x.pdf`), which are never shown to farmers.
  static List<SourceDoc> listFrom(Object? v) {
    final out = <SourceDoc>[];
    for (final e in jsonListOrEmpty(v is String ? [v] : v)) {
      if (e is String && _isWebUrl(e)) {
        out.add(SourceDoc(title: e.trim(), url: e.trim()));
      } else if (e is Map) {
        final m = e.cast<String, Object?>();
        final url = jsonString(m, 'url') ?? jsonString(m, 'source_url');
        if (!_isWebUrl(url)) continue;
        final title = jsonString(m, 'title') ?? jsonString(m, 'name');
        out.add(SourceDoc(title: title != null && !title.contains('/') ? title : url!, url: url));
      }
    }
    return out;
  }
}

/// Contract §6 list item.
class SchemeSummary {
  const SchemeSummary({
    required this.schemeId,
    required this.name,
    this.authority,
    this.level,
    this.active,
    this.crops,
    this.officialUrl,
  });

  final String schemeId;
  final BilingualText name;
  final BilingualText? authority;

  /// `central` | `state`
  final String? level;
  final bool? active;
  final List<String>? crops;
  final String? officialUrl;

  factory SchemeSummary.fromJson(Object? json) {
    final m = asJsonMap(json);
    final id = jsonString(m, 'scheme_id') ?? jsonString(m, 'id') ?? '';
    final crops = m['crops'];
    final active = m['active'];
    return SchemeSummary(
      schemeId: id,
      name: _bi(m, 'name') ?? BilingualText(en: id),
      authority: _bi(m, 'authority'),
      level: jsonString(m, 'level'),
      active: active is bool ? active : null,
      crops: crops is List ? crops.map((e) => '$e').toList() : null,
      officialUrl: jsonString(m, 'official_url'),
    );
  }
}

/// Contract §6 full record. Missing fields are null, never inferred.
class SchemeDetail {
  const SchemeDetail({
    required this.summary,
    this.description,
    this.eligibilityText,
    this.benefits,
    this.applicationMethod,
    this.requiredDocuments,
    this.sourceDocuments = const [],
    this.dateChecked,
    this.lastUpdatedOnSource,
    this.components,
  });

  final SchemeSummary summary;

  /// Optional live-backend field; shown as a list only when present.
  final List<BilingualText>? components;
  final BilingualText? description;
  final BilingualText? eligibilityText;
  final BilingualText? benefits;
  final BilingualText? applicationMethod;
  final List<BilingualText>? requiredDocuments;
  final List<SourceDoc> sourceDocuments;
  final DateTime? dateChecked;
  final DateTime? lastUpdatedOnSource;

  factory SchemeDetail.fromJson(Object? json) {
    final m = asJsonMap(json);
    BilingualText? textOrList(String k) {
      final v = m[k];
      if (v is List) {
        final items = _biList(v);
        if (items == null || items.isEmpty) return null;
        return BilingualText(
          en: items.map((e) => '• ${e.en}').join('\n'),
          ta: items.every((e) => e.ta != null) ? items.map((e) => '• ${e.ta}').join('\n') : null,
        );
      }
      return _bi(m, k);
    }

    return SchemeDetail(
      summary: SchemeSummary.fromJson(m),
      description: textOrList('description'),
      eligibilityText: textOrList('eligibility_text'),
      benefits: textOrList('benefits'),
      applicationMethod: textOrList('application_method'),
      requiredDocuments: _biList(m['required_documents']),
      sourceDocuments: SourceDoc.listFrom(m['source_documents']),
      dateChecked: parseDate(m['date_checked']),
      lastUpdatedOnSource: parseDate(m['last_updated_on_source']),
      components: _biList(m['components']),
    );
  }
}

/// The 4 statuses of contract §6 (+ [unrecognized] for anything else, which
/// the UI never presents as a status).
enum EligibilityStatus {
  meetsKnownCriteria('eligible_known_criteria'),
  failsKnownCriteria('not_eligible_known_criteria'),
  moreInformationRequired('more_information_required'),
  cannotDetermine('cannot_determine'),
  unrecognized('');

  const EligibilityStatus(this.wire);
  final String wire;

  static EligibilityStatus parse(Object? v) =>
      values.firstWhere((s) => s.wire.isNotEmpty && s.wire == v, orElse: () => unrecognized);
}

class EligibilityResult {
  const EligibilityResult({
    required this.status,
    required this.rawStatus,
    this.reasons = const [],
    this.missingFields = const [],
    this.criteriaSourceUrl,
  });

  final EligibilityStatus status;
  final String? rawStatus;
  final List<BilingualText> reasons;
  final List<String> missingFields;
  final String? criteriaSourceUrl;

  factory EligibilityResult.fromJson(Object? json) {
    final m = asJsonMap(json);
    return EligibilityResult(
      status: EligibilityStatus.parse(m['status']),
      rawStatus: jsonString(m, 'status'),
      reasons: _biList(m['reasons']) ?? const [],
      missingFields: jsonListOrEmpty(m['missing_fields']).map((e) => '$e').toList(),
      criteriaSourceUrl: jsonString(m, 'criteria_source_url'),
    );
  }
}

/// Eligibility request key: scheme + optional farm.
@immutable
class EligibilityQuery {
  const EligibilityQuery(this.schemeId, {this.farmId});
  final String schemeId;
  final String? farmId;

  @override
  bool operator ==(Object other) =>
      other is EligibilityQuery && other.schemeId == schemeId && other.farmId == farmId;

  @override
  int get hashCode => Object.hash(schemeId, farmId);
}

@immutable
class SchemeQuery {
  const SchemeQuery({this.q = '', this.level, this.cropId});
  final String q;
  final String? level;
  final String? cropId;

  Map<String, Object?> toQuery() => {
        if (q.trim().isNotEmpty) 'q': q.trim(),
        'level': ?level,
        'crop_id': ?cropId,
      };

  @override
  bool operator ==(Object other) =>
      other is SchemeQuery && other.q == q && other.level == level && other.cropId == cropId;

  @override
  int get hashCode => Object.hash(q, level, cropId);
}
