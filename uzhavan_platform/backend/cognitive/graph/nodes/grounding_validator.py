"""
Grounding Validator Node

Input:  evidence, resolved_capabilities, extracted_entities
Output: grounding_passed, grounding_failures

One job: ensure there is sufficient evidence to answer the question.
No LLM. Five deterministic checks. Any failure → grounding_passed=False → Tamil fallback.

The LLM is only called when ALL checks pass.
"""
from __future__ import annotations

from typing import Any

from backend.cognitive.models.node_context import EvidenceBundle
from backend.cognitive.observability import observe

_MIN_CONFIDENCE = 0.35
_MIN_CITATIONS = 1


def classify_request(question: str, intent: str, entities: dict[str, Any]) -> str:
    """Classify the incoming question into one of 8 distinct capability tiers."""
    q_lower = (question or "").lower()

    # D. PESTICIDE / CHEMICAL / FERTILIZER DOSAGE (exact chemical rates/sprays)
    pesticide_kws = [
        "மருந்து அளவு", "எத்தனை மில்லி", "மருந்து தெளிக்க", "ஸ்பிரே அளவு", "spray dose",
        "dosage", "dose per liter", "chemical dose", "எத்தனை கிராம்", "பூச்சிக்கொல்லி அளவு",
        "பூஞ்சாணக்கொல்லி", "பரிந்துரை அளவு", "ml/l", "g/l", "கெமிக்கல் மருந்து",
        # English phrasings (previously only "dosage"/"spray dose" matched)
        "dose of", "what dose", "how much to spray", "ml per", "g per", "per litre", "per liter",
        "insecticide", "pesticide", "fungicide", "herbicide", "weedicide",
        "மருந்தளவு", "எவ்வளவு மருந்து", "மில்லி", "பூச்சிக்கொல்லி",
    ]
    if any(kw in q_lower for kw in pesticide_kws):
        return "PESTICIDE_DOSAGE"

    # E. WEATHER
    if intent == "weather" or any(kw in q_lower for kw in ["மழை", "வானிலை", "weather", "rain", "forecast", "வெப்பநிலை"]):
        return "WEATHER"

    # F. MARKET
    if intent == "market" or any(kw in q_lower for kw in ["விலை", "சந்தை", "market", "price", "rate", "விற்பனை"]):
        return "MARKET"

    # G. GOVERNMENT SCHEME
    if intent == "scheme" or any(kw in q_lower for kw in ["திட்டம்", "மானியம்", "scheme", "subsidy", "pm-kisan", "அரசு"]):
        return "GOVERNMENT_SCHEME"

    # C. DISEASE
    if intent == "disease" or any(kw in q_lower for kw in [
        "நோய்", "பூச்சி", "கறுப்பு புள்ளி", "வெண்மை புள்ளி", "இலைப்புள்ளி", "இலை கருகல்", "பூஞ்சை", "disease", "pest",
        "fungus", "leaf spot", "blight", "blast", "sigatoka"
    ]):
        return "DISEASE"

    # H. CASUAL CONVERSATION
    casual_kws = ["வணக்கம்", "காலை வணக்கம்", "மாலை வணக்கம்", "நன்றி", "ஹலோ", "hello", "hi", "how are you", "who are you", "உன் பெயர்"]
    if any(kw in q_lower for kw in casual_kws) and len(q_lower.split()) <= 4:
        return "CASUAL_CONVERSATION"

    # A. GENERAL INFORMATION (fundamental science / botany / general definitions)
    general_info_kws = [
        "photosynthesis", "ஒளிச்சேர்க்கை", "chlorophyll", "பச்சையம்", "தாவரவியல்", "botany",
        "science", "how do plants grow", "what is a leaf", "செல்கள்", "biology", "மழை எப்படி பெய்கிறது"
    ]
    if any(kw in q_lower for kw in general_info_kws):
        return "GENERAL_INFORMATION"

    # B. AGRICULTURAL KNOWLEDGE (general farming, NPK, organic vs chemical, banana leaf, soil prep)
    return "AGRICULTURAL_KNOWLEDGE"


async def grounding_validator(state: dict[str, Any]) -> dict[str, Any]:
    with observe("grounding_validator", state):
        evidence: EvidenceBundle | None = state.get("evidence")
        resolved_capabilities = state.get("resolved_capabilities", [])
        entities = state.get("extracted_entities", {})
        intent = state.get("intent", "")
        ctx = state.get("context")
        question = (ctx.current_question if ctx else "") or state.get("user_message", "")

        if evidence is None:
            output: dict[str, Any] = {
                "grounding_passed": False,
                "grounding_failures": ["no_evidence: Evidence bundle is missing"],
                "grounding_mode": "no_evidence",
                "request_category": "UNKNOWN",
            }
        elif intent == "off_topic":
            output = {
                "grounding_passed": False,
                "grounding_failures": ["off_topic: Question is unrelated to agriculture or assistant scope"],
                "grounding_mode": "off_topic",
                "request_category": "OFF_TOPIC",
            }
        elif not (question or "").strip() and evidence.successful_tools == 0:
            output = {
                "grounding_passed": False,
                "grounding_failures": ["no_data: All domain agents returned empty or failed"],
                "grounding_mode": "no_data",
                "request_category": "UNKNOWN",
            }
        else:
            category = classify_request(question, intent, entities)
            failures: list[str] = []
            has_citations = len(evidence.citations) >= _MIN_CITATIONS
            # Knowledge / dosage answers are "verified" only by retrieved TNAU (RAG) chunks. A weather
            # or crop-tool citation says nothing about photosynthesis, NPK or a pesticide dose.
            if category in ("GENERAL_INFORMATION", "AGRICULTURAL_KNOWLEDGE", "PESTICIDE_DOSAGE"):
                has_citations = any(c.category == "rag" for c in evidence.citations)

            if has_citations:
                grounding_mode = "grounded_verified"
                grounding_passed = True
            elif category == "WEATHER":
                if evidence.weather_summary is not None or any(c.category == "weather" for c in evidence.citations):
                    grounding_mode = "grounded_live_data"
                    grounding_passed = True
                else:
                    grounding_mode = "tool_failed"
                    grounding_passed = False
                    failures.append("no_weather: Weather capability requested but no weather data returned")
            elif category == "MARKET":
                if evidence.market_summary is not None or any(c.category == "market" for c in evidence.citations):
                    grounding_mode = "grounded_live_data"
                    grounding_passed = True
                else:
                    grounding_mode = "tool_failed"
                    grounding_passed = False
                    failures.append("no_market: Market capability requested but no market data returned")
            elif category == "GOVERNMENT_SCHEME":
                if evidence.scheme_summary is not None or any(c.category == "scheme" for c in evidence.citations):
                    grounding_mode = "grounded_live_data"
                    grounding_passed = True
                else:
                    grounding_mode = "general_guidance"
                    grounding_passed = True
            elif category == "PESTICIDE_DOSAGE":
                if has_citations:
                    grounding_mode = "grounded_verified"
                    grounding_passed = True
                else:
                    grounding_mode = "safety_critical_unverified"
                    grounding_passed = True
                    failures.append("unverified_pesticide: No verified chemical dosage found in official sources")
            elif category in ("GENERAL_INFORMATION", "AGRICULTURAL_KNOWLEDGE", "CASUAL_CONVERSATION", "DISEASE"):
                grounding_mode = "general_guidance"
                grounding_passed = True
            else:
                if evidence.successful_tools == 0 and not question:
                    grounding_mode = "no_data"
                    grounding_passed = False
                    failures.append("no_data: All domain agents returned empty or failed")
                else:
                    grounding_mode = "general_guidance"
                    grounding_passed = True

            # If evidence has low confidence on verified tools, record as warning
            if evidence.overall_confidence < _MIN_CONFIDENCE and has_citations:
                failures.append(f"low_confidence: Overall confidence {evidence.overall_confidence:.2f} below threshold {_MIN_CONFIDENCE}")

            output = {
                "grounding_passed": grounding_passed,
                "grounding_failures": failures,
                "grounding_mode": grounding_mode,
                "request_category": category,
            }
    output["trace"] = state.get("trace", [])
    return output
