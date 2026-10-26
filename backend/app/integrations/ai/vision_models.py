"""Dual-Stage Vision Classifier for Plant & Crop Disease Detection.

Implements Crop-Aware BASE + SECONDARY fallback inference strategy:
- BASE Model: BCDD MobileNetV2 (19 classes, PyTorch / torchvision) from jitu25/bcdd-mobilenetv2
  Supports: Rice (ধান), Corn (ভুট্টা), Wheat (গম), Potato (আলু), Tomato (টমেটো)
- SECONDARY Model: Plant Disease MobileNetV2 (38 classes, HF Transformers) from jitu25/plant-disease-mobilenetv2
  Supports: Apple (আপেল), Blueberry (ব্লুবেরি), Cherry (চেরি), Corn (ভুট্টা), Grape (আঙুর),
            Orange (কমলা), Peach (পিচ), Bell Pepper (ক্যাপসিকাম), Potato (আলু), Raspberry (রাস্পবেরি),
            Soybean (সয়াবিন), Squash (স্কোয়াশ), Strawberry (স্ট্রবেরি), Tomato (টমেটো)
- 16 Total Supported Crops with strict crop-conditional class filtering (Logit masking / Sub-Softmax).
- Out-Of-Distribution (OOD) & Non-Plant Image Guardrail
- Fallback threshold: Configurable (default 0.70 via settings.BASE_THRESHOLD)
- Strictly avoids merging weights or averaging parameters.
"""

import json
import logging
import threading
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image
import numpy as np

import torch
import torchvision.transforms as T
from torchvision.models import mobilenet_v2
from huggingface_hub import hf_hub_download
from transformers import AutoImageProcessor, AutoModelForImageClassification

from app.core.config import settings
from app.modules.crop_assistant.knowledge_base import (
    DISCLAIMER_TEXT,
    get_crop_disease_knowledge,
    lookup_reviewed_condition,
)

logger = logging.getLogger("shikhor.ai.vision_models")

# ---------------------------------------------------------------------------
# 16 Canonical Supported Crops & Bengali Translations
# ---------------------------------------------------------------------------
CROP_LABELS_BN: Dict[str, str] = {
    "Rice": "ধান",
    "Corn": "ভুট্টা",
    "Wheat": "গম",
    "Potato": "আলু",
    "Tomato": "টমেটো",
    "Apple": "আপেল",
    "Blueberry": "ব্লুবেরি",
    "Cherry": "চেরি",
    "Grape": "আঙুর",
    "Orange": "কমলা",
    "Peach": "পিচ",
    "Bell Pepper": "ক্যাপসিকাম",
    "Raspberry": "রাস্পবেরি",
    "Soybean": "সয়াবিন",
    "Squash": "স্কোয়াশ",
    "Strawberry": "স্ট্রবেরি",
}

# Reverse lookup mapping Bengali and variant spellings to Canonical English key
CROP_LOOKUP_TO_CANONICAL: Dict[str, str] = {
    "ধান": "Rice", "rice": "Rice", "Rice": "Rice",
    "ভুট্টা": "Corn", "corn": "Corn", "Corn": "Corn", "maize": "Corn", "Maize": "Corn", "corn_(maize)": "Corn",
    "গম": "Wheat", "wheat": "Wheat", "Wheat": "Wheat",
    "আলু": "Potato", "potato": "Potato", "Potato": "Potato",
    "টমেটো": "Tomato", "tomato": "Tomato", "Tomato": "Tomato",
    "আপেল": "Apple", "apple": "Apple", "Apple": "Apple",
    "ব্লুবেরি": "Blueberry", "blueberry": "Blueberry", "Blueberry": "Blueberry",
    "চেরি": "Cherry", "cherry": "Cherry", "Cherry": "Cherry",
    "আঙুর": "Grape", "আঙ্গুর": "Grape", "grape": "Grape", "Grape": "Grape",
    "কমলা": "Orange", "কমলা / মাল্টা": "Orange", "মাল্টা": "Orange", "orange": "Orange", "Orange": "Orange", "citrus": "Orange",
    "পিচ": "Peach", "পীচ": "Peach", "peach": "Peach", "Peach": "Peach",
    "ক্যাপসিকাম": "Bell Pepper", "ক্যাপসিকাম / মিষ্টি মরিচ": "Bell Pepper", "মরিচ": "Bell Pepper", "bell pepper": "Bell Pepper", "Bell Pepper": "Bell Pepper", "pepper": "Bell Pepper",
    "রাস্পবেরি": "Raspberry", "raspberry": "Raspberry", "Raspberry": "Raspberry",
    "সয়াবিন": "Soybean", "soybean": "Soybean", "Soybean": "Soybean",
    "স্কোয়াশ": "Squash", "squash": "Squash", "Squash": "Squash",
    "স্ট্রবেরি": "Strawberry", "strawberry": "Strawberry", "Strawberry": "Strawberry",
}

BASE_SUPPORTED_CROPS = {"Rice", "Corn", "Wheat", "Potato", "Tomato"}
SECONDARY_SUPPORTED_CROPS = {
    "Apple", "Blueberry", "Cherry", "Corn", "Grape",
    "Orange", "Peach", "Bell Pepper", "Potato", "Raspberry",
    "Soybean", "Squash", "Strawberry", "Tomato",
}

DISEASE_TRANSLATIONS: Dict[str, str] = {
    "Healthy": "সুস্থ ও নিরোগ গাছ",
    "Early Blight": "আর্লি ব্লাইট (আগাম ধসা রোগ)",
    "Late Blight": "লেট ব্লাইট (নাবী ধসা রোগ)",
    "Bacterial Spot": "ব্যাকটেরিয়াজনিত দাগ (Bacterial Spot)",
    "Bacterial Leaf Blight": "ব্যাকটেরিয়াজনিত পাতা পোড়া (BLB)",
    "Brown Spot": "বাদামি দাগ রোগ (Brown Spot)",
    "Leaf Blast": "পাতা ব্লাস্ট রোগ (Leaf Blast)",
    "Brown Rust": "বাদামি মরিচা রোগ (Brown Rust)",
    "Yellow Rust": "হলুদ মরিচা রোগ (Yellow Rust)",
    "Loose Smut": "লুজ স্মাট (উড়তি ঝুল রোগ)",
    "Common Rust": "কমন রাস্ট (মরিচা রোগ)",
    "Northern Leaf Blight": "নর্দান লিফ ব্লাইট (পাতা ঝলসানো)",
    "Cercospora Leaf Spot Gray Leaf Spot": "সারকোস্পোরা পাতার দাগ ও গ্রে লিফ স্পট",
    "Cercospora and Gray Leaf Spot": "সারকোস্পোরা ও গ্রে লিফ স্পট",
    "Cercospora And Gray Leaf Spot": "সারকোস্পোরা ও গ্রে লিফ স্পট",
    "Apple Scab": "আপেল স্ক্যাব রোগ",
    "Black Rot": "ব্ল্যাক রট (কালো পচা রোগ)",
    "Cedar Apple Rust": "সিডার আপেল রাস্ট",
    "Powdery Mildew": "পাউডারি মিলডিউ (সাদা গুঁড়ো রোগ)",
    "Esca (Black Measles)": "এসকা বা ব্ল্যাক মিসেলস",
    "Isariopsis Leaf Spot": "আইসারিওপসিস পাতার দাগ",
    "Citrus Greening": "সাইট্রাস গ্রিনিং (হলুদাভ রোগ)",
    "Leaf Mold": "লিফ মোল্ড (পাতা পচা ছত্রাক)",
    "Septoria Leaf Spot": "সেপ্টোরিয়া পাতার দাগ",
    "Spider Mites": "লাল মাকড় বা স্পাইডার মাইট আক্রমণ",
    "Spider Mites Or Two-Spotted Spider Mite": "লাল মাকড় বা স্পাইডার মাইট আক্রমণ",
    "Target Spot": "টার্গেট স্পট (গোলাকার দাগ)",
    "Yellow Leaf Curl Virus": "হলুদ পাতা কোঁকড়ানো ভাইরাস (TYLCV)",
    "Mosaic Virus": "মোজাইক ভাইরাস রোগ",
    "Leaf Scorch": "লিফ স্কর্চ (পাতা পোড়া রোগ)",
    "Scab": "আপেল স্ক্যাব রোগ",
}


def parse_crop_and_disease(raw_label: str) -> Tuple[str, str, str, str]:
    """Parses raw class names into (crop, disease, crop_bn, disease_bn)."""
    clean_label = raw_label.strip()

    # Case 1: BCDD format (e.g. "Potato___Early_blight", "Rice_bacterial_leaf_blight", "Wheat Brown rust")
    if "___" in clean_label:
        parts = clean_label.split("___")
        crop_raw = parts[0].replace("Corn_(maize)", "Corn").replace("_", " ").strip()
        disease_raw = parts[1].replace("_", " ").strip()
    elif clean_label.startswith("Rice_"):
        crop_raw = "Rice"
        disease_raw = clean_label.replace("Rice_", "").replace("_", " ").strip()
    elif clean_label.startswith("Wheat "):
        crop_raw = "Wheat"
        disease_raw = clean_label.replace("Wheat ", "").strip()
    elif clean_label.startswith("Corn (Maize) with "):
        crop_raw = "Corn"
        disease_raw = clean_label.replace("Corn (Maize) with ", "").strip()
    elif clean_label == "Cedar Apple Rust":
        crop_raw = "Apple"
        disease_raw = "Cedar Apple Rust"
    elif clean_label == "Apple Scab":
        crop_raw = "Apple"
        disease_raw = "Apple Scab"
    elif clean_label.startswith("Apple with "):
        crop_raw = "Apple"
        disease_raw = clean_label.replace("Apple with ", "").strip()
    elif clean_label.startswith("Healthy ") and clean_label.endswith(" Plant"):
        crop_raw = clean_label.replace("Healthy ", "").replace(" Plant", "").replace("(Maize)", "").strip()
        disease_raw = "Healthy"
    elif clean_label.startswith("Healthy "):
        crop_raw = clean_label.replace("Healthy ", "").strip()
        disease_raw = "Healthy"
    elif " with " in clean_label:
        parts = clean_label.split(" with ", 1)
        crop_raw = parts[0].strip()
        disease_raw = parts[1].strip()
    else:
        tokens = clean_label.split(" ")
        crop_raw = tokens[0]
        disease_raw = " ".join(tokens[1:]) if len(tokens) > 1 else clean_label

    crop = crop_raw.title().replace("Bell Pepper", "Bell Pepper").replace("Bell pepper", "Bell Pepper")
    disease = disease_raw.title()

    if "Healthy" in disease:
        disease = "Healthy"

    crop_bn = CROP_LABELS_BN.get(crop, crop)
    disease_bn = DISEASE_TRANSLATIONS.get(disease, f"{disease} ({crop_bn})")

    return crop, disease, crop_bn, disease_bn


def check_is_plant_or_leaf(image: Image.Image) -> Tuple[bool, float]:
    """Analyzes image chromatic profile to detect non-plant/out-of-distribution images.

    Protects against arbitrary non-agricultural photos (e.g. roads, bridges, snowy mountains, vehicles)
    forcing closed-set Softmax overconfidence.
    """
    if image.mode != "RGB":
        image = image.convert("RGB")

    thumb = image.resize((100, 100))
    rgb_arr = np.array(thumb, dtype=np.float32) / 255.0
    r_chan, g_chan, b_chan = rgb_arr[:, :, 0], rgb_arr[:, :, 1], rgb_arr[:, :, 2]

    hsv = thumb.convert("HSV")
    h, s, v = hsv.split()
    h_arr = np.array(h, dtype=np.float32) / 255.0 * 360.0
    s_arr = np.array(s, dtype=np.float32) / 255.0
    v_arr = np.array(v, dtype=np.float32) / 255.0

    # 1. True Green/Olive plant foliage (Hue 35°-165°, Sat >= 0.12, Val >= 0.10)
    green_mask = (h_arr >= 35) & (h_arr <= 165) & (s_arr >= 0.12) & (v_arr >= 0.10)
    green_ratio = float(np.mean(green_mask))

    # 2. Plant blight/necrosis (Hue 18°-35°, Sat >= 0.20, Val >= 0.15) - must have organic green or plant texture
    yellow_brown_mask = (h_arr >= 18) & (h_arr < 35) & (s_arr >= 0.20) & (v_arr >= 0.15) & (g_chan >= b_chan * 0.90)
    yellow_brown_ratio = float(np.mean(yellow_brown_mask))

    total_foliage_ratio = green_ratio + yellow_brown_ratio

    # 3. Sky / Snow / Blue dominance filter (Landscape detection)
    blue_sky_snow = (b_chan > r_chan * 1.15) & (b_chan > g_chan * 1.05) & (v_arr > 0.35)
    blue_snow_ratio = float(np.mean(blue_sky_snow))

    # Leaf images must have significant plant content and not be dominated by sky/snow
    if blue_snow_ratio > 0.40 and green_ratio < 0.08:
        return False, total_foliage_ratio

    is_plant = (green_ratio >= 0.05) or (total_foliage_ratio >= 0.08 and green_ratio >= 0.02)
    return is_plant, total_foliage_ratio


class CropDiseaseVisionService:
    """Thread-safe Singleton manager for BCDD MobileNetV2 and Plant Disease MobileNetV2."""

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._base_model = None
        self._base_classes: List[str] = []
        self._base_transform = None

        self._secondary_model = None
        self._secondary_processor = None
        self._secondary_id2label: Dict[int, str] = {}

        self._is_base_loaded = False
        self._is_secondary_loaded = False
        self._load_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "CropDiseaseVisionService":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def load_base_model(self):
        """Loads BCDD MobileNetV2 (19 classes) from Hugging Face."""
        if self._is_base_loaded:
            return

        with self._load_lock:
            if self._is_base_loaded:
                return

            try:
                logger.info(f"Loading BASE model from HF repo: {settings.BASE_MODEL_REPO}...")
                pth_path = hf_hub_download(
                    repo_id=settings.BASE_MODEL_REPO,
                    filename="model.pth",
                )
                json_path = hf_hub_download(
                    repo_id=settings.BASE_MODEL_REPO,
                    filename="class_names.json",
                )

                with open(json_path, "r", encoding="utf-8") as f:
                    self._base_classes = json.load(f)

                num_classes = len(self._base_classes)
                model = mobilenet_v2(weights=None)
                model.classifier[1] = torch.nn.Linear(model.last_channel, num_classes)

                state_dict = torch.load(pth_path, map_location=torch.device("cpu"))
                model.load_state_dict(state_dict)
                model.eval()

                self._base_model = model
                self._base_transform = T.Compose([
                    T.Resize((224, 224)),
                    T.ToTensor(),
                    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                ])
                self._is_base_loaded = True
                logger.info(f"BASE model loaded successfully with {num_classes} classes.")
            except Exception as exc:
                logger.error(f"Failed to load BASE model: {exc}", exc_info=True)
                raise RuntimeError(f"Base plant model loading error: {exc}")

    def load_secondary_model(self):
        """Loads Plant Disease MobileNetV2 (38 classes) from Hugging Face."""
        if self._is_secondary_loaded:
            return

        with self._load_lock:
            if self._is_secondary_loaded:
                return

            try:
                logger.info(f"Loading SECONDARY model from HF repo: {settings.SECONDARY_MODEL_REPO}...")
                self._secondary_processor = AutoImageProcessor.from_pretrained(
                    settings.SECONDARY_MODEL_REPO
                )
                self._secondary_model = AutoModelForImageClassification.from_pretrained(
                    settings.SECONDARY_MODEL_REPO
                )
                self._secondary_model.eval()
                self._secondary_id2label = {
                    int(k): v for k, v in self._secondary_model.config.id2label.items()
                }
                self._is_secondary_loaded = True
                logger.info(f"SECONDARY model loaded successfully with {len(self._secondary_id2label)} classes.")
            except Exception as exc:
                logger.error(f"Failed to load SECONDARY model: {exc}", exc_info=True)
                raise RuntimeError(f"Secondary plant model loading error: {exc}")

    def predict_base(self, image: Image.Image, target_crop: Optional[str] = None) -> Dict[str, Any]:
        """Runs crop-aware inference using BASE BCDD MobileNetV2."""
        self.load_base_model()

        if image.mode != "RGB":
            image = image.convert("RGB")

        tensor = self._base_transform(image).unsqueeze(0)  # Shape: [1, 3, 224, 224]

        with torch.no_grad():
            logits = self._base_model(tensor)

        # Crop-Aware Class Filtering
        if target_crop:
            candidate_indices = []
            for idx, raw_c in enumerate(self._base_classes):
                c_crop, _, _, _ = parse_crop_and_disease(raw_c)
                if c_crop.lower() == target_crop.lower():
                    candidate_indices.append(idx)

            if not candidate_indices:
                raise ValueError(f"Crop '{target_crop}' is not supported by the BASE model.")

            sub_logits = logits[0, candidate_indices]
            sub_probs = torch.softmax(sub_logits, dim=-1)

            top_k = min(3, len(candidate_indices))
            sorted_probs, sorted_local_indices = torch.topk(sub_probs, k=top_k)

            top_predictions = []
            for p, local_idx in zip(sorted_probs.tolist(), sorted_local_indices.tolist()):
                orig_idx = candidate_indices[local_idx]
                raw_c = self._base_classes[orig_idx]
                c_crop, c_dis, c_crop_bn, c_dis_bn = parse_crop_and_disease(raw_c)
                top_predictions.append({
                    "class": raw_c,
                    "crop": c_crop,
                    "disease": c_dis,
                    "crop_bn": c_crop_bn,
                    "disease_bn": c_dis_bn,
                    "confidence": round(float(p), 4),
                })

            best_orig_idx = candidate_indices[sorted_local_indices[0].item()]
            best_prob = round(float(sorted_probs[0].item()), 4)
            best_raw_class = self._base_classes[best_orig_idx]
        else:
            probs = torch.softmax(logits, dim=1).squeeze(0)
            top_k = min(3, len(self._base_classes))
            top_probs, top_indices = torch.topk(probs, k=top_k)

            top_predictions = []
            for p, idx in zip(top_probs.tolist(), top_indices.tolist()):
                raw_c = self._base_classes[idx]
                c_crop, c_dis, c_crop_bn, c_dis_bn = parse_crop_and_disease(raw_c)
                top_predictions.append({
                    "class": raw_c,
                    "crop": c_crop,
                    "disease": c_dis,
                    "crop_bn": c_crop_bn,
                    "disease_bn": c_dis_bn,
                    "confidence": round(float(p), 4),
                })

            best_idx = top_indices[0].item()
            best_prob = round(float(top_probs[0].item()), 4)
            best_raw_class = self._base_classes[best_idx]

        crop, disease, crop_bn, disease_bn = parse_crop_and_disease(best_raw_class)

        return {
            "model_used": "base",
            "model_name": "BCDD MobileNetV2",
            "raw_class": best_raw_class,
            "crop": crop,
            "crop_bn": crop_bn,
            "disease": disease,
            "disease_bn": disease_bn,
            "confidence": best_prob,
            "top_predictions": top_predictions,
        }

    def predict_secondary(self, image: Image.Image, target_crop: Optional[str] = None) -> Dict[str, Any]:
        """Runs crop-aware inference using SECONDARY Plant Disease MobileNetV2."""
        self.load_secondary_model()

        if image.mode != "RGB":
            image = image.convert("RGB")

        inputs = self._secondary_processor(images=image, return_tensors="pt")

        with torch.no_grad():
            outputs = self._secondary_model(**inputs)

        # Crop-Aware Class Filtering
        if target_crop:
            candidate_indices = []
            for idx, raw_c in self._secondary_id2label.items():
                c_crop, _, _, _ = parse_crop_and_disease(raw_c)
                if c_crop.lower() == target_crop.lower():
                    candidate_indices.append(idx)

            if not candidate_indices:
                raise ValueError(f"Crop '{target_crop}' is not supported by the SECONDARY model.")

            sub_logits = outputs.logits[0, candidate_indices]
            sub_probs = torch.softmax(sub_logits, dim=-1)

            top_k = min(3, len(candidate_indices))
            sorted_probs, sorted_local_indices = torch.topk(sub_probs, k=top_k)

            top_predictions = []
            for p, local_idx in zip(sorted_probs.tolist(), sorted_local_indices.tolist()):
                orig_idx = candidate_indices[local_idx]
                raw_c = self._secondary_id2label[orig_idx]
                c_crop, c_dis, c_crop_bn, c_dis_bn = parse_crop_and_disease(raw_c)
                top_predictions.append({
                    "class": raw_c,
                    "crop": c_crop,
                    "disease": c_dis,
                    "crop_bn": c_crop_bn,
                    "disease_bn": c_dis_bn,
                    "confidence": round(float(p), 4),
                })

            best_orig_idx = candidate_indices[sorted_local_indices[0].item()]
            best_prob = round(float(sorted_probs[0].item()), 4)
            best_raw_class = self._secondary_id2label[best_orig_idx]
        else:
            probs = torch.softmax(outputs.logits, dim=1).squeeze(0)
            top_k = min(3, len(self._secondary_id2label))
            top_probs, top_indices = torch.topk(probs, k=top_k)

            top_predictions = []
            for p, idx in zip(top_probs.tolist(), top_indices.tolist()):
                raw_c = self._secondary_id2label[idx]
                c_crop, c_dis, c_crop_bn, c_dis_bn = parse_crop_and_disease(raw_c)
                top_predictions.append({
                    "class": raw_c,
                    "crop": c_crop,
                    "disease": c_dis,
                    "crop_bn": c_crop_bn,
                    "disease_bn": c_dis_bn,
                    "confidence": round(float(p), 4),
                })

            best_idx = top_indices[0].item()
            best_prob = round(float(top_probs[0].item()), 4)
            best_raw_class = self._secondary_id2label[best_idx]

        crop, disease, crop_bn, disease_bn = parse_crop_and_disease(best_raw_class)

        return {
            "model_used": "secondary",
            "model_name": "Plant Disease MobileNetV2",
            "raw_class": best_raw_class,
            "crop": crop,
            "crop_bn": crop_bn,
            "disease": disease,
            "disease_bn": disease_bn,
            "confidence": best_prob,
            "top_predictions": top_predictions,
        }

    def predict_crop_disease(
        self,
        image: Image.Image,
        crop: Optional[str] = None,
        threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Executes OOD/Foliage check -> Crop-Aware BASE + SECONDARY fallback inference strategy.

        Step 1: OOD / Foliage Guardrail (rejects non-plant/road/vehicle images)
        Step 2: Canonicalize selected crop (from 16 supported crops)
        Step 3: Route to BASE model if crop supported; evaluate only candidate crop disease classes
        Step 4: If BASE confidence >= threshold (0.70) -> Return BASE result
        Step 5: If BASE confidence < threshold AND crop supported by SECONDARY -> Trigger SECONDARY fallback
        Step 6: If crop supported ONLY by SECONDARY -> Route directly to SECONDARY model
        """
        logger.info("[CropDisease] Image received for disease classification")
        logger.info("[CropDisease] OOD/Foliage check started")

        # Resolve Canonical Crop if provided
        canonical_crop: Optional[str] = None
        if crop:
            clean_crop = crop.strip()
            canonical_crop = CROP_LOOKUP_TO_CANONICAL.get(clean_crop) or CROP_LOOKUP_TO_CANONICAL.get(clean_crop.title())
            if not canonical_crop and clean_crop in CROP_LABELS_BN:
                canonical_crop = clean_crop

        crop_display_bn = CROP_LABELS_BN.get(canonical_crop, "অনির্ধারিত") if canonical_crop else "অনির্ধারিত"
        crop_display_en = canonical_crop or "Unknown"

        # Step 1: OOD / Foliage Guardrail Check
        is_plant, veg_ratio = check_is_plant_or_leaf(image)
        logger.info(f"[CropDisease] Plant foliage ratio: {veg_ratio:.4f} (is_plant: {is_plant})")

        if not is_plant:
            logger.warning(f"[CropDisease] Plant detected: False. Rejecting image (foliage ratio: {veg_ratio:.3f})")
            return {
                "success": False,
                "reason": "no_plant_detected",
                "is_plant_leaf": False,
                "crop": crop_display_en,
                "crop_bn": crop_display_bn,
                "disease": "গাছ বা পাতার ছবি নয়",
                "disease_bn": "গাছ বা পাতার ছবি নয়",
                "raw_class": "Out_Of_Distribution_Non_Plant",
                "confidence": 0.0,
                "model_used": "ood_filter",
                "model_name": "উদ্ভিদ সনাক্তকরণ ফিল্টার",
                "top_predictions": [],
                "guidance": [
                    "আক্রান্ত ফসল বা গাছের পাতার একটি পরিষ্কার ও সরাসরি ছবি আপলোড করুন।",
                    "রাস্তাঘাট, যানবাহন বা অন্য কোনো অপ্রাসঙ্গিক বস্তুর ছবি রোগ নির্ণয়ে প্রযোজ্য নয়।",
                ],
                "reason_summary": [
                    "ছবিটিতে ফসল বা পাতার কোনো স্বাভাবিক জৈব বৈশিষ্ট্য পরিলক্ষিত হয়নি।"
                ],
                "escalation_recommended": False,
                "disclaimer": DISCLAIMER_TEXT,
            }

        logger.info(f"[CropDisease] Plant detected: True. Selected crop: {canonical_crop} ({crop_display_bn})")
        active_threshold = threshold if threshold is not None else settings.BASE_THRESHOLD

        # Step 2: Crop-Aware Inference & Routing
        selected_res: Dict[str, Any]

        if canonical_crop and canonical_crop in BASE_SUPPORTED_CROPS:
            # Crop supported by BASE model (Rice, Corn, Wheat, Potato, Tomato)
            logger.info(f"[CropDisease] Running BASE model for crop: {canonical_crop}")
            base_res = self.predict_base(image, target_crop=canonical_crop)
            base_confidence = base_res["confidence"]
            logger.info(f"[CropDisease] BASE confidence: {base_confidence:.4f} (threshold: {active_threshold})")

            if base_confidence >= active_threshold or canonical_crop not in SECONDARY_SUPPORTED_CROPS:
                selected_res = base_res
                logger.info(f"[CropDisease] BASE model accepted: {base_res['raw_class']}")
            else:
                logger.info(
                    f"[CropDisease] BASE confidence low ({base_confidence:.4f} < {active_threshold}). "
                    f"Triggering SECONDARY fallback for crop: {canonical_crop}..."
                )
                selected_res = self.predict_secondary(image, target_crop=canonical_crop)
                logger.info(f"[CropDisease] SECONDARY fallback accepted: {selected_res['raw_class']}")

        elif canonical_crop and canonical_crop in SECONDARY_SUPPORTED_CROPS:
            # Crop supported ONLY by SECONDARY model (Apple, Grape, Orange, Peach, Bell Pepper, etc.)
            logger.info(f"[CropDisease] Crop {canonical_crop} is handled by SECONDARY model.")
            selected_res = self.predict_secondary(image, target_crop=canonical_crop)
            logger.info(f"[CropDisease] SECONDARY model accepted: {selected_res['raw_class']}")

        else:
            # Unconditioned Fallback if crop was not specified or matched
            logger.info("[CropDisease] Running unconditioned BASE model...")
            base_res = self.predict_base(image, target_crop=None)
            if base_res["confidence"] >= active_threshold:
                selected_res = base_res
            else:
                logger.info("Triggering unconditioned SECONDARY fallback...")
                selected_res = self.predict_secondary(image, target_crop=None)

        # Lookup certified agronomic guidance from knowledge base
        crop_name = selected_res["crop"]
        disease_name = selected_res["disease"]
        cond_knowledge = get_crop_disease_knowledge(crop=crop_name, disease=disease_name)

        is_healthy = cond_knowledge.get("is_healthy", False) or disease_name == "Healthy"
        primary_solution = cond_knowledge.get("primary_solution", "")
        guidance = cond_knowledge.get("guidance", [])
        avoid = cond_knowledge.get("avoid")
        prevention = cond_knowledge.get("prevention")
        special_warning = cond_knowledge.get("special_warning")

        if is_healthy:
            reason_summary = ["কোনো ক্ষতিকর ছত্রাক বা ব্যাকটেরিয়াজনিত সংক্রমণের লক্ষণ দৃশ্যমান নয়। গাছ সুস্থ রয়েছে।"]
            escalation = False
        else:
            reason_summary = [
                f"{selected_res['crop_bn']} ফসলের পাতায় {selected_res['disease_bn']} লক্ষণ প্রত্যক্ষ করা গেছে।"
            ]
            escalation = True if selected_res["confidence"] < 0.70 else False

        return {
            "success": True,
            "crop": selected_res["crop"],
            "crop_bn": selected_res["crop_bn"],
            "disease": selected_res["disease"],
            "disease_bn": selected_res["disease_bn"],
            "raw_class": selected_res["raw_class"],
            "confidence": selected_res["confidence"],
            "model_used": selected_res["model_used"],
            "model_name": selected_res["model_name"],
            "top_predictions": selected_res["top_predictions"],
            "primary_solution": primary_solution,
            "guidance": guidance,
            "avoid": avoid,
            "prevention": prevention,
            "special_warning": special_warning,
            "is_healthy": is_healthy,
            "reason_summary": reason_summary,
            "escalation_recommended": escalation,
            "disclaimer": DISCLAIMER_TEXT,
        }


# Global instance
vision_classifier = CropDiseaseVisionService.get_instance()


# Helper convenience functions
def load_base_model():
    return vision_classifier.load_base_model()


def load_secondary_model():
    return vision_classifier.load_secondary_model()


def predict_base(image: Image.Image, target_crop: Optional[str] = None) -> Dict[str, Any]:
    return vision_classifier.predict_base(image, target_crop=target_crop)


def predict_secondary(image: Image.Image, target_crop: Optional[str] = None) -> Dict[str, Any]:
    return vision_classifier.predict_secondary(image, target_crop=target_crop)


def predict_crop_disease(
    image: Image.Image,
    crop: Optional[str] = None,
    threshold: Optional[float] = None,
) -> Dict[str, Any]:
    return vision_classifier.predict_crop_disease(image, crop=crop, threshold=threshold)
