import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/networking/api_client.dart';
import '../../../core/networking/envelope.dart';
import '../../../core/networking/providers.dart';
import '../domain/diary_models.dart';

/// Contract §8 🔒.
class DiaryRepository {
  DiaryRepository(this._api);
  final ApiClient _api;

  Future<List<DiaryEntry>> list({int limit = 50}) async => jsonListOrEmpty(
        unwrapData(await _api.get('/api/diary', query: {'limit': limit})),
      ).map(DiaryEntry.fromJson).toList();

  /// 201 → the entry (bare or enveloped).
  Future<DiaryEntry> add(DiaryInput input) async {
    final body = await _api.post('/api/diary', body: input.toJson());
    return DiaryEntry.fromJson(body is Map && body.containsKey('data') ? body['data'] : body);
  }
}

final diaryRepositoryProvider =
    Provider<DiaryRepository>((ref) => DiaryRepository(ref.watch(apiClientProvider)));

final diaryProvider = FutureProvider<List<DiaryEntry>>(
  (ref) => ref.watch(diaryRepositoryProvider).list(),
);
