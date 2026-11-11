import 'package:flutter/material.dart';

import 'app_colors.dart';
import 'app_tokens.dart';

/// Material 3 themes built from the UZHAVAN design tokens.
abstract final class AppTheme {
  /// Latin uses the platform sans (Roboto on Android); Tamil glyphs, which
  /// Roboto lacks, come from the bundled Noto Sans Tamil. This order avoids
  /// the serif fallback Latin got when Noto Sans Tamil was the primary family.
  static const fontFamily = 'Roboto';
  static const fontFamilyFallback = <String>['NotoSansTamil', 'sans-serif'];

  static ThemeData light() => _build(AppColors.light, Brightness.light);
  static ThemeData dark() => _build(AppColors.dark, Brightness.dark);

  static TextStyle _t(double size, FontWeight w, Color color, {double height = 1.35, double spacing = 0}) => TextStyle(
        fontFamily: fontFamily,
        fontFamilyFallback: fontFamilyFallback,
        fontSize: size,
        fontWeight: w,
        height: height,
        letterSpacing: spacing,
        color: color,
      );

  /// Type scale. Line heights are generous (>= 1.3) because Tamil glyphs with vowel signs are
  /// taller than Latin; tighter leading clipped them.
  static TextTheme _textTheme(AppColors c) => TextTheme(
        displaySmall: _t(32, FontWeight.w700, c.foreground, height: 1.25, spacing: -0.4),
        headlineMedium: _t(26, FontWeight.w700, c.foreground, height: 1.3, spacing: -0.3),
        headlineSmall: _t(22, FontWeight.w700, c.foreground, height: 1.3, spacing: -0.2),
        titleLarge: _t(19, FontWeight.w700, c.foreground),
        titleMedium: _t(16, FontWeight.w600, c.foreground),
        titleSmall: _t(14, FontWeight.w600, c.foreground),
        bodyLarge: _t(16, FontWeight.w400, c.foreground, height: 1.5),
        bodyMedium: _t(14.5, FontWeight.w400, c.foreground, height: 1.5),
        bodySmall: _t(12.5, FontWeight.w400, c.mutedForeground, height: 1.45),
        labelLarge: _t(14.5, FontWeight.w600, c.foreground),
        labelMedium: _t(12.5, FontWeight.w600, c.foreground),
        labelSmall: _t(11.5, FontWeight.w600, c.mutedForeground, spacing: 0.2),
      );

  static ThemeData _build(AppColors c, Brightness brightness) {
    final scheme = ColorScheme(
      brightness: brightness,
      primary: c.primary,
      onPrimary: c.primaryForeground,
      primaryContainer: c.primarySoft,
      onPrimaryContainer: c.foreground,
      secondary: c.secondary,
      onSecondary: brightness == Brightness.light ? Colors.white : c.primaryForeground,
      secondaryContainer: c.primarySoft,
      onSecondaryContainer: c.foreground,
      tertiary: c.accent,
      onTertiary: c.accentForeground,
      error: c.danger,
      onError: c.dangerForeground,
      surface: c.background,
      onSurface: c.foreground,
      onSurfaceVariant: c.mutedForeground,
      surfaceContainerLowest: c.card,
      surfaceContainerLow: c.card,
      surfaceContainer: c.card,
      surfaceContainerHigh: c.muted,
      surfaceContainerHighest: c.muted,
      outline: c.input,
      outlineVariant: c.border,
    );
    final text = _textTheme(c);
    final control = AppRadius.control;
    OutlineInputBorder inputBorder(Color color, [double width = 1]) =>
        OutlineInputBorder(borderRadius: control, borderSide: BorderSide(color: color, width: width));

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      brightness: brightness,
      fontFamily: fontFamily,
      fontFamilyFallback: fontFamilyFallback,
      textTheme: text,
      scaffoldBackgroundColor: c.background,
      splashFactory: InkSparkle.splashFactory,
      extensions: [c],
      pageTransitionsTheme: const PageTransitionsTheme(builders: {
        TargetPlatform.android: FadeForwardsPageTransitionsBuilder(),
        TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
      }),
      appBarTheme: AppBarTheme(
        // The bar shares the page colour so the screen reads as one surface; a hairline
        // appears only once content scrolls under it.
        backgroundColor: c.background,
        foregroundColor: c.foreground,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0.6,
        shadowColor: c.foreground.withValues(alpha: 0.25),
        centerTitle: false,
        titleTextStyle: text.titleLarge,
        iconTheme: IconThemeData(color: c.foreground, size: 24),
      ),
      cardTheme: CardThemeData(
        color: c.card,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(borderRadius: AppRadius.card, side: BorderSide(color: c.border)),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: c.card,
        contentPadding: const EdgeInsets.symmetric(horizontal: AppSpace.lg, vertical: 15),
        hintStyle: text.bodyLarge?.copyWith(color: c.mutedForeground),
        labelStyle: text.bodyLarge?.copyWith(color: c.mutedForeground),
        floatingLabelStyle: text.labelLarge?.copyWith(color: c.secondary),
        helperStyle: text.bodySmall,
        errorStyle: text.bodySmall?.copyWith(color: c.danger),
        border: inputBorder(c.input),
        enabledBorder: inputBorder(c.input),
        focusedBorder: inputBorder(c.secondary, 1.8),
        errorBorder: inputBorder(c.danger),
        focusedErrorBorder: inputBorder(c.danger, 1.8),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(52),
          shape: RoundedRectangleBorder(borderRadius: control),
          textStyle: text.labelLarge?.copyWith(fontSize: 16, fontWeight: FontWeight.w700),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size.fromHeight(48),
          foregroundColor: c.primary,
          side: BorderSide(color: c.input),
          shape: RoundedRectangleBorder(borderRadius: control),
          textStyle: text.labelLarge,
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: c.secondary,
          minimumSize: const Size(48, 44),
          textStyle: text.labelLarge,
        ),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(minimumSize: const Size(44, 44)),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: c.card,
        selectedColor: c.primarySoft,
        disabledColor: c.muted,
        side: BorderSide(color: c.border),
        shape: RoundedRectangleBorder(borderRadius: AppRadius.chip),
        labelStyle: text.labelLarge?.copyWith(fontWeight: FontWeight.w500),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        showCheckmark: true,
        checkmarkColor: c.secondary,
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: c.card,
        indicatorColor: c.primarySoft,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        height: 68,
        iconTheme: WidgetStateProperty.resolveWith((s) => IconThemeData(
              size: 24,
              color: s.contains(WidgetState.selected) ? c.primary : c.mutedForeground,
            )),
        labelTextStyle: WidgetStateProperty.resolveWith((s) => _t(
              12,
              s.contains(WidgetState.selected) ? FontWeight.w700 : FontWeight.w500,
              s.contains(WidgetState.selected) ? c.primary : c.mutedForeground,
            )),
      ),
      listTileTheme: ListTileThemeData(
        iconColor: c.secondary,
        titleTextStyle: text.titleMedium,
        subtitleTextStyle: text.bodySmall,
        contentPadding: const EdgeInsets.symmetric(horizontal: AppSpace.lg, vertical: 2),
      ),
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: c.card,
        surfaceTintColor: Colors.transparent,
        showDragHandle: true,
        dragHandleColor: c.input,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: c.card,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        titleTextStyle: text.titleLarge,
        contentTextStyle: text.bodyMedium,
      ),
      progressIndicatorTheme: ProgressIndicatorThemeData(
        color: c.secondary,
        linearTrackColor: c.muted,
        circularTrackColor: c.muted,
      ),
      dividerTheme: DividerThemeData(color: c.border, space: 1, thickness: 1),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: c.foreground,
        contentTextStyle: text.bodyMedium?.copyWith(color: c.background),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.md)),
      ),
      tooltipTheme: TooltipThemeData(
        decoration: BoxDecoration(color: c.foreground, borderRadius: BorderRadius.circular(AppRadius.sm)),
        textStyle: text.bodySmall?.copyWith(color: c.background),
      ),
    );
  }
}
