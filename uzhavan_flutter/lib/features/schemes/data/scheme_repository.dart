import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/networking/api_client.dart';
import '../../../core/networking/envelope.dart';
import '../../../core/networking/providers.dart';
import '../domain/scheme_models.dart';

/// Contract §6.
class SchemeRepository {
  SchemeRepository(this._api);
  final ApiClient _api;

  Future<Enveloped<List<SchemeSummary>>> list(SchemeQuery q) async => parseEnvelope(
        await _api.get('/api/schemes', query: q.toQuery()),
        (d) => jsonListOrEmpty(d).map(SchemeSummary.fromJson).toList(),
      );

  Future<Enveloped<SchemeDetail>> detail(String schemeId) async => parseEnvelope(
        await _api.get('/api/schemes/${Uri.encodeComponent(schemeId)}'),
        SchemeDetail.fromJson,
      );

  /// 🔒 Optional `farm_id` query param (live backend).
  Future<Enveloped<EligibilityResult>> eligibility(String schemeId, {String? farmId}) async =>
      parseEnvelope(
        await _api.get('/api/schemes/${Uri.encodeComponent(schemeId)}/eligibility',
            query: {'farm_id': ?farmId}),
        EligibilityResult.fromJson,
      );
}

final schemeRepositoryProvider =
    Provider<SchemeRepository>((ref) => SchemeRepository(ref.watch(apiClientProvider)));

final schemeListProvider = FutureProvider.family<Enveloped<List<SchemeSummary>>, SchemeQuery>(
  (ref, q) => ref.watch(schemeRepositoryProvider).list(q),
);

final schemeDetailProvider = FutureProvider.family<Enveloped<SchemeDetail>, String>(
  (ref, id) => ref.watch(schemeRepositoryProvider).detail(id),
);

final schemeEligibilityProvider = FutureProvider.family<Enveloped<EligibilityResult>, EligibilityQuery>(
  (ref, q) => ref.watch(schemeRepositoryProvider).eligibility(q.schemeId, farmId: q.farmId),
);
