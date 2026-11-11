import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/localization/l10n.dart';

/// Opens an official/source link in the external browser. Only http(s).
Future<void> openExternalLink(BuildContext context, String? url) async {
  final messenger = ScaffoldMessenger.of(context);
  final failText = context.l10n.linkOpenFailed;
  final uri = url == null ? null : Uri.tryParse(url);
  var ok = false;
  if (uri != null && (uri.scheme == 'https' || uri.scheme == 'http')) {
    try {
      ok = await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (_) {
      ok = false;
    }
  }
  if (!ok) messenger.showSnackBar(SnackBar(content: Text(failText)));
}

/// A tappable source link line.
class LinkText extends StatelessWidget {
  const LinkText({super.key, required this.label, required this.url});
  final String label;
  final String? url;

  @override
  Widget build(BuildContext context) {
    final color = Theme.of(context).colorScheme.primary;
    if (url == null) return Text(label);
    return InkWell(
      onTap: () => openExternalLink(context, url),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.open_in_new, size: 16, color: color),
            const SizedBox(width: 6),
            Flexible(
              child: Text(label,
                  style: TextStyle(color: color, decoration: TextDecoration.underline, decorationColor: color)),
            ),
          ],
        ),
      ),
    );
  }
}
