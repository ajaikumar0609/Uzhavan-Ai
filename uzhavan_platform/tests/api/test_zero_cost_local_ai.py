"""Zero-paid-API / local-first policy tests.

Proves: no paid or external AI provider is reachable from the code or config; Ollama is the only
LLM; RAG works against a (copy of the) local ChromaDB and its citations are real; an Ollama outage
yields a local error, never a cloud call; exact chemical doses need evidence; unsourced answers are
labelled GENERAL GUIDANCE. Nothing here writes to the live ChromaDB store.
"""
import re
import shutil
import sqlite3
import types
from pathlib import Path

import httpx
import pytest

from backend.shared.models.citation import Citation
from backend.shared.models.service import ServiceMetadata, ServiceResult

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"

# Hostnames / SDKs of paid or third-party AI + speech services that must never appear in code.
BANNED_HOSTS = [
    "api.openai.com", "openai.azure.com", "api.anthropic.com", "generativelanguage.googleapis.com",
    "aiplatform.googleapis.com", "texttospeech.googleapis.com", "speech.googleapis.com",
    "translate.google", "api-inference.huggingface.co", "inference-endpoints", "api.cohere",
    "api.mistral.ai", "api.deepgram.com", "api.assemblyai.com", "api.elevenlabs.io",
    "bedrock-runtime", "api.groq.com", "api.together.xyz", "api.perplexity.ai",
]
BANNED_IMPORT = re.compile(
    r"^\s*(?:from|import)\s+(openai|anthropic|google\.generativeai|google\.genai|google\.cloud|gtts|"
    r"cohere|mistralai|groq|together|elevenlabs|deepgram|assemblyai|boto3|azure)\b", re.M)
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "testserver", "test"}


def _py_files():
    return [p for p in BACKEND.rglob("*.py") if "__pycache__" not in p.parts]


# ── static: no paid provider anywhere in code or requirements ───────────────────────────────────
def test_no_paid_ai_hosts_in_backend_code():
    hits = []
    for p in _py_files():
        text = p.read_text(encoding="utf-8", errors="ignore").lower()
        for h in BANNED_HOSTS:
            if h in text:
                hits.append(f"{p.relative_to(ROOT)}: {h}")
    assert not hits, hits


def test_no_external_ai_sdk_imports_in_backend_code():
    hits = [str(p.relative_to(ROOT)) for p in _py_files() if BANNED_IMPORT.search(p.read_text(encoding="utf-8", errors="ignore"))]
    assert not hits, hits


def test_requirements_list_no_paid_ai_packages():
    banned = ("openai", "anthropic", "google-generativeai", "google-genai", "google-cloud", "gtts",
              "cohere", "mistralai", "groq", "elevenlabs", "deepgram", "assemblyai", "boto3")
    for f in ROOT.glob("requirements*.txt"):
        for line in f.read_text().splitlines():
            line = line.split("#")[0].strip().lower()
            assert not line.startswith(banned), f"{f.name}: {line}"


def test_env_example_has_no_paid_provider_keys():
    text = (ROOT / ".env.example").read_text()
    for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS", "CLAUDE_MODEL", "OPENAI_MODEL"):
        assert name not in text
    assert "TTS_PROVIDER=gtts" not in text


def test_settings_define_no_paid_provider_fields():
    from backend.shared.settings import Settings
    fields = set(Settings.model_fields)
    assert not {"ANTHROPIC_API_KEY", "OPENAI_API_KEY", "CLAUDE_MODEL", "OPENAI_MODEL",
                "GOOGLE_APPLICATION_CREDENTIALS"} & fields
    assert Settings(ENV="test", JWT_SECRET="x").TTS_PROVIDER == "browser-only"


# ── LLM service: Ollama only, never a cloud call ────────────────────────────────────────────────
class _RecordingClient:
    """Stands in for httpx.AsyncClient: records every URL and fails like a down server."""
    urls: list = []

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, **k):
        _RecordingClient.urls.append(url)
        raise httpx.ConnectError("simulated: connection refused")

    async def get(self, url, **k):
        _RecordingClient.urls.append(url)
        raise httpx.ConnectError("simulated: connection refused")


@pytest.fixture
def down_http(monkeypatch):
    _RecordingClient.urls = []
    monkeypatch.setattr("backend.cognitive.llm.service.httpx.AsyncClient", _RecordingClient)
    return _RecordingClient


@pytest.mark.parametrize("provider", ["claude", "openai", "gemini", "anthropic"])
async def test_llm_service_refuses_external_providers_without_any_network_call(down_http, provider):
    from backend.cognitive.llm.service import LLMService
    r = await LLMService(provider=provider).generate("sys", "hello")
    assert r.success is False and r.content == ""
    assert "ollama" in (r.error or "").lower()
    assert down_http.urls == []          # nothing was even attempted


async def test_ollama_outage_gives_local_error_and_only_contacts_localhost(down_http):
    from urllib.parse import urlparse
    from backend.cognitive.llm.service import LLMService
    r = await LLMService(provider="ollama").generate("sys", "hello")
    assert r.success is False and r.provider == "ollama"
    assert "ollama" in (r.error or "").lower()
    assert down_http.urls, "expected one attempt against the local Ollama"
    assert {urlparse(u).hostname for u in down_http.urls} <= LOCAL_HOSTS


async def test_unsupported_provider_default_is_ollama_not_cloud(monkeypatch):
    import backend.cognitive.llm.service as svc
    assert svc.LLMService().provider_name() == "ollama" or svc._LLM_PROVIDER == "ollama"


def _ollama_up() -> bool:
    try:
        return httpx.get("http://127.0.0.1:11434/api/tags", timeout=2).status_code == 200
    except Exception:
        return False


@pytest.mark.skipif(not _ollama_up(), reason="local Ollama not running")
async def test_ollama_generates_locally():
    """Live check: a real local qwen2.5 completion over 127.0.0.1 (no data is stored)."""
    from backend.cognitive.llm.service import LLMService
    r = await LLMService(provider="ollama").generate("Answer in one short sentence.", "What colour are healthy rice leaves?")
    assert r.success and r.provider == "ollama" and r.content.strip()
    assert r.model.startswith("qwen2.5")


# ── whole conversation with Ollama down + external data down: no paid/cloud service is touched ──
async def test_conversation_with_ollama_and_data_down_never_uses_a_paid_service(api_client, monkeypatch, tmp_path):
    seen = []

    class Down(_RecordingClient):
        async def post(self, url, **k):
            seen.append(url)
            raise httpx.ConnectError("down")

        async def get(self, url, **k):
            seen.append(url)
            raise httpx.ConnectError("down")

    monkeypatch.setattr("httpx.AsyncClient", Down)
    monkeypatch.setattr("backend.cognitive.llm.service.httpx.AsyncClient", Down)
    # no embedding model / no live Chroma in this test
    monkeypatch.setattr("backend.knowledge.rag.engine._CHROMA_PATH", str(tmp_path / "empty_chroma"))
    monkeypatch.setattr("backend.knowledge.rag.engine.RAGService._lazy_embed", lambda self: None)
    r = await api_client.post("/conversation", json={"question": "What is NPK fertilizer?", "language": "English"})
    assert r.status_code == 200
    body = r.text
    assert "event: completed" in body
    # a clear local fallback, never a fabricated answer
    assert "TNAU help centre" in body or "is_fallback" in body
    from urllib.parse import urlparse
    hosts = {urlparse(u).hostname for u in seen}
    assert not any(b in (h or "") for h in hosts for b in ("openai", "anthropic", "googleapis", "google.com", "cohere")), hosts


# ── voice routes cannot send speech or text to a third party ────────────────────────────────────
async def test_voice_tts_is_unavailable_not_cloud(api_client, down_http):
    r = await api_client.post("/voice/tts", params={"text": "வணக்கம்", "language": "ta"})
    assert r.status_code == 503
    assert "on-device" in r.json()["detail"].lower()
    assert down_http.urls == []


async def test_voice_stt_is_disabled_by_default(api_client, down_http):
    r = await api_client.post("/voice/stt", files={"file": ("a.webm", b"x" * 500, "audio/webm")})
    assert r.status_code == 503
    assert down_http.urls == []


# ── RAG: regression for the ServiceResult bug, filters, and real-Chroma retrieval ──────────────
def _cite(title="Mineral Nutrition", conf=0.6):
    return Citation(source="TNAU", title=title, excerpt="Nitrogen deficiency turns leaves yellow.",
                    confidence=conf, category="rag")


class _FakeService:
    def __init__(self, items):
        self.items, self.calls = items, []

    async def retrieve(self, **kw):
        self.calls.append(kw)
        return ServiceResult(data=self.items, metadata=ServiceMetadata(source="chromadb", version="t", latency_ms=1))


def _ctx(question="Why are rice leaves turning yellow?", crop=None):
    farm = types.SimpleNamespace(crop=crop) if crop else None
    return types.SimpleNamespace(current_question=question, farm=farm, farmer=types.SimpleNamespace(district="Thanjavur"))


async def test_rag_agent_unwraps_service_result_and_returns_citations():
    """Regression: RAG used to fail with "'tuple' object has no attribute 'confidence'"."""
    from backend.tools.agents.rag_agent import RAGAgent
    svc = _FakeService([_cite(), _cite("Second", 0.5)])
    res = await RAGAgent(svc).execute("rag.advisory", _ctx(), {})
    assert res.success is True and res.error is None
    assert len(res.data) == 2 and len(res.citations) == 2
    assert 0.5 <= res.confidence <= 0.6


async def test_rag_agent_empty_result_is_success_with_no_citations_never_a_guess():
    from backend.tools.agents.rag_agent import RAGAgent
    res = await RAGAgent(_FakeService([])).execute("rag.advisory", _ctx(), {})
    assert res.success is True and res.data == [] and res.citations == [] and res.confidence == 0.0


def test_rag_crop_filter_uses_knowledge_base_names_plus_general():
    from backend.tools.agents.rag_agent import RAGAgent
    f = RAGAgent(_FakeService([]))._build_filters(_ctx(crop="paddy"), {})
    assert f == {"crop": {"$in": ["Rice", "Paddy", "General"]}}
    assert RAGAgent(_FakeService([]))._build_filters(_ctx(), {}) is None


def test_rag_lexical_terms_english_only():
    from backend.tools.agents.rag_agent import _lexical_terms
    assert _lexical_terms("What is photosynthesis?") == ["photos"]
    assert "npk" in _lexical_terms("What is NPK fertilizer?")
    assert _lexical_terms("நெல் இலை மஞ்சள்") is None       # Tamil: no lexical gate


LIVE_CHROMA = ROOT / "rag" / "chroma"


def _bge_cached() -> bool:
    return any(Path.home().glob(".cache/huggingface/hub/models--BAAI--bge-m3"))


@pytest.mark.skipif(not (LIVE_CHROMA / "chroma.sqlite3").exists() or not _bge_cached(),
                    reason="local TNAU Chroma store or bge-m3 not present")
async def test_rag_uses_local_chroma_and_citations_are_real_chunks(tmp_path, monkeypatch):
    """Works on a COPY of the store (the live one is never opened). Every citation's source/title
    must exist in the local collection's metadata: nothing invented."""
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    copy = tmp_path / "chroma"
    shutil.copytree(LIVE_CHROMA, copy)
    monkeypatch.setattr("backend.knowledge.rag.engine._CHROMA_PATH", str(copy))
    from backend.knowledge.rag.engine import RAGService
    from backend.tools.agents.rag_agent import _lexical_terms

    con = sqlite3.connect(f"file:{copy / 'chroma.sqlite3'}?mode=ro", uri=True)
    titles = {r[0] for r in con.execute("select string_value from embedding_metadata where key='title'")}
    assert con.execute("select count(*) from embeddings").fetchone()[0] >= 500
    q = "What is NPK fertilizer?"
    res = await RAGService().retrieve(q, top_k=6, score_threshold=0.45, must_match_terms=_lexical_terms(q))
    assert res.metadata.source == "chromadb"
    assert res.data, "expected at least one lexically and semantically relevant local chunk"
    for c in res.data:
        assert c.title in titles
        assert c.source == "TNAU" and c.confidence >= 0.45


@pytest.mark.skipif(not (LIVE_CHROMA / "chroma.sqlite3").exists() or not _bge_cached(),
                    reason="local TNAU Chroma store or bge-m3 not present")
async def test_unrelated_question_gets_no_citations_so_it_is_general_guidance(tmp_path, monkeypatch):
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    copy = tmp_path / "chroma"
    shutil.copytree(LIVE_CHROMA, copy)
    monkeypatch.setattr("backend.knowledge.rag.engine._CHROMA_PATH", str(copy))
    from backend.knowledge.rag.engine import RAGService
    from backend.tools.agents.rag_agent import _lexical_terms
    q = "What is photosynthesis?"
    res = await RAGService().retrieve(q, top_k=6, score_threshold=0.45, must_match_terms=_lexical_terms(q))
    assert res.data == []


# ── exact chemical doses need evidence (all grounding modes) ───────────────────────────────────
def _state(evidence_text="", mode="grounded_verified"):
    return {"user_prompt": evidence_text, "user_message": "", "context": None, "evidence": None,
            "tool_results": [], "grounding_mode": mode}


@pytest.mark.parametrize("mode", ["grounded_verified", "general_guidance", "safety_critical_unverified"])
@pytest.mark.parametrize("answer", [
    "Spray chlorpyrifos at 20 ml per liter of water.",
    "Mix 10 ml of neem oil in 1 litre.",
    "அளவு 5 மில்லி ஒரு லிட்டர் தண்ணீரில்.",
])
def test_invented_chemical_dose_is_blocked_in_every_mode(mode, answer):
    from backend.cognitive.graph.nodes.safety_validator import check_numeric_grounding
    failure = check_numeric_grounding(answer, _state("no dose given here", mode))
    assert failure and failure.startswith("unverified_chemical_dosage")


def test_dose_present_in_evidence_is_allowed():
    from backend.cognitive.graph.nodes.safety_validator import check_chemical_dosage_grounding
    ev = "TNAU: apply Pendimethalin 2.5 ml per litre of water within 3 days of sowing."
    assert check_chemical_dosage_grounding("Use 2.5 ml per litre.", _state(ev)) is None


def test_dose_questions_are_classified_as_pesticide_dosage():
    from backend.cognitive.graph.nodes.grounding_validator import classify_request
    for q in ("What dose of chlorpyrifos in ml per litre should I spray on paddy?",
              "Which insecticide for stem borer?"):
        assert classify_request(q, "disease", {}) == "PESTICIDE_DOSAGE"


# ── labelling: unsourced answers say so; "grounded" means evidence-backed ─────────────────────
def _fmt_state(mode, answer="Photosynthesis is how plants make food.", lang="English"):
    ctx = types.SimpleNamespace(system=types.SimpleNamespace(language=lang, trace_id="t"),
                                farmer=types.SimpleNamespace(language=lang))
    return {"raw_llm_response": answer, "evidence": None, "intent": "advisory", "context": ctx,
            "grounding_passed": True, "safety_passed": True, "is_fallback": False,
            "grounding_failures": [], "safety_failures": [], "grounding_mode": mode, "tool_results": []}


async def test_general_guidance_is_labelled_and_not_grounded():
    from backend.cognitive.graph.nodes.formatter import formatter
    out = await formatter(_fmt_state("general_guidance"))
    r = out["final_response"]
    assert r.answer.startswith("General guidance (not from TNAU sources): ")
    assert r.grounded is False and r.grounding_mode == "general_guidance"


async def test_general_guidance_tamil_label():
    from backend.cognitive.graph.nodes.formatter import formatter
    out = await formatter(_fmt_state("general_guidance", "ஒளிச்சேர்க்கை என்பது...", "Tamil"))
    assert out["final_response"].answer.startswith("பொது வழிகாட்டுதல் (TNAU ஆதாரம் இல்லாமல்): ")


async def test_verified_answer_is_grounded_and_unlabelled():
    from backend.cognitive.graph.nodes.formatter import formatter
    r = (await formatter(_fmt_state("grounded_verified")))["final_response"]
    assert r.grounded is True and not r.answer.startswith("General guidance")


async def test_fallback_is_never_grounded():
    from backend.cognitive.graph.nodes.formatter import formatter
    s = _fmt_state("grounded_verified"); s["is_fallback"] = True
    r = (await formatter(s))["final_response"]
    assert r.grounded is False and r.is_fallback is True and r.grounding_mode == ""


# ── intent: ordinary English / inflected-Tamil farming questions are no longer "off topic" ────
@pytest.mark.parametrize("q", [
    "Why are rice leaves turning yellow?", "How can I improve soil health?",
    "நெல் இலைகள் மஞ்சளாக மாறுவது ஏன்?",
])
def test_farming_questions_are_not_off_topic(q):
    from backend.cognitive.graph.nodes.intent import _classify_intent
    assert _classify_intent(q)[0] != "off_topic"


def test_unrelated_small_talk_is_still_off_topic():
    from backend.cognitive.graph.nodes.intent import _classify_intent
    assert _classify_intent("Who won the cricket match yesterday?")[0] == "off_topic"


# ── dose must be backed by the same number AND unit (a bare "2" in the evidence proves nothing) ─
def test_bare_number_in_evidence_does_not_validate_a_dose():
    from backend.cognitive.graph.nodes.safety_validator import check_chemical_dosage_grounding
    ev = "Sown on 2 hectares; seed rate 12 kg; irrigate 2 times."
    assert check_chemical_dosage_grounding("Spray chlorpyrifos at 2 ml per liter.", _state(ev))


def test_dose_unit_must_match_evidence_unit():
    from backend.cognitive.graph.nodes.safety_validator import check_chemical_dosage_grounding
    assert check_chemical_dosage_grounding("Use 2 g per litre.", _state("Apply 2 ml/lit of water"))


def test_tool_fact_fertiliser_rate_is_accepted():
    from backend.cognitive.graph.nodes.safety_validator import check_chemical_dosage_grounding
    assert check_chemical_dosage_grounding("Apply 120 kg/ha nitrogen.", _state("TNAU base N 120 kg/ha")) is None


def test_disease_question_with_tamil_leaf_word_stays_disease():
    """Regression: broad Tamil stems (இலை/நெல்) once turned this into 'advisory'."""
    from backend.cognitive.graph.nodes.intent import _classify_intent
    assert _classify_intent("நெல் இலையில் நோய் இருக்கிறது. என்ன செய்வது?")[0] == "disease"


# ── NPK / definition questions, derived field totals, Tamil vocabulary, truncated tails ──────────
@pytest.mark.parametrize("q", [
    "What is NPK fertilizer?", "Explain the importance of crop rotation.", "What are macronutrients?",
    "NPK உரம் என்றால் என்ன?", "பயிர் சுழற்சியின் முக்கியத்துவம் என்ன?",
])
def test_definition_questions_are_definitional(q):
    from backend.cognitive.graph.nodes.definitional import is_definitional
    assert is_definitional(q)


@pytest.mark.parametrize("q", [
    "What dose of urea per acre?", "How much NPK should I apply?", "What is NPK for my farm?",
    "Why are rice leaves turning yellow?", "NPK உரம் எவ்வளவு போட வேண்டும்?", "Calculate urea for 2 acres",
])
def test_quantity_or_farm_questions_are_not_definitional(q):
    from backend.cognitive.graph.nodes.definitional import is_definitional
    assert not is_definitional(q)


def test_definition_question_plans_rag_only_but_quantity_question_keeps_all_tools():
    from backend.cognitive.graph.nodes.planner import _build_requests
    only = _build_requests("advisory", {}, "What is NPK fertilizer?")
    assert [r.capability_name for r in only] == ["rag.advisory"]
    full = _build_requests("advisory", {}, "How much NPK should I apply?")
    assert "crop.fertilizer_plan" in [r.capability_name for r in full]
    assert "weather.irrigation_advice" in [r.capability_name for r in full]


async def test_definition_prompt_forbids_field_quantities():
    from backend.cognitive.graph.nodes.prompt_builder import prompt_builder
    from backend.cognitive.models.node_context import EvidenceBundle
    ctx = types.SimpleNamespace(
        current_question="What is NPK fertilizer?", farm=None,
        system=types.SimpleNamespace(language="English", trace_id="t"),
        farmer=types.SimpleNamespace(language="English", district="Thanjavur"),
        conversation_history=[])
    out = await prompt_builder({"context": ctx, "evidence": EvidenceBundle(), "intent": "advisory",
                                "grounding_mode": "general_guidance", "extracted_entities": {}})
    assert "Definition question" in out["system_prompt"]
    assert "Do NOT calculate" in out["system_prompt"]


def _dstate(evidence):
    return {"user_prompt": evidence, "user_message": "", "context": None, "evidence": None, "tool_results": []}


def test_dose_guard_accepts_total_derived_from_evidence_rate_times_area():
    from backend.cognitive.graph.nodes.safety_validator import check_chemical_dosage_grounding as g
    ev = "[Farm: Crop: banana, Area: 1.214 ha] TNAU base N 200 kg/ha, P 60 kg/ha"
    assert g("For your 1.214 ha that is 242.8 kg of nitrogen per hectare equivalent.", _dstate(ev)) is None


def test_dose_guard_still_blocks_invented_and_pesticide_doses_even_with_a_rate_in_evidence():
    from backend.cognitive.graph.nodes.safety_validator import check_chemical_dosage_grounding as g
    ev = "[Farm: Crop: banana, Area: 1.214 ha] TNAU base N 200 kg/ha"
    assert g("Apply 300 kg of nitrogen per ha.", _dstate(ev))               # not rate x area
    assert g("Spray chlorpyrifos at 2 ml per litre.", _dstate(ev))          # pesticide: never derived
    assert g("Apply 242.8 g of nitrogen per ha.", _dstate(ev))              # wrong unit family


def test_derived_total_needs_both_a_rate_and_an_area_in_the_evidence():
    from backend.cognitive.graph.nodes.safety_validator import check_chemical_dosage_grounding as g
    assert g("That is 242.8 kg of nitrogen per ha.", _dstate("TNAU base N 200 kg/ha"))          # no area
    assert g("That is 242.8 kg of nitrogen per ha.", _dstate("Area: 1.214 ha"))                 # no rate


@pytest.mark.parametrize("q", [
    "மண் வளத்தை எப்படி மேம்படுத்தலாம்?", "வாழை நடவுக்கு நிலத்தை எப்படி தயார் செய்வது?",
    "நெல் நாற்றங்காலை எப்படி தயாரிப்பது?", "மண் பரிசோதனை ஏன் செய்ய வேண்டும்?",
])
def test_inflected_tamil_farming_questions_are_not_refused(q):
    from backend.cognitive.graph.nodes.intent import _classify_intent
    assert _classify_intent(q)[0] != "off_topic"


def test_vocabulary_fallback_does_not_steal_scored_intents_or_admit_small_talk():
    from backend.cognitive.graph.nodes.intent import _classify_intent
    assert _classify_intent("நெல் இலையில் நோய் இருக்கிறது. என்ன செய்வது?")[0] == "disease"
    assert _classify_intent("இன்று நெல் விலை என்ன?")[0] == "market"
    assert _classify_intent("Who won the cricket match yesterday?")[0] == "off_topic"


def test_trim_incomplete_tail_drops_only_the_unfinished_sentence():
    from backend.cognitive.graph.nodes.llm_node import trim_incomplete_tail as t
    assert t("Nitrogen helps leaves grow. Phosphorus helps ro") == "Nitrogen helps leaves grow."
    assert t("நல்ல பதில் இது. இது முழுமையற்ற வாக்கி") == "நல்ல பதில் இது."
    assert t("Complete sentence.") == "Complete sentence."
    assert t("No terminator at all here") == "No terminator at all here"     # nothing complete to keep
    assert t("") == ""
