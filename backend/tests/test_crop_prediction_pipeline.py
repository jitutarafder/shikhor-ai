"""Automated Tests for Shikhor Crop-Aware Multimodal Disease Detection Pipeline.

Tests all 8 required validation scenarios:
1. No crop selected -> Blocked with Bangla validation
2. Rice image + Rice selected -> Strictly Rice disease classes
3. Rice image + Wheat selected -> Strictly Wheat disease classes
4. Road/bus non-plant image -> Rejected by OOD guardrail without invoking disease classifiers
5. Image + Banglish + Gemini available -> sources_used = [vision, banglish, gemini], ONE final decision
6. Image + Banglish + Gemini unavailable/quota exceeded -> sources_used = [vision, banglish], local deterministic consensus
7. Image without Banglish + Gemini available -> sources_used = [vision, gemini], Banglish model NOT called
8. Image without Banglish + Gemini unavailable -> sources_used = [vision]
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)

def test_case_1_no_crop_selected():
    """Test 1: When no crop is selected, request must be blocked with Bangla message."""
    with open('storage/crop_images/demo_rice_leaf.jpg', 'rb') as f:
        res = client.post('/api/v1/crop-disease/predict', data={'crop': ''}, files={'file': ('leaf.jpg', f, 'image/jpeg')})
    assert res.status_code == 422 or res.status_code == 400
    data = res.json()
    msg = data.get("error", {}).get("message", "") or data.get("detail", "")
    assert "অনুগ্রহ করে আগে ফসল নির্বাচন করুন" in str(msg)
    print("✓ Test 1 Passed: No crop selected was blocked with message:", msg)


def test_case_2_rice_image_rice_selected():
    """Test 2: Rice image + Rice crop selected -> Only Rice disease classes considered."""
    with open('storage/crop_images/demo_rice_leaf.jpg', 'rb') as f:
        res = client.post('/api/v1/crop-disease/predict', data={'crop': 'ধান'}, files={'file': ('rice.jpg', f, 'image/jpeg')})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["selected_crop"] == "Rice"
    assert data["selected_crop_bn"] == "ধান"
    # All top predictions must be Rice diseases
    for pred in data["top_predictions"]:
        assert pred["crop"] == "Rice"
    assert "Wheat" not in data["final_decision"]["crop"]
    print("✓ Test 2 Passed: Rice image with Rice selected yielded:", data["final_decision"]["disease_bn"])


def test_case_3_rice_image_wheat_selected():
    """Test 3: Rice image + Wheat selected -> Prediction must remain strictly within Wheat classes."""
    with open('storage/crop_images/demo_rice_leaf.jpg', 'rb') as f:
        res = client.post('/api/v1/crop-disease/predict', data={'crop': 'গম'}, files={'file': ('leaf.jpg', f, 'image/jpeg')})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["selected_crop"] == "Wheat"
    assert data["selected_crop_bn"] == "গম"
    # Must only predict Wheat classes
    for pred in data["top_predictions"]:
        assert pred["crop"] == "Wheat"
    assert "Rice" not in data["final_decision"]["crop"]
    print("✓ Test 3 Passed: Rice image with Wheat selected constrained to:", data["final_decision"]["disease_bn"])


def test_case_4_road_image_ood_guardrail():
    """Test 4: Road/bus image must be rejected immediately by OOD guardrail."""
    with open('storage/crop_images/test_road_bus.jpg', 'rb') as f:
        res = client.post('/api/v1/crop-disease/predict', data={'crop': 'ধান'}, files={'file': ('road.jpg', f, 'image/jpeg')})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert data["reason"] == "no_plant_detected"
    assert data["is_plant_leaf"] is False
    assert data["disease_bn"] == "গাছ বা পাতার ছবি নয়"
    assert data["sources_used"] == ["ood_guardrail"]
    print("✓ Test 4 Passed: Road image rejected by OOD guardrail with:", data["disease_bn"])


from unittest.mock import patch, AsyncMock, PropertyMock

@patch("app.integrations.ai.gemini_adapter.GeminiCropAdvisorAdapter.is_configured", new_callable=PropertyMock, return_value=True)
@patch("app.integrations.ai.gemini_adapter.gemini_crop_advisor.fuse_multimodal_crop_diagnosis", new_callable=AsyncMock)
def test_case_5_image_banglish_gemini_available(mock_fuse, mock_is_conf):
    """Test 5: Image + Banglish + Gemini available -> Sources = [vision, banglish, gemini], ONE final decision."""
    mock_fuse.return_value = {
        "crop": "Rice",
        "crop_bn": "ধান",
        "disease": "Brown Spot",
        "disease_bn": "বাদামি দাগ রোগ (Brown Spot)",
        "confidence": 0.94,
        "uncertain": False,
        "reason_summary": ["পাতায় বাদামি দাগ ও স্পোর দৃশ্যমান।"],
        "guidance": ["সুষম পটাশ সার ব্যবহার করুন।"],
        "decision_source": "gemini_multimodal_fusion",
    }
    with open('storage/crop_images/demo_rice_leaf.jpg', 'rb') as f:
        res = client.post(
            '/api/v1/crop-disease/predict',
            data={'crop': 'ধান', 'symptoms': 'patay choto choto badami dag poreche'},
            files={'file': ('leaf.jpg', f, 'image/jpeg')},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "vision" in data["sources_used"]
    assert "banglish" in data["sources_used"]
    assert "gemini" in data["sources_used"]
    assert data["gemini_available"] is True
    assert data["banglish_used"] is True
    assert data["final_decision"]["disease"] == "Brown Spot"
    print("✓ Test 5 Passed: Image + Banglish + Gemini -> Sources:", data["sources_used"], "Final:", data["final_decision"]["disease_bn"])


@patch("app.integrations.ai.gemini_adapter.GeminiCropAdvisorAdapter.is_configured", new_callable=PropertyMock, return_value=True)
@patch("app.integrations.ai.gemini_adapter.gemini_crop_advisor.fuse_multimodal_crop_diagnosis", side_effect=Exception("429 Quota Exceeded"))
def test_case_6_image_banglish_gemini_quota_exceeded(mock_fuse, mock_is_conf):
    """Test 6: Image + Banglish + Gemini quota exceeded -> Sources = [vision, banglish], local deterministic consensus."""
    with open('storage/crop_images/demo_rice_leaf.jpg', 'rb') as f:
        res = client.post(
            '/api/v1/crop-disease/predict',
            data={'crop': 'ধান', 'symptoms': 'patay choto choto badami dag poreche'},
            files={'file': ('leaf.jpg', f, 'image/jpeg')},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "vision" in data["sources_used"]
    assert "banglish" in data["sources_used"]
    assert "gemini" not in data["sources_used"]
    assert data["gemini_available"] is False
    assert data["banglish_used"] is True
    assert data["final_decision"] is not None
    print("✓ Test 6 Passed: Gemini quota exceeded gracefully fell back to local fusion -> Sources:", data["sources_used"])


@patch("app.integrations.ai.gemini_adapter.GeminiCropAdvisorAdapter.is_configured", new_callable=PropertyMock, return_value=True)
@patch("app.integrations.ai.gemini_adapter.gemini_crop_advisor.fuse_multimodal_crop_diagnosis", new_callable=AsyncMock)
def test_case_7_image_without_banglish_gemini_available(mock_fuse, mock_is_conf):
    """Test 7: Image without Banglish + Gemini available -> Sources = [vision, gemini], Banglish NOT called."""
    mock_fuse.return_value = {
        "crop": "Potato",
        "crop_bn": "আলু",
        "disease": "Early Blight",
        "disease_bn": "আর্লি ব্লাইট (আগাম ধসা রোগ)",
        "confidence": 0.88,
        "uncertain": False,
        "reason_summary": ["পাতার কিনারায় বলয়যুক্ত দাগ।"],
        "guidance": ["আক্রান্ত পাতা অপসারণ করুন।"],
        "decision_source": "gemini_multimodal_fusion",
    }
    with open('storage/crop_images/demo_potato_leaf.jpg', 'rb') as f:
        res = client.post(
            '/api/v1/crop-disease/predict',
            data={'crop': 'আলু', 'symptoms': ''},
            files={'file': ('leaf.jpg', f, 'image/jpeg')},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "vision" in data["sources_used"]
    assert "gemini" in data["sources_used"]
    assert "banglish" not in data["sources_used"]
    assert data["banglish_used"] is False
    assert data["banglish_result"] is None
    print("✓ Test 7 Passed: No symptom text -> Banglish skipped. Sources:", data["sources_used"])


@patch("app.integrations.ai.gemini_adapter.GeminiCropAdvisorAdapter.is_configured", new_callable=PropertyMock, return_value=False)
def test_case_8_image_without_banglish_gemini_unavailable(mock_is_conf):
    """Test 8: Image without Banglish + Gemini unavailable -> Sources = [vision] only."""
    with open('storage/crop_images/demo_potato_leaf.jpg', 'rb') as f:
        res = client.post(
            '/api/v1/crop-disease/predict',
            data={'crop': 'আলু'},
            files={'file': ('leaf.jpg', f, 'image/jpeg')},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["sources_used"] == ["vision"]
    assert data["banglish_used"] is False
    assert data["gemini_available"] is False
    assert data["final_decision"]["crop_bn"] == "আলু"
    print("✓ Test 8 Passed: Vision only mode -> Sources:", data["sources_used"], "Final:", data["final_decision"]["disease_bn"])


if __name__ == "__main__":
    test_case_1_no_crop_selected()
    test_case_2_rice_image_rice_selected()
    test_case_3_rice_image_wheat_selected()
    test_case_4_road_image_ood_guardrail()
    test_case_5_image_banglish_gemini_available()
    test_case_6_image_banglish_gemini_quota_exceeded()
    test_case_7_image_without_banglish_gemini_available()
    test_case_8_image_without_banglish_gemini_unavailable()
    print("\n==========================================")
    print("ALL 8 MANDATORY PIPELINE TESTS PASSED 100%")
    print("==========================================")
