import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../localization/generated/app_localizations.dart';
import '../localization/locale_controller.dart';
import '../theme/app_theme.dart';
import 'app_config.dart';

/// Shown instead of the app when the build configuration is unsafe
/// (e.g. a release build pointed at plain http).
class ConfigErrorApp extends ConsumerWidget {
  const ConfigErrorApp({super.key, required this.error});
  final ConfigError error;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      locale: ref.watch(localeProvider),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      home: Builder(builder: (context) {
        final l = AppLocalizations.of(context);
        return Scaffold(
          body: SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.gpp_bad_outlined, size: 48, color: Theme.of(context).colorScheme.error),
                  const SizedBox(height: 16),
                  Text(l.configErrorTitle, style: Theme.of(context).textTheme.headlineSmall),
                  const SizedBox(height: 12),
                  Text(error.kind == ConfigErrorKind.insecureInRelease
                      ? l.configErrorInsecure
                      : l.configErrorInvalid),
                  const SizedBox(height: 12),
                  SelectableText(l.configErrorDetail(error.url)),
                ],
              ),
            ),
          ),
        );
      }),
    );
  }
}
