import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/localization/l10n.dart';
import '../../core/localization/locale_controller.dart';

/// Top-right switch: "தமிழ் → English" in Tamil, "English → தமிழ்" in English.
/// Switches instantly (no restart) and is persisted.
class LanguageSwitchButton extends ConsumerWidget {
  const LanguageSwitchButton({super.key});

  static const buttonKey = Key('language-switch');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    return Padding(
      padding: const EdgeInsetsDirectional.only(end: 8),
      child: Tooltip(
        message: l.languageSwitchTooltip,
        child: TextButton.icon(
          key: buttonKey,
          onPressed: () => ref.read(localeProvider.notifier).toggle(),
          icon: const Icon(Icons.translate, size: 18),
          label: Text(l.languageSwitchLabel),
        ),
      ),
    );
  }
}
