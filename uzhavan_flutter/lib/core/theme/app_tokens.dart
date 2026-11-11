import 'package:flutter/material.dart';

import 'app_colors.dart';

/// Spacing scale (dp). Use these instead of ad-hoc numbers.
abstract final class AppSpace {
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
  static const double xl = 20;
  static const double xxl = 24;
  static const double xxxl = 32;

  /// Horizontal page gutter and the standard list padding for a screen body.
  static const double page = 16;
  static const EdgeInsets screen = EdgeInsets.fromLTRB(page, lg, page, xxxl);
}

/// Corner-radius scale.
abstract final class AppRadius {
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
  static const double xl = 20;
  static const double pill = 999;

  static BorderRadius get card => BorderRadius.circular(xl);
  static BorderRadius get control => BorderRadius.circular(lg);
  static BorderRadius get chip => BorderRadius.circular(pill);
}

/// Elevation: one soft, low shadow for raised surfaces; nothing heavier anywhere.
abstract final class AppShadows {
  static List<BoxShadow> card(AppColors c) => [
        BoxShadow(
          color: c.foreground.withValues(alpha: 0.05),
          blurRadius: 18,
          offset: const Offset(0, 6),
        ),
      ];
}

/// Motion: short and consistent. No decorative animation.
abstract final class AppMotion {
  static const Duration fast = Duration(milliseconds: 140);
  static const Duration base = Duration(milliseconds: 220);
  static const Curve curve = Curves.easeOutCubic;
}
