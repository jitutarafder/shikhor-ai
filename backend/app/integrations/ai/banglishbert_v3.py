"""BanglishBERT V3 Plant Disease Detection Module.

Integrates fine-tuned csebuetnlp/banglishbert model (ElectraForSequenceClassification)
supporting 52 plant disease classes with post-hoc temperature scaling (T = 0.4602624177932739).
Complies with AGENTS.md Rule 19 and Banglish Plant Disease Detection V3 Specifications.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Learned temperature scaling parameter from validation set logits
TEMPERATURE_T = 0.4602624177932739
MAX_INPUT_LENGTH = 128
CONFIDENCE_THRESHOLD = 0.90  # Selective prediction threshold

# 52 Disease Classes from V3 Training Specification
DISEASE_CLASSES: List[str] = [
    "and gill rot",
    "anthracnose foliar blight",
    "bacterial blight",
    "bacterial leaf spot",
    "bacterial sheath brown rot",
    "bacterial soft rot",
    "bacterial wilt",
    "banana bunchy top virus",
    "black rot",
    "brown spot",
    "bulb rot",
    "cabbage leaf curl virus",
    "cabbage ring spot",
    "cauliflower mosaic virus",
    "coffee leaf rust",
    "common rust",
    "covered kernel smut",
    "downy mildew",
    "early blight",
    "false smut",
    "foot rot",
    "fusarium root and stalk rot",
    "fusarium wilt",
    "gray leaf spot",
    "late blight",
    "leaf blight",
    "loose kernel smut",
    "maize dwarf mosaic virus",
    "maize mosaic virus",
    "maize streak virus",
    "mosaic virus",
    "narrow brown spot",
    "northern leaf blight",
    "powdery mildew",
    "pythium seedling and root rot",
    "red stripe",
    "rice yellow mottle virus",
    "ring spot",
    "root rot",
    "rough leaf spot",
    "sheath blight",
    "sheath rot",
    "soft rot",
    "sooty stripe",
    "southern leaf spot",
    "stem rust",
    "stemphylium blight",
    "stripe rust",
    "turnip mosaic virus",
    "white rust",
    "willow rust",
    "zonate leaf spot",
]

ID2LABEL: Dict[int, str] = {i: name for i, name in enumerate(DISEASE_CLASSES)}
LABEL2ID: Dict[str, int] = {name: i for i, name in enumerate(DISEASE_CLASSES)}

# Bangla translations & human-readable condition names for all 52 classes
DISEASE_NAMES_BN: Dict[str, str] = {
    "and gill rot": "ফুলকা পচা রোগ",
    "anthracnose foliar blight": "অ্যানথ্রাকনোজ পাতা পোড়া রোগ",
    "bacterial blight": "ব্যাকটেরিয়াল পাতা পোড়া রোগ (Bacterial Blight)",
    "bacterial leaf spot": "ব্যাকটেরিয়াল পাতায় দাগ রোগ",
    "bacterial sheath brown rot": "ব্যাকটেরিয়াল খোল বাদামি পচা রোগ",
    "bacterial soft rot": "ব্যাকটেরিয়াল নরম পচা রোগ",
    "bacterial wilt": "ব্যাকটেরিয়াল ঢলে পড়া রোগ (Bacterial Wilt)",
    "banana bunchy top virus": "কলার বাঞ্চি টপ ভাইরাস রোগ",
    "black rot": "কালো পচা রোগ (Black Rot)",
    "brown spot": "বাদামি দাগ রোগ (Brown Spot)",
    "bulb rot": "কন্দ পচা রোগ (Bulb Rot)",
    "cabbage leaf curl virus": "বাঁধাকপির পাতা কোঁকড়ানো ভাইরাস",
    "cabbage ring spot": "বাঁধাকপির বলয় দাগ রোগ (Ring Spot)",
    "cauliflower mosaic virus": "ফুলকপির মোজাইক ভাইরাস",
    "coffee leaf rust": "কফির পাতা মরিচা রোগ (Leaf Rust)",
    "common rust": "সাধারণ মরিচা রোগ (Common Rust)",
    "covered kernel smut": "আচ্ছাদিত দানা ঝুল রোগ (Covered Smut)",
    "downy mildew": "ডাউনি মিলডিউ রোগ (Downy Mildew)",
    "early blight": "আগাম ধসা রোগ (Early Blight)",
    "false smut": "ভূয়া ঝুল রোগ (False Smut)",
    "foot rot": "গোড়া পচা রোগ (Foot Rot)",
    "fusarium root and stalk rot": "ফিউজারিয়াম শিকড় ও কাণ্ড পচা",
    "fusarium wilt": "ফিউজারিয়াম ঢলে পড়া রোগ (Fusarium Wilt)",
    "gray leaf spot": "ধূসর পাতা দাগ রোগ (Gray Leaf Spot)",
    "late blight": "নাবি ধসা রোগ (Late Blight)",
    "leaf blight": "পাতা পোড়া বা ব্লাইট রোগ",
    "loose kernel smut": "উন্মুক্ত দানা ঝুল রোগ (Loose Smut)",
    "maize dwarf mosaic virus": "ভুট্টার ডোয়ার্ফ মোজাইক ভাইরাস",
    "maize mosaic virus": "ভুট্টার মোজাইক ভাইরাস",
    "maize streak virus": "ভুট্টার স্ট্রিক ভাইরাস রোগ",
    "mosaic virus": "মোজাইক ভাইরাস রোগ",
    "narrow brown spot": "সরু বাদামি দাগ রোগ",
    "northern leaf blight": "নর্দার্ন লিফ ব্লাইট (পাতা পোড়া)",
    "powdery mildew": "পাউডারি মিলডিউ রোগ (Powdery Mildew)",
    "pythium seedling and root rot": "পিথিয়াম চারা ও শিকড় পচা রোগ",
    "red stripe": "লাল ডোরা দাগ রোগ (Red Stripe)",
    "rice yellow mottle virus": "ধানের হলুদ মটল ভাইরাস",
    "ring spot": "রিং স্পট বা বলয় দাগ রোগ",
    "root rot": "শিকড় পচা রোগ (Root Rot)",
    "rough leaf spot": "রুক্ষ পাতা দাগ রোগ",
    "sheath blight": "খোল পোড়া রোগ (Sheath Blight)",
    "sheath rot": "খোল পচা রোগ (Sheath Rot)",
    "soft rot": "নরম পচা রোগ (Soft Rot)",
    "sooty stripe": "সুটি স্ট্রাইপ বা কালো ডোরা রোগ",
    "southern leaf spot": "সাউদার্ন পাতা দাগ রোগ",
    "stem rust": "কাণ্ড মরিচা রোগ (Stem Rust)",
    "stemphylium blight": "স্টেমফিলিয়াম ব্লাইট রোগ",
    "stripe rust": "হলুদ বা ডোরা মরিচা রোগ (Stripe Rust)",
    "turnip mosaic virus": "শালগমের মোজাইক ভাইরাস",
    "white rust": "সাদা মরিচা রোগ (White Rust)",
    "willow rust": "উইলো মরিচা রোগ",
    "zonate leaf spot": "জোনেট পাতা দাগ রোগ",
}


class BanglishBertV3Predictor:
    """Inference predictor for BanglishBERT V3 with temperature scaling."""

    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = model_dir or os.getenv(
            "BANGLISHBERT_MODEL_PATH",
            "storage/models/banglishbert-disease-v3/checkpoint-1025"
        )
        self.tokenizer = None
        self.model = None
        self.is_loaded = False
        self._try_load_model()

    def _try_load_model(self):
        """Attempts to load PyTorch model weights if directory exists."""
        model_path = Path(self.model_dir)

        # Handle nested checkpoint folder if user placed checkpoint-1025 inside checkpoint-1025
        if not (model_path / "config.json").exists() and (model_path / "checkpoint-1025" / "config.json").exists():
            model_path = model_path / "checkpoint-1025"

        if not model_path.exists() or not (model_path / "config.json").exists():
            logger.info(
                f"BanglishBERT V3 config.json not found at {model_path}. "
                f"Running in fallback NLP mode until weights are placed."
            )
            return

        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self.tokenizer = AutoTokenizer.from_pretrained(
                "csebuetnlp/banglishbert",
                use_fast=False
            )
            self.model = AutoModelForSequenceClassification.from_pretrained(
                str(model_path),
                local_files_only=True
            )
            self.model.eval()
            self.is_loaded = True
            logger.info(f"Successfully loaded BanglishBERT V3 checkpoint model from {model_path}.")
        except Exception as e:
            logger.warning(f"Could not load BanglishBERT V3 model weights: {e}")
            self.is_loaded = False

    def predict(self, text: str) -> Dict[str, Any]:
        """Runs inference on Banglish symptom text returning disease and calibrated confidence."""
        if not text or not text.strip():
            return {
                "error": "EMPTY_INPUT",
                "message": "অনুগ্রহ করে ফসলের লক্ষণ বা সমস্যার বিবরণ লিখুন।",
                "disease": None,
                "confidence": 0.0,
            }

        cleaned_text = text.strip()

        # If PyTorch model is loaded in memory, execute real forward pass with temperature scaling
        if self.is_loaded and self.model and self.tokenizer:
            try:
                import torch

                inputs = self.tokenizer(
                    cleaned_text,
                    return_tensors="pt",
                    truncation=True,
                    max_length=MAX_INPUT_LENGTH,
                )

                with torch.no_grad():
                    outputs = self.model(**inputs)

                logits = outputs.logits[0]
                calibrated_probs = torch.softmax(logits / TEMPERATURE_T, dim=-1)
                confidence_tensor, pred_id_tensor = torch.max(calibrated_probs, dim=-1)

                pred_id = pred_id_tensor.item()
                confidence = float(confidence_tensor.item())
                disease_label = ID2LABEL.get(pred_id, "unknown")
                disease_bn = DISEASE_NAMES_BN.get(disease_label, disease_label)

                return {
                    "disease": disease_label,
                    "disease_bn": disease_bn,
                    "confidence": round(confidence, 4),
                    "confidence_band": "high" if confidence >= 0.80 else ("medium" if confidence >= 0.50 else "low"),
                    "calibrated": True,
                    "temperature": TEMPERATURE_T,
                    "model_version": "BanglishBERT-V3 (checkpoint-1025)",
                    "is_accepted_by_threshold": confidence >= CONFIDENCE_THRESHOLD,
                }
            except Exception as e:
                logger.error(f"Inference error with BanglishBERT: {e}")

        # Fallback to deterministic NLP hybrid classification if model weights are pending download
        from app.modules.crop_assistant.nlp_intent import nlp_engine
        nlp_res = nlp_engine.analyze_crop_symptoms(cleaned_text)

        matched_disease = "unknown"
        if nlp_res.possible_condition_bn:
            for en_label, bn_name in DISEASE_NAMES_BN.items():
                if bn_name in nlp_res.possible_condition_bn or nlp_res.possible_condition_bn in bn_name:
                    matched_disease = en_label
                    break

        return {
            "disease": matched_disease,
            "disease_bn": nlp_res.possible_condition_bn or "অনির্দিষ্ট রোগ লক্ষণ",
            "confidence": nlp_res.confidence,
            "confidence_band": nlp_res.confidence_band,
            "calibrated": False,
            "temperature": TEMPERATURE_T,
            "model_version": "BanglishBERT-V3-Hybrid",
            "is_accepted_by_threshold": nlp_res.confidence >= CONFIDENCE_THRESHOLD,
            "guidance": nlp_res.guidance,
            "reason_summary": nlp_res.reason_summary,
        }


# Global singleton predictor instance
banglishbert_predictor = BanglishBertV3Predictor()
