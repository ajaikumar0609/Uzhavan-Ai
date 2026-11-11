import '../../../core/networking/api_client.dart';

/// `GET /api/farmer/profile` → data.
class FarmerProfile {
  const FarmerProfile({
    required this.farmerId,
    required this.phone,
    required this.preferredLanguage,
    required this.profileComplete,
    this.name,
    this.districtId,
    this.village,
    this.createdAt,
    this.updatedAt,
  });

  final String farmerId;
  final String phone;
  final String? name;
  final String? districtId;
  final String? village;

  /// `ta` or `en`.
  final String preferredLanguage;
  final bool profileComplete;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  factory FarmerProfile.fromJson(Object? json) {
    final m = asJsonMap(json);
    String? str(String k) {
      final v = m[k];
      return v is String && v.trim().isNotEmpty ? v : null;
    }

    return FarmerProfile(
      farmerId: '${m['farmer_id']}',
      phone: str('phone') ?? '',
      name: str('name'),
      districtId: str('district_id'),
      village: str('village'),
      preferredLanguage: str('preferred_language') == 'en' ? 'en' : 'ta',
      profileComplete: m['profile_complete'] == true,
      createdAt: DateTime.tryParse(str('created_at') ?? ''),
      updatedAt: DateTime.tryParse(str('updated_at') ?? ''),
    );
  }
}

/// Partial update for `PUT /api/farmer/profile`. Only non-null fields are sent,
/// except fields listed in [clear], which are sent as JSON null.
class ProfileUpdate {
  const ProfileUpdate({
    this.name,
    this.districtId,
    this.village,
    this.preferredLanguage,
    this.clear = const {},
  });

  final String? name;
  final String? districtId;
  final String? village;
  final String? preferredLanguage;
  final Set<String> clear;

  Map<String, Object?> toJson() => {
        if (name != null) 'name': name,
        if (districtId != null) 'district_id': districtId,
        if (village != null) 'village': village,
        if (preferredLanguage != null) 'preferred_language': preferredLanguage,
        for (final k in clear) k: null,
      };
}
