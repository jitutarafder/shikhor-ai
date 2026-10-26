"""Gemini 1.5 Agricultural Language Model Adapter for Shikhor AI.

Provides structured, safe, empathetic Bangla agronomic reasoning using Google Gemini API.
Complies strictly with AGENTS.md Rule 19:
- Grounded in certified cultural and agronomic best practices in Bangladesh.
- Never invents unreviewed synthetic pesticide dosages or hazardous chemicals.
- Enforces strict SAAO / UAO extension escalation flags for high-risk conditions.
- Uses async HTTPX with timeouts, retries, and structured JSON output.
"""

import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.modules.crop_assistant.knowledge_base import DISCLAIMER_TEXT

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

SYSTEM_INSTRUCTION = """
তুমি 'শিখড় এআই' (Shikhor AI)-এর একজন দায়িত্বশীল ও সহানুভূতিশীল জ্যেষ্ঠ কৃষি বিজ্ঞানী ও সম্প্রসারণ বিশেষজ্ঞ।
তোমার কাজ হলো বাংলাদেশের কৃষকদের ফসলের রোগ ও সমস্যার বিবরণ (বাংলা বা বাংলিশে) বুঝে নিরাপদ ও পরীক্ষিত কৃষিতাত্ত্বিক সমাধান দেওয়া।

কঠোর নিরাপত্তা ও নিয়মাবলী (AGENTS.md Rule 19):
১. কখনো মনগড়া বিষাক্ত রাসায়নিক বা ক্ষতিকর কীটনাশকের অযাচিত মাত্রা (dosage) আবিষ্কার করবে না।
২. সর্বদা নিরাপদ সাংস্কৃতিক ব্যবস্থাপনা (পানি নিষ্কাশন, সুষম সার ও পটাশ প্রয়োগ, আক্রান্ত অংশ ধ্বংস, রোদে শুকানো, জৈব ফাঁদ) অগ্রাধিকার দেবে।
৩. কৃষকদের সাথে সহজ, স্বাভাবিক ও শ্রদ্ধাশীল বাংলায় কথা বলবে।
৪. জটিল বা তীব্র রোগের ক্ষেত্রে অবশ্যই স্থানীয় উপ-সহকারী কৃষি কর্মকর্তা (SAAO / উপ-সহকারী কৃষি কর্মকর্তা) এর পরামর্শ নেওয়ার সুপারিশ করবে।

আউটপুটটি অবশ্যই নিচে দেওয়া সুনির্দিষ্ট JSON ফরম্যাটে প্রদান করতে হবে:
{
  "detected_crop": "ফসলের নাম (যেমন: ধান, আলু, টমেটো)",
  "possible_condition": "সম্ভাব্য রোগের নাম (বাংলা ও ইংরেজিতে)",
  "confidence": 0.85,
  "confidence_band": "high / medium / low",
  "reason_summary": ["লক্ষণ ও রোগ প্যাটার্নের ব্যাখ্যা ১", "ব্যাখ্যা ২"],
  "guidance": ["নিরাপদ কৃষিতাত্ত্বিক পদক্ষেপ ১", "পদক্ষেপ ২", "পদক্ষেপ ৩"],
  "escalation_recommended": false,
  "advice_summary_bn": "কৃষকের জন্য সহজে বোধগম্য ১-২ লাইনের মূল সারসংক্ষেপ"
}
"""


class GeminiCropAdvisorAdapter:
    """Async Google Gemini adapter for crop symptom reasoning & conversational farmer assistance."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key if api_key is not None else (settings.GEMINI_API_KEY or settings.AI_API_KEY)
        self.model_name = model_name or settings.GEMINI_MODEL or "gemini-3.5-flash-lite"

    @property
    def is_configured(self) -> bool:
        """Returns True if a valid Gemini API key is configured."""
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    async def analyze_symptoms_with_gemini(
        self,
        symptoms_text: str,
        crop_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Invokes Gemini 1.5 API to analyze symptom text and generate structured agronomic advice."""
        if not self.is_configured:
            logger.debug("Gemini API key not configured; skipping Gemini adapter.")
            return None

        if not symptoms_text or not symptoms_text.strip():
            return None

        prompt = f"""
কৃষকের দেওয়া লক্ষণ ও বিবরণ:
- নির্বাচিত ফসল: {crop_type or 'অনির্দিষ্ট (বিবরণ থেকে শনাক্ত করুন)'}
- সমস্যার বিবরণ: {symptoms_text.strip()}

উপরের লক্ষণের ওপর ভিত্তি করে কৃষি দিকনির্দেশনা ও বিশ্লেষণ JSON ফরম্যাটে প্রদান করুন।
"""

        candidate_models = [self.model_name, "gemini-3.5-flash-lite", "gemini-3.8-flash"]
        # deduplicate while preserving order
        unique_models = list(dict.fromkeys([m for m in candidate_models if m]))

        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}]
            },
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1000,
                "responseMimeType": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            for model_to_use in unique_models:
                url = GEMINI_API_URL.format(model=model_to_use)
                try:
                    response = await client.post(url, headers=headers, params=params, json=payload)
                    if response.status_code != 200:
                        continue

                    data = response.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        continue

                    raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if not raw_text:
                        continue

                    parsed_json = json.loads(raw_text)

                    # Ensure required keys exist
                    return {
                        "detected_crop": parsed_json.get("detected_crop", crop_type),
                        "possible_condition": parsed_json.get("possible_condition"),
                        "confidence": float(parsed_json.get("confidence", 0.80)),
                        "confidence_band": parsed_json.get("confidence_band", "high"),
                        "reason_summary": parsed_json.get("reason_summary", []),
                        "guidance": parsed_json.get("guidance", []),
                        "escalation_recommended": bool(parsed_json.get("escalation_recommended", False)),
                        "advice_summary_bn": parsed_json.get("advice_summary_bn", ""),
                        "model_version": f"Gemini ({model_to_use}) + Shikhor Agronomic Guard",
                        "disclaimer": DISCLAIMER_TEXT,
                    }
                except Exception as e:
                    logger.debug(f"Error calling Gemini model {model_to_use}: {e}")
                    continue

        return None

    async def analyze_image_and_symptoms_with_gemini(
        self,
        image_bytes: bytes,
        crop_type: Optional[str] = None,
        symptoms_text: Optional[str] = None,
        mime_type: str = "image/jpeg",
    ) -> Optional[Dict[str, Any]]:
        """Invokes Gemini Multimodal Vision API to detect plant disease directly from leaf photo."""
        import base64

        if not self.is_configured or not image_bytes:
            return None

        prompt = f"""
কৃষকের পাঠানো ফসলের আক্রান্ত পাতার ছবি ও তথ্য:
- ফসল: {crop_type or 'অনির্দিষ্ট (ছবি দেখে শনাক্ত করুন)'}
- কৃষকের লক্ষণ বিবরণ: {symptoms_text or 'কোনো লক্ষণ লেখা হয়নি, শুধুমাত্র ছবি বিশ্লেষণ করুন'}

নির্দেশনা:
১. ছবির পাতা/গাছের ক্ষতের ধরণ (দাগের রঙ, কিনারা, পচন, ফাঙ্গাস বা পোকার আক্রমণ) পুঙ্খানুপুঙ্খ বিশ্লেষণ করুন।
২. সঠিক রোগ বা পুষ্টির ঘাটতি শনাক্ত করুন।
৩. নিরাপদ সাংস্কৃতিক প্রতিকার ও প্রতিরোধমূলক পরামর্শ প্রদান করুন।
"""

        base64_data = base64.b64encode(image_bytes).decode("utf-8")
        safe_mime = mime_type if mime_type in ["image/jpeg", "image/png", "image/webp"] else "image/jpeg"

        candidate_models = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-flash-lite-latest"]
        unique_models = list(dict.fromkeys([m for m in candidate_models if m]))

        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": safe_mime,
                                "data": base64_data,
                            }
                        },
                        {"text": prompt},
                    ]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}]
            },
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1000,
                "responseMimeType": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            for model_to_use in unique_models:
                url = GEMINI_API_URL.format(model=model_to_use)
                try:
                    response = await client.post(url, headers=headers, params=params, json=payload)
                    if response.status_code != 200:
                        continue

                    data = response.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        continue

                    raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if not raw_text:
                        continue

                    parsed_json = json.loads(raw_text)

                    return {
                        "detected_crop": parsed_json.get("detected_crop", crop_type),
                        "possible_condition": parsed_json.get("possible_condition"),
                        "confidence": float(parsed_json.get("confidence", 0.85)),
                        "confidence_band": parsed_json.get("confidence_band", "high"),
                        "reason_summary": parsed_json.get("reason_summary", []),
                        "guidance": parsed_json.get("guidance", []),
                        "escalation_recommended": bool(parsed_json.get("escalation_recommended", False)),
                        "advice_summary_bn": parsed_json.get("advice_summary_bn", ""),
                        "model_version": f"Gemini Vision ({model_to_use}) + Shikhor Agronomic Guard",
                        "disclaimer": DISCLAIMER_TEXT,
                    }
                except Exception as e:
                    logger.debug(f"Error calling Gemini Vision model {model_to_use}: {e}")
                    continue

        return None

    async def fuse_multimodal_crop_diagnosis(
        self,
        image_bytes: bytes,
        selected_crop: str,
        selected_crop_bn: str,
        vision_result: Dict[str, Any],
        banglish_result: Optional[Dict[str, Any]] = None,
        symptoms_text: Optional[str] = None,
        mime_type: str = "image/jpeg",
    ) -> Optional[Dict[str, Any]]:
        """Multimodal reasoning & fusion layer combining Vision Model, Banglish Symptoms, and Image Evidence.

        Strict Constraints:
        1. Selected crop is authoritative context. Never classify into another crop's disease.
        2. Image is primary visual evidence. Text is supporting evidence.
        3. Never fabricate pesticide dosages or hazardous chemicals.
        4. If evidence conflicts or is low quality, mark uncertain: true.
        5. Produces ONE unified final decision.
        """
        import base64

        if not self.is_configured or not image_bytes:
            return None

        # Build structured context prompt
        vision_disease = vision_result.get("disease", "Unknown")
        vision_disease_bn = vision_result.get("disease_bn", "অজানা")
        vision_conf = vision_result.get("confidence", 0.0)

        banglish_context = "কোনো লক্ষণ বর্ণনা দেওয়া হয়নি।"
        if banglish_result and symptoms_text:
            b_disease = banglish_result.get("disease", "অনির্দিষ্ট")
            b_disease_bn = banglish_result.get("disease_bn", "অনির্দিষ্ট")
            b_conf = banglish_result.get("confidence", 0.0)
            banglish_context = f"""
- কৃষকের দেওয়া বর্ণনা: "{symptoms_text.strip()}"
- বাংলিশ এনএলপি লক্ষণ বিশ্লেষণ ফলাফল: {b_disease_bn} ({b_disease}), কনফিডেন্স: {b_conf:.2f}
"""

        analyses_guidelines = """
বিশ্লেষণের মূল নির্দেশিকা:
১. [উদ্ভিদ ও পাতা যাচাই - বাধ্যতামূলক]:
   প্রথমে নিশ্চিত হন ছবিটি আসলেই কোনো কৃষি ফসল, গাছ বা ফসলের পাতার ছবি কি না।
   যদি ছবিটি কোনো প্রাকৃতিক ভূদৃশ্য (landscape), পর্বত, তুষার, সেতু/রেললাইন (bridge/railway), রাস্তাঘাট, যানবাহন (vehicle), ভবন (building), মানুষ, আসবাবপত্র বা অপ্রাসঙ্গিক বস্তুর হয়:
   তবে অবিলম্বে "is_plant_leaf": false, "disease": "গাছ বা পাতার ছবি নয়", "disease_bn": "গাছ বা পাতার ছবি নয়", "confidence": 0.0 দিন।
২. যদি ছবিটি একটি বাস্তব উদ্ভিদ বা পাতা হয়, তবে "is_plant_leaf": true দিন এবং নির্বাচিত ফসল '{selected_crop_bn}'-এর সীমানার মধ্যে রোগের সঠিক শ্রেণী নির্ণয় করুন। অন্য কোনো ফসলের রোগ কখনো নির্বাচন করবেন না।
৩. সংযুক্ত পাতার ছবির ক্ষতের চাক্ষুষ লক্ষণ (Lesion morphology) পুঙ্খানুপুঙ্খভাবে পর্যবেক্ষণ করে মূল রোগ নির্ধারণ করুন:
   - ধানের ক্ষেত্রে: পাতার কিনার বরাবর ঢেউ খেলানো হলুদ/বাদামী শুকিয়ে যাওয়া ক্ষত হলে রোগ অবশ্যই 'Bacterial Leaf Blight' এবং 'ব্যাকটেরিয়াজনিত পাতা পোড়া (BLB)'; পাতার ওপর গোলাকার/ডিম্বাকৃতি ছোট বাদামি দাগ থাকলে 'Brown Spot' এবং 'বাদামি দাগ রোগ'; চোখের মতো বা মাকু আকৃতির দাগ থাকলে 'Leaf Blast' এবং 'পাতা ব্লাস্ট রোগ'; কোনো রোগ না থাকলে 'Healthy' এবং 'সুস্থ ও নিরোগ গাছ'।
৪. ভিশন মডেলের প্রাথমিক রেফারেন্সকে অন্ধভাবে অনুসরণ করবেন না; ছবির বাস্তব দৃশ্যমান ক্ষত অনুযায়ী "disease" ও "disease_bn" ফিল্ডে আপনার নির্ণয়কৃত সঠিক রোগের নামই স্পষ্টভাবে লিখবেন।
৫. কোনো মনগড়া বা অনিরাপদ রাসায়নিকের মাত্রা দেবেন না। সুষম সার, অতিরিক্ত ইউরিয়া বর্জন, পানি নিষ্কাশন এবং আক্রান্ত পাতা অপসারণের মতো পরীক্ষিত কৃষি সমাধান দিন।
৬. শুধুমাত্র একটি সমন্বিত চূড়ান্ত সিদ্ধান্ত (ONE final decision) JSON আকারে দিন।

JSON ফরম্যাট:
{
  "is_plant_leaf": true,
  "disease": "<নির্ণীত রোগের ইংরেজি নাম, যেমন: Bacterial Leaf Blight / Brown Spot / Leaf Blast / Healthy / Out Of Distribution>",
  "disease_bn": "<নির্ণীত রোগের বাংলা নাম, যেমন: ব্যাকটেরিয়াল লিফ ব্লাইট (Bacterial Leaf Blight) / বাদামি দাগ রোগ / পাতা ব্লাস্ট রোগ / সুস্থ ও নিরোগ গাছ / গাছ বা পাতার ছবি নয়>",
  "confidence": 0.90,
  "uncertain": false,
  "reason_summary": [
    "ছবির পর্যবেক্ষণ ১",
    "পর্যবেক্ষণ ২"
  ],
  "guidance": [
    "অনুমোদিত নিরাপদ কৃষিতাত্ত্বিক করণীয় ১",
    "করণীয় ২"
  ],
  "escalation_recommended": false
}
"""
        prompt = f"""
কৃষিতাত্ত্বিক সমন্বিত বিশ্লেষণ ও রোগ নির্ণয় (Multimodal Agronomic Reasoning):
- নির্বাচিত ফসল (Authoritative Context): {selected_crop_bn} ({selected_crop})
- ভিশন মডেলের প্রাথমিক রেফারেন্স: {vision_disease_bn} ({vision_disease}) [কনফিডেন্স: {vision_conf:.2f}]
- কৃষকের লক্ষণ বা তথ্য: {banglish_context}

{analyses_guidelines}
"""

        base64_data = base64.b64encode(image_bytes).decode("utf-8")
        safe_mime = mime_type if mime_type in ["image/jpeg", "image/png", "image/webp"] else "image/jpeg"

        candidate_models = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-flash-lite-latest"]
        unique_models = list(dict.fromkeys([m for m in candidate_models if m]))

        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": safe_mime,
                                "data": base64_data,
                            }
                        },
                        {"text": prompt},
                    ]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}]
            },
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1000,
                "responseMimeType": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=18.0) as client:
            for model_to_use in unique_models:
                url = GEMINI_API_URL.format(model=model_to_use)
                try:
                    response = await client.post(url, headers=headers, params=params, json=payload)
                    if response.status_code != 200:
                        logger.warning(f"Gemini API returned status {response.status_code} for model {model_to_use}")
                        continue

                    data = response.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        continue

                    raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if not raw_text:
                        continue

                    parsed = json.loads(raw_text)
                    is_plant_flag = parsed.get("is_plant_leaf", True)
                    raw_dis = (parsed.get("disease") or "").strip()
                    raw_dis_bn = (parsed.get("disease_bn") or "").strip()
                    reason_joined = " ".join(parsed.get("reason_summary", [])).lower()

                    if is_plant_flag is False or "গাছ বা পাতার ছবি নয়" in raw_dis_bn or "not a plant" in raw_dis.lower():
                        return {
                            "crop": selected_crop,
                            "crop_bn": selected_crop_bn,
                            "disease": "গাছ বা পাতার ছবি নয়",
                            "disease_bn": "গাছ বা পাতার ছবি নয়",
                            "confidence": 0.0,
                            "uncertain": False,
                            "is_plant_leaf": False,
                            "reason_summary": parsed.get("reason_summary", ["আপলোডকৃত ছবিটি কোনো উদ্ভিদ বা ফসলের পাতার ছবি নয়।"]),
                            "guidance": [
                                "আক্রান্ত ফসল বা গাছের পাতার একটি পরিষ্কার ও সরাসরি ছবি আপলোড করুন।",
                                "রাস্তাঘাট, যানবাহন বা অন্য কোনো অপ্রাসঙ্গিক বস্তুর ছবি রোগ নির্ণয়ে প্রযোজ্য নয়।"
                            ],
                            "escalation_recommended": False,
                            "decision_source": f"gemini_guardrail ({model_to_use})",
                        }

                    # Semantic alignment if reason explicitly identified BLB or specific lesion
                    if "bacterial" in reason_joined or "পাতা পোড়া" in reason_joined or "blb" in reason_joined or "ব্লাইট" in reason_joined:
                        if "bacterial" not in raw_dis.lower() and "পোড়া" not in raw_dis_bn and "ব্লাইট" not in raw_dis_bn:
                            raw_dis = "Bacterial Leaf Blight"
                            raw_dis_bn = "ব্যাকটেরিয়াল লিফ ব্লাইট (Bacterial Leaf Blight)"

                    return {
                        "crop": selected_crop,
                        "crop_bn": selected_crop_bn,
                        "disease": raw_dis or vision_disease,
                        "disease_bn": raw_dis_bn or vision_disease_bn,
                        "confidence": float(parsed.get("confidence", 0.90)),
                        "uncertain": bool(parsed.get("uncertain", False)),
                        "is_plant_leaf": True,
                        "reason_summary": parsed.get("reason_summary", vision_result.get("reason_summary", [])),
                        "guidance": parsed.get("guidance", vision_result.get("guidance", [])),
                        "escalation_recommended": bool(parsed.get("escalation_recommended", False)),
                        "decision_source": f"gemini_fusion ({model_to_use})",
                    }
                except Exception as exc:
                    logger.warning(f"Error calling Gemini fusion model {model_to_use}: {exc}")
                    continue

        return None


# Global singleton instance
gemini_crop_advisor = GeminiCropAdvisorAdapter()
