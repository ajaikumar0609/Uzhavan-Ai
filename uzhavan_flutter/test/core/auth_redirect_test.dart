import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/core/routing/auth_redirect.dart';
import 'package:uzhavan/core/routing/routes.dart';
import 'package:uzhavan/features/auth/domain/session_state.dart';

void main() {
  const restoring = SessionState.restoring();
  const signedOut = SessionState.signedOut();
  const incomplete = SessionState.signedIn(profileComplete: false);
  const complete = SessionState.signedIn(profileComplete: true);

  test('while restoring everything waits on the splash', () {
    expect(authRedirect(restoring, Routes.home), Routes.splash);
    expect(authRedirect(restoring, Routes.splash), isNull);
  });

  test('signed out → /login, but the login flow is allowed', () {
    expect(authRedirect(signedOut, Routes.home), Routes.login);
    expect(authRedirect(signedOut, Routes.farms), Routes.login);
    expect(authRedirect(signedOut, Routes.splash), Routes.login);
    expect(authRedirect(signedOut, Routes.onboardingProfile), Routes.login);
    expect(authRedirect(signedOut, Routes.login), isNull);
    expect(authRedirect(signedOut, Routes.otp), isNull);
    expect(authRedirect(signedOut, '/loginx'), Routes.login);
  });

  test('signed in with an incomplete profile → onboarding', () {
    expect(authRedirect(incomplete, Routes.home), Routes.onboardingProfile);
    expect(authRedirect(incomplete, Routes.login), Routes.onboardingProfile);
    expect(authRedirect(incomplete, Routes.onboardingProfile), isNull);
  });

  test('signed in and complete → never on splash/login/onboarding', () {
    expect(authRedirect(complete, Routes.splash), Routes.home);
    expect(authRedirect(complete, Routes.login), Routes.home);
    expect(authRedirect(complete, Routes.otp), Routes.home);
    expect(authRedirect(complete, Routes.onboardingProfile), Routes.home);
    expect(authRedirect(complete, Routes.home), isNull);
    expect(authRedirect(complete, Routes.farmEdit('f1')), isNull);
    expect(authRedirect(complete, Routes.settings), isNull);
  });
}
