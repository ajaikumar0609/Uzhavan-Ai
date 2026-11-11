"""
POST /api/disease/scan: multipart `image` (+ optional `crop_id`), API contract §10.

Until the M4 disease model is independently approved (setting DISEASE_MODEL_APPROVED,
default false) this endpoint validates the upload and then answers
503 `model_unavailable`. It never calls the model service while the flag is false.

With a farmer token, a valid submission is logged to the diary as kind `scan`,
text "scan submitted" (never a result).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from backend.auth.deps import settings_dep
from backend.conversation.auth import get_farmer_id
from backend.diary.store import auto_log, get_diary_store_factory
from backend.meta.catalog import CROP_IDS
from backend.shared.api_errors import api_error
from backend.shared.settings import Settings

router = APIRouter(prefix="/api/disease", tags=["Disease"])

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
_MAX_FILE_SIZE_MB = 10


def model_unavailable(en: str = "The disease model is not yet approved for use. Please contact your local agriculture officer.") -> Exception:
    return api_error(503, "model_unavailable", en)


@router.post("/scan")
async def scan_disease(
    image: UploadFile = File(..., description="Crop leaf image (JPEG/PNG/WebP)"),
    crop_id: Optional[str] = Form(default=None),
    farmer_id: str = Depends(get_farmer_id),
    settings: Settings = Depends(settings_dep),
    diary_factory=Depends(get_diary_store_factory),
):
    content_type = (image.content_type or "").lower()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise api_error(415, "unsupported_media_type", "Unsupported image type. Use JPEG, PNG or WebP.")
    image_bytes = await image.read()
    if not image_bytes:
        raise api_error(400, "empty_image", "The image file is empty.")
    if len(image_bytes) > _MAX_FILE_SIZE_MB * 1024 * 1024:
        raise api_error(413, "image_too_large", f"Image too large. Maximum {_MAX_FILE_SIZE_MB} MB.")
    if crop_id is not None and crop_id not in CROP_IDS:
        raise api_error(400, "invalid_crop", "Unknown crop_id; see /api/meta/crops")

    # Defence in depth: the research-demo bypass is never honoured in production, even if
    # a Settings object was built without validate_for_env(). Falls through to the
    # fail-closed DISEASE_MODEL_APPROVED check below.
    if settings.M4_DEMO_MODE and not settings.is_production:
        from backend.disease.m4_client import ensure_m4_server_running, run_m4_inference
        target_crop = crop_id if crop_id in {"banana", "coconut", "groundnut", "sugarcane", "black_gram", "chilli"} else "groundnut"
        service_url = settings.DISEASE_SERVICE_URL or "http://127.0.0.1:8001"
        await ensure_m4_server_running(service_url)

        try:
            pred = await run_m4_inference(
                image_bytes=image_bytes,
                crop=target_crop,
                service_url=service_url,
                timeout_s=settings.DISEASE_TIMEOUT_S,
            )
        except Exception as exc:
            raise api_error(502, "inference_failed", f"M4 inference error: {exc}")

        await auto_log(
            diary_factory,
            farmer_id,
            "scan",
            f"M4 Research Demo: {pred['crop']} {pred['predicted_class']} ({round(pred['confidence'] * 100, 1)}%)",
            ref={
                "crop": pred["crop"],
                "crop_id": crop_id,
                "predicted_class": pred["predicted_class"],
                "confidence": pred["confidence"],
                "model_version": pred["model_version"],
                "experiment_id": pred["experiment_id"],
                "timestamp": pred["inference_timestamp"],
                "demo_mode": True,
                "production_certified": False,
            },
        )

        envelope_data = {
            "status": "demo_result",
            "crop": pred["crop"],
            "predicted_class": pred["predicted_class"],
            "confidence": pred["confidence"],
            "top3": pred["top3"],
            "model_architecture": pred["model_architecture"],
            "model_version": pred["model_version"],
            "experiment_id": pred["experiment_id"],
            "demo_mode": True,
            "production_certified": False,
            "inference_timestamp": pred["inference_timestamp"],
            "latency_ms": pred.get("latency_ms"),
            "top": {
                "class_id": pred.get("predicted_class_id", pred["predicted_class"]),
                "label": {"en": pred["predicted_class"].replace("_", " ").title(), "ta": None},
                "probability": pred["confidence"],
            },
            "predictions": [
                {
                    "class_id": t.get("class_id", t["class"]),
                    "label": {"en": t["class"].replace("_", " ").title(), "ta": None},
                    "probability": t["probability"],
                }
                for t in pred.get("top3", [])
            ],
            "inferred_at": pred["inference_timestamp"],
            "production_eligible": False,
        }

        return {
            **envelope_data,
            "data": envelope_data,
            "meta": {
                "source": "UZHAVAN M4 v1 Research Checkpoint",
                "source_url": None,
                "kind": "demo_inference",
                "retrieved_at": pred["inference_timestamp"],
                "notes": [
                    {
                        "en": "M4 v1 Research Demo — Not Production Certified",
                        "ta": "M4 v1 மாதிரி ஆய்வு செயல்முறை - உற்பத்திக்கான சான்றிதழ் பெறப்படவில்லை",
                    }
                ],
            },
        }

    await auto_log(diary_factory, farmer_id, "scan", "scan submitted",
                   ref={"crop_id": crop_id, "status": "model_unavailable"})

    if not settings.DISEASE_MODEL_APPROVED:
        raise model_unavailable()
    # Approved path: the contract §10 200 response (top/predictions/model_version/guidance
    # with cited sources) needs the approved M4 service's output schema, which does not
    # exist yet. Until it is wired and tested, answer honestly instead of guessing.
    raise model_unavailable("The approved disease model service is not connected yet.")
