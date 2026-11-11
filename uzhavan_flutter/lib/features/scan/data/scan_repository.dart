import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/networking/api_client.dart';
import '../../../core/networking/envelope.dart';
import '../../../core/networking/providers.dart';
import '../domain/scan_models.dart';

/// JPEG/PNG/WebP by file extension (the server rejects other types).
DioMediaType imageMediaType(String filename) {
  final f = filename.toLowerCase();
  if (f.endsWith('.png')) return DioMediaType('image', 'png');
  if (f.endsWith('.webp')) return DioMediaType('image', 'webp');
  return DioMediaType('image', 'jpeg');
}

/// Contract §10. Until the model is approved the server answers 503
/// `model_unavailable`, which surfaces as an [ApiFailure] (unavailable).
class ScanRepository {
  ScanRepository(this._api);
  final ApiClient _api;

  Future<Enveloped<ScanResult>> scan({
    required MultipartFile image,
    String? cropId,
    void Function(int sent, int total)? onProgress,
  }) async {
    final form = FormData.fromMap({
      'image': image,
      'crop_id': ?cropId,
    });
    return parseEnvelope(
      await _api.postMultipart('/api/disease/scan', form, onSendProgress: onProgress),
      ScanResult.fromJson,
    );
  }
}

final scanRepositoryProvider =
    Provider<ScanRepository>((ref) => ScanRepository(ref.watch(apiClientProvider)));
