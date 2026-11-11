import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/networking/api_failure.dart';
import '../../../shared/utils/failure_text.dart';
import '../../../shared/utils/validators.dart';
import '../../../shared/widgets/error_banner.dart';
import '../../../shared/widgets/option_picker_field.dart';
import '../../meta/presentation/meta_providers.dart';
import '../domain/farmer_profile.dart';
import 'profile_controller.dart';

/// Name, district, village and language. Used by onboarding and edit.
class ProfileForm extends ConsumerStatefulWidget {
  const ProfileForm({
    super.key,
    required this.initial,
    required this.submitLabel,
    required this.onSaved,
    this.header,
  });

  final FarmerProfile initial;
  final String submitLabel;
  final void Function(FarmerProfile saved) onSaved;
  final Widget? header;

  @override
  ConsumerState<ProfileForm> createState() => _ProfileFormState();
}

class _ProfileFormState extends ConsumerState<ProfileForm> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _name;
  late final TextEditingController _village;
  String? _districtId;
  late String _language;
  bool _saving = false;
  ApiFailure? _failure;

  @override
  void initState() {
    super.initState();
    _name = TextEditingController(text: widget.initial.name ?? '');
    _village = TextEditingController(text: widget.initial.village ?? '');
    _districtId = widget.initial.districtId;
    _language = widget.initial.preferredLanguage;
  }

  @override
  void dispose() {
    _name.dispose();
    _village.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() => _failure = null);
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final init = widget.initial;
    final village = _village.text.trim();
    final update = ProfileUpdate(
      name: _name.text.trim(),
      districtId: _districtId,
      village: village.isEmpty ? null : village,
      preferredLanguage: _language,
      clear: {if (village.isEmpty && init.village != null) 'village'},
    );
    setState(() => _saving = true);
    try {
      final saved = await ref.read(profileProvider.notifier).save(update);
      if (mounted) widget.onSaved(saved);
    } on ApiFailure catch (f) {
      if (mounted) setState(() => _failure = f);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final failure = _failure;
    return Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          ?widget.header,
          TextFormField(
            key: const Key('profile-name'),
            controller: _name,
            textCapitalization: TextCapitalization.words,
            maxLength: 100,
            decoration: InputDecoration(labelText: l.profileName),
            validator: (v) => Validators.isValidName(v ?? '') ? null : l.nameInvalid,
          ),
          const SizedBox(height: 12),
          OptionPickerField(
            label: l.profileDistrict,
            options: ref.watch(districtOptionsProvider),
            selectedId: _districtId,
            searchable: true,
            unavailableText: l.districtsUnavailable,
            onRetry: () => ref.invalidate(districtsProvider),
            onChanged: (id) => setState(() => _districtId = id),
            validator: (v) => v == null ? l.districtRequired : null,
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _village,
            maxLength: 100,
            decoration: InputDecoration(labelText: '${l.profileVillage} ${l.optionalSuffix}'),
          ),
          const SizedBox(height: 12),
          Text(l.profileLanguage, style: Theme.of(context).textTheme.labelLarge),
          const SizedBox(height: 8),
          SegmentedButton<String>(
            segments: [
              ButtonSegment(value: 'ta', label: Text(l.languageTamil)),
              ButtonSegment(value: 'en', label: Text(l.languageEnglish)),
            ],
            selected: {_language},
            onSelectionChanged: (s) => setState(() => _language = s.first),
          ),
          if (failure != null) ...[
            const SizedBox(height: 16),
            ErrorBanner(text: failureText(l, Localizations.localeOf(context), failure)),
          ],
          const SizedBox(height: 24),
          FilledButton(
            key: const Key('profile-save'),
            onPressed: _saving ? null : _save,
            child: _saving
                ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2))
                : Text(widget.submitLabel),
          ),
        ],
      ),
    );
  }
}
