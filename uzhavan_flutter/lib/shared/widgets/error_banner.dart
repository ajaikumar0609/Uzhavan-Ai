import 'package:flutter/material.dart';

import 'ui_kit.dart';

/// Inline error message for forms (auth, profile, farm).
class ErrorBanner extends StatelessWidget {
  const ErrorBanner({super.key, required this.text});
  final String text;

  @override
  Widget build(BuildContext context) => NoticeBanner(text: text, tone: Tone.critical);
}
