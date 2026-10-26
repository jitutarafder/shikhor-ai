"""Seed script to ensure expert user and pending crop cases exist for demonstration."""

import asyncio
from sqlalchemy import select
from app.db.session import async_session_factory
from app.core.security import hash_password
from app.modules.crop_assistant.models import CropCase, CropCaseStatus
from app.modules.users.models import User, UserRole


async def seed():
    from app.db.base import Base
    from app.db.session import engine
    from sqlalchemy import text

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # In SQLite, add column if missing
        try:
            await conn.execute(text("ALTER TABLE crop_cases ADD COLUMN is_reviewed_by_expert BOOLEAN DEFAULT 0"))
        except Exception:
            pass

    async with async_session_factory() as db:
        # 1. Create or get expert user
        res = await db.execute(select(User).where(User.phone == "01711223344"))
        expert = res.scalar_one_or_none()
        if not expert:
            expert = User(
                phone="01711223344",
                hashed_password=hash_password("Password123#Strong"),
                full_name="ড. কৃষিবিদ মো: রফিকুল ইসলাম",
                role=UserRole.EXPERT,
                is_active=True,
            )
            db.add(expert)
            await db.commit()
            await db.refresh(expert)
            print(f"Created expert user: {expert.phone}")
        else:
            expert.role = UserRole.EXPERT
            expert.full_name = "ড. কৃষিবিদ মো: রফিকুল ইসলাম"
            expert.hashed_password = hash_password("Password123#Strong")
            await db.commit()
            print(f"Updated expert user: {expert.phone}")

        # 2. Create or get farmer user
        farmer_res = await db.execute(select(User).where(User.phone == "01799887766"))
        farmer = farmer_res.scalar_one_or_none()
        if not farmer:
            farmer = User(
                phone="01799887766",
                hashed_password=hash_password("Password123#Strong"),
                full_name="মো: রহমত আলী",
                role=UserRole.FARMER,
                is_active=True,
            )
            db.add(farmer)
            await db.commit()
            await db.refresh(farmer)

        # 3. Create demo pending cases if not present
        existing_cases = await db.execute(
            select(CropCase).where(
                CropCase.is_reviewed_by_expert == False,
                CropCase.escalation_recommended == True,
            )
        )
        if len(existing_cases.scalars().all()) == 0:
            cases = [
                CropCase(
                    user_id=farmer.id,
                    crop_type="ধান",
                    symptoms_description="ধানের পাতার অগ্রভাগে ও কিনারায় ভেজা ভেজা বাদামি দাগ পড়ে পুরো পাতা শুকিয়ে যাচ্ছে।",
                    image_filename="demo_rice_leaf.jpg",
                    status=CropCaseStatus.UNCERTAIN,
                    possible_condition="ব্যাকটেরিয়াজনিত পাতা পোড়া রোগ (সন্দেহজনক)",
                    confidence=0.45,
                    confidence_band="low",
                    reason_summary=[
                        "পাতার কিনারার ক্ষত ব্যাকটেরিয়াল ব্লাইটের অনুরূপ",
                        "এআই মডেল শতভাগ নিশ্চিত হতে পারেনি (কম কনফিডেন্স)",
                    ],
                    guidance=[
                        "প্রাথমিকভাবে অতিরিক্ত ইউরিয়া সার প্রয়োগ বন্ধ রাখুন",
                        "নিকটস্থ কৃষি কর্মকর্তার সুনির্দিষ্ট পরামর্শ নিন",
                    ],
                    escalation_recommended=True,
                    model_version="v1.0.0-shikhor-rice",
                    disclaimer="এটি স্বয়ংক্রিয় এআই পরামর্শ। সুনির্দিষ্ট বালাইনাশকের জন্য বিশেষজ্ঞের অনুমোদন আবশ্যক।",
                ),
                CropCase(
                    user_id=farmer.id,
                    crop_type="আলু",
                    symptoms_description="আলু গাছের পাতায় ও ডালপালায় পানিভেজা কালচে ছোপ ছোপ দাগ পড়েছে এবং দ্রুত পচন ছড়াচ্ছে।",
                    image_filename="demo_potato_leaf.jpg",
                    status=CropCaseStatus.UNCERTAIN,
                    possible_condition="আলুর নাবী ধসা (Late Blight) সন্দেহ",
                    confidence=0.49,
                    confidence_band="low",
                    reason_summary=[
                        "স্যাঁতসেঁতে আবহাওয়ায় ছত্রাকজনিত দাগের লক্ষণ স্পষ্ট",
                        "উচ্চ ঝুঁকির সংক্রমণ হওয়ায় বিশেষজ্ঞ পর্যালোচনা জরুরি",
                    ],
                    guidance=[
                        "আক্রান্ত ডালপালা সতর্কভাবে কেটে পুড়িয়ে ফেলুন",
                        "দ্রুত উপ-সহকারী কৃষি কর্মকর্তার সাথে যোগাযোগ করুন",
                    ],
                    escalation_recommended=True,
                    model_version="v1.0.0-shikhor-potato",
                    disclaimer="এটি স্বয়ংক্রিয় এআই পরামর্শ। সুনির্দিষ্ট বালাইনাশকের জন্য বিশেষজ্ঞের অনুমোদন আবশ্যক।",
                ),
                CropCase(
                    user_id=farmer.id,
                    crop_type="টমেটো",
                    symptoms_description="টমেটো গাছের ডগার পাতাগুলো কুঁকড়ে গেছে ও ছোট হয়ে হলদেটে হয়ে আসছে। ফুল ঝরে যাচ্ছে।",
                    image_filename="demo_tomato_leaf.jpg",
                    status=CropCaseStatus.UNSUPPORTED,
                    possible_condition="টমেটোর পাতা কোঁকড়ানো ভাইরাস (Leaf Curl Virus)",
                    confidence=0.38,
                    confidence_band="low",
                    reason_summary=[
                        "সাদা মাছি বাহিত ভাইরাস সংক্রমণের লক্ষণ",
                        "রাসায়নিক ছত্রাকনাশকে কাজ না হওয়ার সম্ভাবনা বেশি",
                    ],
                    guidance=[
                        "বাহক পোকা সাদা মাছি দমনে জরুরি পদক্ষেপ নিন",
                        "সঠিক বালাইনাশক প্রেসক্রিপশনের জন্য কৃষিবিদ রিভিউ কাম্য",
                    ],
                    escalation_recommended=True,
                    model_version="v1.0.0-shikhor-tomato",
                    disclaimer="এটি স্বয়ংক্রিয় এআই পরামর্শ। সুনির্দিষ্ট বালাইনাশকের জন্য বিশেষজ্ঞের অনুমোদন আবশ্যক।",
                ),
            ]
            for c in cases:
                db.add(c)
            await db.commit()
            print(f"Added {len(cases)} demo pending cases for expert review.")
        else:
            print("Pending cases already exist.")


if __name__ == "__main__":
    asyncio.run(seed())
