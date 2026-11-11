/// Route paths (single source for navigation).
abstract final class Routes {
  static const splash = '/splash';
  static const login = '/login';
  static const otp = '/login/otp';
  static const onboardingProfile = '/onboarding/profile';

  static const home = '/home';
  static const assistant = '/assistant';
  static const scan = '/scan';
  static const market = '/market';
  static const more = '/more';

  static const weather = '/more/weather';
  static const schemes = '/more/schemes';
  static String schemeDetail(String id) => '/more/schemes/${Uri.encodeComponent(id)}';
  static const soil = '/more/soil';
  static const soilTestNew = '/more/soil/new';
  static const diaryNew = '/more/diary/new';
  static const farms = '/more/farms';
  static const farmNew = '/more/farms/new';
  static String farmEdit(String farmId) => '/more/farms/${Uri.encodeComponent(farmId)}/edit';
  static const diary = '/more/diary';
  static const satellite = '/more/satellite';
  static const profile = '/more/profile';
  static const profileEdit = '/more/profile/edit';
  static const settings = '/more/settings';
}
