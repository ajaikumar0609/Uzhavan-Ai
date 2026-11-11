import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/l10n.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/data_state_view.dart';
import 'profile_controller.dart';
import 'profile_form.dart';

class ProfileEditScreen extends ConsumerWidget {
  const ProfileEditScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    return AppScaffold(
      title: l.profileEdit,
      body: DataStateView(
        value: ref.watch(profileProvider),
        unavailableText: l.profileUnavailable,
        onRetry: () => ref.invalidate(profileProvider),
        builder: (context, p) => ProfileForm(
          initial: p,
          submitLabel: l.save,
          onSaved: (_) {
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l.saved)));
            if (context.canPop()) context.pop();
          },
        ),
      ),
    );
  }
}
