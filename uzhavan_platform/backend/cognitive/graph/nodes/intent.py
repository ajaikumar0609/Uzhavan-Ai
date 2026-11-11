"""
Intent Router Node

Input:  ConversationState["context"] (user_message inside context.current_question)
Output: intent, intent_confidence, extracted_entities

One job: classify the question and extract Tamil agricultural entities.
No LLM. Pure rule-based Tamil keyword matching.

Intents: advisory | weather | disease | market | scheme | satellite | crop | off_topic
"""
from __future__ import annotations

import re
from typing import Any

from backend.cognitive.observability import observe

# ── Tamil / English keyword maps ──────────────────────────────────────────────

_INTENT_KEYWORDS: dict[str, list[str]] = {
    "weather": [
        "மழை", "வெயில்", "காலநிலை", "வானிலை", "வெதர்", "வெப்பம்", "ஈரப்பதம்", "குளிர்", "புயல்",
        "நாளை மழை", "மழை வருமா", "மழையா", "மழை பெய்யுமா", "மழை வாய்ப்பு", "இடி", "வானிலை எப்படி",
        "weather", "rain", "temperature", "humidity", "forecast",
    ],
    "disease": [
        "நோய்", "நோய்கள்", "பாதிப்பு", "பூச்சி", "கறுப்பு", "வெண்மை", "மஞ்சள்", "இலைப்புள்ளி", "இலை கருகல்", "பூஞ்சை",
        "செம்பழுப்பு", "டிசிஸ்", "டிசீஸ்", "blight", "blast", "disease", "diseases", "pest", "fungus", "leaf spot", "sigatoka",
    ],
    "market": [
        "விலை", "சந்தை", "கிலோ விலை", "market", "price", "rate", "கட்", "விற்பனை",
    ],
    "scheme": [
        "திட்டம்", "மானியம்", "subsidy", "scheme", "அரசு", "நிதி", "கடன்",
        "government", "loan", "PM-KISAN",
    ],
    "satellite": [
        "செயற்கைக்கோள்", "satellite", "sickle", "ndvi", "sentinel", "remote sensing",
    ],
    "crop": [
        "விதை", "seed", "விதைப்பு", "பயிர்", "சுழல்", "rotation", "பருவம்",
        "calendar", "எந்த பயிர்", "which crop", "நாற்று", "பயிர் சாகுபடி",
    ],
    "advisory": [
        "யூரியா", "urea", "உரம்", "fertilizer", "நீர்ப்பாசனம்", "irrigation",
        "தெளிப்பு", "spray", "சாகுபடி", "cultivation", "போட வேண்டுமா",
        "போடலாமா", "எப்போது", "எவ்வளவு", "பரிந்துரை",
        "பத்தி", "பற்றி", "சொல்றியா", "சொல்லுங்க", "சொல்", "விளக்கு", "விளக்கம்",
        "பராமரிப்பு", "வளர்ப்பு",
        "photosynthesis", "ஒளிச்சேர்க்கை", "npk", "botany", "தாவரவியல்",
        # English agronomy terms (previously only Tamil forms existed, so plain English
        # farming questions were wrongly classed off_topic).
        "soil", "yellow", "yellowing", "nutrient", "deficiency", "manure", "compost",
        "organic", "mulch", "leaves turning", "wilting", "stunted",
        # Tamil stems without the final virama, so inflected forms match
        # (e.g. "மஞ்சளாக" did not contain the keyword "மஞ்சள்" and was refused as off-topic).
        "மஞ்சள", "ஊட்டச்சத்து", "வளம்",   # specific stems only: broad ones (இலை/நெல்/மண்) outscored "நோய்"
    ],
}

_AGRI_VOCAB = (
    # English
    "soil", "crop", "paddy", "rice", "banana", "coconut", "sugarcane", "groundnut", "cotton", "seed",
    "nursery", "plant", "farm", "field", "harvest", "fertili", "manure", "compost", "pest", "weed",
    "yield", "sowing", "transplant", "mulch", "agricultur", "irrigat", "cultivat",
    # Tamil stems (no final virama so inflected forms match)
    "மண்", "நெல்", "பயிர்", "வாழை", "தென்னை", "கரும்பு", "நிலக்கடலை", "நாற்று", "நடவு", "நடு", "விதை",
    "வயல்", "நிலம்", "நிலத்", "உரம்", "உரங்", "பரிசோதன", "விவசாய", "அறுவடை", "களை", "பாசன",
    "சாகுபடி", "தாவர", "வளத்", "வளம்",
)

# Multi-intent detection: question contains BOTH weather AND fertilizer/irrigation
_COMBINED_ADVISORY_PAIRS = [
    ({"மழை", "rain", "forecast"}, {"யூரியா", "urea", "உரம்", "நீர்ப்பாசனம்", "irrigation"}),
]

# Tamil crop name → normalized English crop
_CROP_MAP: dict[str, str] = {
    "நெல்": "paddy", "நெல்லு": "paddy", "நெற்பயிர்": "paddy", "சம்பா": "paddy", "குறுவை": "paddy",
    "குருவிகார்": "paddy", "rice": "paddy", "paddy": "paddy",
    "பருத்தி": "cotton", "cotton": "cotton",
    "வாழை": "banana", "வாழைமரம்": "banana", "பனானா": "banana", "banana": "banana",
    "கரும்பு": "sugarcane", "sugarcane": "sugarcane",
    "நிலக்கடலை": "groundnut", "groundnut": "groundnut",
    "மக்காச்சோளம்": "maize", "corn": "maize", "maize": "maize",
    "தக்காளி": "tomato", "tomato": "tomato",
}

# Known Tamil Nadu districts (lowercase for matching)
_DISTRICTS: set[str] = {
    "thanjavur", "தஞ்சாவூர்", "tanjore",
    "tirunelveli", "திருநெல்வேலி", "nellai",
    "madurai", "மதுரை",
    "coimbatore", "கோயம்புத்தூர்",
    "erode", "ஈரோடு",
    "salem", "சேலம்",
    "tiruppur", "திருப்பூர்",
    "chennai", "சென்னை",
    "trichy", "திருச்சி", "tiruchirappalli",
    "vellore", "வேலூர்",
    "villupuram", "விழுப்புரம்",
    "cuddalore", "கடலூர்",
    "nagapattinam", "நாகப்பட்டினம்",
    "tiruvarur", "திருவாரூர்",
    "dindigul", "திண்டுக்கல்",
    "karur", "கரூர்",
    "namakkal", "நாமக்கல்",
    "dharmapuri", "தர்மபுரி",
    "krishnagiri", "கிருஷ்ணகிரி",
    "kancheepuram", "காஞ்சிபுரம்",
    "chengalpattu", "செங்கல்பட்டு",
    "ramanathapuram", "ராமநாதபுரம்",
    "sivaganga", "சிவகங்கை",
    "virudhunagar", "விருதுநகர்",
    "thoothukudi", "தூத்துக்குடி", "tuticorin",
    "kanyakumari", "கன்னியாகுமரி",
    "theni", "தேனி",
    "pudukkottai", "புதுக்கோட்டை",
    "ariyalur", "அரியலூர்",
    "perambalur", "பெரம்பலூர்",
    "nilgiris", "நீலகிரி",
}

# Tamil Nadu district name normalization
_DISTRICT_NORMALIZE: dict[str, str] = {
    "தஞ்சாவூர்": "Thanjavur", "tanjore": "Thanjavur",
    "திருநெல்வேலி": "Tirunelveli", "nellai": "Tirunelveli",
    "மதுரை": "Madurai",
    "கோயம்புத்தூர்": "Coimbatore",
    "ஈரோடு": "Erode",
    "சேலம்": "Salem",
    "திருப்பூர்": "Tiruppur",
    "சென்னை": "Chennai",
    "திருச்சி": "Trichy", "tiruchirappalli": "Trichy",
    "வேலூர்": "Vellore",
    "விழுப்புரம்": "Villupuram",
    "கடலூர்": "Cuddalore",
    "நாகப்பட்டினம்": "Nagapattinam",
    "திருவாரூர்": "Tiruvarur",
    "திண்டுக்கல்": "Dindigul",
    "கரூர்": "Karur",
    "நாமக்கல்": "Namakkal",
}


def _classify_intent(text: str) -> tuple[str, float]:
    text_lower = text.lower()
    scores: dict[str, int] = {}
    for intent, keywords in _INTENT_KEYWORDS.items():
        scores[intent] = sum(1 for kw in keywords if kw.lower() in text_lower)

    # Combined advisory: weather question + fertilizer/irrigation question together
    for weather_kws, action_kws in _COMBINED_ADVISORY_PAIRS:
        has_weather = any(kw in text_lower for kw in weather_kws)
        has_action = any(kw in text_lower for kw in action_kws)
        if has_weather and has_action:
            scores["advisory"] = scores.get("advisory", 0) + 3  # strong boost

    if not any(scores.values()):
        # Nothing matched an intent keyword. Before refusing as off-topic, check for plain farming
        # vocabulary: inflected Tamil ("மண் வளத்தை", "நடவுக்கு", "நாற்றங்காலை") and common English
        # farm words did not contain any stored keyword, so ordinary farming questions were refused
        # in 0.0 s. Only reached when no intent scored, so disease/market/weather routing is unchanged.
        if any(w in text_lower for w in _AGRI_VOCAB):
            return "advisory", 0.5
        return "off_topic", 0.3

    best = max(scores, key=lambda k: scores[k])
    best_score = scores[best]
    total = sum(scores.values())
    confidence = min(0.95, best_score / max(total, 1) + 0.3)
    return best, round(confidence, 2)


def _extract_entities(text: str) -> dict[str, Any]:
    entities: dict[str, Any] = {}

    # Crop
    for tamil, english in _CROP_MAP.items():
        if tamil in text:
            entities["crop"] = english
            break

    # District — also match declension forms (தஞ்சாவூரில் = locative of தஞ்சாவூர்)
    # Tamil nouns inflect: nominative ர் → accusative ரை, locative ரில் etc.
    # Stripping the final virama (்) gives the stem that appears in all cases.
    text_lower = text.lower()
    for district in _DISTRICTS:
        stem = district.rstrip("்")  # remove virama to get stem
        if district in text_lower or (stem != district and stem in text_lower):
            normalized = _DISTRICT_NORMALIZE.get(district, district.capitalize())
            entities["district"] = normalized
            break

    # Area in hectares — also handles Tamil locative suffix (ஹெக்டேரில் etc.)
    area_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hectare[s]?|ஹெக்டேர\S*|ha\b)", text, re.IGNORECASE)
    if area_match:
        entities["area_ha"] = float(area_match.group(1))

    # Rain in mm (e.g., "18 மிமீ", "18mm")
    rain_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:மிமீ|mm\b)", text, re.IGNORECASE)
    if rain_match:
        entities["rain_mm"] = float(rain_match.group(1))

    # Crop age in days (e.g., "45 நாள்", "45 days")
    age_match = re.search(r"(\d+)\s*(?:நாள்|நாட்கள்|நாளு|day[s]?)(?=[.,!?;:\s]|$)", text, re.IGNORECASE)
    if age_match:
        entities["crop_age_days"] = int(age_match.group(1))

    # Leaf symptom location (e.g., lower vs upper leaves)
    if any(w in text for w in ["கீழ் இலை", "அடி இலை", "பழைய இலை", "bottom leaf", "lower leaf"]):
        entities["symptom_location"] = "lower_leaves"
    elif any(w in text for w in ["மேல் இலை", "புதிய இலை", "குருத்து", "top leaf", "upper leaf"]):
        entities["symptom_location"] = "upper_leaves"

    # Symptom descriptions
    if any(w in text_lower for w in ["மஞ்சள்", "மஞ்சளா", "மஞ்சளாய்", "மஞ்சளாகுது", "மஞ்சளாகிறது", "மஞ்சளாக", "yellow"]):
        entities["symptom"] = "yellowing"
    elif any(w in text_lower for w in ["கருகல்", "காய்ந்து", "வாடி", "blight", "wilting", "drying"]):
        entities["symptom"] = "blight_drying"
    elif any(w in text_lower for w in ["புள்ளி", "spot"]):
        entities["symptom"] = "leaf_spot"
    elif any(w in text_lower for w in ["புழு", "பூச்சி", "துளை", "worm", "borer", "pest"]):
        entities["symptom"] = "pest_infestation"

    # Crop stage (simple keyword check)
    stage_map = {
        "நாற்று": "seedling", "seedling": "seedling",
        "வளர்ச்சி": "vegetative", "vegetative": "vegetative",
        "துரும்பு": "tillering", "tillering": "tillering",
        "பூக்கும்": "flowering", "flowering": "flowering",
        "அறுவடை": "harvest", "harvest": "harvest",
    }
    for keyword, stage in stage_map.items():
        if keyword in text:
            entities["crop_stage"] = stage
            break

    text_lower = text.lower()
    if any(w in text_lower for w in ["வாரம்", "week"]):
        entities["days"] = 7
    elif any(w in text_lower for w in ["நாளை", "tomorrow"]):
        entities["days"] = 2
    elif any(w in text_lower for w in ["இன்று", "இன்னைக்கு", "today"]):
        entities["days"] = 1

    return entities


async def intent_router(state: dict[str, Any]) -> dict[str, Any]:
    with observe("intent_router", state):
        ctx = state["context"]
        question = ctx.current_question or state.get("user_message", "")

        intent, confidence = _classify_intent(question)
        entities = _extract_entities(question)

        disease_ctx = state.get("disease_context")
        if disease_ctx and isinstance(disease_ctx, dict) and disease_ctx.get("crop"):
            entities["crop"] = str(disease_ctx["crop"]).lower()

        # Multi-turn conversational context resolution
        recent_turns = state.get("recent_turns") or []
        is_followup = any(w in question.lower() for w in [
            "என்ன செய்யணும்", "என்ன பண்ணனும்", "என்ன தீர்வு", "இப்போ என்ன",
            "what to do", "what should i do", "how to treat", "how to solve",
            "தீர்வு", "வழிமுறை", "மருந்து", "உரம்"
        ])
        if (intent == "off_topic" or confidence <= 0.4 or is_followup) and recent_turns:
            last_intent = None
            inherited_entities: dict[str, Any] = {}
            for t in reversed(recent_turns):
                t_intent = getattr(t, "intent", None)
                if t_intent and t_intent != "off_topic":
                    last_intent = t_intent
                    inherited_entities = getattr(t, "extracted_entities", {}) or {}
                    break
            has_followup_signal = (
                is_followup
                or "crop_age_days" in entities
                or "symptom" in entities
                or "symptom_location" in entities
                or len(question.strip()) < 50
            )
            if last_intent and has_followup_signal:
                intent = last_intent
                confidence = 0.88
                for k, v in inherited_entities.items():
                    if k not in entities or not entities[k]:
                        entities[k] = v

        # Deep multi-turn entity inheritance across all previous turns
        if recent_turns:
            for t in reversed(recent_turns):
                t_entities = getattr(t, "extracted_entities", {}) or {}
                for k in ("crop", "district", "crop_age_days", "symptom", "symptom_location", "crop_stage", "area_ha"):
                    if k in t_entities and (k not in entities or not entities[k]):
                        entities[k] = t_entities[k]

        # Fill in farm context defaults for any entity not found in text
        # If district is not specified in text, resolve from farm or farmer profile;
        # fallback to "Thanjavur" (Cauvery delta agricultural hub) so weather queries succeed.
        farm_values = {
            "crop": ctx.farm.crop if ctx.farm else None,
            "district": (ctx.farm.district if ctx.farm else None) or ctx.farmer.district or "Thanjavur",
            "area_ha": ctx.farm.area_ha if ctx.farm else None,
            "crop_stage": ctx.farm.crop_stage if ctx.farm else None,
        }
        for key, value in farm_values.items():
            if value is not None and value != "":
                entities.setdefault(key, value)

        output = {
            "intent": intent,
            "intent_confidence": confidence,
            "extracted_entities": entities,
        }
    # read trace AFTER observe.__exit__ has appended the new entry
    output["trace"] = state.get("trace", [])
    return output
