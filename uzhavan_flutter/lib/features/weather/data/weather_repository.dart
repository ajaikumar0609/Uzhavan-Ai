import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/networking/api_client.dart';
import '../../../core/networking/envelope.dart';
import '../../../core/networking/providers.dart';
import '../../farm/presentation/selected_farm.dart';
import '../domain/weather_models.dart';

/// Contract §4. Location: `farm_id` › `district_id`.
class WeatherRepository {
  WeatherRepository(this._api);
  final ApiClient _api;

  Future<Enveloped<WeatherCurrent>> current(DataLocation loc) async => parseEnvelope(
        await _api.get('/api/weather/current', query: loc.toQuery()),
        WeatherCurrent.fromJson,
      );

  Future<Enveloped<List<ForecastDay>>> forecast(DataLocation loc, {int days = 7}) async =>
      parseEnvelope(
        await _api.get('/api/weather/forecast', query: {...loc.toQuery(), 'days': days}),
        ForecastDay.listFromData,
      );

  Future<Enveloped<List<WeatherAdvisory>>> advisories(DataLocation loc) async => parseEnvelope(
        await _api.get('/api/weather/advisories', query: loc.toQuery()),
        (d) => jsonListOrEmpty(d).map(WeatherAdvisory.fromJson).toList(),
      );
}

final weatherRepositoryProvider =
    Provider<WeatherRepository>((ref) => WeatherRepository(ref.watch(apiClientProvider)));

final weatherCurrentProvider = FutureProvider.family<Enveloped<WeatherCurrent>, DataLocation>(
  (ref, loc) => ref.watch(weatherRepositoryProvider).current(loc),
);

final weatherForecastProvider = FutureProvider.family<Enveloped<List<ForecastDay>>, DataLocation>(
  (ref, loc) => ref.watch(weatherRepositoryProvider).forecast(loc),
);

final weatherAdvisoriesProvider =
    FutureProvider.family<Enveloped<List<WeatherAdvisory>>, DataLocation>(
  (ref, loc) => ref.watch(weatherRepositoryProvider).advisories(loc),
);
