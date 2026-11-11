import '../../features/auth/domain/session_state.dart';
import 'routes.dart';

bool _isLogin(String location) =>
    location == Routes.login || location.startsWith('${Routes.login}/');

bool _isOnboarding(String location) =>
    location == '/onboarding' || location.startsWith('/onboarding/');

/// Pure redirect rule (unit-tested):
/// restoring → splash · signed out → /login · signed in with an incomplete
/// profile → /onboarding/profile · signed in and complete → never on
/// splash/login/onboarding.
String? authRedirect(SessionState session, String location) {
  switch (session.status) {
    case SessionStatus.restoring:
      return location == Routes.splash ? null : Routes.splash;
    case SessionStatus.signedOut:
      return _isLogin(location) ? null : Routes.login;
    case SessionStatus.signedIn:
      if (!session.profileComplete) {
        return location == Routes.onboardingProfile ? null : Routes.onboardingProfile;
      }
      if (location == Routes.splash || _isLogin(location) || _isOnboarding(location)) {
        return Routes.home;
      }
      return null;
  }
}
