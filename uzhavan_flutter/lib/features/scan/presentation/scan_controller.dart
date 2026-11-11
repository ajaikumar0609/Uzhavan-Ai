import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/networking/api_failure.dart';
import '../../../core/networking/envelope.dart';
import '../data/scan_repository.dart';
import '../domain/scan_models.dart';

enum PickSource { camera, gallery }

class PickDenied implements Exception {
  const PickDenied();
}

/// The farmer's own photo. Overridable in tests.
abstract class ImageSourcePicker {
  /// Returns a file path, null if cancelled; throws [PickDenied].
  Future<String?> pick(PickSource source);
}

class DeviceImagePicker implements ImageSourcePicker {
  final _picker = ImagePicker();

  @override
  Future<String?> pick(PickSource source) async {
    try {
      final f = await _picker.pickImage(
        source: source == PickSource.camera ? ImageSource.camera : ImageSource.gallery,
        maxWidth: 1600,
        maxHeight: 1600,
        imageQuality: 85,
      );
      return f?.path;
    } on PlatformException catch (e) {
      if (e.code.contains('access_denied')) throw const PickDenied();
      rethrow;
    }
  }
}

final imagePickerProvider = Provider<ImageSourcePicker>((ref) => DeviceImagePicker());

/// Builds the upload part from a path (overridable so tests need no files).
typedef ImagePartBuilder = Future<MultipartFile> Function(String path);

final imagePartBuilderProvider = Provider<ImagePartBuilder>(
  (ref) => (path) => MultipartFile.fromFile(path,
      filename: path.split('/').last, contentType: imageMediaType(path)),
);

enum ScanPhase { idle, uploading, done, failed }

@immutable
class ScanState {
  const ScanState({
    this.cropId,
    this.imagePath,
    this.phase = ScanPhase.idle,
    this.progress,
    this.result,
    this.failure,
  });

  final String? cropId;
  final String? imagePath;
  final ScanPhase phase;

  /// 0..1 while uploading; null when the total size is unknown.
  final double? progress;

  /// Set only after a 200 response.
  final Enveloped<ScanResult>? result;
  final ApiFailure? failure;

  bool get canSubmit => imagePath != null && cropId != null && phase != ScanPhase.uploading;
}

class ScanController extends Notifier<ScanState> {
  @override
  ScanState build() => const ScanState();

  void selectCrop(String? cropId) =>
      state = ScanState(cropId: cropId, imagePath: state.imagePath);

  /// Throws [PickDenied] when camera/gallery access is refused.
  Future<void> pick(PickSource source) async {
    final path = await ref.read(imagePickerProvider).pick(source);
    if (path != null) state = ScanState(cropId: state.cropId, imagePath: path);
  }

  void removeImage() => state = ScanState(cropId: state.cropId);

  Future<void> submit() async {
    final path = state.imagePath;
    if (path == null || state.phase == ScanPhase.uploading) return;
    state = ScanState(cropId: state.cropId, imagePath: path, phase: ScanPhase.uploading, progress: 0);
    try {
      final part = await ref.read(imagePartBuilderProvider)(path);
      final env = await ref.read(scanRepositoryProvider).scan(
            image: part,
            cropId: state.cropId,
            onProgress: (sent, total) {
              if (state.phase != ScanPhase.uploading) return;
              state = ScanState(
                cropId: state.cropId,
                imagePath: path,
                phase: ScanPhase.uploading,
                progress: total > 0 ? (sent / total).clamp(0, 1).toDouble() : null,
              );
            },
          );
      state = ScanState(cropId: state.cropId, imagePath: path, phase: ScanPhase.done, result: env);
    } on ApiFailure catch (f) {
      state = ScanState(cropId: state.cropId, imagePath: path, phase: ScanPhase.failed, failure: f);
    } catch (_) {
      state = ScanState(
        cropId: state.cropId,
        imagePath: path,
        phase: ScanPhase.failed,
        failure: const ApiFailure(kind: ApiFailureKind.error, code: 'upload_failed'),
      );
    }
  }
}

final scanProvider = NotifierProvider<ScanController, ScanState>(ScanController.new);
