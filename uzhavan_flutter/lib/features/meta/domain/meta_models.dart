import '../../../core/localization/bilingual_text.dart';
import '../../../core/networking/api_client.dart';
import '../../../shared/widgets/option_picker_field.dart';

/// A TN district with its HQ point (`/api/meta/districts`).
class District {
  const District({required this.id, required this.name, this.lat, this.lon});

  final String id;
  final BilingualText name;
  final double? lat;
  final double? lon;

  factory District.fromJson(Object? json) {
    final m = asJsonMap(json);
    return District(
      id: m['id'] as String,
      name: BilingualText.fromJson(m['name']),
      lat: (m['lat'] as num?)?.toDouble(),
      lon: (m['lon'] as num?)?.toDouble(),
    );
  }

  PickerOption toOption() => PickerOption(id: id, label: name);
}

/// `{id, name:{en,ta}}` used for crops and all enums.
class RefItem {
  const RefItem({required this.id, required this.name});

  final String id;
  final BilingualText name;

  factory RefItem.fromJson(Object? json) {
    final m = asJsonMap(json);
    return RefItem(id: m['id'] as String, name: BilingualText.fromJson(m['name']));
  }

  PickerOption toOption() => PickerOption(id: id, label: name);
}

/// `/api/meta/enums`.
class MetaEnums {
  const MetaEnums({
    required this.cropStages,
    required this.seasons,
    required this.irrigationTypes,
    required this.diaryKinds,
  });

  final List<RefItem> cropStages;
  final List<RefItem> seasons;
  final List<RefItem> irrigationTypes;
  final List<RefItem> diaryKinds;

  factory MetaEnums.fromJson(Object? json) {
    final m = asJsonMap(json);
    List<RefItem> list(String key) =>
        m[key] == null ? const [] : asJsonList(m[key]).map(RefItem.fromJson).toList();
    return MetaEnums(
      cropStages: list('crop_stages'),
      seasons: list('seasons'),
      irrigationTypes: list('irrigation_types'),
      diaryKinds: list('diary_kinds'),
    );
  }
}

/// Finds an item's label by id; null when unknown.
BilingualText? labelFor(Iterable<RefItem>? items, String? id) {
  if (items == null || id == null) return null;
  for (final i in items) {
    if (i.id == id) return i.name;
  }
  return null;
}
