import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/localization/l10n.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/data_state_view.dart';
import '../../auth/presentation/session_controller.dart';
import 'profile_controller.dart';
import 'profile_form.dart';

/// First-run profile step for new farmers (name + district required).
class OnboardingProfileScreen extends ConsumerWidget {
  const OnboardingProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final profile = ref.watch(profileProvider);
    return AppScaffold(
      title: l.onboardingTitle,
      automaticallyImplyLeading: false,
      actions: [
        IconButton(
          tooltip: l.logout,
          icon: const Icon(Icons.logout),
          onPressed: () => ref.read(sessionProvider.notifier).logout(),
        ),
      ],
      body: DataStateView(
        value: profile,
        unavailableText: l.profileUnavailable,
        onRetry: () => ref.invalidate(profileProvider),
        builder: (context, p) => ProfileForm(
          initial: p,
          submitLabel: l.onboardingContinue,
          header: Padding(
            padding: const EdgeInsets.only(bottom: 20),
            child: Text(l.onboardingSubtitle, style: Theme.of(context).textTheme.titleMedium),
          ),
          onSaved: (saved) {
            if (!saved.profileComplete) {
              ScaffoldMessenger.of(context)
                  .showSnackBar(SnackBar(content: Text(l.profileStillIncomplete)));
            }
            // When complete, the router redirect moves on to Home.
          },
        ),
      ),
    );
  }
}
