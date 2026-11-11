import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/localization/bilingual_text.dart';
import '../../core/localization/l10n.dart';

/// One choice from a server reference list (`{id, name:{en,ta}}`).
@immutable
class PickerOption {
  const PickerOption({required this.id, required this.label});
  final String id;
  final BilingualText label;
}

/// A form field that opens a searchable bottom-sheet list.
class OptionPickerField extends StatelessWidget {
  const OptionPickerField({
    super.key,
    required this.label,
    required this.options,
    required this.selectedId,
    required this.onChanged,
    required this.unavailableText,
    this.onRetry,
    this.allowNone = false,
    this.validator,
    this.searchable = false,
  });

  final String label;
  final AsyncValue<List<PickerOption>> options;
  final String? selectedId;
  final ValueChanged<String?> onChanged;
  final String unavailableText;
  final VoidCallback? onRetry;
  final bool allowNone;
  final String? Function(String?)? validator;
  final bool searchable;

  @override
  Widget build(BuildContext context) {
    final list = options.hasValue && !options.hasError ? options.requireValue : null;
    return FormField<String>(
      key: ValueKey('picker-$label-$selectedId'),
      initialValue: selectedId,
      validator: validator,
      builder: (field) {
        String? display;
        final id = field.value;
        if (id != null) {
          final match = list?.where((o) => o.id == id).firstOrNull;
          display = match == null ? id : context.bi(match.label);
        }
        final failed = options.hasError && !options.isLoading;
        return InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: list == null
              ? (failed ? onRetry : null)
              : () async {
                  final picked = await showModalBottomSheet<_Pick>(
                    context: context,
                    isScrollControlled: true,
                    useSafeArea: true,
                    showDragHandle: true,
                    builder: (_) => _PickerSheet(
                      title: label,
                      options: list,
                      allowNone: allowNone,
                      searchable: searchable,
                    ),
                  );
                  if (picked != null) {
                    field.didChange(picked.id);
                    onChanged(picked.id);
                  }
                },
          child: InputDecorator(
            isEmpty: display == null,
            decoration: InputDecoration(
              labelText: label,
              errorText: field.errorText,
              helperText: failed ? unavailableText : null,
              suffixIcon: options.isLoading && list == null
                  ? const Padding(
                      padding: EdgeInsets.all(14),
                      child: SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)),
                    )
                  : Icon(failed ? Icons.refresh : Icons.arrow_drop_down),
            ),
            child: display == null ? null : Text(display),
          ),
        );
      },
    );
  }
}

class _Pick {
  const _Pick(this.id);
  final String? id;
}

class _PickerSheet extends StatefulWidget {
  const _PickerSheet({
    required this.title,
    required this.options,
    required this.allowNone,
    required this.searchable,
  });

  final String title;
  final List<PickerOption> options;
  final bool allowNone;
  final bool searchable;

  @override
  State<_PickerSheet> createState() => _PickerSheetState();
}

class _PickerSheetState extends State<_PickerSheet> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final q = _query.trim().toLowerCase();
    final filtered = q.isEmpty
        ? widget.options
        : widget.options
            .where((o) =>
                o.label.en.toLowerCase().contains(q) ||
                (o.label.ta?.contains(_query.trim()) ?? false))
            .toList();
    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.7,
      maxChildSize: 0.95,
      builder: (context, controller) => Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: Text(widget.title, style: Theme.of(context).textTheme.titleMedium),
          ),
          if (widget.searchable)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
              child: TextField(
                decoration: InputDecoration(prefixIcon: const Icon(Icons.search), hintText: l.searchHint),
                onChanged: (v) => setState(() => _query = v),
              ),
            ),
          Expanded(
            child: ListView(
              controller: controller,
              children: [
                if (widget.allowNone && q.isEmpty)
                  ListTile(
                    title: Text(l.pickerNone),
                    onTap: () => Navigator.of(context).pop(const _Pick(null)),
                  ),
                if (filtered.isEmpty) ListTile(title: Text(l.noMatches)),
                for (final o in filtered)
                  ListTile(
                    title: Text(context.bi(o.label)),
                    onTap: () => Navigator.of(context).pop(_Pick(o.id)),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
