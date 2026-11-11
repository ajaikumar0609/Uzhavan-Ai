import 'package:intl/intl.dart';

import '../../core/networking/envelope.dart';

/// Display helpers. A null input returns null so the caller shows the
/// localized "not available": nothing is ever defaulted to a number.
abstract final class Fmt {
  /// Up to [digits] decimals, trailing zeros removed.
  static String? num(double? v, {int digits = 1}) {
    if (v == null || v.isNaN || v.isInfinite) return null;
    final pattern = digits <= 0 ? '#,##0' : '#,##0.${'#' * digits}';
    return NumberFormat(pattern, 'en').format(v);
  }

  static String? integer(int? v) => v == null ? null : NumberFormat('#,##0', 'en').format(v);

  /// `YYYY-MM-DD` (locale-independent, as the contract writes dates).
  static String? date(DateTime? d) => d == null ? null : dateOnly(d);

  /// Local `HH:mm` when [t] is today, otherwise `YYYY-MM-DD HH:mm`.
  static String? time(DateTime? t, {DateTime? now}) {
    if (t == null) return null;
    final local = t.toLocal();
    final n = (now ?? DateTime.now()).toLocal();
    final hm = DateFormat('HH:mm').format(local);
    final sameDay = local.year == n.year && local.month == n.month && local.day == n.day;
    return sameDay ? hm : '${dateOnly(local)} $hm';
  }

  /// Short weekday in the app locale (e.g. "Thu" / "வியா"), falling back to
  /// the ISO date if locale data is not loaded.
  static String weekday(DateTime d, String locale) {
    try {
      return DateFormat.E(locale).format(d);
    } catch (_) {
      return dateOnly(d);
    }
  }
}
