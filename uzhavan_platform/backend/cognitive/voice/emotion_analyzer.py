"""
Emotion and Conversational Tone Analyzer for UZHAVAN AI.

Infers the farmer's conversational state without pretending to have human emotions:
- worried: Reassuring, simple, practical, calming next steps.
- confused: Step-by-step explanation, one question at a time.
- urgent: Clear warning, immediate action first, no conversational filler.
- casual / informational: Direct, clear, farmer-friendly answer.
"""
from __future__ import annotations

import re
from typing import NamedTuple


class ToneGuidance(NamedTuple):
    state: str
    guidance_ta: str
    guidance_en: str


_WORRIED_PATTERNS = [
    r"தெரியல", r"தெரியவில்லை", r"என்ன\s*பண்ணுறதுன்னே\s*தெரியல", r"என்ன\s*பண்றதுன்னே\s*தெரியல",
    r"கவலையா", r"பயமா", r"காப்பாத்துங்க", r"பாதிப்பு\s*அதிக", r"அழிஞ்சி", r"சேதம்",
    r"கெட்டுப்போச்சு", r"நாசமா", r"நஷ்டம்", r"அழுதுடுவேன்", r"எல்லாம்\s*போச்சு",
    r"\bworried\b", r"\bscared\b", r"\bdying\b", r"\bruined\b", r"\bsevere\s*damage\b",
    r"\bhelpless\b", r"\bdon't\s*know\s*what\s*to\s*do\b",
]

_CONFUSED_PATTERNS = [
    r"புரியல", r"புரியவில்லை", r"குழப்பமா", r"குழப்பம்", r"எப்படி\s*செய்யணும்",
    r"எப்படி\s*பண்றது", r"சரியா\s*வரல", r"விளங்கல",
    r"\bconfused\b", r"\bhow\s*to\s*do\b", r"\bnot\s*clear\b", r"\bdon't\s*understand\b",
]

_URGENT_PATTERNS = [
    r"உடனே", r"அவசரம்", r"திடீரென", r"திடீர்னு", r"முழுக்க\s*பரவுது", r"வேகமா\s*பரவுது",
    r"அபாயம்", r"உடனடி", r"தீவிரம்",
    r"\burgent\b", r"\bimmediate\b", r"\bemergency\b", r"\bspreading\s*fast\b", r"\bcritical\b",
]


def analyze_conversational_state(text: str) -> ToneGuidance:
    """Analyze the farmer's input to determine the conversational tone guidance."""
    text_lower = text.lower()

    # 1. Urgent priority check
    if any(re.search(pat, text_lower) for pat in _URGENT_PATTERNS):
        return ToneGuidance(
            state="urgent",
            guidance_ta=(
                "விவசாயி அவசரமான பாதிப்பை தெரிவிக்கிறார். "
                "உடனடி எச்சரிக்கையையும், தாமதிக்காமல் உடனே செய்ய வேண்டிய முதன்மை நடவடிக்கையையும் "
                "முதலில் தெளிவாகக் கூறவும். தேவையற்ற முன்னுரைகளைத் தவிர்க்கவும்."
            ),
            guidance_en=(
                "The farmer is reporting an urgent agricultural issue. "
                "State immediate actions and clear warnings directly at the beginning. "
                "Avoid unnecessary conversational filler."
            ),
        )

    # 2. Worried check
    if any(re.search(pat, text_lower) for pat in _WORRIED_PATTERNS):
        return ToneGuidance(
            state="worried",
            guidance_ta=(
                "விவசாயி கவலையுடனும் பதற்றத்துடனும் கேட்கிறார். "
                "ஆறுதலளிக்கும் வகையிலும் எளிமையாகவும் பேசவும் (எ.கா: 'கவலைப்படாதீங்க. முதலில் ஒரு விஷயம் பார்க்கலாம்.'). "
                "அச்சத்தை நீக்கி, நடைமுறைக்கு சாத்தியமான அடுத்த படியைக் கூறவும்."
            ),
            guidance_en=(
                "The farmer sounds worried and anxious about their crop. "
                "Be reassuring, warm, and simple (e.g., 'Do not worry. First, let us check one thing.'). "
                "Focus on simple, actionable next steps to calm their anxiety."
            ),
        )

    # 3. Confused check
    if any(re.search(pat, text_lower) for pat in _CONFUSED_PATTERNS):
        return ToneGuidance(
            state="confused",
            guidance_ta=(
                "விவசாயி குழப்பத்தில் உள்ளார். "
                "படிப்படியாக (Step-by-step) எளிமையாக விளக்கவும். "
                "ஒரே நேரத்தில் பல கேள்விகள் கேட்காமல், ஒரு நேரத்தில் ஒரு தெளிவான கேள்வியை மட்டும் கேட்கவும்."
            ),
            guidance_en=(
                "The farmer seems confused. "
                "Explain step-by-step in plain language. "
                "Ask only one clear question at a time instead of overwhelming them."
            ),
        )

    # 4. Casual / Informational default
    return ToneGuidance(
        state="informational",
        guidance_ta=(
            "நேரடியான எளிய பேச்சுத்தமிழில் நடைமுறை விவசாயப் பதிலை தெளிவாகக் கூறவும்."
        ),
        guidance_en=(
            "Provide a direct, practical, farmer-friendly answer in clear conversational language."
        ),
    )
