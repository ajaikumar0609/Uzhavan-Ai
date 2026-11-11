import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/widgets/option_picker_field.dart';
import '../data/meta_repository.dart';
import '../domain/meta_models.dart';

final districtsProvider = FutureProvider<List<District>>(
  (ref) => ref.watch(metaRepositoryProvider).districts(),
);

final cropsProvider = FutureProvider<List<RefItem>>(
  (ref) => ref.watch(metaRepositoryProvider).crops(),
);

final enumsProvider = FutureProvider<MetaEnums>(
  (ref) => ref.watch(metaRepositoryProvider).enums(),
);

final districtOptionsProvider = Provider<AsyncValue<List<PickerOption>>>(
  (ref) => ref.watch(districtsProvider).whenData((d) => d.map((e) => e.toOption()).toList()),
);

final cropOptionsProvider = Provider<AsyncValue<List<PickerOption>>>(
  (ref) => ref.watch(cropsProvider).whenData((d) => d.map((e) => e.toOption()).toList()),
);
