import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/networking/api_failure.dart';
import '../../../shared/utils/failure_text.dart';
import '../../../shared/utils/formatters.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/error_banner.dart';
import '../../farm/domain/farm.dart';
import '../../farm/presentation/farms_controller.dart';
import '../../farm/presentation/selected_farm.dart';
import '../data/soil_repository.dart';
import '../domain/soil_models.dart';
import 'soil_screen.dart' show soilParamLabel;

/// Validates one optional lab value against [p]'s range. Null → valid.
String? validateSoilValue(AppLocalizations l, SoilParam p, String? raw) {
  final t = raw?.trim() ?? '';
  if (t.isEmpty) return null;
  final v = double.tryParse(t);
  if (v == null) return l.soilValueInvalid;
  if (v < p.min || v > p.max) return l.soilValueRange(Fmt.num(p.min)!, Fmt.num(p.max)!);
  return null;
}

class SoilTestFormScreen extends ConsumerStatefulWidget {
  const SoilTestFormScreen({super.key});

  @override
  ConsumerState<SoilTestFormScreen> createState() => _SoilTestFormScreenState();
}

class _SoilTestFormScreenState extends ConsumerState<SoilTestFormScreen> {
  final _form = GlobalKey<FormState>();
  final _lab = TextEditingController();
  final _fields = {for (final p in soilTestParams) p.key: TextEditingController()};
  String? _farmId;
  DateTime? _date;
  bool _saving = false;
  String? _error;

  @override
  void dispose() {
    _lab.dispose();
    for (final c in _fields.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final d = await showDatePicker(
      context: context,
      initialDate: _date ?? now,
      firstDate: DateTime(now.year - 10),
      lastDate: now,
    );
    if (d != null) setState(() => _date = d);
  }

  Future<void> _save(List<Farm> farms) async {
    final l = context.l10n;
    final locale = Localizations.localeOf(context);
    setState(() => _error = null);
    if (!_form.currentState!.validate()) return;
    final farmId = _farmId ?? ref.read(selectedFarmProvider).value?.farmId;
    if (farmId == null || _date == null) {
      setState(() => _error = farmId == null ? l.soilFarmRequired : l.soilDateRequired);
      return;
    }
    final values = {
      for (final p in soilTestParams)
        p.key: _fields[p.key]!.text.trim().isEmpty ? null : double.parse(_fields[p.key]!.text.trim()),
    };
    if (values.values.every((v) => v == null)) {
      setState(() => _error = l.soilAtLeastOne);
      return;
    }
    setState(() => _saving = true);
    try {
      await ref.read(soilRepositoryProvider).addTest(
            SoilTestInput(farmId: farmId, sampleDate: _date!, labName: _lab.text, values: values),
          );
      ref.invalidate(soilProvider);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l.saved)));
      context.pop();
    } on ApiFailure catch (f) {
      if (mounted) setState(() => _error = failureText(l, locale, f));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final farms = ref.watch(farmsProvider).value ?? const <Farm>[];
    final selected = _farmId ?? ref.watch(selectedFarmProvider).value?.farmId;
    return AppScaffold(
      title: l.soilAddTest,
      body: Form(
        key: _form,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
          children: [
            DropdownButtonFormField<String>(
              initialValue: selected,
              isExpanded: true,
              decoration: InputDecoration(labelText: l.farmPickerLabel),
              items: [for (final f in farms) DropdownMenuItem(value: f.farmId, child: Text(f.name))],
              validator: (v) => v == null ? l.soilFarmRequired : null,
              onChanged: (v) => setState(() => _farmId = v),
            ),
            const SizedBox(height: 12),
            InkWell(
              onTap: _pickDate,
              borderRadius: BorderRadius.circular(16),
              child: InputDecorator(
                decoration: InputDecoration(
                  labelText: l.soilSampleDate,
                  suffixIcon: const Icon(Icons.calendar_month_outlined),
                ),
                child: Text(Fmt.date(_date) ?? l.soilPickDate),
              ),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _lab,
              maxLength: 120,
              decoration: InputDecoration(labelText: '${l.soilLabName} ${l.optionalSuffix}'),
            ),
            const SizedBox(height: 4),
            Text(l.soilValuesHint, style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 8),
            for (final p in soilTestParams)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: TextFormField(
                  key: Key('soil-field-${p.key}'),
                  controller: _fields[p.key],
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[0-9.]'))],
                  decoration: InputDecoration(
                    labelText: soilParamLabel(l, p.key),
                    suffixText: p.unit.isEmpty ? null : p.unit,
                    helperText: l.soilValueRange(Fmt.num(p.min)!, Fmt.num(p.max)!),
                  ),
                  validator: (v) => validateSoilValue(l, p, v),
                ),
              ),
            if (_error != null) ...[ErrorBanner(text: _error!), const SizedBox(height: 12)],
            FilledButton(
              onPressed: _saving ? null : () => _save(farms),
              child: _saving
                  ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2))
                  : Text(l.save),
            ),
          ],
        ),
      ),
    );
  }
}
