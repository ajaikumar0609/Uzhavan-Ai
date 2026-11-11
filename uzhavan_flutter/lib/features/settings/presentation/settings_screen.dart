import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:package_info_plus/package_info_plus.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/localization/locale_controller.dart';
import '../../../core/networking/providers.dart';
import '../../../core/theme/theme_mode_controller.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../auth/presentation/logout_dialog.dart';

final packageInfoProvider = FutureProvider<PackageInfo>((ref) => PackageInfo.fromPlatform());

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final locale = ref.watch(localeProvider);
    final mode = ref.watch(themeModeProvider);
    final info = ref.watch(packageInfoProvider).value;
    final text = Theme.of(context).textTheme;

    Widget section(String title) => Padding(
          padding: const EdgeInsets.fromLTRB(16, 20, 16, 8),
          child: Text(title, style: text.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
        );

    return AppScaffold(
      title: l.featureSettings,
      body: ListView(
        padding: const EdgeInsets.only(bottom: 24),
        children: [
          section(l.settingsLanguage),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: SegmentedButton<String>(
              key: const Key('settings-language'),
              segments: [
                ButtonSegment(value: 'ta', label: Text(l.languageTamil)),
                ButtonSegment(value: 'en', label: Text(l.languageEnglish)),
              ],
              selected: {locale.languageCode},
              onSelectionChanged: (s) => ref
                  .read(localeProvider.notifier)
                  .setLocale(AppLocales.fromCode(s.first)),
            ),
          ),
          section(l.settingsTheme),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: SegmentedButton<ThemeMode>(
              segments: [
                ButtonSegment(value: ThemeMode.light, label: Text(l.themeLight), icon: const Icon(Icons.light_mode_outlined)),
                ButtonSegment(value: ThemeMode.dark, label: Text(l.themeDark), icon: const Icon(Icons.dark_mode_outlined)),
                ButtonSegment(value: ThemeMode.system, label: Text(l.themeSystem), icon: const Icon(Icons.settings_suggest_outlined)),
              ],
              selected: {mode},
              onSelectionChanged: (s) => ref.read(themeModeProvider.notifier).setMode(s.first),
            ),
          ),
          section(l.settingsAbout),
          ListTile(
            leading: const Icon(Icons.eco_outlined),
            title: Text(l.appTitle),
            subtitle: Text(l.aboutDescription),
          ),
          if (info != null)
            ListTile(
              leading: const Icon(Icons.info_outline),
              title: Text(l.appVersion('${info.version}+${info.buildNumber}')),
            ),
          if (kDebugMode)
            ListTile(
              leading: const Icon(Icons.bug_report_outlined),
              title: Text(l.apiBaseUrlDebug(ref.watch(appConfigProvider).apiBaseUrl)),
            ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.logout),
            title: Text(l.logout),
            onTap: () => confirmAndLogout(context, ref),
          ),
        ],
      ),
    );
  }
}
