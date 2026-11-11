import 'package:flutter/foundation.dart';

import '../localization/bilingual_text.dart';
import 'api_client.dart';

/// `meta.location` (contract §0): which point the server used.
@immutable
class MetaLocation {
  const MetaLocation({this.name, this.lat, this.lon});

  final String? name;
  final double? lat;
  final double? lon;

  static MetaLocation? tryParse(Object? json) {
    if (json is! Map) return null;
    final name = json['name'];
    return MetaLocation(
      name: name is String && name.trim().isNotEmpty ? name : null,
      lat: _toDouble(json['lat']),
      lon: _toDouble(json['lon']),
    );
  }
}

/// The contract's `meta` block. Every field is optional on the client side:
/// a missing field is shown as "not available", never guessed.
@immutable
class ApiMeta {
  const ApiMeta({
    this.source,
    this.sourceUrl,
    this.kind,
    this.retrievedAt,
    this.observedAt,
    this.location,
    this.notes = const [],
    this.stale = false,
  });

  final String? source;
  final String? sourceUrl;

  /// current | forecast | historical | latest_observed | estimated | measured | reference
  final String? kind;
  final DateTime? retrievedAt;
  final DateTime? observedAt;
  final MetaLocation? location;
  final List<BilingualText> notes;

  /// Only when the server says so (`meta.stale == true`).
  final bool stale;

  static const empty = ApiMeta();

  factory ApiMeta.fromJson(Object? json) {
    if (json is! Map) return empty;
    String? str(String k) {
      final v = json[k];
      return v is String && v.trim().isNotEmpty ? v : null;
    }

    final rawNotes = json['notes'];
    return ApiMeta(
      source: str('source'),
      sourceUrl: str('source_url'),
      kind: str('kind'),
      retrievedAt: parseDateTime(json['retrieved_at']),
      observedAt: parseDateTime(json['observed_at']),
      location: MetaLocation.tryParse(json['location']),
      notes: rawNotes is List
          ? rawNotes.map(parseBilingualLoose).whereType<BilingualText>().toList()
          : const [],
      stale: json['stale'] == true,
    );
  }
}

/// `{data, meta}`.
@immutable
class Enveloped<T> {
  const Enveloped(this.data, this.meta);
  final T data;
  final ApiMeta meta;
}

/// Parses the contract envelope. `meta` is optional; extra keys are ignored.
Enveloped<T> parseEnvelope<T>(Object? body, T Function(Object? data) parse) {
  final data = unwrapData(body);
  final meta = body is Map ? ApiMeta.fromJson(body['meta']) : ApiMeta.empty;
  return Enveloped(parse(data), meta);
}

/// Accepts `{en, ta}` or a plain string (treated as English).
BilingualText? parseBilingualLoose(Object? json) {
  if (json is String) return json.trim().isEmpty ? null : BilingualText(en: json);
  final t = BilingualText.tryParse(json);
  if (t == null || (t.en.trim().isEmpty && (t.ta?.trim().isEmpty ?? true))) return null;
  return t;
}

DateTime? parseDateTime(Object? v) => v is String ? DateTime.tryParse(v) : null;

/// `YYYY-MM-DD` → a date-only value (local midnight, no timezone shift).
DateTime? parseDate(Object? v) {
  if (v is! String || v.length < 10) return null;
  final d = DateTime.tryParse(v.substring(0, 10));
  return d == null ? null : DateTime(d.year, d.month, d.day);
}

double? _toDouble(Object? v) {
  if (v is num) return v.toDouble();
  if (v is String) return double.tryParse(v);
  return null;
}

/// Tolerant numeric read: null stays null (never a default).
double? jsonDouble(Map<String, Object?> m, String key) => _toDouble(m[key]);

int? jsonInt(Map<String, Object?> m, String key) {
  final v = m[key];
  if (v is int) return v;
  if (v is num) return v.round();
  if (v is String) return int.tryParse(v);
  return null;
}

String? jsonString(Map<String, Object?> m, String key) {
  final v = m[key];
  if (v is String && v.trim().isNotEmpty) return v;
  if (v is num) return '$v';
  return null;
}

List<Object?> jsonListOrEmpty(Object? v) => v is List ? v.cast<Object?>() : const [];

String dateOnly(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
