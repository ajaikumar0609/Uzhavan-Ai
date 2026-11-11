import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../farm/presentation/location_gate.dart';
import '../../farm/presentation/selected_farm.dart' show FarmPicker;
import '../data/weather_repository.dart';
import 'weather_widgets.dart';

/// Contract §4: current, 7-day forecast, rule-based advisories and notes.
class WeatherScreen extends ConsumerWidget {
  const WeatherScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return AppScaffold(
      title: context.l10n.featureWeather,
      body: LocationGate(
        builder: (context, loc) => RefreshIndicator(
          onRefresh: () async {
            ref.invalidate(weatherCurrentProvider(loc));
            ref.invalidate(weatherForecastProvider(loc));
            ref.invalidate(weatherAdvisoriesProvider(loc));
          },
          child: ListView(
            padding: AppSpace.screen,
            children: [
              const FarmPicker(),
              WeatherCurrentCard(loc: loc),
              const SizedBox(height: AppSpace.md),
              WeatherForecastCard(loc: loc),
              const SizedBox(height: AppSpace.md),
              WeatherAdvisoriesCard(loc: loc),
            ],
          ),
        ),
      ),
    );
  }
}
