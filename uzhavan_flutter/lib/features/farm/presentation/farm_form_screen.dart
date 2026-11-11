import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/networking/api_failure.dart';
import '../../../shared/utils/area_units.dart';
import '../../../shared/utils/failure_text.dart';
import '../../../shared/utils/validators.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/error_banner.dart';
import '../../../shared/widgets/data_state_view.dart';
import '../../../shared/widgets/option_picker_field.dart';
import '../../meta/presentation/meta_providers.dart';
import '../../profile/presentation/profile_controller.dart';
import '../domain/farm.dart';
import 'farms_controller.dart';

/// Add (farmId == null) or edit a farm.
class FarmFormScreen extends ConsumerWidget {
  const FarmFormScreen({super.key, this.farmId});
  final String? farmId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final id = farmId;
    if (id == null) {
      return AppScaffold(
        title: l.farmAdd,
        body: _FarmForm(
          initial: null,
          defaultDistrictId: ref.watch(profileProvider).value?.districtId,
        ),
      );
    }
    final farms = ref.watch(farmsProvider);
    return AppScaffold(
      title: l.farmEdit,
      body: DataStateView(
        value: farms.whenData((list) => list.where((f) => f.farmId == id).firstOrNull),
        unavailableText: l.farmsUnavailable,
        emptyText: l.errNotFound,
        isEmpty: (f) => f == null,
        onRetry: () => ref.invalidate(farmsProvider),
        builder: (context, farm) => _FarmForm(initial: farm, defaultDistrictId: null),
      ),
    );
  }
}

class _FarmForm extends ConsumerStatefulWidget {
  const _FarmForm({required this.initial, required this.defaultDistrictId});
  final Farm? initial;
  final String? defaultDistrictId;

  @override
  ConsumerState<_FarmForm> createState() => _FarmFormState();
}

class _FarmFormState extends ConsumerState<_FarmForm> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _name, _village, _lat, _lon, _acres;
  String? _districtId, _cropId, _stageId, _seasonId, _irrigationId;
  bool _saving = false;
  ApiFailure? _failure;

  @override
  void initState() {
    super.initState();
    final f = widget.initial;
    _name = TextEditingController(text: f?.name ?? '');
    _village = TextEditingController(text: f?.village ?? '');
    _lat = TextEditingController(text: f?.latitude?.toString() ?? '');
    _lon = TextEditingController(text: f?.longitude?.toString() ?? '');
    _acres = TextEditingController(
      text: f?.areaHa == null ? '' : AreaUnits.acresForInput(f!.areaHa!),
    );
    _districtId = f?.districtId ?? widget.defaultDistrictId;
    _cropId = f?.cropId;
    _stageId = f?.cropStageId;
    _seasonId = f?.seasonId;
    _irrigationId = f?.irrigationTypeId;
  }

  @override
  void dispose() {
    for (final c in [_name, _village, _lat, _lon, _acres]) {
      c.dispose();
    }
    super.dispose();
  }

  String? _validateLat(String? v) {
    final l = context.l10n;
    final lat = Validators.parseDecimal(v ?? '');
    final lonText = _lon.text.trim();
    if ((v ?? '').trim().isEmpty) return lonText.isEmpty ? null : l.farmLatLonPair;
    if (lat == null || !Validators.isLatInTamilNadu(lat)) return l.farmLatInvalid;
    return null;
  }

  String? _validateLon(String? v) {
    final l = context.l10n;
    final lon = Validators.parseDecimal(v ?? '');
    final latText = _lat.text.trim();
    if ((v ?? '').trim().isEmpty) return latText.isEmpty ? null : l.farmLatLonPair;
    if (lon == null || !Validators.isLonInTamilNadu(lon)) return l.farmLonInvalid;
    return null;
  }

  String? _validateAcres(String? v) {
    if ((v ?? '').trim().isEmpty) return null;
    final a = Validators.parseDecimal(v!);
    return a == null || !Validators.isValidAcres(a) ? context.l10n.farmAreaInvalid : null;
  }

  Future<void> _save() async {
    setState(() => _failure = null);
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final village = _village.text.trim();
    final input = FarmInput(
      name: _name.text.trim(),
      districtId: _districtId!,
      village: village.isEmpty ? null : village,
      latitude: Validators.parseDecimal(_lat.text),
      longitude: Validators.parseDecimal(_lon.text),
      areaAcres: Validators.parseDecimal(_acres.text),
      cropId: _cropId,
      cropStageId: _stageId,
      seasonId: _seasonId,
      irrigationTypeId: _irrigationId,
    );
    setState(() => _saving = true);
    try {
      final ctrl = ref.read(farmsProvider.notifier);
      final init = widget.initial;
      if (init == null) {
        await ctrl.create(input);
      } else {
        await ctrl.updateFarm(init.farmId, input);
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(context.l10n.saved)));
        context.pop();
      }
    } on ApiFailure catch (f) {
      if (mounted) setState(() => _failure = f);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final enums = ref.watch(enumsProvider);
    void retryEnums() => ref.invalidate(enumsProvider);
    final failure = _failure;
    const gap = SizedBox(height: 16);

    return Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          TextFormField(
            key: const Key('farm-name'),
            controller: _name,
            maxLength: 100,
            decoration: InputDecoration(labelText: l.farmName),
            validator: (v) => (v ?? '').trim().isEmpty ? l.farmNameRequired : null,
          ),
          const SizedBox(height: 4),
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
          gap,
          TextFormField(
            controller: _village,
            maxLength: 100,
            decoration: InputDecoration(labelText: '${l.profileVillage} ${l.optionalSuffix}'),
          ),
          const SizedBox(height: 4),
          TextFormField(
            key: const Key('farm-acres'),
            controller: _acres,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: InputDecoration(labelText: '${l.farmArea} ${l.optionalSuffix}'),
            validator: _validateAcres,
          ),
          gap,
          Text('${l.farmLocation} ${l.optionalSuffix}', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 4),
          Text(l.farmLocationHelp, style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 8),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: TextFormField(
                  key: const Key('farm-lat'),
                  controller: _lat,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                  decoration: InputDecoration(labelText: l.farmLatitude, errorMaxLines: 3),
                  validator: _validateLat,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextFormField(
                  key: const Key('farm-lon'),
                  controller: _lon,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                  decoration: InputDecoration(labelText: l.farmLongitude, errorMaxLines: 3),
                  validator: _validateLon,
                ),
              ),
            ],
          ),
          gap,
          OptionPickerField(
            label: '${l.farmCrop} ${l.optionalSuffix}',
            options: ref.watch(cropOptionsProvider),
            selectedId: _cropId,
            allowNone: true,
            searchable: true,
            unavailableText: l.optionsUnavailable,
            onRetry: () => ref.invalidate(cropsProvider),
            onChanged: (id) => setState(() => _cropId = id),
          ),
          gap,
          OptionPickerField(
            label: '${l.farmStage} ${l.optionalSuffix}',
            options: enums.whenData((e) => e.cropStages.map((i) => i.toOption()).toList()),
            selectedId: _stageId,
            allowNone: true,
            unavailableText: l.optionsUnavailable,
            onRetry: retryEnums,
            onChanged: (id) => setState(() => _stageId = id),
          ),
          gap,
          OptionPickerField(
            label: '${l.farmSeason} ${l.optionalSuffix}',
            options: enums.whenData((e) => e.seasons.map((i) => i.toOption()).toList()),
            selectedId: _seasonId,
            allowNone: true,
            unavailableText: l.optionsUnavailable,
            onRetry: retryEnums,
            onChanged: (id) => setState(() => _seasonId = id),
          ),
          gap,
          OptionPickerField(
            label: '${l.farmIrrigation} ${l.optionalSuffix}',
            options: enums.whenData((e) => e.irrigationTypes.map((i) => i.toOption()).toList()),
            selectedId: _irrigationId,
            allowNone: true,
            unavailableText: l.optionsUnavailable,
            onRetry: retryEnums,
            onChanged: (id) => setState(() => _irrigationId = id),
          ),
          if (failure != null) ...[
            gap,
            ErrorBanner(text: failureText(l, Localizations.localeOf(context), failure)),
          ],
          const SizedBox(height: 24),
          FilledButton(
            key: const Key('farm-save'),
            onPressed: _saving ? null : _save,
            child: _saving
                ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2))
                : Text(l.save),
          ),
        ],
      ),
    );
  }
}

