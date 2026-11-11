import '../../../core/localization/bilingual_text.dart';
import '../../../core/networking/api_client.dart';
import '../../../core/networking/envelope.dart';

/// Contract §4 `GET /api/weather/current` data. Null stays null.
class WeatherCurrent {
  const WeatherCurrent({
    this.temperatureC,
    this.apparentTemperatureC,
    this.humidityPct,
    this.precipitationMm,
    this.windSpeedKmph,
    this.windDirectionDeg,
    this.weatherCode,
    this.condition,
    this.isDay,
  });

  final double? temperatureC;
  final double? apparentTemperatureC;
  final double? humidityPct;
  final double? precipitationMm;
  final double? windSpeedKmph;
  final double? windDirectionDeg;
  final int? weatherCode;
  final BilingualText? condition;
  final bool? isDay;

  factory WeatherCurrent.fromJson(Object? json) {
    final m = asJsonMap(json);
    final day = m['is_day'];
    return WeatherCurrent(
      temperatureC: jsonDouble(m, 'temperature_c'),
      apparentTemperatureC: jsonDouble(m, 'apparent_temperature_c'),
      humidityPct: jsonDouble(m, 'humidity_pct'),
      precipitationMm: jsonDouble(m, 'precipitation_mm'),
      windSpeedKmph: jsonDouble(m, 'wind_speed_kmph'),
      windDirectionDeg: jsonDouble(m, 'wind_direction_deg'),
      weatherCode: jsonInt(m, 'weather_code'),
      condition: parseBilingualLoose(m['condition']),
      isDay: day is bool ? day : (day is num ? day != 0 : null),
    );
  }
}

class ForecastDay {
  const ForecastDay({
    required this.date,
    this.tempMaxC,
    this.tempMinC,
    this.precipitationMm,
    this.precipitationProbabilityPct,
    this.windMaxKmph,
    this.weatherCode,
    this.condition,
  });

  final DateTime? date;
  final double? tempMaxC;
  final double? tempMinC;
  final double? precipitationMm;
  final double? precipitationProbabilityPct;
  final double? windMaxKmph;
  final int? weatherCode;
  final BilingualText? condition;

  factory ForecastDay.fromJson(Object? json) {
    final m = asJsonMap(json);
    return ForecastDay(
      date: parseDate(m['date']),
      tempMaxC: jsonDouble(m, 'temp_max_c'),
      tempMinC: jsonDouble(m, 'temp_min_c'),
      precipitationMm: jsonDouble(m, 'precipitation_mm'),
      precipitationProbabilityPct: jsonDouble(m, 'precipitation_probability_pct'),
      windMaxKmph: jsonDouble(m, 'wind_max_kmph'),
      weatherCode: jsonInt(m, 'weather_code'),
      condition: parseBilingualLoose(m['condition']),
    );
  }

  /// `data: {daily: [...]}`; a bare list is accepted too.
  static List<ForecastDay> listFromData(Object? data) {
    final raw = data is Map ? data['daily'] : data;
    return jsonListOrEmpty(raw).map(ForecastDay.fromJson).toList();
  }
}

/// A rule that fired (contract §4). Only what the server returns.
class WeatherAdvisory {
  const WeatherAdvisory({
    required this.ruleId,
    required this.severity,
    required this.text,
    this.ruleSource,
    this.ruleSourceUrl,
  });

  final String ruleId;

  /// `info` | `caution`
  final String severity;
  final BilingualText? text;
  final String? ruleSource;
  final String? ruleSourceUrl;

  /// `rule_source` may be a string or `{title|name|source, url}`.
  factory WeatherAdvisory.fromJson(Object? json) {
    final m = asJsonMap(json);
    final src = m['rule_source'];
    String? source;
    String? url;
    if (src is String && src.trim().isNotEmpty) {
      source = src;
      if (src.startsWith('http')) url = src;
    } else if (src is Map) {
      final sm = src.cast<String, Object?>();
      // Deployed shape: {title, document, page, quote}.
      final title = jsonString(sm, 'title') ?? jsonString(sm, 'name') ?? jsonString(sm, 'source');
      final page = jsonString(sm, 'page');
      source = title == null ? null : (page == null ? title : '$title · $page');
      url = jsonString(sm, 'url') ?? jsonString(sm, 'source_url');
    }
    url ??= jsonString(m, 'rule_source_url') ?? jsonString(m, 'source_url');
    return WeatherAdvisory(
      ruleId: jsonString(m, 'rule_id') ?? '',
      severity: jsonString(m, 'severity') ?? 'info',
      text: parseBilingualLoose(m['text']),
      ruleSource: source ?? url,
      ruleSourceUrl: url,
    );
  }
}
