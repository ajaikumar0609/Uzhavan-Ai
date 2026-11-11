import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/assistant/presentation/assistant_screen.dart';
import '../../features/auth/domain/session_state.dart';
import '../../features/auth/presentation/otp_screen.dart';
import '../../features/auth/presentation/phone_screen.dart';
import '../../features/auth/presentation/session_controller.dart';
import '../../features/auth/presentation/splash_screen.dart';
import '../../features/diary/presentation/diary_form_screen.dart';
import '../../features/diary/presentation/diary_screen.dart';
import '../../features/farm/presentation/farm_form_screen.dart';
import '../../features/farm/presentation/farm_list_screen.dart';
import '../../features/home/presentation/home_screen.dart';
import '../../features/market/presentation/market_screen.dart';
import '../../features/profile/presentation/onboarding_profile_screen.dart';
import '../../features/profile/presentation/profile_edit_screen.dart';
import '../../features/profile/presentation/profile_screen.dart';
import '../../features/satellite/presentation/satellite_screen.dart';
import '../../features/scan/presentation/scan_screen.dart';
import '../../features/schemes/presentation/scheme_detail_screen.dart';
import '../../features/schemes/presentation/schemes_screen.dart';
import '../../features/settings/presentation/settings_screen.dart';
import '../../features/shell/presentation/main_shell.dart';
import '../../features/shell/presentation/more_screen.dart';
import '../../features/soil/presentation/soil_screen.dart';
import '../../features/soil/presentation/soil_test_form_screen.dart';
import '../../features/weather/presentation/weather_screen.dart';
import 'auth_redirect.dart';
import 'routes.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final session = ValueNotifier<SessionState>(ref.read(sessionProvider));
  ref.listen(sessionProvider, (_, next) => session.value = next);

  GoRoute leaf(String path, Widget child) =>
      GoRoute(path: path, builder: (_, _) => child);

  final router = GoRouter(
    initialLocation: Routes.splash,
    refreshListenable: session,
    redirect: (context, state) => authRedirect(session.value, state.uri.path),
    routes: [
      leaf(Routes.splash, const SplashScreen()),
      GoRoute(
        path: Routes.login,
        builder: (_, _) => const PhoneScreen(),
        routes: [GoRoute(path: 'otp', builder: (_, _) => const OtpScreen())],
      ),
      leaf(Routes.onboardingProfile, const OnboardingProfileScreen()),
      StatefulShellRoute.indexedStack(
        builder: (context, state, shell) => MainShell(navigationShell: shell),
        branches: [
          StatefulShellBranch(routes: [leaf(Routes.home, const HomeScreen())]),
          StatefulShellBranch(routes: [leaf(Routes.assistant, const AssistantScreen())]),
          StatefulShellBranch(routes: [leaf(Routes.scan, const ScanScreen())]),
          StatefulShellBranch(routes: [leaf(Routes.market, const MarketScreen())]),
          StatefulShellBranch(routes: [
            GoRoute(
              path: Routes.more,
              builder: (_, _) => const MoreScreen(),
              routes: [
                GoRoute(path: 'weather', builder: (_, _) => const WeatherScreen()),
                GoRoute(
                  path: 'schemes',
                  builder: (_, _) => const SchemesScreen(),
                  routes: [
                    GoRoute(
                      path: ':schemeId',
                      builder: (_, state) => SchemeDetailScreen(schemeId: state.pathParameters['schemeId']!),
                    ),
                  ],
                ),
                GoRoute(
                  path: 'soil',
                  builder: (_, _) => const SoilScreen(),
                  routes: [GoRoute(path: 'new', builder: (_, _) => const SoilTestFormScreen())],
                ),
                GoRoute(
                  path: 'farms',
                  builder: (_, _) => const FarmListScreen(),
                  routes: [
                    GoRoute(path: 'new', builder: (_, _) => const FarmFormScreen()),
                    GoRoute(
                      path: ':farmId/edit',
                      builder: (_, state) => FarmFormScreen(farmId: state.pathParameters['farmId']),
                    ),
                  ],
                ),
                GoRoute(
                  path: 'diary',
                  builder: (_, _) => const DiaryScreen(),
                  routes: [GoRoute(path: 'new', builder: (_, _) => const DiaryFormScreen())],
                ),
                GoRoute(path: 'satellite', builder: (_, _) => const SatelliteScreen()),
                GoRoute(
                  path: 'profile',
                  builder: (_, _) => const ProfileScreen(),
                  routes: [GoRoute(path: 'edit', builder: (_, _) => const ProfileEditScreen())],
                ),
                GoRoute(path: 'settings', builder: (_, _) => const SettingsScreen()),
              ],
            ),
          ]),
        ],
      ),
    ],
  );
  ref.onDispose(() {
    router.dispose();
    session.dispose();
  });
  return router;
});
