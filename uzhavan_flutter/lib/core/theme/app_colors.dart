import 'package:flutter/material.dart';

/// Colour tokens of the UZHAVAN design system (light and dark).
@immutable
class AppColors extends ThemeExtension<AppColors> {
  const AppColors({
    required this.background,
    required this.foreground,
    required this.card,
    required this.primary,
    required this.primaryForeground,
    required this.primarySoft,
    required this.secondary,
    required this.muted,
    required this.mutedForeground,
    required this.accent,
    required this.accentForeground,
    required this.success,
    required this.warning,
    required this.warningForeground,
    required this.danger,
    required this.dangerForeground,
    required this.info,
    required this.border,
    required this.input,
  });

  final Color background;
  final Color foreground;
  final Color card;
  final Color primary;
  final Color primaryForeground;
  final Color primarySoft;
  final Color secondary;
  final Color muted;
  final Color mutedForeground;
  final Color accent;
  final Color accentForeground;
  final Color success;
  final Color warning;
  final Color warningForeground;
  final Color danger;
  final Color dangerForeground;
  final Color info;
  final Color border;
  final Color input;

  /// Light palette: deep forest + leaf green on warm ivory, with a restrained harvest amber.
  /// These are the ONLY colour literals in the app; widgets read them through `context.colors`.
  static const light = AppColors(
    background: Color(0xFFF7F6F0), // warm ivory
    foreground: Color(0xFF1C2923), // charcoal-green text
    card: Color(0xFFFFFFFF),
    primary: Color(0xFF173D32), // forest
    primaryForeground: Color(0xFFFFFFFF),
    primarySoft: Color(0xFFE8F1E9), // light green wash
    secondary: Color(0xFF347657), // leaf
    muted: Color(0xFFEFEEE6),
    mutedForeground: Color(0xFF68756D),
    accent: Color(0xFFD89B35), // harvest amber
    accentForeground: Color(0xFF3A2A08),
    success: Color(0xFF2F7D55),
    warning: Color(0xFFA9630F), // muted orange, AA on white
    warningForeground: Color(0xFF3A2206),
    danger: Color(0xFFB3261E), // muted red, AA on white
    dangerForeground: Color(0xFFFFFFFF),
    info: Color(0xFF2C6E9B),
    border: Color(0xFFE3E2D8),
    input: Color(0xFFD6D5C9),
  );

  /// Dark palette: the same hues at night. `primary` lightens so it stays readable on dark
  /// surfaces; hero surfaces therefore use dark text (`primaryForeground`).
  static const dark = AppColors(
    background: Color(0xFF0F1512),
    foreground: Color(0xFFE6EDE8),
    card: Color(0xFF18211C),
    primary: Color(0xFF8FD0AE),
    primaryForeground: Color(0xFF0B1F17),
    primarySoft: Color(0xFF1D2E26),
    secondary: Color(0xFF6DB893),
    muted: Color(0xFF1F2924),
    mutedForeground: Color(0xFF9CAAA1),
    accent: Color(0xFFE5B45C),
    accentForeground: Color(0xFF2A1E05),
    success: Color(0xFF7CC79F),
    warning: Color(0xFFE5A55A),
    warningForeground: Color(0xFF2A1800),
    danger: Color(0xFFF08A82),
    dangerForeground: Color(0xFF2A0907),
    info: Color(0xFF8BBEE0),
    border: Color(0xFF26322C),
    input: Color(0xFF34423A),
  );

  @override
  AppColors copyWith() => this;

  @override
  AppColors lerp(ThemeExtension<AppColors>? other, double t) =>
      (other is AppColors && t >= 0.5) ? other : this;
}

extension AppColorsContext on BuildContext {
  AppColors get colors =>
      Theme.of(this).extension<AppColors>() ?? AppColors.light;
}
