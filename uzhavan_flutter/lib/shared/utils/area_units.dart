import 'package:intl/intl.dart';

/// Farmers enter and read land size in acres; the API stores hectares.
abstract final class AreaUnits {
  /// 1 acre = 0.404686 ha (contract M-06 / FP task).
  static const double hectaresPerAcre = 0.404686;

  static double acresToHectares(double acres) =>
      _round(acres * hectaresPerAcre, 6);

  static double hectaresToAcres(double hectares) => hectares / hectaresPerAcre;

  /// Acres to one decimal, e.g. `2.5`. Never prints float noise.
  static String formatAcres(double hectares, {String? locale}) =>
      NumberFormat('0.0', locale).format(hectaresToAcres(hectares));

  /// Acres for an edit field: up to 2 decimals, no trailing zeros.
  static String acresForInput(double hectares) {
    final a = _round(hectaresToAcres(hectares), 2);
    return a == a.roundToDouble() ? a.toStringAsFixed(0) : a.toString();
  }

  static double _round(double v, int places) {
    final f = List.filled(places, 10).fold<int>(1, (a, b) => a * b);
    return (v * f).round() / f;
  }
}
