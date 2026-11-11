from __future__ import annotations

import time
from typing import Any, Literal

from backend.knowledge.disease.client import DiseaseService
from backend.shared.agents.base import BaseDomainAgent
from backend.shared.models.citation import Citation
from backend.shared.models.context import ConversationContext
from backend.shared.models.disease import DiseaseContext, DiseaseResult, TNAUGuidance
from backend.shared.models.tool import AgentManifest, ToolCapability, ToolResult


class DiseaseAgent(BaseDomainAgent):
    """
    Owns all agricultural reasoning about plant disease.
    predict() calls ML service; treatment/prevention/severity are pure agricultural reasoning.
    """

    VERSION = "1.0"
    _CAPABILITIES = ["identify", "predict", "severity", "organic_treatment", "chemical_treatment", "prevention"]

    # FP-015 / contract §10: no diagnosis until the M4 model is approved AND its service is wired.
    UNAVAILABLE_FACT = ("Disease identification is not available: the disease detection model is not yet "
                        "approved for use, so UZHAVAN cannot diagnose a disease. Contact the local agriculture officer.")
    UNAVAILABLE_TAMIL = ("நோய் கண்டறிதல் தற்போது கிடைக்கவில்லை: நோய் கண்டறியும் மாதிரி இன்னும் அங்கீகரிக்கப்படவில்லை. "
                         "உள்ளூர் வேளாண் அலுவலரை தொடர்பு கொள்ளவும்.")

    def __init__(self, service: DiseaseService | None = None) -> None:
        self._service = service or DiseaseService()

    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_name="disease",
            version=self.VERSION,
            description="Plant disease identification and TNAU-grounded treatment recommendations",
            avg_latency_ms=800,
            typical_confidence=0.82,
            feature_flag="ENABLE_DISEASE",
            dependencies=["disease-detection-service", "postgresql"],
            capabilities=[
                ToolCapability(name="identify", description="Disease identification status (model_unavailable until approved)", avg_latency_ms=5),
                ToolCapability(name="predict", description="Identify plant disease from leaf image", avg_latency_ms=1200),
                ToolCapability(name="severity", description="Assess disease severity from confidence score", avg_latency_ms=50),
                ToolCapability(name="organic_treatment", description="Organic/biological disease control from TNAU", avg_latency_ms=200),
                ToolCapability(name="chemical_treatment", description="Chemical pesticide recommendation from TNAU", avg_latency_ms=200),
                ToolCapability(name="prevention", description="Preventive measures based on crop stage", avg_latency_ms=200),
            ],
        )

    def can_handle(self, capability_name: str) -> bool:
        parts = capability_name.split(".", 1)
        return len(parts) == 2 and parts[0] == "disease" and parts[1] in self._CAPABILITIES

    async def execute(
        self, capability_name: str, context: ConversationContext, params: dict[str, Any]
    ) -> ToolResult:
        start_ns = time.monotonic_ns()
        _, method = capability_name.split(".", 1)
        try:
            if method in ("identify", "predict", "severity") and not self._model_approved():
                return self._model_unavailable(capability_name, start_ns)
            if method == "identify":
                # Approved flag alone is not enough: the approved service schema is not wired yet.
                return self._model_unavailable(capability_name, start_ns)
            if method == "predict":
                return await self._predict(start_ns, params.get("image_path", ""))
            elif method == "severity":
                confidence = float(params.get("confidence", 0.5))
                return self._severity(start_ns, capability_name, confidence)
            elif method == "organic_treatment":
                disease = params.get("disease_label", "")
                crop = params.get("crop", context.farm.crop if context.farm else "unknown")
                return await self._organic_treatment(start_ns, disease, crop)
            elif method == "chemical_treatment":
                disease = params.get("disease_label", "")
                crop = params.get("crop", context.farm.crop if context.farm else "unknown")
                return await self._chemical_treatment(start_ns, disease, crop)
            elif method == "prevention":
                disease = params.get("disease_label", "")
                stage = params.get("crop_stage") or (context.farm.crop_stage if context.farm else None)
                return self._prevention(start_ns, disease, stage)
            else:
                return self._timed_result(capability_name, start_ns, False, error=f"Unknown method: {method}")
        except NotImplementedError:
            return self._timed_result(capability_name, start_ns, False, error="Disease service not yet implemented (Phase D)")
        except Exception as exc:
            return self._timed_result(capability_name, start_ns, False, error=str(exc))

    async def _predict(self, start_ns: int, image_path: str) -> ToolResult:
        if not image_path:
            return self._timed_result("disease.predict", start_ns, False, error="image_path required for disease prediction")
        result = await self._service.predict(image_path)
        guidance = await self._service.get_guidance(result.disease_label, result.crop)
        ctx = DiseaseContext(result=result, guidance=guidance)
        severity_label = self._compute_severity(result.confidence)
        citation = Citation(
            source="TNAU Plant Protection Manual",
            title=f"{result.disease_label} — {result.crop}",
            excerpt=guidance.symptoms[:200] if guidance else f"Detected {result.disease_label} with {result.confidence:.0%} confidence.",
            confidence=result.confidence,
            category="disease",
        )
        return self._timed_result("disease.predict", start_ns, True, data=ctx, citations=[citation], confidence=result.confidence)

    @staticmethod
    def _model_approved() -> bool:
        from backend.shared.settings import get_settings
        return bool(get_settings().DISEASE_MODEL_APPROVED)

    def _model_unavailable(self, capability_name: str, start_ns: int) -> ToolResult:
        data = {"status": "model_unavailable", "diagnosis": None,
                "facts": [self.UNAVAILABLE_FACT], "message_tamil": self.UNAVAILABLE_TAMIL}
        return self._timed_result(capability_name, start_ns, True, data=data, confidence=0.9)

    def _severity(self, start_ns: int, capability_name: str, confidence: float) -> ToolResult:
        label = self._compute_severity(confidence)
        data = {
            "severity": label,
            "confidence": confidence,
            "action_urgency": {"low": "Monitor closely", "medium": "Treat within 3 days", "high": "Treat immediately"}[label],
            "action_urgency_tamil": {"low": "கவனமாக கண்காணிக்கவும்", "medium": "3 நாட்களுக்குள் சிகிச்சை செய்யவும்", "high": "உடனடியாக சிகிச்சை செய்யவும்"}[label],
        }
        return self._timed_result(capability_name, start_ns, True, data=data, confidence=0.95)

    async def _organic_treatment(self, start_ns: int, disease: str, crop: str) -> ToolResult:
        guidance = await self._service.get_guidance(disease, crop)
        if not guidance or not guidance.biological_control:
            return self._timed_result("disease.organic_treatment", start_ns, False, error=f"No organic treatment data for {disease}")
        data = {
            "disease": disease,
            "crop": crop,
            "organic_treatment": guidance.biological_control,
            "cultural_practices": guidance.cultural_practices,
        }
        citation = Citation(source=guidance.source, title=f"Organic Control — {disease}", excerpt=guidance.biological_control[:200], confidence=0.88, category="disease")
        return self._timed_result("disease.organic_treatment", start_ns, True, data=data, citations=[citation], confidence=0.88)

    async def _chemical_treatment(self, start_ns: int, disease: str, crop: str) -> ToolResult:
        guidance = await self._service.get_guidance(disease, crop)
        if not guidance or not guidance.chemical_control:
            return self._timed_result("disease.chemical_treatment", start_ns, False, error=f"No chemical treatment data for {disease}")
        data = {
            "disease": disease,
            "crop": crop,
            "chemical_treatment": guidance.chemical_control,
            "warning": "Follow label instructions. Use protective equipment.",
            "warning_tamil": "பயன்பாட்டு அறிவுரைகளை பின்பற்றவும். பாதுகாப்பு உபகரணங்கள் அணியவும்.",
        }
        citation = Citation(source=guidance.source, title=f"Chemical Control — {disease}", excerpt=guidance.chemical_control[:200], confidence=0.85, category="disease")
        return self._timed_result("disease.chemical_treatment", start_ns, True, data=data, citations=[citation], confidence=0.85)

    def _prevention(self, start_ns: int, disease: str, stage: str | None) -> ToolResult:
        """
        Stage-aware disease prevention reasoning.
        Key principle: prevention is cheaper than treatment at early crop stages.
        """
        early_stages = {"seedling", "vegetative", "tillering"}
        prevention_measures = self._get_prevention_measures(disease, stage in early_stages)
        data = {
            "disease": disease,
            "crop_stage": stage,
            "prevention_measures": prevention_measures,
            "timing_note": "Early application is most effective before symptoms appear.",
            "timing_note_tamil": "அறிகுறிகள் தோன்றுவதற்கு முன்பே தடுப்பு நடவடிக்கை மிகவும் பயனுள்ளது.",
        }
        return self._timed_result("disease.prevention", start_ns, True, data=data, confidence=0.80)

    # ── Agricultural reasoning ────────────────────────────────────────────────

    def _compute_severity(self, confidence: float) -> Literal["low", "medium", "high"]:
        if confidence >= 0.80:
            return "high"
        elif confidence >= 0.55:
            return "medium"
        return "low"

    def _get_prevention_measures(self, disease: str, is_early_stage: bool) -> list[str]:
        base = [
            "Use certified disease-free seeds",
            "Maintain field sanitation — remove crop debris",
            "Ensure proper spacing for air circulation",
        ]
        if is_early_stage:
            base.append("Seed treatment before sowing as per the TNAU crop production guide")
        else:
            base.append("Scout field weekly for early symptom detection")
        return base

    async def health(self) -> bool:
        return await self._service.health()
