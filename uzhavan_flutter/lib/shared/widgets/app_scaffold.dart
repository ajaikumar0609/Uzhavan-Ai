import 'package:flutter/material.dart';

import 'language_switch_button.dart';

/// Standard screen frame: real system status bar only (no fake one), an app
/// bar with the language switch at the top right, and a SafeArea body.
class AppScaffold extends StatelessWidget {
  const AppScaffold({
    super.key,
    required this.title,
    required this.body,
    this.actions = const [],
    this.floatingActionButton,
    this.automaticallyImplyLeading = true,
  });

  final String title;
  final Widget body;
  final List<Widget> actions;
  final Widget? floatingActionButton;
  final bool automaticallyImplyLeading;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        // Up to 2 lines so long Tamil titles are not cut next to the language
        // switch (QA F3); the switch label itself is never shortened.
        title: Text(title, maxLines: 2, softWrap: true, overflow: TextOverflow.ellipsis),
        titleSpacing: automaticallyImplyLeading ? 0 : 20,
        automaticallyImplyLeading: automaticallyImplyLeading,
        actions: [...actions, const LanguageSwitchButton()],
      ),
      floatingActionButton: floatingActionButton,
      body: SafeArea(top: false, child: body),
    );
  }
}
