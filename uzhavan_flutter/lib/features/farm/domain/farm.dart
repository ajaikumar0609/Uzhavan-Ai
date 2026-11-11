import '../../../core/networking/api_client.dart';
import '../../../shared/utils/area_units.dart';

/// Contract §3 `Farm`. Area is stored in hectares. The server's extra
/// nullable `boundary_geojson` is not edited in this app and is ignored.
class Farm {
  const Farm({
    required this.farmId,
    required this.name,
    required this.districtId,
    this.village,
    this.latitude,
    this.longitude,
    this.areaHa,
    this.cropId,
    this.cropStageId,
    this.seasonId,
    this.irrigationTypeId,
    this.createdAt,
    this.updatedAt,
  });

  final String farmId;
  final String name;
  final String districtId;
  final String? village;
  final double? latitude;
  final double? longitude;
  final double? areaHa;
  final String? cropId;
  final String? cropStageId;
  final String? seasonId;
  final String? irrigationTypeId;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  factory Farm.fromJson(Object? json) {
    final m = asJsonMap(json);
    String? str(String k) {
      final v = m[k];
      return v is String && v.trim().isNotEmpty ? v : null;
    }

    double? num_(String k) => (m[k] as num?)?.toDouble();
    return Farm(
      farmId: '${m['farm_id']}',
      name: str('name') ?? '',
      districtId: str('district_id') ?? '',
      village: str('village'),
      latitude: num_('latitude'),
      longitude: num_('longitude'),
      areaHa: num_('area_ha'),
      cropId: str('crop_id'),
      cropStageId: str('crop_stage_id'),
      seasonId: str('season_id'),
      irrigationTypeId: str('irrigation_type_id'),
      createdAt: DateTime.tryParse(str('created_at') ?? ''),
      updatedAt: DateTime.tryParse(str('updated_at') ?? ''),
    );
  }
}

/// `FarmIn`: what the form sends. The farmer types acres; this sends hectares.
class FarmInput {
  const FarmInput({
    required this.name,
    required this.districtId,
    this.village,
    this.latitude,
    this.longitude,
    this.areaAcres,
    this.cropId,
    this.cropStageId,
    this.seasonId,
    this.irrigationTypeId,
  });

  final String name;
  final String districtId;
  final String? village;
  final double? latitude;
  final double? longitude;
  final double? areaAcres;
  final String? cropId;
  final String? cropStageId;
  final String? seasonId;
  final String? irrigationTypeId;

  /// Every editable field is sent; null clears it (PUT is partial on the
  /// server). `boundary_geojson` is never sent, so an existing boundary is kept.
  Map<String, Object?> toJson() => {
        'name': name,
        'district_id': districtId,
        'village': village,
        'latitude': latitude,
        'longitude': longitude,
        'area_ha': areaAcres == null ? null : AreaUnits.acresToHectares(areaAcres!),
        'crop_id': cropId,
        'crop_stage_id': cropStageId,
        'season_id': seasonId,
        'irrigation_type_id': irrigationTypeId,
      };
}
