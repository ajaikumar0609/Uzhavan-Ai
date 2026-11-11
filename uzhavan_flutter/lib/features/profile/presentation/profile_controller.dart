import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/localization/locale_controller.dart';
import '../../../core/networking/api_failure.dart';
import '../../auth/domain/session_state.dart';
import '../../auth/presentation/session_controller.dart';
import '../data/profile_repository.dart';
import '../domain/farmer_profile.dart';

/// The signed-in farmer's profile. Refetches whenever the session changes.
class ProfileController extends AsyncNotifier<FarmerProfile> {
  @override
  Future<FarmerProfile> build() async {
    final status = ref.watch(sessionProvider.select((s) => s.status));
    if (status != SessionStatus.signedIn) {
      throw const ApiFailure(kind: ApiFailureKind.unauthenticated, code: 'unauthenticated');
    }
    return ref.read(profileRepositoryProvider).fetch();
  }

  /// Saves, updates the session's `profile_complete`, and applies the
  /// chosen language to the app. Throws [ApiFailure].
  Future<FarmerProfile> save(ProfileUpdate update) async {
    final saved = await ref.read(profileRepositoryProvider).update(update);
    state = AsyncData(saved);
    final lang = update.preferredLanguage;
    if (lang != null) {
      await ref.read(localeProvider.notifier).setLocale(AppLocales.fromCode(lang));
    }
    await ref.read(sessionProvider.notifier).setProfileComplete(saved.profileComplete);
    return saved;
  }
}

final profileProvider =
    AsyncNotifierProvider<ProfileController, FarmerProfile>(ProfileController.new);
