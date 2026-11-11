import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/theme/app_colors.dart';

/// Bottom navigation: Home · Assistant · Scan · Market · More.
class MainShell extends StatelessWidget {
  const MainShell({super.key, required this.navigationShell});
  final StatefulNavigationShell navigationShell;

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final c = context.colors;
    final onHome = navigationShell.currentIndex == 0;
    // System Back at the top of any other tab returns to Home instead of leaving the app
    // (it used to drop straight to the launcher). Sub-screens pop normally first.
    return PopScope(
      canPop: onHome,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) navigationShell.goBranch(0);
      },
      child: Scaffold(
        body: navigationShell,
        bottomNavigationBar: DecoratedBox(
          decoration: BoxDecoration(border: Border(top: BorderSide(color: c.border))),
          child: NavigationBar(
            selectedIndex: navigationShell.currentIndex,
            onDestinationSelected: (i) =>
                navigationShell.goBranch(i, initialLocation: i == navigationShell.currentIndex),
            destinations: [
              navDestination(Icons.home_outlined, Icons.home_rounded, l.navHome),
              navDestination(Icons.forum_outlined, Icons.forum_rounded, l.navAssistant),
              navDestination(Icons.center_focus_weak_rounded, Icons.center_focus_strong_rounded, l.navScan),
              navDestination(Icons.storefront_outlined, Icons.storefront_rounded, l.navMarket),
              navDestination(Icons.grid_view_outlined, Icons.grid_view_rounded, l.navMore),
            ],
          ),
        ),
      ),
    );
  }

  /// Labels never wrap (QA F1: a wrapped Tamil label split a grapheme).
  /// NavigationDestination builds a plain `Text`, which inherits these.
  static Widget navDestination(IconData icon, IconData? selected, String label) =>
      DefaultTextStyle.merge(
        maxLines: 1,
        softWrap: false,
        overflow: TextOverflow.ellipsis,
        child: NavigationDestination(
          icon: Icon(icon),
          selectedIcon: selected == null ? null : Icon(selected),
          label: label,
          tooltip: label,
        ),
      );
}
