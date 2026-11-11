import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/networking/api_client.dart';
import '../../../core/networking/providers.dart';
import '../domain/meta_models.dart';

class MetaRepository {
  MetaRepository(this._api);
  final ApiClient _api;

  Future<List<District>> districts() async => asJsonList(
        unwrapData(await _api.get('/api/meta/districts', auth: false)),
      ).map(District.fromJson).toList();

  Future<List<RefItem>> crops() async => asJsonList(
        unwrapData(await _api.get('/api/meta/crops', auth: false)),
      ).map(RefItem.fromJson).toList();

  Future<MetaEnums> enums() async =>
      MetaEnums.fromJson(unwrapData(await _api.get('/api/meta/enums', auth: false)));
}

final metaRepositoryProvider =
    Provider<MetaRepository>((ref) => MetaRepository(ref.watch(apiClientProvider)));
