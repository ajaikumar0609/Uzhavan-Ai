import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/localization/l10n.dart';
import 'session_controller.dart';

/// Asks for confirmation, then logs out (the router moves to /login).
Future<void> confirmAndLogout(BuildContext context, WidgetRef ref) async {
  final l = context.l10n;
  final ok = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      content: Text(l.logoutConfirm),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(l.cancel)),
        FilledButton(onPressed: () => Navigator.pop(ctx, true), child: Text(l.logout)),
      ],
    ),
  );
  if (ok == true) await ref.read(sessionProvider.notifier).logout();
}
