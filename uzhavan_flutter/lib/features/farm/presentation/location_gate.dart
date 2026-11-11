import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/routing/routes.dart';
import '../../../shared/widgets/data_state_view.dart';
import '../../profile/presentation/profile_controller.dart';
import 'farms_controller.dart';
import 'selected_farm.dart';

/// Resolves the data location (selected farm › profile district) and builds
/// [builder] with it. With neither, shows an empty state that links to farms.
class LocationGate extends ConsumerWidget {
  const LocationGate({super.key, required this.builder});
  final Widget Function(BuildContext context, DataLocation loc) builder;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    return DataStateView<DataLocation>(
      value: ref.watch(dataLocationProvider),
      unavailableText: l.profileUnavailable,
      isEmpty: (loc) => loc.isEmpty,
      emptyText: l.locationMissing,
      emptyAction: FilledButton.tonal(
        style: FilledButton.styleFrom(minimumSize: const Size(0, 40)),
        onPressed: () => context.go(Routes.farmNew),
        child: Text(l.farmAdd),
      ),
      onRetry: () {
        ref.invalidate(farmsProvider);
        ref.invalidate(profileProvider);
      },
      builder: builder,
    );
  }
}
