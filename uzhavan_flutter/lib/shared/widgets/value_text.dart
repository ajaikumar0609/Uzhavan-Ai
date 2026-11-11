import 'package:flutter/material.dart';

import '../../core/localization/l10n.dart';
import '../../core/theme/app_colors.dart';

/// A label/value row. A null or blank value shows the localized "Not set",
/// never a placeholder name or number.
class LabeledValue extends StatelessWidget {
  const LabeledValue({super.key, required this.label, required this.value, this.icon});

  final String label;
  final String? value;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final v = value;
    final missing = v == null || v.trim().isEmpty;
    return ListTile(
      leading: icon == null ? null : Icon(icon),
      title: Text(label, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: context.colors.mutedForeground)),
      subtitle: Text(
        missing ? context.l10n.notSet : v,
        style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: missing ? context.colors.mutedForeground : null,
              fontStyle: missing ? FontStyle.italic : null,
            ),
      ),
    );
  }
}
