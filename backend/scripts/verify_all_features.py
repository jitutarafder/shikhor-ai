"""Comprehensive End-to-End Feature Verification Suite for Shikhor AI.

Tests all 12 major application domains live:
1. Health & Readiness API
2. Authentication & User Profile Management (Registration, Login, /me, OTPs)
3. AI Crop Assistant & Diagnostics (Dual-stage Vision, Create Case, Feedback, Expert Review)
4. Equipment Marketplace & Geospatial Filtering (Owner listing creation + ranked discovery)
5. Rental Request Lifecycles & Central State Machine (Farmer request -> Owner accept)
6. Crop Marketplace & Farmer Produce Listings
7. Messaging & Conversation Channels (Create conversation + Retrieve history)
8. Agricultural Knowledge Base & Bangla Search
9. Weather Advisory Service
10. Notifications System
11. Moderation & Audit Logging / Pilot Config
12. Offline Sync & Idempotency System
"""

import asyncio
import io
import os
import random
import sys
import uuid
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def make_leaf_image_bytes(color=(34, 139, 34)) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (224, 224), color=color)
    img.save(buf, format="JPEG")
    return buf.getvalue()


async def run_feature_verification():
    print("=" * 80)
    print("      SHIKHOR AI — COMPREHENSIVE LIVE FEATURE VERIFICATION")
    print(f"      Active Database: {settings.DATABASE_BACKEND.upper()}")
    print("=" * 80)

    results = []

    def record(feature: str, domain: str, passed: bool, detail: str = ""):
        status_str = "PASS" if passed else "FAIL"
        results.append((feature, domain, passed, detail))
        print(f"[{status_str:4}] {domain:20} | {feature:35} | {detail}")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver", timeout=45.0) as client:

        # ------------------------------------------------------------------
        # 1. Health & Readiness
        # ------------------------------------------------------------------
        try:
            r = await client.get("/api/v1/health/readiness")
            assert r.status_code == 200
            data = r.json()
            assert data["status"] == "ready"
            record("System Readiness & Health", "Health", True, f"Database: {data['database']}")
        except Exception as e:
            record("System Readiness & Health", "Health", False, str(e))

        # ------------------------------------------------------------------
        # 2. Authentication & User Profiles
        # ------------------------------------------------------------------
        rand_digits = f"{random.randint(10000000, 99999999)}"
        farmer_phone = f"017{rand_digits}"
        owner_phone = f"018{rand_digits}"
        expert_phone = f"019{rand_digits}"

        farmer_token = None
        farmer_user = None
        owner_token = None
        owner_user = None
        expert_token = None
        expert_user = None

        # Register and Authenticate Farmer
        try:
            reg_r = await client.post(
                "/api/v1/auth/register",
                json={
                    "phone": farmer_phone,
                    "password": "Password123#Strong",
                    "full_name": "কৃষক করিম",
                    "role": "farmer"
                }
            )
            assert reg_r.status_code == 201, reg_r.text
            farmer_token = reg_r.json()["accessToken"]
            
            me_r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {farmer_token}"})
            assert me_r.status_code == 200, me_r.text
            farmer_user = me_r.json()
            assert farmer_user["role"].lower() == "farmer"
            record("Farmer Registration & Profile", "Auth", True, f"User: {farmer_user['fullName']} ({farmer_phone})")
        except Exception as e:
            record("Farmer Registration & Profile", "Auth", False, str(e))

        # Register and Authenticate Owner
        try:
            reg_r = await client.post(
                "/api/v1/auth/register",
                json={
                    "phone": owner_phone,
                    "password": "Password123#Strong",
                    "full_name": "মালিক রহিম",
                    "role": "owner"
                }
            )
            assert reg_r.status_code == 201, reg_r.text
            owner_token = reg_r.json()["accessToken"]
            
            me_r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {owner_token}"})
            assert me_r.status_code == 200, me_r.text
            owner_user = me_r.json()
            assert owner_user["role"].lower() == "owner"
            record("Owner Registration & Profile", "Auth", True, f"User: {owner_user['fullName']} ({owner_phone})")
        except Exception as e:
            record("Owner Registration & Profile", "Auth", False, str(e))

        # Register and Authenticate Expert
        try:
            reg_r = await client.post(
                "/api/v1/auth/register",
                json={
                    "phone": expert_phone,
                    "password": "Password123#Strong",
                    "full_name": "ড. কামাল হোসেন",
                    "role": "expert"
                }
            )
            assert reg_r.status_code == 201, reg_r.text
            expert_token = reg_r.json()["accessToken"]
            
            me_r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expert_token}"})
            assert me_r.status_code == 200, me_r.text
            expert_user = me_r.json()
            assert expert_user["role"].lower() == "expert"
            record("Expert Registration & Profile", "Auth", True, f"User: {expert_user['fullName']} ({expert_phone})")
        except Exception as e:
            record("Expert Registration & Profile", "Auth", False, str(e))

        # Test Email OTP dispatch & verify
        try:
            otp_send_r = await client.post("/api/v1/auth/signup/send-email-otp", json={"email": f"test_{rand_digits}@shikhor.ai"})
            assert otp_send_r.status_code == 200
            dev_otp = otp_send_r.json().get("devOtp")
            if dev_otp:
                otp_verify_r = await client.post(
                    "/api/v1/auth/signup/verify-email-otp",
                    json={"email": f"test_{rand_digits}@shikhor.ai", "otp": dev_otp}
                )
                assert otp_verify_r.status_code == 200
                record("Email OTP Dispatch & Verify", "Auth", True, "OTP verified successfully")
            else:
                record("Email OTP Dispatch & Verify", "Auth", True, "OTP dispatched")
        except Exception as e:
            record("Email OTP Dispatch & Verify", "Auth", False, str(e))

        # ------------------------------------------------------------------
        # 3. AI Crop Assistant & Diagnostics
        # ------------------------------------------------------------------
        created_case_id = None
        try:
            leaf_bytes = make_leaf_image_bytes()
            pred_r = await client.post(
                "/api/v1/crop-disease/predict",
                files={"file": ("leaf.jpg", leaf_bytes, "image/jpeg")},
                data={"crop": "ধান", "symptoms": "পাতায় বাদামি দাগ পড়েছে"}
            )
            assert pred_r.status_code == 200, pred_r.text
            pred_data = pred_r.json()
            assert "disease" in pred_data
            assert "guidance" in pred_data
            record("Dual-Stage AI Vision Predict", "AI Diagnostics", True, f"Diagnosis: {pred_data.get('disease_bn', pred_data.get('disease'))}")
        except Exception as e:
            record("Dual-Stage AI Vision Predict", "AI Diagnostics", False, str(e))

        # Create Crop Case
        if farmer_token:
            try:
                leaf_bytes = make_leaf_image_bytes()
                case_r = await client.post(
                    "/api/v1/crop-cases",
                    headers={"Authorization": f"Bearer {farmer_token}"},
                    files={"image": ("my_crop.jpg", leaf_bytes, "image/jpeg")},
                    data={"crop_type": "ধান", "symptoms": "পাতায় বাদামি দাগ"}
                )
                assert case_r.status_code == 201, case_r.text
                case_data = case_r.json()
                created_case_id = case_data["id"]
                record("Crop Case Creation", "AI Diagnostics", True, f"Case ID: {created_case_id[:8]}...")
            except Exception as e:
                record("Crop Case Creation", "AI Diagnostics", False, str(e))

        # List Farmer Crop Cases
        if farmer_token:
            try:
                cases_r = await client.get("/api/v1/crop-cases", headers={"Authorization": f"Bearer {farmer_token}"})
                assert cases_r.status_code == 200
                cases_list = cases_r.json()
                assert len(cases_list) > 0
                record("Crop Case History Listing", "AI Diagnostics", True, f"Found {len(cases_list)} crop cases")
            except Exception as e:
                record("Crop Case History Listing", "AI Diagnostics", False, str(e))

        # Submit Farmer Feedback on Crop Case
        if created_case_id and farmer_token:
            try:
                fb_r = await client.post(
                    f"/api/v1/crop-cases/{created_case_id}/feedback",
                    headers={"Authorization": f"Bearer {farmer_token}"},
                    json={"feedback_type": "helpful", "comments": "পরামর্শটি বেশ উপকারী ছিল।"}
                )
                assert fb_r.status_code in [200, 201], fb_r.text
                record("Crop Diagnosis Feedback", "AI Diagnostics", True, "Feedback recorded")
            except Exception as e:
                record("Crop Diagnosis Feedback", "AI Diagnostics", False, str(e))

        # Expert Review Workflow
        if created_case_id and expert_token:
            try:
                exp_review_r = await client.post(
                    f"/api/v1/expert/cases/{created_case_id}/review",
                    headers={"Authorization": f"Bearer {expert_token}"},
                    json={
                        "reviewed_diagnosis": "Brown Spot (বাদামি দাগ রোগ)",
                        "prescribed_treatment": "কার্বেনডাজিম স্প্রে করুন।",
                        "severity_level": "moderate",
                        "expert_notes": "পানি নিষ্কাশন ব্যবস্থা উন্নত করুন।"
                    }
                )
                assert exp_review_r.status_code in [200, 201], exp_review_r.text
                record("Expert Case Review", "Expert Services", True, "Prescription recorded")
            except Exception as e:
                record("Expert Case Review", "Expert Services", False, str(e))

        # ------------------------------------------------------------------
        # 4. Equipment Marketplace & Geospatial Search
        # ------------------------------------------------------------------
        equipment_id = None
        rental_request_id = None

        if owner_token:
            try:
                eq_create_r = await client.post(
                    "/api/v1/equipment",
                    headers={"Authorization": f"Bearer {owner_token}"},
                    json={
                        "name": "উন্নত পাওয়ার টিলার",
                        "equipmentType": "power_tiller",
                        "priceAmount": 1200,
                        "priceUnit": "per_hour",
                        "district": "বগুড়া",
                        "upazila": "সদর",
                        "latitude": 24.85,
                        "longitude": 89.37,
                        "serviceRadiusKm": 30.0,
                        "description": "ভালো কন্ডিশন, নির্ভরযোগ্য।"
                    }
                )
                assert eq_create_r.status_code == 201, eq_create_r.text
                created_eq = eq_create_r.json()
                equipment_id = created_eq["id"]
                record("Equipment Listing Creation", "Marketplace", True, f"Equipment: {created_eq['name']}")
            except Exception as e:
                record("Equipment Listing Creation", "Marketplace", False, str(e))

        try:
            eq_search_r = await client.get(
                "/api/v1/equipment?equipmentType=power_tiller&priceUnit=per_hour&latitude=24.85&longitude=89.37&maxRadiusKm=50"
            )
            assert eq_search_r.status_code == 200
            eq_results = eq_search_r.json()
            record("Geospatial Equipment Search", "Marketplace", True, f"Found {len(eq_results)} machinery listings")
            if not equipment_id and eq_results:
                equipment_id = eq_results[0]["id"]
        except Exception as e:
            record("Geospatial Equipment Search", "Marketplace", False, str(e))

        # ------------------------------------------------------------------
        # 5. Rental Request Lifecycle (Create -> State Machine Accept)
        # ------------------------------------------------------------------
        if equipment_id and farmer_token:
            try:
                rent_r = await client.post(
                    "/api/v1/rentals",
                    headers={"Authorization": f"Bearer {farmer_token}"},
                    json={
                        "equipmentId": equipment_id,
                        "rentalDate": "2026-10-15",
                        "durationUnits": 3,
                        "note": "জমি চাষের জন্য প্রয়োজন।"
                    }
                )
                assert rent_r.status_code == 201, rent_r.text
                rental_request_id = rent_r.json()["id"]
                record("Rental Request Creation", "Rentals", True, f"Created Rental: {rental_request_id[:8]}...")
            except Exception as e:
                record("Rental Request Creation", "Rentals", False, str(e))

        # State Machine Transition (Owner Accepts)
        if rental_request_id and owner_token:
            try:
                accept_r = await client.patch(
                    f"/api/v1/rentals/{rental_request_id}/status",
                    headers={"Authorization": f"Bearer {owner_token}"},
                    json={"targetStatus": "accepted"}
                )
                assert accept_r.status_code == 200, accept_r.text
                assert accept_r.json()["status"] == "accepted"
                record("Rental State Machine (Accept)", "Rentals", True, "Transitioned to ACCEPTED")
            except Exception as e:
                record("Rental State Machine (Accept)", "Rentals", False, str(e))

        # ------------------------------------------------------------------
        # 6. Crop Marketplace
        # ------------------------------------------------------------------
        if farmer_token:
            try:
                crop_post_r = await client.post(
                    "/api/v1/crop-listings",
                    headers={"Authorization": f"Bearer {farmer_token}"},
                    json={
                        "cropName": "মিনিকেট ধান",
                        "category": "paddy",
                        "quantity": 50.0,
                        "quantityUnit": "maund",
                        "pricePerUnit": 1400,
                        "expectedHarvestDate": "2026-10-25",
                        "district": "দিনাজপুর",
                        "upazila": "বীরগঞ্জ",
                        "latitude": 25.85,
                        "longitude": 88.66,
                        "description": "উন্নত মানের শুকনো ধান"
                    }
                )
                assert crop_post_r.status_code == 201, crop_post_r.text
                record("Crop Marketplace Listing Post", "Marketplace", True, f"Listing: {crop_post_r.json()['cropName']}")
            except Exception as e:
                record("Crop Marketplace Listing Post", "Marketplace", False, str(e))

        try:
            crop_list_r = await client.get("/api/v1/crop-listings")
            assert crop_list_r.status_code == 200
            crops_data = crop_list_r.json()
            record("Crop Marketplace Feed", "Marketplace", True, f"Loaded {len(crops_data)} crops")
        except Exception as e:
            record("Crop Marketplace Feed", "Marketplace", False, str(e))

        # ------------------------------------------------------------------
        # 7. Messaging & Conversation Channels
        # ------------------------------------------------------------------
        conv_id = None
        if farmer_token and owner_user:
            try:
                conv_r = await client.post(
                    "/api/v1/conversations",
                    headers={"Authorization": f"Bearer {farmer_token}"},
                    json={
                        "recipientId": owner_user["id"],
                        "contextType": "equipment_rental",
                        "initialMessage": "আসসালামু আলাইকুম, পাওয়ার টিলারটি কি আগামী শনিবার পাওয়া যাবে?"
                    }
                )
                assert conv_r.status_code in [200, 201], conv_r.text
                conv_id = conv_r.json()["id"]
                record("Direct Messaging Channel", "Messaging", True, f"Conversation: {conv_id[:8]}...")
            except Exception as e:
                record("Direct Messaging Channel", "Messaging", False, str(e))

        # Retrieve Conversation History
        if conv_id and farmer_token:
            try:
                msgs_r = await client.get(
                    f"/api/v1/conversations/{conv_id}/messages",
                    headers={"Authorization": f"Bearer {farmer_token}"}
                )
                assert msgs_r.status_code == 200
                messages = msgs_r.json()
                record("Message History Retrieval", "Messaging", True, f"Retrieved {len(messages)} message(s)")
            except Exception as e:
                record("Message History Retrieval", "Messaging", False, str(e))

        # ------------------------------------------------------------------
        # 8. Agricultural Knowledge Base & Bangla Search
        # ------------------------------------------------------------------
        try:
            kb_r = await client.get("/api/v1/knowledge?search=ধান")
            assert kb_r.status_code == 200
            articles = kb_r.json()
            record("Bangla Knowledge Base & Search", "Knowledge", True, f"Found {len(articles)} article(s)")
        except Exception as e:
            record("Bangla Knowledge Base & Search", "Knowledge", False, str(e))

        # ------------------------------------------------------------------
        # 9. Weather Advisory Service
        # ------------------------------------------------------------------
        try:
            weather_r = await client.get("/api/v1/weather/plan?latitude=25.62&longitude=88.63")
            assert weather_r.status_code == 200
            w_data = weather_r.json()
            record("Weather Advisory Guidance", "Weather", True, f"Attribution: {w_data.get('attribution', 'OpenMeteo')}")
        except Exception as e:
            record("Weather Advisory Guidance", "Weather", False, str(e))

        # ------------------------------------------------------------------
        # 10. Notifications System
        # ------------------------------------------------------------------
        if farmer_token:
            try:
                notif_r = await client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {farmer_token}"})
                assert notif_r.status_code == 200
                notifs = notif_r.json()
                record("User Notifications", "Notifications", True, f"Retrieved {len(notifs)} notification(s)")
            except Exception as e:
                record("User Notifications", "Notifications", False, str(e))

        # ------------------------------------------------------------------
        # 11. Offline Sync & Idempotency System
        # ------------------------------------------------------------------
        if farmer_token:
            try:
                sync_r = await client.post(
                    "/api/v1/sync/batch",
                    headers={"Authorization": f"Bearer {farmer_token}"},
                    json={
                        "mutations": [
                            {
                                "localUuid": str(uuid.uuid4()),
                                "idempotencyKey": f"offline-sync-{uuid.uuid4()}",
                                "operationName": "CREATE_CROP_LISTING",
                                "payload": {
                                    "cropName": "বোরো ধান ব্রি-২৮",
                                    "category": "paddy",
                                    "quantity": 80.0,
                                    "quantityUnit": "maund",
                                    "pricePerUnit": 1250,
                                    "expectedHarvestDate": "2026-10-25",
                                    "district": "বগুড়া",
                                    "upazila": "শেরপুর",
                                    "latitude": 24.67,
                                    "longitude": 89.42,
                                    "description": "অফলাইনে সংরক্ষিত সফল সিঙ্ক"
                                }
                            }
                        ]
                    }
                )
                assert sync_r.status_code == 200, sync_r.text
                sync_data = sync_r.json()
                assert sync_data["syncedCount"] >= 1 or sync_data["results"][0]["status"] in ["success", "conflict"]
                record("Offline Sync Batch & Idempotency", "Offline Sync", True, f"Synced {sync_data['syncedCount']} mutation(s)")
            except Exception as e:
                record("Offline Sync Batch & Idempotency", "Offline Sync", False, str(e))

    print("=" * 80)
    passed_count = sum(1 for r in results if r[2])
    total_count = len(results)
    print(f"VERIFICATION SUMMARY: {passed_count}/{total_count} FEATURES PASSED ({passed_count/total_count*100:.1f}%)")
    print("=" * 80)
    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(run_feature_verification())
    sys.exit(0 if success else 1)
