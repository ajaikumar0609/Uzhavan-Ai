"""Is the question a request to EXPLAIN a concept (what is NPK / why rotate crops), as opposed to
asking what to apply, how much, or what to do on the farmer's own field?

Why: a definition question such as "What is NPK fertilizer?" used to run the weather and
fertilizer-plan tools. The model then received the farm's area and per-hectare rates and
"helpfully" computed kilograms for the farm, which the dosage guard (correctly) blocked, so a
plain definition came back as "information not available". Definition questions now run RAG
only and tell the model not to calculate quantities. The dosage guard is unchanged.
"""
from __future__ import annotations

import re

# Words that mean the farmer wants quantities / an action on their own field -> NOT definitional.
_ACTION = re.compile(
    r"\b(how much|how many|dose|dosage|quantity|per (?:acre|hectare|ha|litre|liter)|my (?:farm|field|crop|land)|"
    r"calculate|apply|spray|should i|need for)\b|\d",
    re.IGNORECASE,
)
_ACTION_TA = ("எவ்வளவு", "எத்தனை", "அளவு", "கிலோ", "ஏக்கர்", "ஹெக்டேர்", "என் வயல்", "என் நிலம்", "தெளிக்க", "இட வேண்டும்", "போட வேண்டும்")

_DEFINE = re.compile(
    r"^\s*(?:what\s+(?:is|are|'s)|what\s+does|define|explain|meaning\s+of|tell\s+me\s+about|"
    r"importance\s+of|why\s+is\s+.+\s+important)\b",
    re.IGNORECASE,
)
_DEFINE_TA = ("என்றால் என்ன", "என்பது என்ன", "என்ன என்று விளக்க", "விளக்குங்கள்", "விளக்கு", "முக்கியத்துவம்", "என்றால்")


def is_definitional(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if _ACTION.search(q) or any(w in q for w in _ACTION_TA):
        return False
    return bool(_DEFINE.search(q)) or any(w in q for w in _DEFINE_TA)


DEFINITIONAL_INSTRUCTION_EN = (
    "\n\n### Definition question\nExplain the concept in plain words only. Do NOT calculate or state "
    "quantities, rates or doses for the farmer's field, and do not use the farm area. If they want an "
    "amount to apply, tell them to ask for a recommendation for their crop and stage."
)
DEFINITIONAL_INSTRUCTION_TA = (
    "\n\n### விளக்கக் கேள்வி\nகருத்தை எளிய சொற்களில் மட்டும் விளக்கவும். விவசாயியின் வயலுக்கான அளவு, "
    "கிலோ, மருந்தளவு போன்றவற்றை கணக்கிடவோ கூறவோ வேண்டாம்; வயல் பரப்பைப் பயன்படுத்த வேண்டாம்."
)
