from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from backend.shared.models.disease import TNAUGuidance
from backend.shared.models.service import ServiceMetadata, ServiceResult


class DiseaseKnowledgeService:
    """
    Disease knowledge database from TNAU Plant Protection Manual.
    Manages: disease metadata, treatments, prevention, severity mapping.
    Does NOT run the CNN — that is api/disease_detection/main.py.
    DiseaseAgent composes prediction + this knowledge for actionable advice.
    """

    VERSION = "1.0"
    _LAST_UPDATED = datetime(2023, 6, 1, tzinfo=timezone.utc)

    async def get(self, disease_label: str, **kwargs) -> ServiceResult[TNAUGuidance | None]:
        crop = kwargs.get("crop", "")
        key = self._make_key(disease_label, crop)
        guidance = self._KNOWLEDGE_BASE.get(key) or self._KNOWLEDGE_BASE.get(disease_label.lower())
        return ServiceResult(data=guidance, metadata=ServiceMetadata(source="tnau-plant-protection-manual", version=self.VERSION))

    async def search(self, query: str, **kwargs) -> ServiceResult[list[TNAUGuidance]]:
        crop_filter = kwargs.get("crop", "").lower()
        results = [g for g in self._KNOWLEDGE_BASE.values() if not crop_filter or g.crop.lower() == crop_filter]
        return ServiceResult(data=results, metadata=ServiceMetadata(source="tnau-plant-protection-manual", version=self.VERSION))

    async def get_guidance(self, disease_label: str, crop: str) -> TNAUGuidance | None:
        result = await self.get(disease_label, crop=crop)
        return result.data

    async def health(self) -> bool:
        return True  # in-memory data

    def version(self) -> str:
        return self.VERSION

    async def last_updated(self) -> datetime:
        return self._LAST_UPDATED

    @staticmethod
    def _make_key(disease: str, crop: str) -> str:
        return f"{disease.lower()}:{crop.lower()}" if crop else disease.lower()

    # ── TNAU Plant Protection Manual knowledge base ───────────────────────────
    # Source: TNAU Plant Protection Manual (2022 edition)
    # Maps disease_label → TNAUGuidance (same labels as PlantVillage dataset)

    _KNOWLEDGE_BASE: dict[str, TNAUGuidance] = {
        "rice_brown_spot": TNAUGuidance(
            disease_label="Rice_Brown_spot",
            crop="rice",
            symptoms="Small oval to circular brown spots with yellow halo on leaves. Causes blast-like lesions on grains.",
            chemical_control="Spray Edifenphos 50 EC 500 ml/ha or Carbendazim 50 WP 500 g/ha in 500 L water.",
            biological_control="Spray Pseudomonas fluorescens 0.5% WP at 2.5 kg/ha at 45 and 60 days after transplanting.",
            cultural_practices="Maintain adequate potassium nutrition. Avoid water stress at panicle initiation stage.",
        ),
        "rice_leaf_blight": TNAUGuidance(
            disease_label="Rice_Leaf_blight",
            crop="rice",
            symptoms="Water-soaked grayish-green lesions on leaf margins. Lesions turn yellowish-white with wavy margins.",
            chemical_control="Spray Validamycin 3 L 2 ml/L or Propiconazole 25 EC 1 ml/L at disease appearance.",
            biological_control="Seed treatment with Pseudomonas fluorescens talc formulation 10 g/kg seed.",
            cultural_practices="Use resistant varieties. Maintain proper spacing. Avoid excess nitrogen.",
        ),
        "tomato_early_blight": TNAUGuidance(
            disease_label="Tomato_Early_blight",
            crop="tomato",
            symptoms="Dark brown circular spots with concentric rings (target board pattern) on older leaves.",
            chemical_control="Spray Mancozeb 75 WP 2.0 g/L or Chlorothalonil 75 WP 2.0 g/L at 10-day intervals.",
            biological_control="Spray Trichoderma viride 2 g/L. Apply neem oil 3% at 10-day intervals.",
            cultural_practices="Stake plants for air circulation. Remove infected plant debris. Avoid overhead irrigation.",
        ),
        "tomato_late_blight": TNAUGuidance(
            disease_label="Tomato_Late_blight",
            crop="tomato",
            symptoms="Dark brown water-soaked lesions on leaves, stems, and fruits. White sporulation on leaf undersides.",
            chemical_control="Spray Metalaxyl + Mancozeb 72 WP 2.5 g/L at first appearance. Repeat at 7-day intervals.",
            biological_control="Spray Bacillus subtilis at 5 g/L as preventive measure.",
            cultural_practices="Avoid excessive irrigation. Improve drainage. Remove and destroy infected plant parts.",
        ),
        "cotton_bacterial_blight": TNAUGuidance(
            disease_label="Cotton_Bacterial_blight",
            crop="cotton",
            symptoms="Angular water-soaked lesions on leaves that turn brown. Black cankers on stems.",
            chemical_control="Spray Copper oxychloride 50 WP 3.0 g/L or Streptomycin sulphate 100 ppm.",
            biological_control="Seed treatment with Pseudomonas fluorescens 10 g/kg.",
            cultural_practices="Use certified disease-free seed. Maintain proper plant spacing. Avoid field operations when wet.",
        ),
        "groundnut_early_leaf_spot": TNAUGuidance(
            disease_label="Groundnut_Early_leaf_spot",
            crop="groundnut",
            symptoms="Circular dark brown spots with yellow halo on upper leaf surface.",
            chemical_control="Spray Mancozeb 75 WP 2 g/L or Chlorothalonil 75 WP 2 g/L at 15-day intervals.",
            biological_control="Spray Trichoderma harzianum 5 g/L.",
            cultural_practices="Maintain balanced nitrogen. Avoid waterlogging. Remove infected leaves.",
        ),
    }
