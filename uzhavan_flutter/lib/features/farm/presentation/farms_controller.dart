import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/networking/api_failure.dart';
import '../../auth/domain/session_state.dart';
import '../../auth/presentation/session_controller.dart';
import '../data/farm_repository.dart';
import '../domain/farm.dart';

/// Contract §3: a farmer can own at most 5 farms.
const maxFarms = 5;

class FarmsController extends AsyncNotifier<List<Farm>> {
  @override
  Future<List<Farm>> build() async {
    final status = ref.watch(sessionProvider.select((s) => s.status));
    if (status != SessionStatus.signedIn) {
      throw const ApiFailure(kind: ApiFailureKind.unauthenticated, code: 'unauthenticated');
    }
    return ref.read(farmRepositoryProvider).list();
  }

  List<Farm> get _current => state.value ?? const [];

  /// Throws [ApiFailure].
  Future<Farm> create(FarmInput input) async {
    final farm = await ref.read(farmRepositoryProvider).create(input);
    state = AsyncData([..._current, farm]);
    return farm;
  }

  Future<Farm> updateFarm(String farmId, FarmInput input) async {
    final farm = await ref.read(farmRepositoryProvider).update(farmId, input);
    state = AsyncData([for (final f in _current) f.farmId == farmId ? farm : f]);
    return farm;
  }

  Future<void> delete(String farmId) async {
    await ref.read(farmRepositoryProvider).delete(farmId);
    state = AsyncData(_current.where((f) => f.farmId != farmId).toList());
  }
}

final farmsProvider =
    AsyncNotifierProvider<FarmsController, List<Farm>>(FarmsController.new);
