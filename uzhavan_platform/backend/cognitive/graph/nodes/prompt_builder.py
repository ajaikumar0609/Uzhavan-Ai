"""
Prompt Builder Node

Input:  evidence, context, intent
Output: system_prompt, user_prompt

One job: assemble the LLM prompts from markdown templates and evidence.
All templates live in backend/cognitive/prompts/*.md — never inline Python strings.
Qwen3 receives only what is in these prompts. Nothing else.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.cognitive.graph.nodes.definitional import (
    DEFINITIONAL_INSTRUCTION_EN,
    DEFINITIONAL_INSTRUCTION_TA,
    is_definitional,
)
from backend.cognitive.models.node_context import EvidenceBundle
from backend.cognitive.observability import observe
from backend.cognitive.voice.emotion_analyzer import analyze_conversational_state

_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def _load_template(name: str) -> str:
    path = _PROMPTS_DIR / f"{name}.md"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _build_evidence_block(evidence: EvidenceBundle) -> str:
    sections: list[str] = []
    if evidence.facts:
        # FP-015: the tool values (with source/date) or explicit "not available" lines.
        sections.append("**Facts from tools (use only these values)**:")
        for fact in evidence.facts:
            sections.append(f"  - {fact}")
    if evidence.weather_summary:
        sections.append(f"**Weather**: {evidence.weather_summary}")
    if evidence.crop_summary:
        sections.append(f"**Crop guidance**: {evidence.crop_summary}")
    if evidence.disease_summary:
        sections.append(f"**Disease**: {evidence.disease_summary}")
    if evidence.market_summary:
        sections.append(f"**Market**: {evidence.market_summary}")
    if evidence.scheme_summary:
        sections.append(f"**Scheme**: {evidence.scheme_summary}")
    if evidence.rag_excerpts:
        sections.append("**TNAU Knowledge Base**:")
        for excerpt in evidence.rag_excerpts:
            sections.append(f"  - {excerpt}")
    if evidence.citations:
        sections.append("\n**Sources**:")
        for c in evidence.citations[:6]:
            sections.append(f"  - [{c.source}] {c.title} (confidence: {c.confidence:.0%})")
    if evidence.conflict_warnings:
        sections.append("\n**Warnings**:")
        for w in evidence.conflict_warnings:
            sections.append(f"  - {w}")
    return "\n".join(sections) if sections else "No structured evidence available."


def farm_line(context) -> str:
    """FP-015: the farm context shown to the LLM. A missing field is stated as "not recorded"
    (never a default), so the model cannot silently assume an area, stage or district."""
    if not context.farm:
        return ""
    f = context.farm

    def val(v, unit: str = "") -> str:
        return "not recorded" if v is None or v == "" else f"{v}{unit}"

    parts = [f"Crop: {val(f.crop)}", f"Stage: {val(f.crop_stage)}", f"Area: {val(f.area_ha, ' ha')}",
             f"District: {val(f.district or context.farmer.district)}"]
    return f"\n[Farm: {', '.join(parts)}]"


def _build_dialog_history(state: dict[str, Any], context: Any, is_tamil: bool) -> str:
    recent_turns = state.get("recent_turns") or []
    history_lines: list[str] = []
    if recent_turns:
        for t in recent_turns[-3:]:
            q = getattr(t, "question", "")
            a = getattr(t, "answer", "")
            if q:
                history_lines.append(f"விவசாயி: {q}" if is_tamil else f"Farmer: {q}")
            if a:
                # Keep preview concise to preserve LLM token context
                history_lines.append(f"உழவன்: {a[:160]}..." if is_tamil else f"Uzhavan: {a[:160]}...")
    elif context.conversation_history:
        for msg in context.conversation_history[-4:]:
            role_label = ("விவசாயி" if msg.role == "user" else "உழவன்") if is_tamil else ("Farmer" if msg.role == "user" else "Uzhavan")
            history_lines.append(f"{role_label}: {msg.content[:160]}")

    return "\n".join(history_lines) if history_lines else ("முந்தைய தகவல்கள் ஏதுமில்லை (புதிய உரையாடல்)." if is_tamil else "No prior turns in this session.")


async def prompt_builder(state: dict[str, Any]) -> dict[str, Any]:
    with observe("prompt_builder", state):
        evidence: EvidenceBundle | None = state.get("evidence")
        context = state["context"]
        intent: str = state.get("intent", "advisory")
        question: str = context.current_question
        language = context.system.language or context.farmer.language or "Tamil"
        is_tamil = language.lower().startswith("ta")

        # Conversational tone & emotional guidance
        tone = analyze_conversational_state(question)
        tone_guidance = tone.guidance_ta if is_tamil else tone.guidance_en

        # Dialog history from prior turns
        dialog_history = _build_dialog_history(state, context, is_tamil)

        grounding_mode = state.get("grounding_mode", "general_guidance")
        category = state.get("request_category", "AGRICULTURAL_KNOWLEDGE")

        if grounding_mode == "general_guidance":
            mode_instruction = (
                "### பொதுவான வழிகாட்டுதல் முறை (General Guidance Mode):\n"
                "- விவசாயியின் கேள்விக்கான பொதுவான அறிவியல் மற்றும் வேளாண்மை கருத்துக்களை (Photosynthesis, ஒளிச்சேர்க்கை, இலை அமைப்பு, தாவரவியல், NPK விகிதங்கள், மண் தயாரிப்பு, பொது சாகுபடி முறைகள்) எளிய, தெளிவான, இயல்பான பேச்சுத்தமிழில் விளக்கவும்.\n"
                "- TNAU அல்லது ஆய்வக ஆவணம் நேரடியாக கிடைக்காத பொதுவான அறிவியல்/வேளாண் அடிப்படைக் கேள்விகளுக்கு 'ஆதாரம் இல்லை', 'TNAU-வை அணுகவும்' என்று தேவையின்றி மறுக்காமல், பயனுள்ள அறிவை அன்புடன் வழங்கவும்.\n"
                "- ஆனால், சரிபார்க்கப்படாத ரசாயன பூச்சிக்கொல்லி / பூஞ்சாணக்கொல்லி மருந்து தெளிப்பு அளவுகளை (specific chemical dosages in ml/L or g/L) நீங்களாக உருவாக்க வேண்டாம். பாதுகாப்பான இயற்கை முறைகளை (வேப்ப எண்ணெய் கரைசல், வடிகால்) மட்டும் கூறவும்."
            )
        elif grounding_mode == "safety_critical_unverified":
            mode_instruction = (
                "### சரிபார்க்கப்படாத ரசாயன மருந்து எச்சரிக்கை (Safety-Critical Mode):\n"
                "- விவசாயி ரசாயன பூச்சிக்கொல்லி/மருந்து தெளிப்பு அளவைக் கேட்கிறார், ஆனால் நமது தரவுத்தளத்தில் இந்த குறிப்பிட்ட சூழலுக்கான அதிகாரப்பூர்வ பரிந்துரை அளவு தற்போது இல்லை.\n"
                "- பயிர்களுக்கு நச்சுத்தன்மை அல்லது சேதம் ஏற்படுவதைத் தவிர்க்க, நீங்களாக ரசாயன மருந்து தெளிப்பு அளவுகளை (chemical ml/L or g/L) உருவாக்கக் கூடாது.\n"
                "- ரசாயன மருந்தின் சரியான அளவை அறிய அருகில் உள்ள வேளாண்மை அலுவலர் அல்லது TNAU உதவி மையத்தை (0431-2371622) அணுகுமாறு அன்புடன் வழிகாட்டவும்.\n"
                "- அதே நேரத்தில், பாதுகாப்பான இயற்கை முறை அல்லது வயல் சுகாதாரம் போன்ற முதலுதவி வழிகளை கூறலாம்."
            )
        else:
            mode_instruction = (
                "### அதிகாரப்பூர்வ ஆதாரம் (Verified Grounded Mode):\n"
                "- கீழே உள்ள உழவன் AI ஆதாரங்கள் மற்றும் TNAU வழிகாட்டுதலை மட்டுமே முழுமையாக அடிப்படையாகக் கொண்டு விவசாயிக்குத் துல்லியமான பதிலை வழங்கவும்."
            )

        if is_definitional(question):
            mode_instruction += DEFINITIONAL_INSTRUCTION_TA if is_tamil else DEFINITIONAL_INSTRUCTION_EN

        system_template = _load_template("system")
        evidence_block = _build_evidence_block(evidence) if evidence else "No evidence available."

        system_prompt = system_template.format(
            language=language,
            mode_instruction=mode_instruction,
            evidence_block=evidence_block,
            tone_guidance=tone_guidance,
            dialog_history=dialog_history,
        )

        farm_info = farm_line(context)
        extracted = state.get("extracted_entities", {}) or {}
        context_parts = []
        if extracted.get("crop") and (not context.farm or not context.farm.crop):
            context_parts.append(f"Crop: {extracted['crop']}")
        if extracted.get("crop_age_days"):
            context_parts.append(f"Crop Age: {extracted['crop_age_days']} days")
        if extracted.get("symptom_location"):
            context_parts.append(f"Symptom Location: {extracted['symptom_location']}")

        extra_info = f"\n[Context: {', '.join(context_parts)}]" if context_parts else ""

        # The mode instructions above are written in Tamil, which pulled English requests into
        # Tamil answers; state the output language explicitly in the user turn as well.
        language_rule = (
            "\n[தமிழில் மட்டும், எளிய பேச்சுத்தமிழில், அதிகபட்சம் 3 சிறிய வாக்கியங்களில் பதிலளிக்கவும். "
            "முதலில் நேரடி பதில், பிறகு ஒரு செய்ய வேண்டிய செயல். ஒவ்வொரு வாக்கியமும் முழுமையாக முடிய வேண்டும்.]" if is_tamil
            else "\n[Reply in English only. Do not use Tamil script.]"
        )
        output = {
            "system_prompt": system_prompt,
            "user_prompt": f"{question}{farm_info}{extra_info}{language_rule}",
        }
    output["trace"] = state.get("trace", [])
    return output
