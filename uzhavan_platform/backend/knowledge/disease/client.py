"""
DiseaseService — HTTP client to the disease detection microservice (port 8001).

If the service is unavailable, returns a safe fallback with is_available=False
so the DiseaseAgent can report clearly instead of crashing.
"""
from __future__ import annotations

import os

import httpx

from backend.shared.models.disease import DiseaseResult, TNAUGuidance

_DISEASE_SERVICE_URL = os.getenv("DISEASE_SERVICE_URL", "http://localhost:8001")
_TIMEOUT_S = float(os.getenv("DISEASE_TIMEOUT_S", "15"))


class DiseaseService:
    """HTTP client to api/disease_detection running on port 8001."""

    async def predict(self, image_path: str) -> DiseaseResult:
        """
        Send an image file to the disease detection service.
        image_path must be a local file path accessible by this process.
        """
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
                with open(image_path, "rb") as f:
                    files = {"file": (os.path.basename(image_path), f, "image/jpeg")}
                    resp = await client.post(f"{_DISEASE_SERVICE_URL}/predict", files=files)
                resp.raise_for_status()
                data = resp.json()
                return DiseaseResult(
                    disease_label=data.get("disease", data.get("class_name", "unknown")),
                    crop=data.get("crop", self._infer_crop(data.get("disease", ""))),
                    confidence=float(data.get("confidence", 0.0)),
                    severity=self._map_severity(float(data.get("confidence", 0.0))),
                    image_path=image_path,
                )
        except FileNotFoundError:
            raise ValueError(f"Image file not found: {image_path}")
        except httpx.ConnectError:
            raise ConnectionError(
                f"Disease detection service not running at {_DISEASE_SERVICE_URL}. "
                "Start with: uvicorn api.disease_detection.main:app --port 8001"
            )
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Disease service error {exc.response.status_code}: {exc.response.text}")

    async def predict_bytes(self, image_bytes: bytes, filename: str = "image.jpg") -> DiseaseResult:
        """Send image bytes directly — used when image comes from multipart upload."""
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
                files = {"file": (filename, image_bytes, "image/jpeg")}
                resp = await client.post(f"{_DISEASE_SERVICE_URL}/predict", files=files)
                resp.raise_for_status()
                data = resp.json()
                return DiseaseResult(
                    disease_label=data.get("disease", data.get("class_name", "unknown")),
                    crop=data.get("crop", self._infer_crop(data.get("disease", ""))),
                    confidence=float(data.get("confidence", 0.0)),
                    severity=self._map_severity(float(data.get("confidence", 0.0))),
                    image_path=None,
                )
        except httpx.ConnectError:
            raise ConnectionError(
                f"Disease detection service not running at {_DISEASE_SERVICE_URL}."
            )

    async def get_guidance(self, disease_label: str, crop: str) -> TNAUGuidance:
        """Fetch TNAU treatment guidance for a disease from the knowledge endpoint."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{_DISEASE_SERVICE_URL}/disease/{disease_label}",
                    params={"crop": crop},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return TNAUGuidance(
                        disease_label=disease_label,
                        crop=crop,
                        symptoms=data.get("symptoms", ""),
                        chemical_control=data.get("chemical_control"),
                        biological_control=data.get("biological_control"),
                        cultural_practices=data.get("cultural_practices"),
                    )
        except Exception:
            pass
        # Fallback: generic guidance so the agent can still respond
        return TNAUGuidance(
            disease_label=disease_label,
            crop=crop,
            symptoms="நோய் அறிகுறிகள் கண்டறியப்பட்டுள்ளன.",
            chemical_control="TNAU பரிந்துரைப்படி பூச்சிக்கொல்லி தெளிக்கவும்.",
            biological_control=None,
            cultural_practices="நோய்வாய்ப்பட்ட இலைகளை அகற்றவும்.",
            source="TNAU Plant Protection Manual",
        )

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{_DISEASE_SERVICE_URL}/health")
                return resp.status_code == 200
        except Exception:
            return False

    @staticmethod
    def _map_severity(confidence: float) -> str:
        if confidence >= 0.80:
            return "high"
        if confidence >= 0.55:
            return "medium"
        return "low"

    @staticmethod
    def _infer_crop(disease_label: str) -> str:
        """Best-effort crop inference from disease label string."""
        label = disease_label.lower()
        for crop in ("apple", "cherry", "corn", "grape", "orange", "peach", "pepper",
                     "potato", "raspberry", "soybean", "squash", "strawberry", "tomato"):
            if crop in label:
                return crop
        return "unknown"
