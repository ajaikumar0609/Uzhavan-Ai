"""
Spoken Response Planner for UZHAVAN AI.

Transforms AI response text into a natural, voice-friendly spoken form:
- Strips markdown formatting, tables, and code blocks
- Strips raw JSON, citations, database IDs, and URLs
- Converts bullet lists into conversational spoken connectors
- Expands numbers, units, and symbols to natural spoken words
- Preserves critical agricultural safety and dosage advice
- Enforces natural conversational cadence suitable for TTS
"""
from __future__ import annotations

import re

_TAMIL_UNIT_REPLACEMENTS = [
    (r"(\d+(?:\.\d+)?)\s*(?:ml/l|மில்லி/லிட்டர்|மி\.லி/லிட்டர்|மி\.லி/லி)(?=[.,!?;:\s]|$)", r"ஒரு லிட்டர் தண்ணீருக்கு \1 மில்லி"),
    (r"(\d+(?:\.\d+)?)\s*(?:g/l|கிராம்/லிட்டர்)(?=[.,!?;:\s]|$)", r"ஒரு லிட்டர் தண்ணீருக்கு \1 கிராம்"),
    (r"(\d+(?:\.\d+)?)\s*(?:kg/ha|கிலோ/ஹெக்)(?=[.,!?;:\s]|$)", r"ஒரு ஹெக்டேருக்கு \1 கிலோ"),
    (r"(\d+(?:\.\d+)?)\s*(?:kg/acre|கிலோ/ஏக்கர்)(?=[.,!?;:\s]|$)", r"ஒரு ஏக்கருக்கு \1 கிலோ"),
    (r"(\d+(?:\.\d+)?)\s*(?:ml|மில்லி|மி\.லி)(?=[.,!?;:\s]|$)", r"\1 மில்லி"),
    (r"(\d+(?:\.\d+)?)\s*(?:மிமீ|mm)(?=[.,!?;:\s]|$)", r"\1 மில்லிமீட்டர்"),
    (r"(\d+(?:\.\d+)?)\s*(?:ஹெக்டேர்|ha)(?=[.,!?;:\s]|$)", r"\1 ஹெக்டேர்"),
    (r"(\d+(?:\.\d+)?)\s*(?:கிலோ|kg|கிகி)(?=[.,!?;:\s]|$)", r"\1 கிலோ"),
    (r"(\d+(?:\.\d+)?)\s*(?:கிராம்|gm|g)(?=[.,!?;:\s]|$)", r"\1 கிராம்"),
    (r"(\d+(?:\.\d+)?)\s*(?:லிட்டர்|litres?|l)(?=[.,!?;:\s]|$)", r"\1 லிட்டர்"),
    (r"(\d+(?:\.\d+)?)\s*%", r"\1 சதவீதம்"),
    (r"(?:₹|ரூ\.)\s*(\d+(?:,\d+)*(?:\.\d+)?)", r"\1 ரூபாய்"),
    (r"(\d+(?:\.\d+)?)\s*(?:°C|டிகிரி\s*செ)(?=[.,!?;:\s]|$)", r"\1 டிகிரி செல்சியஸ்"),
]

_ENGLISH_UNIT_REPLACEMENTS = [
    (r"(\d+(?:\.\d+)?)\s*(?:mm|மிமீ)(?=[.,!?;:\s]|$)", r"\1 millimeters"),
    (r"(\d+(?:\.\d+)?)\s*(?:ha|ஹெக்டேர்)(?=[.,!?;:\s]|$)", r"\1 hectares"),
    (r"(\d+(?:\.\d+)?)\s*(?:kg|கிலோ)(?=[.,!?;:\s]|$)", r"\1 kilograms"),
    (r"(\d+(?:\.\d+)?)\s*%", r"\1 percent"),
    (r"(?:₹|Rs\.?)\s*(\d+(?:,\d+)*(?:\.\d+)?)", r"\1 rupees"),
    (r"(\d+(?:\.\d+)?)\s*(?:°C)(?=[.,!?;:\s]|$)", r"\1 degrees Celsius"),
]

# Formal bureaucratic phrases to replace with spoken phrases in Tamil
_TAMIL_SPOKEN_REPLACEMENTS = [
    (r"பின்வரும்\s+பரிந்துரைகளை\s+கடைப்பிடிக்கவும்[:.]?", "முதலில் இதை பாருங்க:"),
    (r"பின்வரும்\s+நடவடிக்கைகளை\s+மேற்கொள்ளவும்[:.]?", "இந்த வழிகளை செய்யலாம்:"),
    (r"கீழ்க்கண்ட\s+விவரங்களை[:.]?", "இதை கவனியுங்கள்:"),
    (r"மேற்கண்ட\s+", "இந்த "),
    (r"அச்சம்\s+கொள்ளத்\s+தேவையில்லை", "கவலைப்படாதீங்க"),
    (r"நிழற்படத்தை\s+சமர்ப்பிக்கவும்", "ஒரு புகைப்படம் அனுப்புங்க"),
    (r"சாத்தியக்கூறுகள்\s+உள்ளன", "வாய்ப்பு இருக்கு"),
]


def _strip_markdown(text: str) -> str:
    """Removes markdown syntax while preserving textual content."""
    # Remove code blocks and inline code
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Remove JSON structures if any accidentally output
    text = re.sub(r"\{[\s\S]*?\}", "", text)

    # Remove markdown images and links: [alt](url) -> alt
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove raw URLs
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"www\.\S+", "", text)

    # Remove headers (# Title -> Title)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

    # Remove bold, italics, strikethrough
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    text = re.sub(r"~~([^~]+)~~", r"\1", text)

    # Remove blockquotes and horizontal rules
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[=\-_*]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Remove internal citation badges e.g. [TNAU], (confidence: 90%), [Farm: ...]
    text = re.sub(r"\[(?:TNAU|IMD|CACP|RAG|Farm|Weather|Market|Disease)[^\]]*\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\((?:confidence|ஆதாரம்)[^)]*\)", "", text, flags=re.IGNORECASE)

    # Remove DB IDs or uuid-like tokens
    text = re.sub(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", "", text, flags=re.IGNORECASE)

    return text


def _convert_bullets(text: str, is_tamil: bool) -> str:
    """Converts bullet points into natural spoken sequence connectors."""
    lines = text.split("\n")
    processed_lines: list[str] = []
    bullet_idx = 0

    tamil_connectors = ["முதலில், ", "அடுத்ததாக, ", "மேலும், ", "இறுதியாக, "]
    english_connectors = ["First, ", "Next, ", "Also, ", "Finally, "]

    for line in lines:
        stripped = line.strip()
        bullet_match = re.match(r"^[-*•]\s+(.*)$|^\d+[\.)]\s+(.*)$", stripped)
        if bullet_match:
            item_text = bullet_match.group(1) or bullet_match.group(2)
            if not item_text:
                continue
            item_text = item_text.strip()
            connectors = tamil_connectors if is_tamil else english_connectors
            prefix = connectors[min(bullet_idx, len(connectors) - 1)]
            processed_lines.append(f"{prefix}{item_text}")
            bullet_idx += 1
        else:
            bullet_idx = 0
            if stripped:
                processed_lines.append(stripped)

    return " ".join(processed_lines)


def plan_spoken_response(text: str, language: str = "Tamil") -> str:
    """
    Produce a clean, natural spoken version of the assistant's answer for TTS.
    """
    if not text or not text.strip():
        return ""

    is_tamil = language.lower().startswith("ta") or bool(re.search(r"[\u0B80-\u0BFF]", text))

    # Convert bullets to spoken connectors first, while bullet markers (*, -, •, 1.) are intact
    cleaned = _convert_bullets(text, is_tamil)

    cleaned = _strip_markdown(cleaned)

    # Apply spoken vocabulary transforms
    if is_tamil:
        for pattern, replacement in _TAMIL_SPOKEN_REPLACEMENTS:
            cleaned = re.sub(pattern, replacement, cleaned)
        for pattern, replacement in _TAMIL_UNIT_REPLACEMENTS:
            cleaned = re.sub(pattern, replacement, cleaned)
    else:
        for pattern, replacement in _ENGLISH_UNIT_REPLACEMENTS:
            cleaned = re.sub(pattern, replacement, cleaned)

    # Collapse multiple whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Clean leading punctuation or awkward colons left by heading removal
    cleaned = re.sub(r"^[ ,:;.-]+", "", cleaned).strip()

    # Safety safeguard: if empty or corrupted, return fallback speech
    if not cleaned:
        return "மன்னிக்கவும், தகவலைப் பெற முடியவில்லை. மீண்டும் முயற்சிக்கவும்." if is_tamil else "Sorry, could not prepare the voice answer. Please try again."

    return cleaned
