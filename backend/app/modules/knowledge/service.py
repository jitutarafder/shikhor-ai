"""Agricultural Knowledge Library domain service."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge.models import KnowledgeArticle
from app.modules.knowledge.schemas import KnowledgeArticleResponse, KnowledgeCatalogResponse

DEFAULT_KNOWLEDGE_SEEDS = [
    {
        "id": "know-rice-blast-01",
        "crop_type": "paddy",
        "category": "disease",
        "title_bn": "ধানের ব্লাস্ট রোগ ব্যবস্থাপনা ও প্রতিকার",
        "title_en": "Rice Blast Disease Management",
        "summary_bn": "ম্যাগনাপর্থে ওরাইজি ছত্রাকজনিত এই রোগে ধানের পাতায় চোখের মতো দাগ হয় এবং শিষ ভেঙে পড়ে।",
        "content_bn": "ধানের ব্লাস্ট একটি মারাত্মক ছত্রাকজনিত রোগ। শিষ বা পাতায় বাদামি ও ধূসর বর্ণের ডিম্বাকৃতি দাগ দেখা যায়। অতিরিক্ত ইউরিয়া সার প্রয়োগ ও মেঘলা স্যাঁতসেঁতে আবহাওয়ায় এই রোগের প্রাদুর্ভাব বাড়ে।",
        "recommended_practices_bn": "১. জমিতে ইউরিয়া সারের মাত্রাতিরিক্ত প্রয়োগ বন্ধ করুন এবং পরিমিত পটাশ সার ব্যবহার করুন। ২. আক্রমণ বেশি হলে অনুমোদিত ট্রাইসাইক্লাজল বা কাসুগামাইসিন গ্রুপের ছত্রাকনাশক স্প্রে করুন। ৩. জমি শুকিয়ে কিছুদিন পর পুনরায় সেচ দিন।",
        "version": 1,
    },
    {
        "id": "know-potato-blight-02",
        "crop_type": "potato",
        "category": "disease",
        "title_bn": "আলুর লেট ব্লাইট (নাবি ধসা) রোগ নিয়ন্ত্রণ",
        "title_en": "Late Blight of Potato Management",
        "summary_bn": "কুয়াশাচ্ছন্ন ও শীতল আবহাওয়ায় আলুর গাছে দ্রুত পচন ধরে এবং সম্পূর্ণ খেত নষ্ট হতে পারে।",
        "content_bn": "ফাইটোফথোরা ইনফেস্ট্যান্স ছত্রাক দ্বারা সৃষ্ট এই রোগ আলু ফসলের প্রধান শত্রু। কুয়াশাচ্ছন্ন আবহাওয়ায় পাতার কিনারা থেকে জলছাপ দাগ শুরু হয়ে পাতা ও কাণ্ড পচে যায়।",
        "recommended_practices_bn": "১. পূর্বাভাস অনুযায়ী কুয়াশাচ্ছন্ন আবহাওয়া দেখা দিলে আগাম ম্যানকোজেব স্প্রে করুন। ২. রোগ দেখা দিলে মেটালেক্সিল ও ম্যানকোজেবের সমন্বিত ছত্রাকনাশক স্প্রে করুন। ৩. আক্রান্ত গাছ তুলে মাটির নিচে পুঁতে ফেলুন।",
        "version": 1,
    },
    {
        "id": "know-irrigation-wheat-03",
        "crop_type": "wheat",
        "category": "irrigation",
        "title_bn": "গম চাষে পরিমিত সেচ প্রয়োগের সময়সূচি",
        "title_en": "Irrigation Schedule for Wheat Cultivation",
        "summary_bn": "গমের সর্বোচ্চ ফলনের জন্য শিকড় বের হওয়া, ফুল ফোটা এবং দানা গঠনের সময় সেচ অপরিহার্য।",
        "content_bn": "গমে সাধারণত ৩টি সংকটময় পর্যায়ে সেচ দেওয়া জরুরি: প্রথম সেচ বীজ বপনের ১৭-২১ দিন পর (মুকুট শিকড় গজানোর সময়), দ্বিতীয় সেচ ৫০-৫৫ দিন পর (শীষ আসার পূর্বে), এবং তৃতীয় সেচ ৭৫-৮০ দিন পর (দানা গঠনের সময়)।",
        "recommended_practices_bn": "১. সেচের পর জমিতে যাতে কোনোভাবেই অতিরিক্ত পানি জমে না থাকে সেদিকে লক্ষ্য রাখুন। ২. অতিরিক্ত বাতাসে সেচ দেওয়া থেকে বিরত থাকুন যাতে গম গাছ হেলে না পড়ে।",
        "version": 1,
    },
    {
        "id": "know-fertilizer-rice-04",
        "crop_type": "paddy",
        "category": "fertilizer",
        "title_bn": "বোরো ধানে সুষম সার ব্যবস্থাপনা ও প্রয়োগ",
        "title_en": "Balanced Fertilizer Management in Boro Rice",
        "summary_bn": "ইউরিয়া, টিএসপি, ডিএপি ও জিপসাম সঠিক অনুপাতে প্রয়োগ করে ধানের উৎপাদনশীলতা বৃদ্ধি।",
        "content_bn": "ইউরিয়া সার সমান তিন কিস্তিতে প্রয়োগ করা উচিত। প্রথম কিস্তি চারা রোপণের ১৫ দিন পর, দ্বিতীয় কিস্তি ৩০ দিন পর এবং তৃতীয় কিস্তি কাইচ থোড় আসার ৫-৭ দিন পূর্বে প্রয়োগ করতে হবে।",
        "recommended_practices_bn": "১. টিএসপি বা ডিএপি, পটাশ এবং জিপসাম সার শেষ চাষের সময় মূল জমিতে সমানভাবে ছিটিয়ে দিন। ২. জমিতে ছিপছিপে পানি থাকা অবস্থায় ইউরিয়া সার ছিটিয়ে হাত দিয়ে নিড়ানি দিন।",
        "version": 1,
    },
]


async def seed_default_knowledge(db: AsyncSession) -> None:
    """Seeds default verified agricultural knowledge articles if database is empty."""
    count_stmt = select(func.count()).select_from(KnowledgeArticle)
    count = await db.scalar(count_stmt)
    if count == 0:
        for seed in DEFAULT_KNOWLEDGE_SEEDS:
            article = KnowledgeArticle(
                id=seed["id"],
                crop_type=seed["crop_type"],
                category=seed["category"],
                title_bn=seed["title_bn"],
                title_en=seed.get("title_en"),
                summary_bn=seed["summary_bn"],
                content_bn=seed["content_bn"],
                recommended_practices_bn=seed.get("recommended_practices_bn"),
                version=seed["version"],
            )
            db.add(article)
        await db.commit()


def _map_article(article: KnowledgeArticle) -> KnowledgeArticleResponse:
    return KnowledgeArticleResponse(
        id=article.id,
        cropType=article.crop_type,
        category=article.category,
        titleBn=article.title_bn,
        titleEn=article.title_en,
        summaryBn=article.summary_bn,
        contentBn=article.content_bn,
        recommendedPracticesBn=article.recommended_practices_bn,
        version=article.version,
        publishedAt=article.published_at,
        updatedAt=article.updated_at,
    )


async def get_knowledge_catalog(
    db: AsyncSession,
    crop_type: Optional[str] = None,
    category: Optional[str] = None,
    since_version: Optional[int] = None,
) -> KnowledgeCatalogResponse:
    """Retrieves knowledge articles with optional filtering and incremental version sync."""
    stmt = select(KnowledgeArticle).order_by(KnowledgeArticle.crop_type, KnowledgeArticle.version.desc())

    if crop_type:
        stmt = stmt.where(KnowledgeArticle.crop_type == crop_type.lower())
    if category:
        stmt = stmt.where(KnowledgeArticle.category == category.lower())
    if since_version is not None:
        stmt = stmt.where(KnowledgeArticle.version > since_version)

    result = await db.execute(stmt)
    articles = list(result.scalars().all())

    latest_version = max([a.version for a in articles], default=1)
    mapped = [_map_article(a) for a in articles]

    return KnowledgeCatalogResponse(
        articles=mapped,
        totalCount=len(mapped),
        latestVersion=latest_version,
        syncedAt=datetime.now(timezone.utc),
    )
