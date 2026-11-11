import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:mocktail/mocktail.dart';
import 'package:uzhavan/core/networking/api_failure.dart';
import 'package:uzhavan/core/storage/preferences.dart';
import 'package:uzhavan/core/storage/token_store.dart';
import 'package:uzhavan/features/auth/data/auth_repository.dart';
import 'package:uzhavan/features/auth/domain/auth_models.dart';
import 'package:uzhavan/features/auth/domain/session_state.dart';
import 'package:uzhavan/features/auth/presentation/otp_flow_controller.dart';
import 'package:uzhavan/features/auth/presentation/otp_screen.dart';
import 'package:uzhavan/features/auth/presentation/phone_screen.dart';
import 'package:uzhavan/features/auth/presentation/session_controller.dart';

import '../helpers/test_app.dart';

class MockAuthRepository extends Mock implements AuthRepository {}

void main() {
  late MockAuthRepository repo;
  late MemoryTokenStore store;

  setUp(() {
    repo = MockAuthRepository();
    store = MemoryTokenStore();
  });

  Future<ProviderContainer> container() => makeContainer(
        prefs: {PrefKeys.language: 'en'},
        tokenStore: store,
        overrides: [authRepositoryProvider.overrideWithValue(repo)],
      );

  Widget app(ProviderContainer c, String initial) => UncontrolledProviderScope(
        container: c,
        child: TestApp(
          routerConfig: GoRouter(initialLocation: initial, routes: [
            GoRoute(
              path: '/login',
              builder: (_, _) => const PhoneScreen(),
              routes: [GoRoute(path: 'otp', builder: (_, _) => const OtpScreen())],
            ),
          ]),
        ),
      );

  const sent = OtpSent(expiresIn: Duration(seconds: 300), resendAfter: Duration(seconds: 60));

  group('phone screen', () {
    testWidgets('rejects numbers that are not 10 digits starting 6–9', (tester) async {
      final c = await container();
      addTearDown(c.dispose);
      await tester.pumpWidget(app(c, '/login'));
      await tester.pumpAndSettle();

      for (final bad in ['12345', '5876543210']) {
        await tester.enterText(find.byKey(PhoneScreen.phoneFieldKey), bad);
        await tester.tap(find.byKey(PhoneScreen.sendButtonKey));
        await tester.pumpAndSettle();
        expect(find.text('Enter a 10-digit number starting with 6, 7, 8 or 9'), findsOneWidget);
      }
      verifyNever(() => repo.sendOtp(any()));
    });

    testWidgets('strips non-digits and caps input at 10 digits', (tester) async {
      final c = await container();
      addTearDown(c.dispose);
      await tester.pumpWidget(app(c, '/login'));
      await tester.pumpAndSettle();
      await tester.enterText(find.byKey(PhoneScreen.phoneFieldKey), '98a7654321099');
      final field = tester.widget<TextField>(find.descendant(
          of: find.byKey(PhoneScreen.phoneFieldKey), matching: find.byType(TextField)));
      expect(field.controller!.text, '9876543210');
    });

    testWidgets('valid number sends the OTP and opens the OTP screen', (tester) async {
      when(() => repo.sendOtp('9876543210')).thenAnswer((_) async => sent);
      final c = await container();
      addTearDown(c.dispose);
      await tester.pumpWidget(app(c, '/login'));
      await tester.pumpAndSettle();

      await tester.enterText(find.byKey(PhoneScreen.phoneFieldKey), '9876543210');
      await tester.tap(find.byKey(PhoneScreen.sendButtonKey));
      await tester.pump();
      await tester.pump();
      verify(() => repo.sendOtp('9876543210')).called(1);
      expect(find.text('OTP sent to +91 9876543210'), findsOneWidget);
      expect(find.text('Resend in 60 s'), findsOneWidget);
      await tester.pumpWidget(const SizedBox()); // dispose the countdown timer
    });

    testWidgets('maps rate_limited with Retry-After', (tester) async {
      when(() => repo.sendOtp(any())).thenThrow(const ApiFailure(
        kind: ApiFailureKind.rateLimited,
        code: 'rate_limited',
        retryAfter: Duration(seconds: 1800),
      ));
      final c = await container();
      addTearDown(c.dispose);
      await tester.pumpWidget(app(c, '/login'));
      await tester.pumpAndSettle();
      await tester.enterText(find.byKey(PhoneScreen.phoneFieldKey), '9876543210');
      await tester.tap(find.byKey(PhoneScreen.sendButtonKey));
      await tester.pumpAndSettle();
      expect(find.text('Too many requests. Try again in 30 min.'), findsOneWidget);
    });

    testWidgets('maps otp_delivery_not_configured (503)', (tester) async {
      when(() => repo.sendOtp(any())).thenThrow(const ApiFailure(
        kind: ApiFailureKind.unavailable,
        code: 'otp_delivery_not_configured',
        statusCode: 503,
      ));
      final c = await container();
      addTearDown(c.dispose);
      await tester.pumpWidget(app(c, '/login'));
      await tester.pumpAndSettle();
      await tester.enterText(find.byKey(PhoneScreen.phoneFieldKey), '9876543210');
      await tester.tap(find.byKey(PhoneScreen.sendButtonKey));
      await tester.pumpAndSettle();
      expect(find.text('SMS delivery is not available right now. Please try later.'), findsOneWidget);
    });
  });

  group('OTP screen', () {
    Future<ProviderContainer> withFlow() async {
      when(() => repo.sendOtp('9876543210')).thenAnswer((_) async => sent);
      final c = await container();
      await c.read(otpFlowProvider.notifier).send('9876543210');
      return c;
    }

    FilledButton verifyButton(WidgetTester t) =>
        t.widget<FilledButton>(find.byKey(OtpScreen.verifyButtonKey));

    testWidgets('verify is enabled only for exactly 6 digits', (tester) async {
      final c = await withFlow();
      addTearDown(c.dispose);
      await tester.pumpWidget(app(c, '/login/otp'));
      await tester.pump();

      expect(verifyButton(tester).onPressed, isNull);
      await tester.enterText(find.byKey(OtpScreen.otpFieldKey), '12345');
      await tester.pump();
      expect(verifyButton(tester).onPressed, isNull);
      expect(find.text('Enter the 6-digit code'), findsOneWidget);
      await tester.enterText(find.byKey(OtpScreen.otpFieldKey), '1234567');
      await tester.pump();
      expect(find.text('123456'), findsOneWidget, reason: 'capped at 6 digits');
      expect(verifyButton(tester).onPressed, isNotNull);
      await tester.pumpWidget(const SizedBox());
    });

    testWidgets('resend counts down from resend_after', (tester) async {
      final c = await withFlow();
      addTearDown(c.dispose);
      await tester.pumpWidget(app(c, '/login/otp'));
      await tester.pump();
      expect(find.text('Resend in 60 s'), findsOneWidget);
      expect(tester.widget<TextButton>(find.byKey(OtpScreen.resendButtonKey)).onPressed, isNull);
      await tester.pump(const Duration(seconds: 1));
      expect(find.text('Resend in 59 s'), findsOneWidget);
      await tester.pump(const Duration(seconds: 59));
      expect(find.text('Resend code'), findsOneWidget);
      expect(tester.widget<TextButton>(find.byKey(OtpScreen.resendButtonKey)).onPressed, isNotNull);
      await tester.pumpWidget(const SizedBox());
    });

    for (final (code, kind, expected) in [
      ('otp_incorrect', ApiFailureKind.validation, 'Incorrect code. Please try again.'),
      ('otp_expired', ApiFailureKind.validation, 'The code has expired. Request a new one.'),
      ('otp_not_found', ApiFailureKind.unavailable, 'No active code. Request a new one.'),
    ]) {
      testWidgets('maps $code', (tester) async {
        when(() => repo.verifyOtp(any(), any()))
            .thenThrow(ApiFailure(kind: kind, code: code));
        final c = await withFlow();
        addTearDown(c.dispose);
        await tester.pumpWidget(app(c, '/login/otp'));
        await tester.pump();
        await tester.enterText(find.byKey(OtpScreen.otpFieldKey), '123456');
        await tester.pump();
        await tester.tap(find.byKey(OtpScreen.verifyButtonKey));
        await tester.pump();
        await tester.pump();
        expect(find.text(expected), findsOneWidget);
        expect(store.tokens, isNull);
        await tester.pumpWidget(const SizedBox());
      });
    }

    testWidgets('success stores tokens and signs in', (tester) async {
      when(() => repo.verifyOtp('9876543210', '123456')).thenAnswer((_) async => const VerifyResult(
            tokens: AuthTokens(accessToken: 'acc', refreshToken: 'ref'),
            isNewFarmer: true,
            profileComplete: false,
          ));
      final c = await withFlow();
      addTearDown(c.dispose);
      await tester.pumpWidget(app(c, '/login/otp'));
      await tester.pump();
      await tester.enterText(find.byKey(OtpScreen.otpFieldKey), '123456');
      await tester.pump();
      await tester.tap(find.byKey(OtpScreen.verifyButtonKey));
      await tester.pump();
      await tester.pump();
      expect(store.tokens?.refreshToken, 'ref');
      expect(c.read(sessionProvider), const SessionState.signedIn(profileComplete: false));
      await tester.pumpWidget(const SizedBox());
    });
  });
}
