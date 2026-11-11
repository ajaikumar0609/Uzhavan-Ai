# UZHAVAN AI: Flutter app (Android)

The farmer-facing mobile app. Tamil first, English second. It talks only to
the FastAPI backend described in
`uzhavan_platform/docs/architecture/API_CONTRACT_M06.md` (the source of truth).

Sprint scope (FP-016 core, FP-017 localization): auth (phone OTP), profile, farms,
settings and the app shell. Wave B adds Home, Assistant (SSE + voice), Scan,
Market, Weather, Schemes, Soil, Diary and Satellite (contract §4–§11). Every data
card carries a `SourceLine` built from `meta` (source · updated/observed date ·
"old data" chip). A null value shows "not available". Nothing is defaulted or invented.
Location-based screens use the selected farm (`selectedFarmProvider`), else the
profile district (`LocationGate`).

## Architecture

```
lib/
  main.dart                  bootstrap: prefs, AppConfig (or the config error screen), ProviderScope
  app.dart                   MaterialApp.router (theme, locale, router)
  core/
    config/                  AppConfig (API_BASE_URL, release https rule), ConfigErrorApp
    networking/              ApiClient (Dio), AuthInterceptor, TokenRefresher, ApiFailure, error mapper
    storage/                 TokenStore (flutter_secure_storage), shared_preferences keys
    theme/                   Material 3 light/dark from the React styles.css tokens; Noto Sans Tamil
    localization/            ARB files (arb/), generated code (generated/), BilingualText, LocaleController
    routing/                 go_router + pure authRedirect()
  shared/
    utils/                   area units (acres↔ha), validators, failure → localized text
    widgets/                 AppScaffold, LanguageSwitchButton, DataStateView, pickers, ComingSoonScreen
  features/<feature>/
    data/                    repository (uses ApiClient only)
    domain/                  models with fromJson
    presentation/            screens + Riverpod controllers
```

Rules:
- **State:** Riverpod 3 (`Notifier` / `AsyncNotifier`). Widgets never call Dio or
  build URLs. They read providers and call repository or controller methods.
- **Errors:** every request either returns JSON or throws `ApiFailure{kind, code, message{en,ta}}`.
  Mapping follows contract §0: network failure / 404 / 501 / 503 → `unavailable`;
  500 → `error`; 401 → `unauthenticated` (after one refresh attempt); 429 →
  `rateLimited` (+ `Retry-After`); other 4xx → `validation`.
- **Auth:** tokens are kept only in secure storage. On a 401, the interceptor calls
  `/api/auth/refresh` once. The refresh is single-flight: concurrent 401s share it,
  because the refresh token is single-use and rotates. It then retries the request once.
  If the server rejects the refresh token, the tokens are cleared and the router sends the user to `/login`.
- **Routing:** `authRedirect()` does this: restoring → `/splash`; signed out → `/login`;
  signed in with an incomplete profile → `/onboarding/profile`; otherwise the shell
  (Home · Assistant · Scan · Market · More).
- **Data states:** `DataStateView` mirrors the React `DataState`
  (loading / success / empty / unavailable / error / unsure, with Retry). Nothing
  is ever substituted for missing data. Unset profile or farm fields show "Not set".
- **Units:** farmers type and read acres (1 decimal). The API gets hectares
  (`1 acre = 0.404686 ha`).
- **Riverpod retry is disabled.** Failures show a Retry button instead of retrying silently.

## Run

Always use the Flutter SDK at `~/flutter/bin/flutter` (the `dart` on PATH is a different install).

```bash
cd ~/Desktop/agri/uzhavan_flutter
~/flutter/bin/flutter pub get

# Android emulator (backend on the host at :8000; 10.0.2.2 is the host loopback)
~/flutter/bin/flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000

# Physical device on the same Wi-Fi as the backend machine
~/flutter/bin/flutter run --dart-define=API_BASE_URL=http://<LAN-IP>:8000
#   or, over USB: adb reverse tcp:8000 tcp:8000, then use http://127.0.0.1:8000

# Debug APK
~/flutter/bin/flutter build apk --debug --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

- Without `API_BASE_URL`, Android uses `http://10.0.2.2:8000` and other targets use `http://127.0.0.1:8000`.
- Plain `http` works only in debug and profile builds (`usesCleartextTraffic` is set in
  `android/app/src/debug|profile/AndroidManifest.xml`).
- A **release** build shows a configuration error screen and does not start
  if `API_BASE_URL` isn't `https://`. `--dart-define=ALLOW_INSECURE_API=true` overrides this for
  a controlled test build only. Release signing isn't configured yet.
- In debug builds, the API base URL appears under More → Settings → About.

## Checks

```bash
~/flutter/bin/flutter analyze          # must report: No issues found
~/flutter/bin/flutter test             # unit + widget tests
./tool/check_no_fabrication.sh         # blocked fabricated strings (same list as the React check)
```

## Adding or changing a user-facing string

1. Add the key to **both** `lib/core/localization/arb/app_ta.arb` (the template;
   placeholder metadata `@key` goes here) and `app_en.arb`.
2. Run `~/flutter/bin/flutter gen-l10n` (it also runs automatically on `pub get` / build).
3. Use it as `context.l10n.yourKey` (`import 'core/localization/l10n.dart'`).

Never hard-code text in widgets. Never branch on the language (`lang == 'ta' ? … : …`).
Server text arrives as `{en, ta}`: parse it with `BilingualText.fromJson` and render it
with `context.bi(text)`. That helper shows `ta` in Tamil mode and falls back to
`en` only when `ta` is null or blank.

Do not write sample names, numbers or claims of data provenance in strings.
`tool/check_no_fabrication.sh` fails the build on the known ones.
