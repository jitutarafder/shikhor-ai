"""Bangla and Banglish NLP Intent and Symptom Classification Model.

Provides lightweight, fast, offline-capable intent classification, crop auto-detection,
and symptom-to-disease matching for both Bangla script and phonetic Banglish input.
Complies with AGENTS.md Rule 19.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# =====================================================================
# 1. Phonetic Banglish & Bangla Normalization Lexicon
# =====================================================================

CROP_MAPPINGS: Dict[str, List[str]] = {
    "ধান": [
        "ধান", "ধানে", "ধানের", "চাল", "dhan", "dhaan", "dhaner", "dhane", "rice", "paddy", "chawl"
    ],
    "আলু": [
        "আলু", "আলুতে", "আলুর", "alu", "aloo", "alur", "alute", "potato", "potatoes"
    ],
    "টমেটো": [
        "টমেটো", "টমেটোর", "টমেটোতে", "টমেটু", "tomato", "tomatoes", "tomator", "tometo", "tamatar"
    ],
    "গম": [
        "গম", "গমে", "গমের", "gom", "gomer", "gome", "wheat"
    ],
    "ভুট্টা": [
        "ভুট্টা", "ভুট্টায়", "ভুট্টার", "bhutta", "bhuttar", "butta", "vutta", "maize", "corn"
    ],
    "বেগুন": [
        "বেগুন", "বেগুনে", "বেগুনের", "begun", "beguner", "begune", "brinjal", "eggplant", "baigon"
    ],
    "মরিচ": [
        "মরিচ", "মরিচে", "মরিচের", "লঙ্কা", "morich", "moricher", "moriche", "moris", "chili", "chilli", "chili-r"
    ],
    "সরিষা": [
        "সরিষা", "সরিষায়", "সরিষার", "sorisha", "sorishar", "shorisha", "shorishar", "sorisa", "mustard"
    ],
    "পাট": [
        "পাট", "পাটে", "পাটের", "pat", "paat", "pater", "pate", "jute"
    ],
    "পেঁয়াজ": [
        "পেঁয়াজ", "পেয়াজ", "পেঁয়াজের", "পেয়াজের", "peyaj", "peyajer", "piyaj", "piyazer", "onion", "pyaj"
    ],
}

SYMPTOM_PHONETIC_SYNONYMS: Dict[str, List[str]] = {
    "পাতা": ["pata", "patay", "patar", "leaf", "leaves", "পাতা", "পাতায়", "পাতার"],
    "হলুদ": ["holud", "holod", "yellow", "halud", "হলুদ", "হলদে", "হলদেটে"],
    "দাগ": ["dag", "daag", "spot", "spots", "blotch", "dhaag", "দাগ", "দাগযুক্ত", "ছিটদাগ"],
    "পোড়া": ["pora", "pora rog", "burn", "burnt", "blight", "পোড়া", "ঝলসানো", "ব্লাইট"],
    "শুকিয়ে": ["shukiye", "shukay", "sukhe", "dry", "drying", "shukanor", "শুকিয়ে", "শুকনো", "শুকাচ্ছে"],
    "ব্লাস্ট": ["blast", "blust", "blast rog", "ব্লাস্ট", "ব্লাস্ট রোগ"],
    "কালো": ["kalo", "kala", "black", "dark", "কালো", "কালচে"],
    "পচন": ["pacha", "pache", "rot", "rotting", "pachan", "poche", "পচা", "পচন", "পচে"],
    "কোঁকড়ানো": ["kokrano", "mochray", "curling", "curl", "murchano", "কোঁকড়ানো", "কুঁকড়ে", "মোচড়ানো"],
    "মরিচা": ["moricha", "murcha", "rust", "morica", "মরিচা", "মরিচা রোগ", "রাস্ট"],
    "ছিদ্র": ["chidro", "futo", "hole", "holes", "keta", "ছিদ্র", "কাটা", "ফুটো"],
    "পোকা": ["poka", "kida", "insect", "pest", "leeda", "worm", "armyworm", "bichapoka", "পোকা", "কীট", "লেদা"],
    "ঢলে পড়া": ["dhole pora", "dholay", "wilt", "wilting", "ঢলে পড়া", "ঢলে", "নেতিয়ে পড়া"],
    "ফল পচা": ["fol pacha", "fruit rot", "anthracnose", "ফল পচা", "অ্যানথ্রাকনোজ"],
    "সাদা গুঁড়া": ["sada guro", "shada guro", "white rust", "white powder", "সাদা গুঁড়া", "সাদা পাউডার"],
    "বেগুনি": ["beguni", "purple", "violet", "beguni dag", "বেগুনি", "পার্পল"],
}

INTENT_DEFINITIONS = {
    "DIAGNOSE_DISEASE": [
        "rog", "problem", "somossa", "symptom", "lokkhon", "ki rog", "kiser rog",
        "রোগ", "সমস্যা", "লক্ষণ", "কী রোগ", "কী হয়েছে", "অসুখ", "আক্রান্ত", "কী করব"
    ],
    "PEST_CONTROL": [
        "poka", "bichapoka", "leeda", "majra", "pest", "insect", "dhamon",
        "পোকা", "মাজরা", "লেদা", "বিছা", "কীটপতঙ্গ", "দমন"
    ],
    "PREVENTION_ADVICE": [
        "protirodh", "protikar", "upai", "advice", "paramorsho", "prevention",
        "প্রতিরোধ", "প্রতিকার", "উপায়", "পরামর্শ", "বাঁচার উপায়"
    ],
    "FERTILIZER_SOIL": [
        "shar", "sar", "urea", "potash", "mop", "dap", "fertilizer", "mati",
        "সার", "ইউরিয়া", "পটাশ", "টিএসপি", "এমওপি", "মাটি"
    ],
}


@dataclass
class SymptomIntentResult:
    detected_crop: Optional[str]
    detected_crop_bn: Optional[str]
    detected_intent: str
    intent_confidence: float
    matched_condition_key: Optional[str]
    possible_condition_bn: Optional[str]
    confidence: float
    confidence_band: str
    matched_symptoms_bn: List[str] = field(default_factory=list)
    matched_tokens: List[str] = field(default_factory=list)
    reason_summary: List[str] = field(default_factory=list)
    guidance: List[str] = field(default_factory=list)
    escalation_recommended: bool = False
    disclaimer: str = ""


# =====================================================================
# 2. Lightweight Bangla & Banglish NLP Engine
# =====================================================================

class BanglaBanglishNLPEngine:
    """Hybrid rule + phonetic n-gram + TF-IDF similarity matcher for Bangla & Banglish."""

    def __init__(self):
        self._build_vocab()

    def _build_vocab(self):
        """Precomputes reverse lookup indexes for rapid token matching."""
        self.crop_lookup: Dict[str, str] = {}
        for crop_bn, aliases in CROP_MAPPINGS.items():
            for alias in aliases:
                self.crop_lookup[alias.lower().strip()] = crop_bn

        self.symptom_lookup: Dict[str, str] = {}
        for sym_bn, aliases in SYMPTOM_PHONETIC_SYNONYMS.items():
            for alias in aliases:
                self.symptom_lookup[alias.lower().strip()] = sym_bn

    def clean_text(self, text: str) -> str:
        """Removes punctuation and normalizes spacing."""
        cleaned = re.sub(r"[^\w\s\u0980-\u09FF]", " ", text.lower())
        return re.sub(r"\s+", " ", cleaned).strip()

    def tokenize(self, text: str) -> List[str]:
        """Tokenizes text into words and 2-word n-grams."""
        cleaned = self.clean_text(text)
        words = cleaned.split()
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
        return words + bigrams

    def detect_crop(self, text: str, user_selected_crop: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """Detects crop name from Bangla or Banglish text with user selection fallback."""
        tokens = self.tokenize(text)
        for token in tokens:
            # 1. Direct match
            if token in self.crop_lookup:
                crop_bn = self.crop_lookup[token]
                return crop_bn, f"{crop_bn}"
            # 2. Strip common Banglish/Bangla grammatical suffixes (-r, -er, -te, -e, -র, -ের, -তে, -য়)
            for suffix in ["er", "ar", "r", "te", "e", "y", "ay", "ের", "র", "তে", "ে", "য়", "ায়"]:
                if token.endswith(suffix) and len(token) > len(suffix) + 2:
                    stem = token[:-len(suffix)]
                    if stem in self.crop_lookup:
                        crop_bn = self.crop_lookup[stem]
                        return crop_bn, f"{crop_bn}"

        if user_selected_crop:
            clean_sel = user_selected_crop.strip().lower()
            for token in [clean_sel] + clean_sel.split():
                if token in self.crop_lookup:
                    crop_bn = self.crop_lookup[token]
                    return crop_bn, f"{crop_bn}"
            # Direct match
            if user_selected_crop in CROP_MAPPINGS:
                return user_selected_crop, f"{user_selected_crop}"

        return None, None

    def detect_intent(self, text: str) -> Tuple[str, float]:
        """Classifies intent into diagnostic, pest control, prevention, or general inquiry."""
        tokens = self.tokenize(text)
        scores: Dict[str, int] = {intent: 0 for intent in INTENT_DEFINITIONS}

        for token in tokens:
            for intent, keywords in INTENT_DEFINITIONS.items():
                for kw in keywords:
                    if kw in token or token in kw:
                        scores[intent] += 1

        best_intent = "DIAGNOSE_DISEASE"
        max_score = scores[best_intent]

        for intent, score in scores.items():
            if score > max_score:
                best_intent = intent
                max_score = score

        confidence = 0.85 if max_score >= 2 else (0.70 if max_score == 1 else 0.55)
        return best_intent, confidence

    def extract_symptoms(self, text: str) -> Tuple[List[str], List[str]]:
        """Extracts recognized Bangla symptom concepts and source tokens from text."""
        tokens = self.tokenize(text)
        matched_symptoms: Set[str] = set()
        matched_tokens: Set[str] = set()

        for token in tokens:
            if token in self.symptom_lookup:
                sym_concept = self.symptom_lookup[token]
                matched_symptoms.add(sym_concept)
                matched_tokens.add(token)

        return sorted(list(matched_symptoms)), sorted(list(matched_tokens))

    def analyze_crop_symptoms(
        self,
        symptoms_text: str,
        user_crop: Optional[str] = None,
        reviewed_conditions: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> SymptomIntentResult:
        """Performs full Bangla/Banglish intent classification & disease matching."""
        from app.modules.crop_assistant.knowledge_base import (
            DISCLAIMER_TEXT,
            REVIEWED_CONDITIONS,
        )

        conditions_db = reviewed_conditions or REVIEWED_CONDITIONS
        text = symptoms_text.strip() if symptoms_text else ""

        detected_crop, detected_crop_bn = self.detect_crop(text, user_crop)
        intent, intent_conf = self.detect_intent(text)
        symptoms_bn, tokens_matched = self.extract_symptoms(text)

        if not text and not detected_crop:
            return SymptomIntentResult(
                detected_crop=None,
                detected_crop_bn=None,
                detected_intent="DIAGNOSE_DISEASE",
                intent_confidence=0.5,
                matched_condition_key=None,
                possible_condition_bn=None,
                confidence=0.0,
                confidence_band="low",
                reason_summary=["কোনো লক্ষণ বা ফসলের বিবরণ দেওয়া হয়নি।"],
                guidance=["আক্রান্ত পাতার ছবি তুলুন অথবা বাংলা/বাংলিশে লক্ষণ উল্লেখ করুন।"],
                escalation_recommended=True,
                disclaimer=DISCLAIMER_TEXT,
            )

        # Match against conditions in knowledge base
        best_cond_key: Optional[str] = None
        best_cond_data: Optional[Dict[str, Any]] = None
        highest_score = 0.0

        target_crop = detected_crop or user_crop or ""

        for cond_key, cond_data in conditions_db.items():
            cond_crop = cond_data.get("crop", "")
            crop_match = (
                target_crop.lower() in cond_crop.lower()
                or cond_crop.lower() in target_crop.lower()
            ) if target_crop else False

            score = 0.0
            if crop_match:
                score += 0.40

            # Match keywords
            keywords = cond_data.get("keywords", [])
            matched_kws = 0
            for kw in keywords:
                clean_kw = kw.lower().strip()
                if clean_kw in text.lower():
                    matched_kws += 1
                else:
                    # Check phonetic aliases
                    if clean_kw in self.symptom_lookup:
                        sym = self.symptom_lookup[clean_kw]
                        if sym in symptoms_bn:
                            matched_kws += 1

            if matched_kws > 0:
                score += min(0.50, matched_kws * 0.20)

            if score > highest_score:
                highest_score = score
                best_cond_key = cond_key
                best_cond_data = cond_data

        if best_cond_data and highest_score >= 0.40:
            final_conf = min(0.92, highest_score + (0.10 if len(tokens_matched) >= 2 else 0.0))
            conf_band = "high" if final_conf >= 0.75 else ("medium" if final_conf >= 0.50 else "low")

            return SymptomIntentResult(
                detected_crop=target_crop,
                detected_crop_bn=best_cond_data.get("crop", target_crop),
                detected_intent=intent,
                intent_confidence=intent_conf,
                matched_condition_key=best_cond_key,
                possible_condition_bn=best_cond_data.get("condition_name_bn"),
                confidence=round(final_conf, 2),
                confidence_band=conf_band,
                matched_symptoms_bn=symptoms_bn,
                matched_tokens=tokens_matched,
                reason_summary=best_cond_data.get("reason_summary", []),
                guidance=best_cond_data.get("guidance", []),
                escalation_recommended=(final_conf < 0.60),
                disclaimer=DISCLAIMER_TEXT,
            )

        # Fallback if no specific condition met threshold
        return SymptomIntentResult(
            detected_crop=target_crop if target_crop else None,
            detected_crop_bn=target_crop if target_crop else None,
            detected_intent=intent,
            intent_confidence=intent_conf,
            matched_condition_key=None,
            possible_condition_bn=None,
            confidence=0.35,
            confidence_band="low",
            matched_symptoms_bn=symptoms_bn,
            matched_tokens=tokens_matched,
            reason_summary=["উল্লেখিত লক্ষণের সাথে সুনির্দিষ্ট কোনো একক রোগের সরাসরি মিল পাওয়া যায়নি।"],
            guidance=["পরিষ্কার আলোতে আরও বিস্তারিত লক্ষণ লিখুন বা উপ-সহকারী কৃষি কর্মকর্তার (SAAO) সহায়তা নিন।"],
            escalation_recommended=True,
            disclaimer=DISCLAIMER_TEXT,
        )


# Global singleton instance
nlp_engine = BanglaBanglishNLPEngine()
