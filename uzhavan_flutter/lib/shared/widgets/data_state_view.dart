import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/localization/l10n.dart';
import '../../core/networking/api_failure.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_tokens.dart';
import 'ui_kit.dart';

/// Mirrors the React `DataState` (FP-006). The app only shows what it knows:
/// network failure / 404 / 501 / 503 → unavailable · other failures → error ·
/// 200 with nothing → empty · 200 with data → success · model "unsure" → unsure.
enum DataStatus { loading, success, empty, unavailable, error, unsure }

DataStatus statusOf<T>(
  AsyncValue<T> value, {
  bool Function(T data)? isEmpty,
  bool Function(T data)? isUnsure,
}) {
  if (value.hasError && !value.isLoading) {
    final e = value.error;
    return e is ApiFailure && e.kind == ApiFailureKind.unavailable
        ? DataStatus.unavailable
        : DataStatus.error;
  }
  if (value.hasValue && !value.hasError) {
    final data = value.requireValue;
    if (isUnsure != null && isUnsure(data)) return DataStatus.unsure;
    if (isEmpty != null && isEmpty(data)) return DataStatus.empty;
    return DataStatus.success;
  }
  return DataStatus.loading;
}

class DataStateView<T> extends StatelessWidget {
  const DataStateView({
    super.key,
    required this.value,
    required this.builder,
    required this.unavailableText,
    this.emptyText,
    this.emptyAction,
    this.isEmpty,
    this.isUnsure,
    this.onRetry,
    this.padding = const EdgeInsets.all(AppSpace.lg),
    this.loadingLines = 3,
  });

  /// Outer padding of the non-success card. Pass [EdgeInsets.zero] inside an already padded list.
  final EdgeInsetsGeometry padding;
  final int loadingLines;

  final AsyncValue<T> value;
  final Widget Function(BuildContext context, T data) builder;
  final String unavailableText;
  final String? emptyText;
  final Widget? emptyAction;
  final bool Function(T data)? isEmpty;
  final bool Function(T data)? isUnsure;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final status = statusOf(value, isEmpty: isEmpty, isUnsure: isUnsure);
    if (status == DataStatus.success) return builder(context, value.requireValue);
    final l = context.l10n;
    final text = switch (status) {
      DataStatus.empty => emptyText ?? l.stateEmpty,
      DataStatus.unavailable => unavailableText,
      DataStatus.error => l.stateError,
      DataStatus.unsure => l.stateUnsure,
      _ => l.loading,
    };
    return DataStateCard(
      status: status,
      message: text,
      onRetry: onRetry,
      emptyAction: emptyAction,
      padding: padding,
      loadingLines: loadingLines,
    );
  }
}

/// The non-success card (also usable without an AsyncValue).
class DataStateCard extends StatelessWidget {
  const DataStateCard({
    super.key,
    required this.status,
    required this.message,
    this.onRetry,
    this.emptyAction,
    this.icon,
    this.padding = const EdgeInsets.all(AppSpace.lg),
    this.loadingLines = 3,
  });

  final DataStatus status;
  final String message;
  final VoidCallback? onRetry;
  final Widget? emptyAction;
  final IconData? icon;
  final EdgeInsetsGeometry padding;
  final int loadingLines;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final t = Theme.of(context).textTheme;
    if (status == DataStatus.loading) {
      // A calm skeleton in the shape of the card that will replace it.
      return Semantics(
        label: message.isEmpty ? context.l10n.loading : message,
        liveRegion: true,
        child: Padding(padding: padding, child: SkeletonCard(lines: loadingLines)),
      );
    }
    final (IconData defaultIcon, Tone tone) = switch (status) {
      DataStatus.error => (Icons.error_outline_rounded, Tone.critical),
      DataStatus.unsure => (Icons.help_outline_rounded, Tone.caution),
      DataStatus.empty => (Icons.inbox_outlined, Tone.neutral),
      _ => (Icons.cloud_off_outlined, Tone.neutral),
    };
    final showRetry = onRetry != null && (status == DataStatus.unavailable || status == DataStatus.error);
    final hasActions = showRetry || (status == DataStatus.empty && emptyAction != null);
    return Padding(
      padding: padding,
      child: AppCard(
        key: ValueKey('data-state-${status.name}'),
        raised: false,
        color: status == DataStatus.unsure ? c.warning.withValues(alpha: 0.08) : null,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                IconTile(icon ?? defaultIcon, tone: tone, size: 40),
                const SizedBox(width: AppSpace.md),
                Expanded(child: Text(message, style: t.titleSmall?.copyWith(height: 1.4))),
              ],
            ),
            if (hasActions)
              Padding(
                padding: const EdgeInsetsDirectional.only(start: 52, top: AppSpace.md),
                child: Wrap(
                  spacing: AppSpace.sm,
                  runSpacing: AppSpace.sm,
                  children: [
                    if (showRetry)
                      FilledButton.tonalIcon(
                        style: FilledButton.styleFrom(minimumSize: const Size(0, 44)),
                        onPressed: onRetry,
                        icon: const Icon(Icons.refresh_rounded, size: 18),
                        label: Text(context.l10n.retry),
                      ),
                    if (status == DataStatus.empty && emptyAction != null) emptyAction!,
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
