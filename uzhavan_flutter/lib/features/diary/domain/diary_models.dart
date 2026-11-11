import '../../../core/networking/api_client.dart';
import '../../../core/networking/envelope.dart';

/// Kinds a farmer can add (contract §8); `question` and `scan` are
/// written by the server and shown as history only.
const diaryAddableKinds = ['note', 'observation', 'expense', 'income'];
const diaryMoneyKinds = {'expense', 'income'};

/// Contract §8 entry.
class DiaryEntry {
  const DiaryEntry({
    required this.entryId,
    required this.kind,
    required this.text,
    this.farmId,
    this.amountInr,
    this.entryDate,
    this.createdAt,
  });

  final String entryId;
  final String kind;
  final String text;
  final String? farmId;
  final double? amountInr;
  final DateTime? entryDate;
  final DateTime? createdAt;

  factory DiaryEntry.fromJson(Object? json) {
    final m = asJsonMap(json);
    return DiaryEntry(
      entryId: jsonString(m, 'entry_id') ?? '',
      kind: jsonString(m, 'kind') ?? 'note',
      text: m['text'] is String ? m['text'] as String : '',
      farmId: jsonString(m, 'farm_id'),
      amountInr: jsonDouble(m, 'amount_inr'),
      entryDate: parseDate(m['entry_date']),
      createdAt: parseDateTime(m['created_at']),
    );
  }
}

class DiaryInput {
  const DiaryInput({
    required this.kind,
    required this.text,
    required this.entryDate,
    this.farmId,
    this.amountInr,
  });

  final String kind;
  final String text;
  final DateTime entryDate;
  final String? farmId;
  final double? amountInr;

  Map<String, Object?> toJson() => {
        'kind': kind,
        'text': text.trim(),
        'entry_date': dateOnly(entryDate),
        'farm_id': ?farmId,
        if (diaryMoneyKinds.contains(kind)) 'amount_inr': amountInr,
      };
}
