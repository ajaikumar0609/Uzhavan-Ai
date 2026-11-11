import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/networking/api_client.dart';
import '../../../core/networking/envelope.dart';
import '../../../core/networking/providers.dart';
import '../domain/market_models.dart';

/// Contract §5. Observed prices only: no advice, no forecast.
class MarketRepository {
  MarketRepository(this._api);
  final ApiClient _api;

  Future<Enveloped<List<Commodity>>> commodities() async => parseEnvelope(
        await _api.get('/api/market/commodities'),
        (d) => jsonListOrEmpty(d).map(Commodity.fromJson).toList(),
      );

  Future<Enveloped<List<MarketInfo>>> markets({String? districtId}) async => parseEnvelope(
        await _api.get('/api/market/markets', query: {'district_id': ?districtId}),
        (d) => jsonListOrEmpty(d).map(MarketInfo.fromJson).toList(),
      );

  Future<Enveloped<List<MarketObservation>>> latest(LatestQuery q) async => parseEnvelope(
        await _api.get('/api/market/latest', query: q.toQuery()),
        (d) => jsonListOrEmpty(d).map(MarketObservation.fromJson).toList(),
      );

  Future<Enveloped<List<TrendPoint>>> trend(TrendQuery q) async => parseEnvelope(
        await _api.get('/api/market/trend',
            query: {'commodity': q.commodity, 'market': q.market, 'days': q.days}),
        TrendPoint.listFromData,
      );
}

final marketRepositoryProvider =
    Provider<MarketRepository>((ref) => MarketRepository(ref.watch(apiClientProvider)));

final commoditiesProvider = FutureProvider<Enveloped<List<Commodity>>>(
  (ref) => ref.watch(marketRepositoryProvider).commodities(),
);

final marketLatestProvider = FutureProvider.family<Enveloped<List<MarketObservation>>, LatestQuery>(
  (ref, q) => ref.watch(marketRepositoryProvider).latest(q),
);

final marketTrendProvider = FutureProvider.family<Enveloped<List<TrendPoint>>, TrendQuery>(
  (ref, q) => ref.watch(marketRepositoryProvider).trend(q),
);
