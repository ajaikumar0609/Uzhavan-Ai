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
import '../data/diary_repository.dart';
import '../domain/diary_models.dart';
import 'diary_screen.dart' show diaryKindLabel;

class DiaryFormScreen extends ConsumerStatefulWidget {
  const DiaryFormScreen({super.key});

  @override
  ConsumerState<DiaryFormScreen> createState() => _DiaryFormScreenState();
}

class _DiaryFormScreenState extends ConsumerState<DiaryFormScreen> {
  final _form = GlobalKey<FormState>();
  final _text = TextEditingController();
  final _amount = TextEditingController();
  String _kind = 'note';
  String? _farmId;
  DateTime _date = DateTime.now();
  bool _saving = false;
  String? _error;

  @override
  void dispose() {
    _text.dispose();
    _amount.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final l = context.l10n;
    final locale = Localizations.localeOf(context);
    setState(() => _error = null);
    if (!_form.currentState!.validate()) return;
    setState(() => _saving = true);
    try {
      await ref.read(diaryRepositoryProvider).add(DiaryInput(
            kind: _kind,
            text: _text.text,
            entryDate: _date,
            farmId: _farmId,
            amountInr: diaryMoneyKinds.contains(_kind) ? double.parse(_amount.text.trim()) : null,
          ));
      ref.invalidate(diaryProvider);
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
    final money = diaryMoneyKinds.contains(_kind);
    return AppScaffold(
      title: l.diaryAdd,
      body: Form(
        key: _form,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
          children: [
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final k in diaryAddableKinds)
                  ChoiceChip(
                    key: Key('diary-kind-$k'),
                    label: Text(diaryKindLabel(l, k)),
                    selected: _kind == k,
                    onSelected: (_) => setState(() => _kind = k),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            TextFormField(
              key: const Key('diary-text'),
              controller: _text,
              minLines: 2,
              maxLines: 6,
              maxLength: 1000,
              decoration: InputDecoration(labelText: l.diaryText),
              validator: (v) => (v == null || v.trim().isEmpty) ? l.diaryTextRequired : null,
            ),
            if (money) ...[
              const SizedBox(height: 12),
              TextFormField(
                key: const Key('diary-amount'),
                controller: _amount,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[0-9.]'))],
                decoration: InputDecoration(labelText: l.diaryAmount, prefixText: '₹ '),
                validator: (v) {
                  final a = double.tryParse(v?.trim() ?? '');
                  if (a == null || a <= 0) return l.diaryAmountInvalid;
                  if (a > 100000000) return l.diaryAmountInvalid;
                  return null;
                },
              ),
            ],
            const SizedBox(height: 12),
            InkWell(
              borderRadius: BorderRadius.circular(16),
              onTap: () async {
                final now = DateTime.now();
                final d = await showDatePicker(
                  context: context,
                  initialDate: _date,
                  firstDate: DateTime(now.year - 5),
                  lastDate: now,
                );
                if (d != null) setState(() => _date = d);
              },
              child: InputDecorator(
                decoration: InputDecoration(
                  labelText: l.diaryDate,
                  suffixIcon: const Icon(Icons.calendar_month_outlined),
                ),
                child: Text(Fmt.date(_date)!),
              ),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String?>(
              initialValue: _farmId,
              isExpanded: true,
              decoration: InputDecoration(labelText: '${l.farmPickerLabel} ${l.optionalSuffix}'),
              items: [
                DropdownMenuItem<String?>(value: null, child: Text(l.pickerNone)),
                for (final f in farms) DropdownMenuItem<String?>(value: f.farmId, child: Text(f.name)),
              ],
              onChanged: (v) => setState(() => _farmId = v),
            ),
            const SizedBox(height: 16),
            if (_error != null) ...[ErrorBanner(text: _error!), const SizedBox(height: 12)],
            FilledButton(
              key: const Key('diary-save'),
              onPressed: _saving ? null : _save,
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
