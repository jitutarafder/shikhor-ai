"""Tests for BanglishBERT V3 and Bangla/Banglish NLP Intent Classification."""

import pytest
from app.integrations.ai.banglishbert_v3 import (
    DISEASE_CLASSES,
    TEMPERATURE_T,
    banglishbert_predictor,
)
from app.modules.crop_assistant.nlp_intent import nlp_engine


def test_52_disease_classes_present():
    """Verifies that all 52 trained disease classes are properly registered."""
    assert len(DISEASE_CLASSES) == 52
    assert "common rust" in DISEASE_CLASSES
    assert "early blight" in DISEASE_CLASSES
    assert "late blight" in DISEASE_CLASSES
    assert "bacterial blight" in DISEASE_CLASSES
    assert "maize streak virus" in DISEASE_CLASSES
    assert "cabbage ring spot" in DISEASE_CLASSES


def test_temperature_scaling_constant():
    """Verifies that the learned temperature scaling constant matches V3 spec."""
    assert round(TEMPERATURE_T, 6) == 0.460262


def test_nlp_engine_banglish_crop_and_disease():
    """Verifies Banglish input resolves crop and disease intent."""
    text = "vuttar patay lalche moricha rong er pustule hoise"
    res = nlp_engine.analyze_crop_symptoms(text)

    assert res.detected_crop == "ভুট্টা"
    assert "পোকা" in res.matched_symptoms_bn or "মরিচা" in res.matched_symptoms_bn or res.confidence > 0


def test_nlp_engine_bangla_symptoms():
    """Verifies Bangla script input resolves crop and disease guidance."""
    text = "ধানের পাতায় হলুদ দাগ পড়েছে এবং পাতা শুকিয়ে যাচ্ছে"
    res = nlp_engine.analyze_crop_symptoms(text)

    assert res.detected_crop == "ধান"
    assert "হলুদ" in res.matched_symptoms_bn
    assert "দাগ" in res.matched_symptoms_bn
    assert res.confidence >= 0.30
    assert len(res.guidance) > 0


def test_banglishbert_predictor_empty_input():
    """Verifies predictor handles empty input gracefully without errors."""
    res = banglishbert_predictor.predict("")
    assert res.get("error") == "EMPTY_INPUT"
    assert res["confidence"] == 0.0


def test_banglishbert_predictor_valid_banglish_query():
    """Verifies predictor returns standard response structure with confidence."""
    res = banglishbert_predictor.predict("alu te kalo dag porse late blight")
    assert "disease" in res
    assert "confidence" in res
    assert 0.0 <= res["confidence"] <= 1.0
    assert "model_version" in res


def test_gemini_adapter_fallback_when_unconfigured():
    """Verifies Gemini adapter handles missing key gracefully without crashing."""
    from app.integrations.ai.gemini_adapter import GeminiCropAdvisorAdapter

    adapter = GeminiCropAdvisorAdapter(api_key="")
    assert not adapter.is_configured

