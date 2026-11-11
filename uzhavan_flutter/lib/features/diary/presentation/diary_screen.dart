import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/routing/routes.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/utils/formatters.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/data_state_view.dart';
import '../../farm/presentation/farms_controller.dart';
import '../data/diary_repository.dart';
import '../domain/diary_models.dart';

String diaryKindLabel(AppLocalizations l, String kind) => switch (kind) {
      'note' => l.diaryKindNote,
      'observation' => l.diaryKindObservation,
      'expense' => l.diaryKindExpense,
      'income' => l.diaryKindIncome,
      'question' => l.diaryKindQuestion,
      'scan' => l.diaryKindScan,
      _ => kind,
    };

IconData diaryKindIcon(String kind) => switch (kind) {
      'observation' => Icons.visibility_outlined,
      'expense' => Icons.arrow_upward,
      'income' => Icons.arrow_downward,
      'question' => Icons.chat_bubble_outline,
      'scan' => Icons.document_scanner_outlined,
      _ => Icons.sticky_note_2_outlined,
    };

class DiaryScreen extends ConsumerWidget {
  const DiaryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    return AppScaffold(
      title: l.featureDiary,
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push(Routes.diaryNew),
        icon: const Icon(Icons.add),
        label: Text(l.diaryAdd),
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(diaryProvider),
        child: DataStateView<List<DiaryEntry>>(
          value: ref.watch(diaryProvider),
          unavailableText: l.diaryUnavailable,
          isEmpty: (e) => e.isEmpty,
          emptyText: l.diaryEmpty,
          onRetry: () => ref.invalidate(diaryProvider),
          builder: (context, entries) => ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
            children: [
              for (final e in entries) ...[DiaryEntryTile(entry: e), const SizedBox(height: 8)],
            ],
          ),
        ),
      ),
    );
  }
}

class DiaryEntryTile extends ConsumerWidget {
  const DiaryEntryTile({super.key, required this.entry});
  final DiaryEntry entry;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final c = context.colors;
    final farm = entry.farmId == null
        ? null
        : ref.watch(farmsProvider).value?.where((f) => f.farmId == entry.farmId).firstOrNull;
    final amount = Fmt.num(entry.amountInr, digits: 2);
    final history = entry.kind == 'question' || entry.kind == 'scan';
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: c.muted,
          child: Icon(diaryKindIcon(entry.kind), color: c.foreground),
        ),
        title: Text(entry.text.isEmpty ? l.notAvailable : entry.text, maxLines: 3, overflow: TextOverflow.ellipsis),
        subtitle: Text(
          [
            diaryKindLabel(l, entry.kind),
            Fmt.date(entry.entryDate) ?? Fmt.date(entry.createdAt) ?? l.notAvailable,
            ?farm?.name,
            if (history) l.diaryHistory,
          ].join(' · '),
        ),
        trailing: diaryMoneyKinds.contains(entry.kind)
            ? Text(
                amount == null ? l.notAvailable : '₹ $amount',
                style: TextStyle(
                  fontWeight: FontWeight.w700,
                  color: entry.kind == 'income' ? c.success : c.danger,
                ),
              )
            : null,
      ),
    );
  }
}
