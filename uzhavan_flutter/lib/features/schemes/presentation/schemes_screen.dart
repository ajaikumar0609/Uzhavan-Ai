import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/networking/envelope.dart';
import '../../../core/routing/routes.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/data_state_view.dart';
import '../../../shared/widgets/option_picker_field.dart';
import '../../../shared/widgets/source_line.dart';
import '../../meta/presentation/meta_providers.dart';
import '../data/scheme_repository.dart';
import '../domain/scheme_models.dart';

/// Contract §6 list: search + level filter + crop filter.
class SchemesScreen extends ConsumerStatefulWidget {
  const SchemesScreen({super.key});

  @override
  ConsumerState<SchemesScreen> createState() => _SchemesScreenState();
}

class _SchemesScreenState extends ConsumerState<SchemesScreen> {
  final _search = TextEditingController();
  Timer? _debounce;
  SchemeQuery _query = const SchemeQuery();

  @override
  void dispose() {
    _debounce?.cancel();
    _search.dispose();
    super.dispose();
  }

  void _onSearch(String v) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 400), () {
      if (!mounted) return;
      setState(() => _query = SchemeQuery(q: v, level: _query.level, cropId: _query.cropId));
    });
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final list = ref.watch(schemeListProvider(_query));
    Widget levelChip(String? level, String label) => Padding(
          padding: const EdgeInsetsDirectional.only(end: 8),
          child: ChoiceChip(
            label: Text(label),
            selected: _query.level == level,
            onSelected: (_) => setState(() => _query = SchemeQuery(q: _query.q, level: level, cropId: _query.cropId)),
          ),
        );
    return AppScaffold(
      title: l.featureSchemes,
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
        children: [
          TextField(
            controller: _search,
            textInputAction: TextInputAction.search,
            decoration: InputDecoration(prefixIcon: const Icon(Icons.search), hintText: l.schemeSearchHint),
            onChanged: _onSearch,
          ),
          const SizedBox(height: 8),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(children: [
              levelChip(null, l.levelAll),
              levelChip('central', l.levelCentral),
              levelChip('state', l.levelState),
            ]),
          ),
          const SizedBox(height: 8),
          OptionPickerField(
            label: l.schemeCropFilter,
            options: ref.watch(cropOptionsProvider),
            selectedId: _query.cropId,
            allowNone: true,
            searchable: true,
            unavailableText: l.optionsUnavailable,
            onRetry: () => ref.invalidate(cropsProvider),
            onChanged: (id) => setState(() => _query = SchemeQuery(q: _query.q, level: _query.level, cropId: id)),
          ),
          const SizedBox(height: 8),
          DataStateView<Enveloped<List<SchemeSummary>>>(
            value: list,
            unavailableText: l.schemesUnavailable,
            isEmpty: (e) => e.data.isEmpty,
            emptyText: l.schemesEmpty,
            onRetry: () => ref.invalidate(schemeListProvider(_query)),
            builder: (context, env) => Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l.schemesCount(env.data.length), style: TextStyle(color: context.colors.mutedForeground)),
                const SizedBox(height: 8),
                for (final s in env.data) ...[
                  _SchemeTile(scheme: s),
                  const SizedBox(height: 8),
                ],
                SourceLine(meta: env.meta),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

String levelLabel(BuildContext context, String? level) {
  final l = context.l10n;
  return switch (level) {
    'central' => l.levelCentral,
    'state' => l.levelState,
    null => l.notAvailable,
    _ => level,
  };
}

class _SchemeTile extends StatelessWidget {
  const _SchemeTile({required this.scheme});
  final SchemeSummary scheme;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(24),
        onTap: () => context.push(Routes.schemeDetail(scheme.schemeId)),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(context.bi(scheme.name),
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                    const SizedBox(height: 4),
                    Wrap(spacing: 8, runSpacing: 4, children: [
                      _Pill(levelLabel(context, scheme.level)),
                      if (scheme.active == false) _Pill(context.l10n.schemeInactive),
                      if (scheme.active == null) _Pill(context.l10n.schemeStatusNotStated),
                    ]),
                    if (scheme.authority != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text(context.bi(scheme.authority!), style: TextStyle(color: c.mutedForeground)),
                      ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right),
            ],
          ),
        ),
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill(this.text);
  final String text;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        decoration: BoxDecoration(color: context.colors.muted, borderRadius: BorderRadius.circular(999)),
        child: Text(text, style: Theme.of(context).textTheme.labelSmall),
      );
}
