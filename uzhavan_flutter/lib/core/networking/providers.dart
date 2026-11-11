import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/app_config.dart';
import '../storage/token_store.dart';
import 'api_client.dart';

/// Overridden in `main()` with the resolved configuration.
final appConfigProvider = Provider<AppConfig>(
  (ref) => throw UnimplementedError('appConfigProvider not overridden'),
);

final tokenStoreProvider = Provider<TokenStore>((ref) => SecureTokenStore());

/// Emits when the server rejects the refresh token (session over).
class SessionEvents {
  final _expired = StreamController<void>.broadcast();
  Stream<void> get expired => _expired.stream;
  void notifyExpired() => _expired.add(null);
  void dispose() => _expired.close();
}

final sessionEventsProvider = Provider<SessionEvents>((ref) {
  final events = SessionEvents();
  ref.onDispose(events.dispose);
  return events;
});

final apiClientProvider = Provider<ApiClient>((ref) {
  final config = ref.watch(appConfigProvider);
  final events = ref.watch(sessionEventsProvider);
  return ApiClient(
    baseUrl: config.apiBaseUrl,
    tokenStore: ref.watch(tokenStoreProvider),
    onSessionExpired: events.notifyExpired,
  );
});
