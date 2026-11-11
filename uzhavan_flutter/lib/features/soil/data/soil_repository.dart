import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/networking/api_client.dart';
import '../../../core/networking/envelope.dart';
import '../../../core/networking/providers.dart';
import '../../farm/presentation/selected_farm.dart';
import '../domain/soil_models.dart';

/// Contract §7.
class SoilRepository {
  SoilRepository(this._api);
  final ApiClient _api;

  Future<Enveloped<SoilData>> soil(DataLocation loc) async =>
      parseEnvelope(await _api.get('/api/soil', query: loc.toQuery()), SoilData.fromJson);

  Future<List<SoilTest>> tests(String farmId) async => jsonListOrEmpty(
        unwrapData(await _api.get('/api/soil/tests', query: {'farm_id': farmId})),
      ).map(SoilTest.fromJson).toList();

  /// 201 → SoilTest (bare or enveloped).
  Future<SoilTest> addTest(SoilTestInput input) async {
    final body = await _api.post('/api/soil/tests', body: input.toJson());
    return SoilTest.fromJson(body is Map && body.containsKey('data') ? body['data'] : body);
  }
}

final soilRepositoryProvider =
    Provider<SoilRepository>((ref) => SoilRepository(ref.watch(apiClientProvider)));

final soilProvider = FutureProvider.family<Enveloped<SoilData>, DataLocation>(
  (ref, loc) => ref.watch(soilRepositoryProvider).soil(loc),
);
