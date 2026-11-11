import 'dart:async';
import 'dart:convert';

/// One SSE event from `POST /conversation` (contract §9):
/// `data:` JSON `{event, session_id, conversation_id, timestamp, data}`.
class ConversationEvent {
  const ConversationEvent({
    required this.type,
    required this.data,
    this.sessionId,
    this.conversationId,
  });

  final String type;
  final Map<String, Object?> data;
  final String? sessionId;
  final String? conversationId;

  @override
  String toString() => 'ConversationEvent($type)';
}

/// Parses a `text/event-stream` byte stream. Robust to chunks that split
/// lines or multi-byte UTF-8 characters, CRLF line ends, comments
/// (`: keepalive`), multi-line `data:` fields and a missing trailing blank
/// line. The event type comes from the JSON `event` field, else the
/// `event:` line. Unparseable payloads are skipped (never shown raw).
Stream<ConversationEvent> parseSse(Stream<List<int>> bytes) async* {
  var buffer = '';
  String? eventName;
  final dataLines = <String>[];

  ConversationEvent? dispatch() {
    if (dataLines.isEmpty) {
      eventName = null;
      return null;
    }
    final payload = dataLines.join('\n');
    final fallbackName = eventName;
    dataLines.clear();
    eventName = null;
    Object? json;
    try {
      json = jsonDecode(payload);
    } on FormatException {
      return null;
    }
    if (json is! Map) return null;
    final type = json['event'] is String ? json['event'] as String : fallbackName;
    if (type == null || type.isEmpty) return null;
    final data = json['data'];
    return ConversationEvent(
      type: type,
      data: data is Map ? data.cast<String, Object?>() : const {},
      sessionId: json['session_id'] is String ? json['session_id'] as String : null,
      conversationId: json['conversation_id'] is String ? json['conversation_id'] as String : null,
    );
  }

  ConversationEvent? handleLine(String line) {
    if (line.isEmpty) return dispatch();
    if (line.startsWith(':')) return null;
    final colon = line.indexOf(':');
    final field = colon < 0 ? line : line.substring(0, colon);
    var value = colon < 0 ? '' : line.substring(colon + 1);
    if (value.startsWith(' ')) value = value.substring(1);
    switch (field) {
      case 'data':
        dataLines.add(value);
      case 'event':
        eventName = value;
    }
    return null;
  }

  await for (final text in bytes.cast<List<int>>().transform(utf8.decoder)) {
    buffer += text;
    while (true) {
      final nl = buffer.indexOf('\n');
      if (nl < 0) break;
      var line = buffer.substring(0, nl);
      buffer = buffer.substring(nl + 1);
      if (line.endsWith('\r')) line = line.substring(0, line.length - 1);
      final e = handleLine(line);
      if (e != null) yield e;
    }
  }
  if (buffer.isNotEmpty) {
    final e = handleLine(buffer.endsWith('\r') ? buffer.substring(0, buffer.length - 1) : buffer);
    if (e != null) yield e;
  }
  final last = dispatch();
  if (last != null) yield last;
}
