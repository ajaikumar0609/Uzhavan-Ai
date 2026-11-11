import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/storage/preferences.dart';
import '../../profile/presentation/profile_controller.dart';
import '../domain/farm.dart';
import 'farms_controller.dart';

/// The farm the farmer picked (persisted). Null → the first farm.
class SelectedFarmIdController extends Notifier<String?> {
  @override
  String? build() => ref.watch(sharedPreferencesProvider).getString(PrefKeys.selectedFarm);

  Future<void> select(String farmId) async {
    state = farmId;
    await ref.read(sharedPreferencesProvider).setString(PrefKeys.selectedFarm, farmId);
  }
}

final selectedFarmIdProvider =
    NotifierProvider<SelectedFarmIdController, String?>(SelectedFarmIdController.new);

/// The selected farm; null when the farmer has none.
final selectedFarmProvider = Provider<AsyncValue<Farm?>>((ref) {
  final id = ref.watch(selectedFarmIdProvider);
  return ref.watch(farmsProvider).whenData((farms) {
    if (farms.isEmpty) return null;
    return farms.where((f) => f.farmId == id).firstOrNull ?? farms.first;
  });
});

/// Where location-based data comes from: the selected farm, else the
/// profile district (contract §4 location resolution). Null → neither.
@immutable
class DataLocation {
  const DataLocation({this.farmId, this.districtId});
  final String? farmId;
  final String? districtId;

  bool get isEmpty => farmId == null && districtId == null;

  Map<String, Object?> toQuery() =>
      farmId != null ? {'farm_id': farmId} : {'district_id': districtId};

  @override
  bool operator ==(Object other) =>
      other is DataLocation && other.farmId == farmId && other.districtId == districtId;

  @override
  int get hashCode => Object.hash(farmId, districtId);
}

/// Resolves once farms and profile have loaded. A farms failure falls back to
/// the profile district so a single failed call does not blank the screen.
final dataLocationProvider = Provider<AsyncValue<DataLocation>>((ref) {
  final farm = ref.watch(selectedFarmProvider);
  final profile = ref.watch(profileProvider);
  if (farm.hasValue && !farm.hasError && farm.value != null) {
    return AsyncData(DataLocation(farmId: farm.value!.farmId));
  }
  if (farm.isLoading && !farm.hasValue) return const AsyncLoading();
  if (profile.isLoading && !profile.hasValue) return const AsyncLoading();
  if (profile.hasValue && !profile.hasError) {
    return AsyncData(DataLocation(districtId: profile.value!.districtId));
  }
  return AsyncError(profile.error ?? farm.error ?? StateError('no location'), StackTrace.empty);
});

/// A compact farm switcher; hidden when the farmer has fewer than 2 farms.
class FarmPicker extends ConsumerWidget {
  const FarmPicker({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final farms = ref.watch(farmsProvider).value ?? const <Farm>[];
    if (farms.length < 2) return const SizedBox.shrink();
    final selected = ref.watch(selectedFarmProvider).value;
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: DropdownButtonFormField<String>(
        key: const Key('farm-picker'),
        initialValue: selected?.farmId,
        isExpanded: true,
        decoration: InputDecoration(
          labelText: context.l10n.farmPickerLabel,
          prefixIcon: const Icon(Icons.agriculture_outlined),
        ),
        items: [
          for (final f in farms)
            DropdownMenuItem(
              value: f.farmId,
              child: Text(f.name, maxLines: 1, overflow: TextOverflow.ellipsis),
            ),
        ],
        onChanged: (id) {
          if (id != null) ref.read(selectedFarmIdProvider.notifier).select(id);
        },
      ),
    );
  }
}
