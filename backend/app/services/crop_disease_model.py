"""Crop Disease Model Service module.

Re-exports vision classifier functions from app.integrations.ai.vision_models.
"""

from app.integrations.ai.vision_models import (
    load_base_model,
    load_secondary_model,
    predict_base,
    predict_secondary,
    predict_crop_disease,
    parse_crop_and_disease,
    vision_classifier,
    CropDiseaseVisionService,
)

__all__ = [
    "load_base_model",
    "load_secondary_model",
    "predict_base",
    "predict_secondary",
    "predict_crop_disease",
    "parse_crop_and_disease",
    "vision_classifier",
    "CropDiseaseVisionService",
]
