import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/networking/api_client.dart';
import '../../../core/networking/providers.dart';
import 'sse_parser.dart';

/// Contract §9 `POST /conversation` (SSE).
class AssistantRepository {
  AssistantRepository(this._api);
  final ApiClient _api;

  /// Throws [ApiFailure] if the request itself fails; stream errors are
  /// forwarded to the listener.
  Future<Stream<ConversationEvent>> ask({
    required String question,
    required String language,
    String? sessionId,
    String? farmId,
    Map<String, dynamic>? diseaseContext,
  }) async {
    final bytes = await _api.postStream('/conversation', body: {
      'question': question,
      'language': language,
      'session_id': ?sessionId,
      'farm_id': ?farmId,
      'disease_context': ?diseaseContext,
    });
    return parseSse(bytes);
  }
}

final assistantRepositoryProvider =
    Provider<AssistantRepository>((ref) => AssistantRepository(ref.watch(apiClientProvider)));
