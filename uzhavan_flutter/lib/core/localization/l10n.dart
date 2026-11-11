import 'package:flutter/widgets.dart';

import 'generated/app_localizations.dart';

export 'bilingual_text.dart' show BilingualContext;
export 'generated/app_localizations.dart';

extension L10nContext on BuildContext {
  AppLocalizations get l10n => AppLocalizations.of(this);
}
