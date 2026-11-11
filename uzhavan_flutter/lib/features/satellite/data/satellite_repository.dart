import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/networking/api_client.dart';
import '../../../core/networking/envelope.dart';
import '../../../core/networking/providers.dart';

/// Contract §11 status. No imagery and no predictions are modelled here.
class SatelliteStatus {
  const SatelliteStatus({required this.available, this.reason, this.gates = const {}});

  final bool available;
  final String? reason;

  /// Gate name → value (bool or text), in server order.
  final Map<String, Object?> gates;

  factory SatelliteStatus.fromJson(Object? json) {
    final m = asJsonMap(json);
    final g = m['gates'];
    return SatelliteStatus(
      // Anything other than an explicit `true` is treated as not available.
      available: m['available'] == true,
      reason: jsonString(m, 'reason'),
      gates: g is Map ? g.cast<String, Object?>() : const {},
    );
  }
}

class SatelliteRepository {
  SatelliteRepository(this._api);
  final ApiClient _api;

  Future<Enveloped<SatelliteStatus>> status() async =>
      parseEnvelope(await _api.get('/api/satellite/status'), SatelliteStatus.fromJson);
}

final satelliteRepositoryProvider =
    Provider<SatelliteRepository>((ref) => SatelliteRepository(ref.watch(apiClientProvider)));

final satelliteStatusProvider = FutureProvider<Enveloped<SatelliteStatus>>(
  (ref) => ref.watch(satelliteRepositoryProvider).status(),
);
