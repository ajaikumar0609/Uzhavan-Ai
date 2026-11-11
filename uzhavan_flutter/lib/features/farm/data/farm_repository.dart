import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/networking/api_client.dart';
import '../../../core/networking/providers.dart';
import '../domain/farm.dart';

class FarmRepository {
  FarmRepository(this._api);
  final ApiClient _api;

  static const path = '/api/farms';

  Future<List<Farm>> list() async =>
      asJsonList(unwrapData(await _api.get(path))).map(Farm.fromJson).toList();

  Future<Farm> create(FarmInput input) async =>
      Farm.fromJson(_lenient(await _api.post(path, body: input.toJson())));

  Future<Farm> update(String farmId, FarmInput input) async => Farm.fromJson(
        _lenient(await _api.put('$path/${Uri.encodeComponent(farmId)}', body: input.toJson())),
      );

  Future<void> delete(String farmId) async {
    await _api.delete('$path/${Uri.encodeComponent(farmId)}');
  }

  /// POST (201) and PUT return the bare Farm (no envelope) on the deployed
  /// backend; an enveloped body is accepted too.
  static Object? _lenient(Object? body) =>
      body is Map && body.containsKey('data') ? body['data'] : body;
}

final farmRepositoryProvider =
    Provider<FarmRepository>((ref) => FarmRepository(ref.watch(apiClientProvider)));
