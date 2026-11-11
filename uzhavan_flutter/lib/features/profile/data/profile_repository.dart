import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/networking/api_client.dart';
import '../../../core/networking/providers.dart';
import '../domain/farmer_profile.dart';

class ProfileRepository {
  ProfileRepository(this._api);
  final ApiClient _api;

  static const path = '/api/farmer/profile';

  Future<FarmerProfile> fetch() async =>
      FarmerProfile.fromJson(unwrapData(await _api.get(path)));

  /// PUT returns the `{data}` envelope on the deployed backend; a bare
  /// profile is accepted too.
  Future<FarmerProfile> update(ProfileUpdate update) async {
    final body = await _api.put(path, body: update.toJson());
    return FarmerProfile.fromJson(
      body is Map && body.containsKey('data') ? body['data'] : body,
    );
  }
}

final profileRepositoryProvider =
    Provider<ProfileRepository>((ref) => ProfileRepository(ref.watch(apiClientProvider)));
