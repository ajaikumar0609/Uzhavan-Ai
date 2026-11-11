"""
UZHAVAN AI — Plant Disease Detection Microservice
==================================================
Enhanced FastAPI service wrapping the MobileNetV2 plant disease model
(linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification / 38 classes).

New endpoints added over the original backend:
  POST /batch_predict          — predict on multiple images
  GET  /supported_crops        — list all detectable crop species
  GET  /supported_diseases     — list all detectable diseases + TNAU guidance
  GET  /disease/{name}         — TNAU treatment detail for a specific disease

All original endpoints kept:
  POST /predict                — single image prediction (with TNAU guidance appended)
  GET  /history                — prediction log
  GET  /health                 — readiness check
  GET  /model-info             — model metadata

Run:
  pip install -r requirements.txt
  uvicorn main:app --host 0.0.0.0 --port 8001 --reload

Or via Docker:
  docker compose up disease-detection
"""

from __future__ import annotations

import asyncio
import logging
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, AsyncIterator

import uvicorn
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Allow importing from the original backend directory
BACKEND_DIR = Path(__file__).parent.parent.parent.parent / "plant-disease-repo" / "backend"
if BACKEND_DIR.exists():
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from model_loader import LOCAL_MODEL_DIR, MODEL_NAME, get_model, load_model
    from predict import run_inference
    from utils import (
        log_prediction,
        open_and_validate_image,
        read_prediction_history,
        validate_image_file,
    )
    MODEL_AVAILABLE = True
except ImportError:
    MODEL_AVAILABLE = False

from tnau_guidance import (
    GUIDANCE,
    SUPPORTED_CROPS,
    SUPPORTED_DISEASES,
    estimate_severity,
    get_guidance,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("disease_detection")

MAX_BATCH_SIZE = 10
MAX_FILE_MB    = 10


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if MODEL_AVAILABLE:
        try:
            load_model()
            logger.info("Plant disease model loaded successfully")
        except Exception:
            logger.exception("Model load failed — prediction endpoints will return 503")
    else:
        logger.warning("Model backend not available — running in guidance-only mode")
    yield
    logger.info("Disease detection service shutting down")


app = FastAPI(
    title="UZHAVAN AI — Plant Disease Detection",
    description="MobileNetV2 disease classifier + TNAU treatment guidance for 14 crop species",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── SCHEMAS ──────────────────────────────────────────────────────────────────

class TNAUGuidance(BaseModel):
    pathogen:    str | None
    symptoms:    str
    severity:    str
    chemical:    str
    biological:  str
    cultural:    str


class PredictionResponse(BaseModel):
    prediction_id: str
    disease:       str
    crop:          str
    confidence:    float
    severity:      str
    top_k:         dict[str, float]
    timestamp:     str
    tnau_guidance: TNAUGuidance


class BatchItem(BaseModel):
    filename:      str
    disease:       str
    crop:          str
    confidence:    float
    severity:      str
    top_k:         dict[str, float]
    tnau_guidance: TNAUGuidance
    error:         str | None = None


class BatchPredictionResponse(BaseModel):
    batch_id:    str
    total:       int
    succeeded:   int
    failed:      int
    timestamp:   str
    predictions: list[BatchItem]


class DiseaseInfo(BaseModel):
    name:          str
    crop:          str
    pathogen:      str | None
    severity:      str
    symptoms:      str
    tnau_guidance: TNAUGuidance


class SupportedDiseasesResponse(BaseModel):
    total:    int
    diseases: list[DiseaseInfo]


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _crop_from_label(label: str) -> str:
    label_lower = label.lower()
    for crop in sorted(SUPPORTED_CROPS, key=len, reverse=True):
        if crop.lower() in label_lower:
            return crop
    return "Unknown"


def _build_prediction_response(
    disease: str,
    confidence: float,
    top_k: dict[str, float],
    filename: str = "",
) -> PredictionResponse:
    crop     = _crop_from_label(disease)
    severity = estimate_severity(confidence, disease)
    guidance = get_guidance(disease)

    return PredictionResponse(
        prediction_id = str(uuid.uuid4()),
        disease       = disease,
        crop          = crop,
        confidence    = confidence,
        severity      = severity,
        top_k         = top_k,
        timestamp     = datetime.now(UTC).isoformat(),
        tnau_guidance = TNAUGuidance(**guidance),
    )


async def _predict_single(file: UploadFile) -> BatchItem:
    try:
        raw_bytes = await file.read()
        validate_image_file(file.filename or "image.jpg", file.content_type, len(raw_bytes))
        image = open_and_validate_image(raw_bytes)
        processor, model, device = get_model()
        result = run_inference(image, processor, model, device)

        disease    = str(result["disease"])
        confidence = float(result["confidence"])
        top_k      = dict(result["top_k"])
        crop       = _crop_from_label(disease)
        severity   = estimate_severity(confidence, disease)
        guidance   = get_guidance(disease)

        return BatchItem(
            filename      = file.filename or "image.jpg",
            disease       = disease,
            crop          = crop,
            confidence    = confidence,
            severity      = severity,
            top_k         = top_k,
            tnau_guidance = TNAUGuidance(**guidance),
        )
    except Exception as exc:
        return BatchItem(
            filename      = file.filename or "image.jpg",
            disease       = "Error",
            crop          = "Unknown",
            confidence    = 0.0,
            severity      = "Unknown",
            top_k         = {},
            tnau_guidance = TNAUGuidance(
                pathogen   = None,
                symptoms   = str(exc),
                severity   = "Unknown",
                chemical   = "N/A",
                biological = "N/A",
                cultural   = "N/A",
            ),
            error = str(exc),
        )


# ─── ENDPOINTS ────────────────────────────────────────────────────────────────

@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(file: UploadFile = File(...)) -> PredictionResponse:
    """Single image prediction with TNAU treatment guidance."""
    if not MODEL_AVAILABLE:
        raise HTTPException(status_code=503, detail="Model backend not available")
    try:
        raw_bytes = await file.read()
        validate_image_file(file.filename or "image.jpg", file.content_type, len(raw_bytes))
        image = open_and_validate_image(raw_bytes)
        processor, model, device = get_model()
        result = run_inference(image, processor, model, device)

        disease    = str(result["disease"])
        confidence = float(result["confidence"])
        top_k      = dict(result["top_k"])

        log_prediction(
            filename   = file.filename or "image.jpg",
            disease    = disease,
            confidence = confidence,
            top_k_scores = top_k,
        )

        return _build_prediction_response(disease, confidence, top_k, file.filename or "image.jpg")

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in /predict")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.post("/batch-predict", response_model=BatchPredictionResponse, tags=["Prediction"])
async def batch_predict(
    files: list[UploadFile] = File(...),
) -> BatchPredictionResponse:
    """
    Predict on multiple images in a single request.
    Maximum batch size: 10 images.
    Images are processed concurrently.
    """
    if not MODEL_AVAILABLE:
        raise HTTPException(status_code=503, detail="Model backend not available")

    if len(files) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size {len(files)} exceeds maximum of {MAX_BATCH_SIZE}",
        )
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")

    results = await asyncio.gather(*[_predict_single(f) for f in files])

    succeeded = sum(1 for r in results if r.error is None)
    failed    = len(results) - succeeded

    return BatchPredictionResponse(
        batch_id    = str(uuid.uuid4()),
        total       = len(results),
        succeeded   = succeeded,
        failed      = failed,
        timestamp   = datetime.now(UTC).isoformat(),
        predictions = list(results),
    )


@app.get("/supported-crops", tags=["Catalogue"])
async def supported_crops() -> dict[str, Any]:
    """
    List all crop species detectable by the model.
    Returns crop names, disease count per crop, and detectable conditions.
    """
    crop_index: dict[str, list[str]] = {}
    for label in GUIDANCE.keys():
        crop = _crop_from_label(label)
        if "Healthy" not in label:
            crop_index.setdefault(crop, []).append(label)

    crops_detail = [
        {
            "crop": crop,
            "disease_count": len(diseases),
            "detectable_diseases": sorted(diseases),
        }
        for crop, diseases in sorted(crop_index.items())
    ]

    return {
        "total_crops": len(crops_detail),
        "crops": crops_detail,
        "model": "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification",
        "note": "This model is trained on PlantVillage dataset. For Indian crops not in this list, use the TNAU RAG knowledge base.",
    }


@app.get("/supported-diseases", response_model=SupportedDiseasesResponse, tags=["Catalogue"])
async def supported_diseases(
    crop: str | None = Query(default=None, description="Filter by crop name (e.g. 'Tomato')"),
) -> SupportedDiseasesResponse:
    """
    List all detectable diseases with TNAU treatment guidance.
    Optionally filter by crop name.
    """
    diseases: list[DiseaseInfo] = []

    for label, guidance in GUIDANCE.items():
        if "Healthy" in label:
            continue
        crop_name = _crop_from_label(label)
        if crop and crop.lower() not in crop_name.lower():
            continue
        diseases.append(DiseaseInfo(
            name          = label,
            crop          = crop_name,
            pathogen      = guidance.get("pathogen"),
            severity      = guidance.get("severity", "Unknown"),
            symptoms      = guidance.get("symptoms", ""),
            tnau_guidance = TNAUGuidance(**guidance),
        ))

    diseases.sort(key=lambda d: (d.crop, d.name))
    return SupportedDiseasesResponse(total=len(diseases), diseases=diseases)


@app.get("/disease/{disease_name}", response_model=DiseaseInfo, tags=["Catalogue"])
async def disease_detail(disease_name: str) -> DiseaseInfo:
    """
    Detailed TNAU treatment guidance for a specific disease.
    Use exact label names from /supported_diseases or URL-encode them.
    Example: GET /disease/Tomato%20With%20Early%20Blight
    """
    guidance = GUIDANCE.get(disease_name)
    if guidance is None:
        # fuzzy fallback
        name_lower = disease_name.lower()
        for key in GUIDANCE:
            if name_lower in key.lower():
                guidance = GUIDANCE[key]
                disease_name = key
                break
        if guidance is None:
            raise HTTPException(status_code=404, detail=f"Disease '{disease_name}' not found. Try GET /supported_diseases")

    return DiseaseInfo(
        name          = disease_name,
        crop          = _crop_from_label(disease_name),
        pathogen      = guidance.get("pathogen"),
        severity      = guidance.get("severity", "Unknown"),
        symptoms      = guidance.get("symptoms", ""),
        tnau_guidance = TNAUGuidance(**guidance),
    )


@app.get("/history", tags=["History"])
async def history(limit: int = Query(default=50, ge=1, le=200)) -> dict[str, Any]:
    """Prediction history log."""
    if not MODEL_AVAILABLE:
        return {"predictions": [], "total": 0, "note": "Model backend not available"}
    predictions = read_prediction_history(limit)
    return {"predictions": predictions, "total": len(predictions)}


@app.get("/health", tags=["Meta"])
async def health() -> dict[str, Any]:
    model_loaded = False
    device_name  = "N/A"
    if MODEL_AVAILABLE:
        try:
            _, _, device = get_model()
            device_name  = str(device)
            model_loaded = True
        except RuntimeError:
            pass
    return {
        "status": "ok",
        "model_loaded": model_loaded,
        "device": device_name,
        "guidance_db": len(GUIDANCE),
        "supported_crops": len(SUPPORTED_CROPS),
        "supported_diseases": len(SUPPORTED_DISEASES),
    }


@app.get("/model-info", tags=["Meta"])
async def model_info() -> dict[str, Any]:
    if not MODEL_AVAILABLE:
        return {"status": "Model backend not available", "guidance_only": True}
    try:
        _, model, device = get_model()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "model_name": MODEL_NAME,
        "num_classes": int(model.config.num_labels),
        "device": str(device),
        "offline_mode": (LOCAL_MODEL_DIR / "config.json").exists(),
        "tnau_guidance_db": len(GUIDANCE),
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
