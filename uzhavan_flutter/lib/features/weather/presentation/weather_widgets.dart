import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/networking/envelope.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../shared/utils/formatters.dart';
import '../../../shared/utils/links.dart';
import '../../../shared/widgets/data_state_view.dart';
import '../../../shared/widgets/source_line.dart';
import '../../../shared/widgets/ui_kit.dart';
import '../../farm/presentation/selected_farm.dart';
import '../data/weather_repository.dart';
import '../domain/weather_models.dart';

String? _unit(String? v, String unit) => v == null ? null : '$v $unit';

/// Icon for a WMO weather code as sent by the API. A missing code gets a neutral icon:
/// the picture never claims more than the data says.
IconData weatherIcon(int? code, {bool? isDay}) {
  if (code == null) return Icons.thermostat_outlined;
  final night = isDay == false;
  if (code == 0) return night ? Icons.nightlight_round : Icons.wb_sunny_rounded;
  if (code == 1 || code == 2) return night ? Icons.nights_stay_rounded : Icons.wb_cloudy_outlined;
  if (code == 3) return Icons.cloud_rounded;
  if (code == 45 || code == 48) return Icons.foggy;
  if (code >= 51 && code <= 57) return Icons.grain_rounded;
  if ((code >= 61 && code <= 67) || (code >= 80 && code <= 82)) return Icons.water_drop_rounded;
  if ((code >= 71 && code <= 77) || code == 85 || code == 86) return Icons.ac_unit_rounded;
  if (code >= 95) return Icons.thunderstorm_rounded;
  return Icons.cloud_outlined;
}

class WeatherCurrentCard extends ConsumerWidget {
  const WeatherCurrentCard({super.key, required this.loc, this.compact = false});
  final DataLocation loc;

  /// Home shows the headline and three key readings; the Weather screen shows everything.
  final bool compact;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final c = context.colors;
    final t = Theme.of(context).textTheme;
    final value = ref.watch(weatherCurrentProvider(loc));
    return DataStateView<Enveloped<WeatherCurrent>>(
      value: value,
      unavailableText: l.weatherUnavailable,
      padding: EdgeInsets.zero,
      loadingLines: 4,
      onRetry: () => ref.invalidate(weatherCurrentProvider(loc)),
      builder: (context, env) {
        final w = env.data;
        final temp = Fmt.num(w.temperatureC);
        final metrics = <(IconData, String, String?)>[
          (Icons.device_thermostat_rounded, l.weatherFeelsLike, _unit(Fmt.num(w.apparentTemperatureC), '°C')),
          (Icons.opacity_rounded, l.weatherHumidity, _unit(Fmt.num(w.humidityPct, digits: 0), '%')),
          (Icons.umbrella_outlined, l.weatherRain, _unit(Fmt.num(w.precipitationMm), 'mm')),
          (Icons.air_rounded, l.weatherWind, _unit(Fmt.num(w.windSpeedKmph), 'km/h')),
        ];
        return InfoCard(
          key: const Key('weather-current'),
          title: l.weatherNow,
          trailing: KindBadge(kind: env.meta.kind ?? 'current'),
          children: [
            if (env.meta.location?.name != null)
              Row(
                children: [
                  Icon(Icons.place_outlined, size: 16, color: c.mutedForeground),
                  const SizedBox(width: 4),
                  Expanded(child: Text(l.weatherLocation(env.meta.location!.name!), style: t.bodySmall)),
                ],
              ),
            const SizedBox(height: AppSpace.md),
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                IconTile(weatherIcon(w.weatherCode, isDay: w.isDay), size: 60, tone: Tone.brand),
                const SizedBox(width: AppSpace.lg),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(temp == null ? l.notAvailable : '$temp °C', style: t.displaySmall),
                      if (w.condition != null) Text(context.bi(w.condition!), style: t.titleMedium?.copyWith(color: c.mutedForeground)),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpace.lg),
            _MetricGrid(metrics: compact ? metrics.sublist(1) : metrics, columns: compact ? 3 : 2),
            if (!compact && env.meta.observedAt != null) ...[
              const SizedBox(height: AppSpace.sm),
              KV(l.weatherModelTime, Fmt.time(env.meta.observedAt)),
            ],
            const SizedBox(height: AppSpace.md),
            SourceLine(meta: env.meta),
          ],
        );
      },
    );
  }
}

/// Readings as small labelled tiles. A missing reading says "not available".
class _MetricGrid extends StatelessWidget {
  const _MetricGrid({required this.metrics, required this.columns});
  final List<(IconData, String, String?)> metrics;
  final int columns;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final t = Theme.of(context).textTheme;
    return LayoutBuilder(
      builder: (context, box) {
        const gap = AppSpace.sm;
        final w = (box.maxWidth - gap * (columns - 1)) / columns;
        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: [
            for (final (icon, label, value) in metrics)
              Container(
                width: w,
                padding: const EdgeInsets.symmetric(horizontal: AppSpace.md, vertical: AppSpace.sm + 2),
                decoration: BoxDecoration(color: c.muted.withValues(alpha: 0.6), borderRadius: BorderRadius.circular(AppRadius.md)),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(icon, size: 15, color: c.secondary),
                        const SizedBox(width: 4),
                        Expanded(child: Text(label, style: t.bodySmall, maxLines: 2, overflow: TextOverflow.ellipsis)),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(
                      value ?? context.l10n.notAvailable,
                      style: value == null
                          ? t.bodySmall?.copyWith(fontStyle: FontStyle.italic)
                          : t.titleSmall?.copyWith(fontWeight: FontWeight.w700),
                    ),
                  ],
                ),
              ),
          ],
        );
      },
    );
  }
}

class WeatherForecastCard extends ConsumerWidget {
  const WeatherForecastCard({super.key, required this.loc, this.maxDays});
  final DataLocation loc;

  /// Home shows only today.
  final int? maxDays;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final locale = Localizations.localeOf(context).toString();
    final value = ref.watch(weatherForecastProvider(loc));
    return DataStateView<Enveloped<List<ForecastDay>>>(
      value: value,
      unavailableText: l.weatherUnavailable,
      padding: EdgeInsets.zero,
      isEmpty: (e) => e.data.isEmpty,
      emptyText: l.weatherForecastEmpty,
      onRetry: () => ref.invalidate(weatherForecastProvider(loc)),
      builder: (context, env) {
        final days = maxDays == null ? env.data : env.data.take(maxDays!).toList();
        return InfoCard(
          key: const Key('weather-forecast'),
          title: maxDays == 1 ? l.weatherToday : l.weatherForecast7,
          trailing: KindBadge(kind: env.meta.kind ?? 'forecast'),
          children: [
            for (var i = 0; i < days.length; i++) ...[
              if (i > 0) Divider(color: context.colors.border, height: 1),
              _DayRow(day: days[i], locale: locale),
            ],
            const SizedBox(height: 8),
            // The live provider gives no issue time (observed_at null).
            Text(
              env.meta.observedAt == null
                  ? l.weatherIssuedNotProvided
                  : l.weatherIssuedAt(Fmt.time(env.meta.observedAt)!),
              key: const Key('forecast-issued'),
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 2),
            SourceLine(meta: env.meta),
            if (maxDays == null) NotesBlock(notes: env.meta.notes),
          ],
        );
      },
    );
  }
}

class _DayRow extends StatelessWidget {
  const _DayRow({required this.day, required this.locale});
  final ForecastDay day;
  final String locale;

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final c = context.colors;
    final t = Theme.of(context).textTheme;
    final na = l.notAvailable;
    final max = Fmt.num(day.tempMaxC);
    final min = Fmt.num(day.tempMinC);
    final rain = Fmt.num(day.precipitationMm);
    final prob = Fmt.num(day.precipitationProbabilityPct, digits: 0);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpace.md),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 84,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(day.date == null ? na : Fmt.weekday(day.date!, locale), style: t.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
                Text(Fmt.date(day.date) ?? '', style: t.bodySmall),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(right: AppSpace.md, top: 2),
            child: Icon(weatherIcon(day.weatherCode), size: 26, color: c.secondary),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (day.condition != null) Text(context.bi(day.condition!), style: t.titleSmall),
                Text(l.weatherMaxMin(max == null ? na : '$max °C', min == null ? na : '$min °C'), style: t.bodyMedium),
                Text(l.weatherRainLine(rain == null ? na : '$rain mm', prob == null ? na : '$prob %'), style: t.bodySmall),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class WeatherAdvisoriesCard extends ConsumerWidget {
  const WeatherAdvisoriesCard({super.key, required this.loc});
  final DataLocation loc;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final c = context.colors;
    final value = ref.watch(weatherAdvisoriesProvider(loc));
    return DataStateView<Enveloped<List<WeatherAdvisory>>>(
      value: value,
      unavailableText: l.weatherUnavailable,
      padding: EdgeInsets.zero,
      onRetry: () => ref.invalidate(weatherAdvisoriesProvider(loc)),
      builder: (context, env) => InfoCard(
        key: const Key('weather-advisories'),
        title: l.weatherAdvisories,
        children: [
          if (env.data.isEmpty)
            Text(l.weatherNoAdvisories, style: TextStyle(color: c.mutedForeground)),
          for (final a in env.data)
            Container(
              margin: const EdgeInsets.only(top: 8),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: (a.severity == 'caution' ? c.warning : c.info).withValues(alpha: 0.08),
                border: Border.all(color: (a.severity == 'caution' ? c.warning : c.info).withValues(alpha: 0.5)),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(children: [
                    Icon(a.severity == 'caution' ? Icons.warning_amber_rounded : Icons.info_outline,
                        size: 18, color: a.severity == 'caution' ? c.warning : c.info),
                    const SizedBox(width: 6),
                    Text(a.severity == 'caution' ? l.severityCaution : l.severityInfo,
                        style: const TextStyle(fontWeight: FontWeight.w700)),
                  ]),
                  const SizedBox(height: 4),
                  Text(a.text == null ? l.notAvailable : context.bi(a.text!)),
                  const SizedBox(height: 4),
                  if (a.ruleSourceUrl != null)
                    LinkText(label: l.ruleSource(a.ruleSource ?? a.ruleSourceUrl!), url: a.ruleSourceUrl)
                  else
                    Text(l.ruleSource(a.ruleSource ?? l.notAvailable),
                        style: TextStyle(color: c.mutedForeground, fontSize: 12)),
                ],
              ),
            ),
          const SizedBox(height: 8),
          SourceLine(meta: env.meta),
          NotesBlock(notes: env.meta.notes),
        ],
      ),
    );
  }
}
