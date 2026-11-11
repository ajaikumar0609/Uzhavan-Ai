/// Input rules shared by forms (mirrors API contract M-06).
abstract final class Validators {
  static final _phone = RegExp(r'^[6-9]\d{9}$');
  static final _otp = RegExp(r'^\d{6}$');

  /// Indian mobile: 10 digits starting 6–9.
  static bool isValidPhone(String input) => _phone.hasMatch(input.trim());

  static bool isValidOtp(String input) => _otp.hasMatch(input.trim());

  /// Profile name: 2–100 characters after trimming.
  static bool isValidName(String input) {
    final n = input.trim().runes.length;
    return n >= 2 && n <= 100;
  }

  // Tamil Nadu bounding box (contract §3).
  static const double minLat = 8.0, maxLat = 13.6;
  static const double minLon = 76.2, maxLon = 80.4;

  static bool isLatInTamilNadu(double lat) => lat >= minLat && lat <= maxLat;
  static bool isLonInTamilNadu(double lon) => lon >= minLon && lon <= maxLon;

  /// Parses a decimal typed by the user (accepts `,` as decimal separator).
  static double? parseDecimal(String input) {
    final t = input.trim().replaceAll(',', '.');
    if (t.isEmpty) return null;
    final v = double.tryParse(t);
    return (v == null || v.isNaN || v.isInfinite) ? null : v;
  }

  /// Area in acres: > 0 and at most 10,000.
  static bool isValidAcres(double acres) => acres > 0 && acres <= 10000;
}
