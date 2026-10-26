"""Tests for Dual-Stage Vision Crop Disease Classification Models.

Validates:
- BASE Model: BCDD MobileNetV2 (19 classes)
- SECONDARY Model: Plant Disease MobileNetV2 (38 classes)
- Confidence-based fallback inference strategy (BASE threshold routing)
- Class label parsing and Bengali translations
- FastAPI prediction endpoints (/api/crop-disease/predict and /api/v1/crop-disease/predict)
"""

import io
import pytest
from httpx import AsyncClient
from PIL import Image

from app.integrations.ai.vision_models import (
    parse_crop_and_disease,
    predict_base,
    predict_secondary,
    predict_crop_disease,
    load_base_model,
    load_secondary_model,
    vision_classifier,
)


def create_dummy_leaf_image(color=(40, 140, 60), size=(224, 224)) -> Image.Image:
    """Generates a dummy in-memory RGB leaf image for inference."""
    return Image.new("RGB", size, color=color)


def create_dummy_leaf_bytes(format="JPEG") -> bytes:
    buf = io.BytesIO()
    img = create_dummy_leaf_image()
    img.save(buf, format=format)
    return buf.getvalue()


def test_parse_crop_and_disease_mappings():
    # Test BCDD classes
    c, d, cb, db = parse_crop_and_disease("Potato___Early_blight")
    assert c == "Potato"
    assert d == "Early Blight"
    assert cb == "আলু"
    assert len(db) > 0

    c, d, cb, db = parse_crop_and_disease("Wheat Yellow rust")
    assert c == "Wheat"
    assert d == "Yellow Rust"
    assert cb == "গম"
    assert len(db) > 0

    c, d, cb, db = parse_crop_and_disease("Rice_bacterial_leaf_blight")
    assert c == "Rice"
    assert d == "Bacterial Leaf Blight"
    assert cb == "ধান"

    c, d, cb, db = parse_crop_and_disease("Corn_(maize)___healthy")
    assert c == "Corn"
    assert d == "Healthy"
    assert cb == "ভুট্টা"
    assert "সুস্থ" in db

    # Test Secondary Plant Disease classes
    c, d, cb, db = parse_crop_and_disease("Apple Scab")
    assert c == "Apple"
    assert d in ["Scab", "Apple Scab"]
    assert cb == "আপেল"

    c, d, cb, db = parse_crop_and_disease("Corn (Maize) with Common Rust")
    assert c == "Corn"
    assert d == "Common Rust"
    assert cb == "ভুট্টা"

    c, d, cb, db = parse_crop_and_disease("Healthy Blueberry Plant")
    assert c == "Blueberry"
    assert d == "Healthy"
    assert cb == "ব্লুবেরি"


def test_base_model_loading_and_inference():
    load_base_model()
    assert vision_classifier._is_base_loaded is True
    assert len(vision_classifier._base_classes) == 19

    img = create_dummy_leaf_image()
    res = predict_base(img)

    assert res["model_used"] == "base"
    assert res["model_name"] == "BCDD MobileNetV2"
    assert "crop" in res
    assert "disease" in res
    assert "confidence" in res
    assert 0.0 <= res["confidence"] <= 1.0
    assert len(res["top_predictions"]) <= 3
    assert len(res["top_predictions"]) > 0


def test_secondary_model_loading_and_inference():
    load_secondary_model()
    assert vision_classifier._is_secondary_loaded is True
    assert len(vision_classifier._secondary_id2label) == 38

    img = create_dummy_leaf_image()
    res = predict_secondary(img)

    assert res["model_used"] == "secondary"
    assert res["model_name"] == "Plant Disease MobileNetV2"
    assert "crop" in res
    assert "disease" in res
    assert "confidence" in res
    assert 0.0 <= res["confidence"] <= 1.0
    assert len(res["top_predictions"]) <= 3
    assert len(res["top_predictions"]) > 0


def test_dual_stage_fallback_routing():
    img = create_dummy_leaf_image()

    # If threshold is 0.0, BASE model is always chosen
    res_base = predict_crop_disease(img, threshold=0.0)
    assert res_base["success"] is True
    assert res_base["model_used"] == "base"
    assert res_base["model_name"] == "BCDD MobileNetV2"
    assert len(res_base["top_predictions"]) > 0
    assert len(res_base["guidance"]) > 0

    # If threshold is 1.01 (impossible for BASE), SECONDARY model fallback is triggered
    res_sec = predict_crop_disease(img, threshold=1.01)
    assert res_sec["success"] is True
    assert res_sec["model_used"] == "secondary"
    assert res_sec["model_name"] == "Plant Disease MobileNetV2"
    assert len(res_sec["top_predictions"]) > 0
    assert len(res_sec["guidance"]) > 0


@pytest.mark.asyncio
async def test_crop_disease_prediction_endpoint_v1(client: AsyncClient):
    img_bytes = create_dummy_leaf_bytes("JPEG")
    files = {"file": ("leaf.jpg", img_bytes, "image/jpeg")}
    data_payload = {"crop": "rice"}

    res = await client.post("/api/v1/crop-disease/predict", files=files, data=data_payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["success"] is True
    assert "crop" in data
    assert "crop_bn" in data
    assert "disease" in data
    assert "disease_bn" in data
    assert "confidence" in data
    assert data["model_used"] in ["base", "secondary"]
    assert len(data["top_predictions"]) > 0
    assert len(data["guidance"]) > 0
    assert "disclaimer" in data


@pytest.mark.asyncio
async def test_crop_disease_prediction_endpoint_root_api(client: AsyncClient):
    img_bytes = create_dummy_leaf_bytes("PNG")
    files = {"image": ("test_leaf.png", img_bytes, "image/png")}
    data_payload = {"crop": "ধান"}

    res = await client.post("/api/crop-disease/predict", files=files, data=data_payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert "crop" in data
    assert "disease" in data
    assert "disclaimer" in data


@pytest.mark.asyncio
async def test_crop_disease_prediction_invalid_file(client: AsyncClient):
    fake_bytes = b"Not a real image file."
    files = {"file": ("fake.jpg", fake_bytes, "image/jpeg")}
    data_payload = {"crop": "ধান"}

    res = await client.post("/api/v1/crop-disease/predict", files=files, data=data_payload)
    assert res.status_code in [400, 422]
    assert res.json()["error"]["code"] in ["VALIDATION_ERROR", "INVALID_FILE_HEADER", "UNSUPPORTED_IMAGE_FORMAT", "INVALID_IMAGE_FORMAT"]
