import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/networking/api_failure.dart';
import '../../../core/networking/providers.dart';
import '../../profile/data/profile_repository.dart';
import '../data/auth_repository.dart';
import '../domain/session_state.dart';

/// Owns the signed-in state. Restores the session on start-up, signs in with
/// an OTP, logs out, and reacts to a server-rejected refresh token.
class SessionController extends Notifier<SessionState> {
  @override
  SessionState build() {
    final sub = ref.watch(sessionEventsProvider).expired.listen((_) => _expire());
    ref.onDispose(sub.cancel);
    Future.microtask(_restore);
    return const SessionState.restoring();
  }

  Future<void> _restore() async {
    final store = ref.read(tokenStoreProvider);
    final tokens = await store.read();
    if (tokens == null) {
      state = const SessionState.signedOut();
      return;
    }
    try {
      final profile = await ref.read(profileRepositoryProvider).fetch();
      await store.saveProfileComplete(profile.profileComplete);
      state = SessionState.signedIn(profileComplete: profile.profileComplete);
    } on ApiFailure catch (f) {
      if (f.kind == ApiFailureKind.unauthenticated) {
        await store.clear();
        state = const SessionState.signedOut(expired: true);
      } else {
        // Offline or server down: keep the session with the last known state.
        final cached = await store.readProfileComplete();
        state = SessionState.signedIn(profileComplete: cached ?? true);
      }
    }
  }

  /// Verifies the OTP and stores the tokens. Throws [ApiFailure].
  Future<void> signInWithOtp(String phone, String otp) async {
    final result = await ref.read(authRepositoryProvider).verifyOtp(phone, otp);
    final store = ref.read(tokenStoreProvider);
    await store.save(result.tokens);
    await store.saveProfileComplete(result.profileComplete);
    state = SessionState.signedIn(profileComplete: result.profileComplete);
  }

  Future<void> setProfileComplete(bool complete) async {
    await ref.read(tokenStoreProvider).saveProfileComplete(complete);
    if (state.isSignedIn) state = SessionState.signedIn(profileComplete: complete);
  }

  /// Revokes server-side when reachable, then always clears local tokens.
  Future<void> logout() async {
    final store = ref.read(tokenStoreProvider);
    final tokens = await store.read();
    if (tokens != null) {
      try {
        await ref.read(authRepositoryProvider).logout(tokens.refreshToken);
      } on ApiFailure {
        // Local sign-out still happens; the refresh token expires server-side.
      }
    }
    await store.clear();
    state = const SessionState.signedOut();
  }

  Future<void> _expire() async {
    await ref.read(tokenStoreProvider).clear();
    state = const SessionState.signedOut(expired: true);
  }
}

final sessionProvider =
    NotifierProvider<SessionController, SessionState>(SessionController.new);
