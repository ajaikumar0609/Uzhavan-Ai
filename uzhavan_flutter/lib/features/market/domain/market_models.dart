import 'package:flutter/foundation.dart';

import '../../../core/localization/bilingual_text.dart';
import '../../../core/networking/api_client.dart';
import '../../../core/networking/envelope.dart';

/// Contract §5 `GET /api/market/commodities`.
class Commodity {
  const Commodity({required this.id, required this.name, this.unit, this.unitNote});

  final String id;
  final BilingualText name;
  final String? unit;

  /// e.g. coconut: "unit unverified (per quintal vs per 1000 nuts)".
  final BilingualText? unitNote;

  factory Commodity.fromJson(Object? json) {
    final m = asJsonMap(json);
    final id = jsonString(m, 'id') ?? '';
    return Commodity(
      id: id,
      name: parseBilingualLoose(m['name']) ?? BilingualText(en: id),
      unit: jsonString(m, 'unit'),
      unitNote: parseBilingualLoose(m['unit_note']),
    );
  }
}

/// `GET /api/market/markets`.
class MarketInfo {
  const MarketInfo({required this.market, this.districtId, this.marketType});
  final String market;
  final String? districtId;
  final String? marketType;

  factory MarketInfo.fromJson(Object? json) {
    final m = asJsonMap(json);
    return MarketInfo(
      market: jsonString(m, 'market') ?? '',
      districtId: jsonString(m, 'district_id'),
      marketType: jsonString(m, 'market_type'),
    );
  }
}

/// One `GET /api/market/latest` row. Prices are as observed; null stays null.
class MarketObservation {
  const MarketObservation({
    required this.commodity,
    required this.commodityName,
    required this.market,
    this.variety,
    this.districtId,
    this.modalPrice,
    this.minPrice,
    this.maxPrice,
    this.unit,
    this.unitNote,
    this.arrivalsTonnes,
    this.observedOn,
    this.serverStale = false,
  });

  final String commodity;
  final BilingualText commodityName;
  final String? variety;
  final String market;
  final String? districtId;
  final double? modalPrice;
  final double? minPrice;
  final double? maxPrice;
  final String? unit;
  final BilingualText? unitNote;
  final double? arrivalsTonnes;
  final DateTime? observedOn;
  final bool serverStale;

  factory MarketObservation.fromJson(Object? json) {
    final m = asJsonMap(json);
    final commodity = jsonString(m, 'commodity') ?? '';
    return MarketObservation(
      commodity: commodity,
      commodityName: parseBilingualLoose(m['commodity_name']) ?? BilingualText(en: commodity),
      variety: jsonString(m, 'variety'),
      market: jsonString(m, 'market') ?? '',
      districtId: jsonString(m, 'district_id'),
      modalPrice: jsonDouble(m, 'modal_price'),
      minPrice: jsonDouble(m, 'min_price'),
      maxPrice: jsonDouble(m, 'max_price'),
      unit: jsonString(m, 'unit'),
      unitNote: parseBilingualLoose(m['unit_note']),
      arrivalsTonnes: jsonDouble(m, 'arrivals_tonnes'),
      observedOn: parseDate(m['observed_on']),
      serverStale: m['stale'] == true,
    );
  }

  bool isStale({DateTime? now}) => isMarketStale(observedOn, serverStale: serverStale, now: now);
}

/// Contract §5: rows older than 7 days are stale. The server flag wins; the
/// client applies the same 7-day rule so an old cached row still gets the chip.
/// An unknown date is treated as stale (it cannot be shown as current).
bool isMarketStale(DateTime? observedOn, {bool serverStale = false, DateTime? now}) {
  if (serverStale) return true;
  if (observedOn == null) return true;
  final n = now ?? DateTime.now();
  final today = DateTime(n.year, n.month, n.day);
  final day = DateTime(observedOn.year, observedOn.month, observedOn.day);
  return today.difference(day).inDays > 7;
}

class TrendPoint {
  const TrendPoint({required this.date, required this.modalPrice, this.variety});
  final DateTime date;
  final double modalPrice;

  /// Live backend: points carry `variety` and are NOT averaged; several
  /// points can share a date. The client never averages them either.
  final String? variety;

  /// `data: {points: [...]}`; rows without a date or price are dropped
  /// (never interpolated).
  static List<TrendPoint> listFromData(Object? data) {
    final raw = data is Map ? data['points'] : data;
    final out = <TrendPoint>[];
    for (final p in jsonListOrEmpty(raw)) {
      if (p is! Map) continue;
      final m = p.cast<String, Object?>();
      final d = parseDate(m['date']);
      final v = jsonDouble(m, 'modal_price');
      if (d != null && v != null) out.add(TrendPoint(date: d, modalPrice: v, variety: jsonString(m, 'variety')));
    }
    out.sort((a, b) => a.date.compareTo(b.date));
    return out;
  }
}

/// Groups trend points by variety (null variety → key ''), keeping each
/// series sorted by date. Nothing is merged or averaged.
Map<String, List<TrendPoint>> trendByVariety(List<TrendPoint> points) {
  final out = <String, List<TrendPoint>>{};
  for (final p in points) {
    (out[p.variety ?? ''] ??= []).add(p);
  }
  for (final l in out.values) {
    l.sort((a, b) => a.date.compareTo(b.date));
  }
  return out;
}

@immutable
class LatestQuery {
  const LatestQuery({this.commodity, this.districtId, this.market, this.limit = 20});
  final String? commodity;
  final String? districtId;
  final String? market;
  final int limit;

  Map<String, Object?> toQuery() => {
        'commodity': ?commodity,
        'district_id': ?districtId,
        'market': ?market,
        'limit': limit,
      };

  @override
  bool operator ==(Object other) =>
      other is LatestQuery &&
      other.commodity == commodity &&
      other.districtId == districtId &&
      other.market == market &&
      other.limit == limit;

  @override
  int get hashCode => Object.hash(commodity, districtId, market, limit);
}

@immutable
class TrendQuery {
  const TrendQuery({required this.commodity, required this.market, this.days = 90});
  final String commodity;
  final String market;
  final int days;

  @override
  bool operator ==(Object other) =>
      other is TrendQuery && other.commodity == commodity && other.market == market && other.days == days;

  @override
  int get hashCode => Object.hash(commodity, market, days);
}
