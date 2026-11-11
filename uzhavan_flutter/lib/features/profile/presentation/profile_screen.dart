import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/routing/routes.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/data_state_view.dart';
import '../../../shared/widgets/value_text.dart';
import '../../auth/presentation/logout_dialog.dart';
import '../../meta/presentation/meta_providers.dart';
import 'profile_controller.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final districts = ref.watch(districtsProvider).value;
    return AppScaffold(
      title: l.featureProfile,
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(profileProvider.future),
        child: DataStateView(
          value: ref.watch(profileProvider),
          unavailableText: l.profileUnavailable,
          onRetry: () => ref.invalidate(profileProvider),
          builder: (context, p) {
            String? district;
            if (p.districtId != null) {
              final match = districts?.where((d) => d.id == p.districtId).firstOrNull;
              district = match == null ? p.districtId : context.bi(match.name);
            }
            return ListView(
              padding: const EdgeInsets.symmetric(vertical: 8),
              children: [
                LabeledValue(icon: Icons.person_outline, label: l.profileName, value: p.name),
                LabeledValue(
                  icon: Icons.phone_outlined,
                  label: l.profilePhone,
                  value: p.phone.isEmpty ? null : '${l.phonePrefix} ${p.phone}',
                ),
                LabeledValue(icon: Icons.map_outlined, label: l.profileDistrict, value: district),
                LabeledValue(icon: Icons.home_work_outlined, label: l.profileVillage, value: p.village),
                LabeledValue(
                  icon: Icons.translate,
                  label: l.profileLanguage,
                  value: p.preferredLanguage == 'en' ? l.languageEnglish : l.languageTamil,
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                  child: FilledButton.icon(
                    onPressed: () => context.push(Routes.profileEdit),
                    icon: const Icon(Icons.edit_outlined),
                    label: Text(l.profileEdit),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: OutlinedButton.icon(
                    onPressed: () => confirmAndLogout(context, ref),
                    icon: const Icon(Icons.logout),
                    label: Text(l.logout),
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}
