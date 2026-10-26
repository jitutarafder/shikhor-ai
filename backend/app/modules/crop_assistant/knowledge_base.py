"""Reviewed Agricultural Knowledge Base for Bangladeshi Crops & Vegetables.

Strictly complies with AGENTS.md Rule 19:
- Sourced directly from certified agronomic guidelines for Bangladesh.
- Covers all 16 crops and 35 disease & healthy conditions.
- Structured with primary_solution, guidance (করণীয়), avoid (এড়িয়ে চলুন), prevention (প্রতিরোধ), and special warnings.
- Dedicated non-alarmist treatment for Healthy crop predictions ("🌱 রোগ শনাক্ত হয়নি").
"""

from typing import Any, Dict, List, Optional

DISCLAIMER_TEXT = (
    "এটি AI-ভিত্তিক প্রাথমিক বিশ্লেষণ ও কৃষিতাত্ত্বিক সিদ্ধান্ত সহায়তা। "
    "চূড়ান্ত পদক্ষেপ গ্রহণের পূর্বে স্থানীয় উপজেলা কৃষি কর্মকর্তা বা উপ-সহকারী কৃষি কর্মকর্তার (SAAO) পরামর্শ নিন।"
)

HEALTHY_GENERAL_GUIDANCE = [
    "নিয়মিত গাছ পর্যবেক্ষণ করুন",
    "সঠিক পানি ও সার ব্যবস্থাপনা করুন",
    "আক্রান্ত/অস্বাভাবিক পাতা দেখলে পুনরায় পরীক্ষা করুন",
    "পরিষ্কার কৃষি সরঞ্জাম ব্যবহার করুন",
    "রোগ প্রতিরোধী জাত ব্যবহার করুন",
]

# Supported Field Crops and Vegetables
SUPPORTED_CROPS = [
    {"id": "Rice", "name_bn": "ধান", "category": "দানাশস্য"},
    {"id": "Wheat", "name_bn": "গম", "category": "দানাশস্য"},
    {"id": "Corn", "name_bn": "ভুট্টা", "category": "দানাশস্য"},
    {"id": "Potato", "name_bn": "আলু", "category": "সবজি ও কন্দ"},
    {"id": "Tomato", "name_bn": "টমেটো", "category": "সবজি ও কন্দ"},
    {"id": "Bell Pepper", "name_bn": "ক্যাপসিকাম", "category": "সবজি ও কন্দ"},
    {"id": "Soybean", "name_bn": "সয়াবিন", "category": "সবজি ও কন্দ"},
    {"id": "Squash", "name_bn": "স্কোয়াশ", "category": "সবজি ও কন্দ"},
    {"id": "Apple", "name_bn": "আপেল", "category": "ফলমূল"},
    {"id": "Blueberry", "name_bn": "ব্লুবেরি", "category": "ফলমূল"},
    {"id": "Cherry", "name_bn": "চেরি", "category": "ফলমূল"},
    {"id": "Grape", "name_bn": "আঙুর", "category": "ফলমূল"},
    {"id": "Orange", "name_bn": "কমলা", "category": "ফলমূল"},
    {"id": "Peach", "name_bn": "পিচ", "category": "ফলমূল"},
    {"id": "Raspberry", "name_bn": "রাস্পবেরি", "category": "ফলমূল"},
    {"id": "Strawberry", "name_bn": "স্ট্রবেরি", "category": "ফলমূল"},
]

REVIEWED_CONDITIONS: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # 🌾 ধান — Rice
    # =========================================================================
    "rice_bacterial_leaf_blight": {
        "crop": "Rice",
        "crop_bn": "ধান",
        "disease_en": "Bacterial Leaf Blight",
        "condition_name_bn": "ব্যাকটেরিয়াল লিফ ব্লাইট (Bacterial Leaf Blight)",
        "is_healthy": False,
        "primary_solution": "আক্রান্ত জমিতে রোগের বিস্তার কমানো এবং গাছের পানি ও পুষ্টি ব্যবস্থাপনা ঠিক রাখা।",
        "guidance": [
            "আক্রান্ত গাছ ও পাতার অবস্থা নিয়মিত পর্যবেক্ষণ করুন।",
            "জমিতে অতিরিক্ত পানি জমে থাকলে পানি ব্যবস্থাপনা করুন।",
            "অতিরিক্ত ইউরিয়া/নাইট্রোজেন ব্যবহার এড়িয়ে চলুন।",
            "সুষম N-P-K সার প্রয়োগ করুন।",
            "রোগমুক্ত ও সহনশীল জাত ব্যবহার করুন।",
            "জমির আগাছা ও আক্রান্ত ফসলের অবশিষ্টাংশ পরিষ্কার রাখুন।",
            "প্রয়োজন হলে স্থানীয় কৃষি কর্মকর্তার পরামর্শে অনুমোদিত ব্যাকটেরিয়া নিয়ন্ত্রণ ব্যবস্থা ব্যবহার করুন।",
        ],
        "avoid": "অতিরিক্ত নাইট্রোজেন ও অপ্রয়োজনীয় সেচ।",
        "prevention": "রোগমুক্ত বীজ, সহনশীল জাত এবং সুষম সার ব্যবস্থাপনা।",
        "keywords": ["পাতা পোড়া", "ব্লাইট", "blight", "bacterial leaf blight", "হলুদ দাগ"],
    },
    "rice_brown_spot": {
        "crop": "Rice",
        "crop_bn": "ধান",
        "disease_en": "Brown Spot",
        "condition_name_bn": "ব্রাউন স্পট (Brown Spot)",
        "is_healthy": False,
        "primary_solution": "গাছের পুষ্টির ঘাটতি দূর করা এবং পাতায় রোগের বিস্তার কমানো।",
        "guidance": [
            "সুষম সার প্রয়োগ করুন।",
            "পটাশের ঘাটতি থাকলে তা পূরণ করুন।",
            "জমিতে প্রয়োজনীয় পানি নিশ্চিত করুন কিন্তু দীর্ঘসময় জলাবদ্ধতা রাখবেন না।",
            "আক্রান্ত পাতাগুলো পর্যবেক্ষণ করুন।",
            "ফসলের অবশিষ্টাংশ সঠিকভাবে ব্যবস্থাপনা করুন।",
            "প্রয়োজন হলে অনুমোদিত ছত্রাকনাশক ব্যবহার করুন।",
        ],
        "avoid": "দীর্ঘস্থায়ী পুষ্টির ঘাটতি ও দুর্বল গাছের অবস্থা।",
        "prevention": "ভালো মানের বীজ, সুষম সার এবং নিয়মিত field monitoring।",
        "keywords": ["বাদামি দাগ", "brown spot", "তিলের মতো দাগ", "পটাশ ঘাটতি"],
    },
    "rice_leaf_blast": {
        "crop": "Rice",
        "crop_bn": "ধান",
        "disease_en": "Leaf Blast",
        "condition_name_bn": "লিফ ব্লাস্ট (Rice Leaf Blast)",
        "is_healthy": False,
        "primary_solution": "রোগের দ্রুত বিস্তার কমানো এবং অতিরিক্ত নাইট্রোজেন এড়িয়ে গাছকে সুষম পুষ্টি দেওয়া।",
        "guidance": [
            "আক্রান্ত পাতাগুলো নিয়মিত পর্যবেক্ষণ করুন।",
            "অতিরিক্ত ইউরিয়া প্রয়োগ করবেন না।",
            "সুষম সার প্রয়োগ করুন।",
            "জমির পানি ব্যবস্থাপনা ঠিক রাখুন।",
            "রোগের শুরুতেই ব্যবস্থা নিন।",
            "প্রয়োজন হলে স্থানীয় কৃষি বিশেষজ্ঞের পরামর্শে অনুমোদিত ছত্রাকনাশক ব্যবহার করুন।",
            "পরবর্তী মৌসুমে সহনশীল জাত ব্যবহার করুন।",
        ],
        "prevention": "সহনশীল জাত + সুষম সার + নিয়মিত পর্যবেক্ষণ।",
        "keywords": ["ব্লাস্ট", "blast", "চোখের মত দাগ", "ধূসর কেন্দ্র"],
    },

    # =========================================================================
    # 🌽 ভুট্টা — Corn
    # =========================================================================
    "corn_cercospora_gray_leaf_spot": {
        "crop": "Corn",
        "crop_bn": "ভুট্টা",
        "disease_en": "Cercospora Leaf Spot Gray Leaf Spot",
        "condition_name_bn": "Cercospora / Gray Leaf Spot",
        "is_healthy": False,
        "primary_solution": "আক্রান্ত পাতার পরিমাণ ও fungal spread কমানো।",
        "guidance": [
            "আক্রান্ত পাতাগুলো নিয়মিত পর্যবেক্ষণ করুন।",
            "ফসলের অবশিষ্টাংশ মাঠে জমিয়ে রাখবেন না।",
            "একই জমিতে ধারাবাহিকভাবে একই ফসল করার প্রবণতা কমান।",
            "গাছের মধ্যে পর্যাপ্ত দূরত্ব রাখুন।",
            "সুষম সার প্রয়োগ করুন।",
            "রোগ বেশি হলে অনুমোদিত ছত্রাকনাশক ব্যবহার করুন।",
        ],
        "prevention": "crop rotation, resistant variety এবং sanitation।",
        "keywords": ["সারকোস্পোরা", "gray leaf spot", "ধূসর দাগ", "cercospora"],
    },
    "corn_common_rust": {
        "crop": "Corn",
        "crop_bn": "ভুট্টা",
        "disease_en": "Common Rust",
        "condition_name_bn": "Common Rust",
        "is_healthy": False,
        "primary_solution": "রোগের বিস্তার পর্যবেক্ষণ এবং প্রয়োজন হলে fungal control।",
        "guidance": [
            "পাতার উপর rust-like দাগ নিয়মিত পর্যবেক্ষণ করুন।",
            "আক্রান্ত অংশের বিস্তার লক্ষ্য করুন।",
            "রোগ সহনশীল জাত ব্যবহার করুন।",
            "জমিতে অতিরিক্ত আর্দ্রতা এড়িয়ে চলুন।",
            "প্রয়োজন হলে অনুমোদিত ছত্রাকনাশক ব্যবহার করুন।",
        ],
        "prevention": "resistant variety + field monitoring।",
        "keywords": ["মরিচা", "common rust", "গুটি", "কমলা দাগ"],
    },
    "corn_northern_leaf_blight": {
        "crop": "Corn",
        "crop_bn": "ভুট্টা",
        "disease_en": "Northern Leaf Blight",
        "condition_name_bn": "Northern Leaf Blight",
        "is_healthy": False,
        "primary_solution": "আক্রান্ত leaf tissue এবং fungal source কমানো।",
        "guidance": [
            "আক্রান্ত পাতাগুলো পর্যবেক্ষণ করুন।",
            "আক্রান্ত crop residue পরিষ্কার করুন।",
            "crop rotation করুন।",
            "সুষম সার ব্যবহার করুন।",
            "পর্যাপ্ত spacing বজায় রাখুন।",
            "রোগের মাত্রা বেশি হলে অনুমোদিত ছত্রাকনাশক ব্যবহার করুন।",
        ],
        "prevention": "resistant variety + crop rotation + sanitation।",
        "keywords": ["northern leaf blight", "লম্বা দাগ", "ঝলসানো পাতা"],
    },

    # =========================================================================
    # 🌾 গম — Wheat
    # =========================================================================
    "wheat_brown_rust": {
        "crop": "Wheat",
        "crop_bn": "গম",
        "disease_en": "Brown Rust",
        "condition_name_bn": "Brown Rust",
        "is_healthy": False,
        "primary_solution": "রোগের বিস্তার কমানো এবং resistant variety ব্যবহার।",
        "guidance": [
            "পাতায় rust symptoms নিয়মিত পরীক্ষা করুন।",
            "রোগের শুরুতেই ব্যবস্থা নিন।",
            "রোগ প্রতিরোধী জাত নির্বাচন করুন।",
            "অতিরিক্ত nitrogen এড়িয়ে সুষম fertilizer ব্যবহার করুন।",
            "প্রয়োজন হলে অনুমোদিত fungicide ব্যবহার করুন।",
        ],
        "keywords": ["বাদামি মরিচা", "brown rust", "পাতা মরিচা"],
    },
    "wheat_yellow_rust": {
        "crop": "Wheat",
        "crop_bn": "গম",
        "disease_en": "Yellow Rust",
        "condition_name_bn": "Yellow Rust",
        "is_healthy": False,
        "primary_solution": "early detection এবং দ্রুত disease management।",
        "guidance": [
            "মাঠ নিয়মিত পর্যবেক্ষণ করুন।",
            "হলুদ rust-like streak দেখা দিলে দ্রুত ব্যবস্থা নিন।",
            "resistant variety ব্যবহার করুন।",
            "প্রয়োজন হলে স্থানীয় কৃষি কর্মকর্তার পরামর্শে অনুমোদিত fungicide ব্যবহার করুন।",
            "আক্রান্ত জমি থেকে পরবর্তী মৌসুমের জন্য বীজ নির্বাচন না করাই ভালো।",
        ],
        "prevention": "resistant variety + early monitoring।",
        "keywords": ["হলুদ মরিচা", "yellow rust", "স্ট্রাইপ রাস্ট"],
    },
    "wheat_loose_smut": {
        "crop": "Wheat",
        "crop_bn": "গম",
        "disease_en": "Loose Smut",
        "condition_name_bn": "Loose Smut",
        "is_healthy": False,
        "primary_solution": "রোগমুক্ত বীজ এবং seed treatment।",
        "guidance": [
            "রোগমুক্ত certified seed ব্যবহার করুন।",
            "বপনের আগে উপযুক্ত seed treatment করুন।",
            "আক্রান্ত spike/গাছ চিহ্নিত করে সরিয়ে ফেলুন।",
            "আক্রান্ত ফসল থেকে পরবর্তী মৌসুমের seed সংগ্রহ করবেন না।",
        ],
        "special_warning": "সবচেয়ে গুরুত্বপূর্ণ: এই রোগে বীজ ব্যবস্থাপনা খুব গুরুত্বপূর্ণ।",
        "keywords": ["লুজ স্মাট", "loose smut", "উড়তি ঝুল", "কালো গুঁড়া"],
    },

    # =========================================================================
    # 🥔 আলু — Potato
    # =========================================================================
    "potato_early_blight": {
        "crop": "Potato",
        "crop_bn": "আলু",
        "disease_en": "Early Blight",
        "condition_name_bn": "Early Blight",
        "is_healthy": False,
        "primary_solution": "আক্রান্ত foliage কমানো এবং fungal spread নিয়ন্ত্রণ।",
        "guidance": [
            "আক্রান্ত পাতা পর্যবেক্ষণ করুন।",
            "আক্রান্ত leaf material সরিয়ে ফেলুন।",
            "crop residue পরিষ্কার করুন।",
            "পর্যাপ্ত plant spacing রাখুন।",
            "সুষম fertilizer ব্যবহার করুন।",
            "প্রয়োজন হলে অনুমোদিত fungicide ব্যবহার করুন।",
        ],
        "prevention": "healthy seed + crop rotation + field sanitation।",
        "keywords": ["আর্লি ব্লাইট", "early blight", "বলয়যুক্ত দাগ", "চক্রাকার দাগ"],
    },
    "potato_late_blight": {
        "crop": "Potato",
        "crop_bn": "আলু",
        "disease_en": "Late Blight",
        "condition_name_bn": "Late Blight",
        "is_healthy": False,
        "primary_solution": "রোগ দ্রুত শনাক্ত করে fungal spread কমানো।",
        "guidance": [
            "পাতায় dark/water-soaked lesion আছে কিনা পর্যবেক্ষণ করুন।",
            "আক্রান্ত গাছ/পাতা দ্রুত আলাদা করুন।",
            "জমিতে অতিরিক্ত আর্দ্রতা কমানোর চেষ্টা করুন।",
            "আক্রান্ত crop residue সরিয়ে ফেলুন।",
            "রোগ দ্রুত ছড়ালে স্থানীয় কৃষি কর্মকর্তার পরামর্শে অনুমোদিত fungicide ব্যবহার করুন।",
            "রোগমুক্ত seed potato ব্যবহার করুন।",
        ],
        "special_warning": "বিশেষ সতর্কতা: Late Blight দ্রুত ছড়াতে পারে, তাই early detection গুরুত্বপূর্ণ।",
        "keywords": ["লেট ব্লাইট", "late blight", "নাবি ধসা", "পানিভেজা দাগ", "কালো পচা"],
    },

    # =========================================================================
    # 🍅 টমেটো — Tomato
    # =========================================================================
    "tomato_bacterial_spot": {
        "crop": "Tomato",
        "crop_bn": "টমেটো",
        "disease_en": "Bacterial Spot",
        "condition_name_bn": "Bacterial Spot",
        "is_healthy": False,
        "primary_solution": "bacterial spread কমানো এবং আক্রান্ত foliage management।",
        "guidance": [
            "আক্রান্ত পাতা/গাছ নিয়মিত পর্যবেক্ষণ করুন।",
            "আক্রান্ত plant material সরিয়ে ফেলুন।",
            "পাতায় উপর থেকে পানি ছিটানো এড়িয়ে চলুন।",
            "পরিষ্কার gardening tools ব্যবহার করুন।",
            "seedling/planting material স্বাস্থ্যকর কিনা নিশ্চিত করুন।",
            "প্রয়োজন হলে অনুমোদিত bacterial disease management ব্যবহার করুন।",
        ],
        "keywords": ["ব্যাকটেরিয়াল স্পট", "bacterial spot", "ছোট কালো দাগ"],
    },
    "tomato_early_blight": {
        "crop": "Tomato",
        "crop_bn": "টমেটো",
        "disease_en": "Early Blight",
        "condition_name_bn": "Early Blight",
        "is_healthy": False,
        "primary_solution": "আক্রান্ত foliage এবং fungal source কমানো।",
        "guidance": [
            "নিচের পুরোনো পাতাগুলো নিয়মিত পরীক্ষা করুন।",
            "আক্রান্ত পাতা সরিয়ে ফেলুন।",
            "মাটির সংস্পর্শে পাতার পানি/মাটি ছিটকে পড়া কমান।",
            "crop residue পরিষ্কার করুন।",
            "crop rotation করুন।",
            "প্রয়োজন হলে অনুমোদিত fungicide ব্যবহার করুন।",
        ],
        "keywords": ["আগাম ধসা", "early blight", "চক্রাকার দাগ"],
    },
    "tomato_late_blight": {
        "crop": "Tomato",
        "crop_bn": "টমেটো",
        "disease_en": "Late Blight",
        "condition_name_bn": "Late Blight",
        "is_healthy": False,
        "primary_solution": "দ্রুত শনাক্তকরণ এবং আক্রান্ত অংশের বিস্তার নিয়ন্ত্রণ।",
        "guidance": [
            "পাতার dark lesion দ্রুত পরীক্ষা করুন।",
            "আক্রান্ত পাতা/গাছ সরিয়ে ফেলুন।",
            "অতিরিক্ত আর্দ্রতা ও দীর্ঘসময় leaf wetness কমান।",
            "গাছের মধ্যে পর্যাপ্ত বাতাস চলাচলের ব্যবস্থা রাখুন।",
            "প্রয়োজন হলে অনুমোদিত fungicide ব্যবহার করুন।",
        ],
        "special_warning": "বিশেষ সতর্কতা: রোগ দ্রুত ছড়াতে পারে।",
        "keywords": ["নাবি ধসা", "late blight", "কালো পচন"],
    },
    "tomato_leaf_mold": {
        "crop": "Tomato",
        "crop_bn": "টমেটো",
        "disease_en": "Leaf Mold",
        "condition_name_bn": "Leaf Mold",
        "is_healthy": False,
        "primary_solution": "humidity কমানো এবং airflow বৃদ্ধি।",
        "guidance": [
            "গাছের মধ্যে পর্যাপ্ত spacing রাখুন।",
            "greenhouse হলে ventilation বাড়ান।",
            "আক্রান্ত পাতা সরিয়ে ফেলুন।",
            "পাতায় অতিরিক্ত পানি দেওয়া এড়িয়ে চলুন।",
            "প্রয়োজন হলে অনুমোদিত fungicide ব্যবহার করুন।",
        ],
        "keywords": ["লিফ মোল্ড", "leaf mold", "ছাতা পড়া পাতা"],
    },
    "tomato_septoria_leaf_spot": {
        "crop": "Tomato",
        "crop_bn": "টমেটো",
        "disease_en": "Septoria Leaf Spot",
        "condition_name_bn": "Septoria Leaf Spot",
        "is_healthy": False,
        "primary_solution": "আক্রান্ত foliage এবং fungal source নিয়ন্ত্রণ।",
        "guidance": [
            "আক্রান্ত পাতা দ্রুত সরান।",
            "মাটির পানি পাতায় ছিটানো কমান।",
            "crop residue পরিষ্কার করুন।",
            "crop rotation করুন।",
            "প্রয়োজন হলে অনুমোদিত fungicide ব্যবহার করুন।",
        ],
        "keywords": ["সেপ্টোরিয়া", "septoria", "ছোট গোল দাগ"],
    },
    "tomato_spider_mites": {
        "crop": "Tomato",
        "crop_bn": "টমেটো",
        "disease_en": "Spider Mites",
        "condition_name_bn": "Spider Mites",
        "is_healthy": False,
        "primary_solution": "mite population কমানো এবং গাছের stress কমানো।",
        "guidance": [
            "পাতার নিচের অংশ পরীক্ষা করুন।",
            "webbing ও ছোট দাগ আছে কিনা দেখুন।",
            "গাছকে অতিরিক্ত drought stress থেকে রক্ষা করুন।",
            "আক্রান্ত অংশ আলাদা করুন।",
            "beneficial insects সংরক্ষণ করুন।",
            "infestation বেশি হলে স্থানীয় কৃষি বিশেষজ্ঞের পরামর্শে অনুমোদিত miticide ব্যবহার করুন।",
        ],
        "special_warning": "বিশেষ সতর্কতা: অপ্রয়োজনীয় broad-spectrum pesticide ব্যবহার করলে উপকারী predator কমে গিয়ে mite সমস্যা বাড়তে পারে।",
        "keywords": ["স্পাইডার মাইট", "মাকড়", "spider mite", "জাল", "webbing"],
    },
    "tomato_target_spot": {
        "crop": "Tomato",
        "crop_bn": "টমেটো",
        "disease_en": "Target Spot",
        "condition_name_bn": "Target Spot",
        "is_healthy": False,
        "primary_solution": "আক্রান্ত foliage কমানো এবং fungal spread নিয়ন্ত্রণ।",
        "guidance": [
            "আক্রান্ত পাতা সরিয়ে ফেলুন।",
            "গাছের মধ্যে airflow বাড়ান।",
            "crop residue পরিষ্কার রাখুন।",
            "অতিরিক্ত leaf wetness কমান।",
            "প্রয়োজন হলে অনুমোদিত fungicide ব্যবহার করুন।",
        ],
        "keywords": ["টার্গেট স্পট", "target spot", "গোলাকার দাগ"],
    },
    "tomato_yellow_leaf_curl_virus": {
        "crop": "Tomato",
        "crop_bn": "টমেটো",
        "disease_en": "Yellow Leaf Curl Virus",
        "condition_name_bn": "Yellow Leaf Curl Virus",
        "is_healthy": False,
        "primary_solution": "আক্রান্ত গাছ ও virus vector নিয়ন্ত্রণ।",
        "guidance": [
            "আক্রান্ত গাছ দ্রুত শনাক্ত করুন।",
            "প্রয়োজন হলে আক্রান্ত গাছ সরিয়ে ফেলুন।",
            "whitefly population পর্যবেক্ষণ করুন।",
            "weed host নিয়ন্ত্রণ করুন।",
            "রোগমুক্ত planting material ব্যবহার করুন।",
            "vector control-এর জন্য স্থানীয় কৃষি বিশেষজ্ঞের পরামর্শ নিন।",
        ],
        "special_warning": "গুরুত্বপূর্ণ: Virus আক্রান্ত গাছকে শুধু fungicide দিয়ে ভালো করা যায় না।",
        "keywords": ["হলুদ পাতা কোঁকড়ানো", "yellow leaf curl", "সাদামাছি", "ভাইরাস"],
    },
    "tomato_mosaic_virus": {
        "crop": "Tomato",
        "crop_bn": "টমেটো",
        "disease_en": "Mosaic Virus",
        "condition_name_bn": "Mosaic Virus",
        "is_healthy": False,
        "primary_solution": "infected plant ও transmission source নিয়ন্ত্রণ।",
        "guidance": [
            "আক্রান্ত গাছ আলাদা/অপসারণ করুন।",
            "pruning tools পরিষ্কার রাখুন।",
            "আক্রান্ত গাছের অংশ অন্য সুস্থ গাছে ব্যবহার করবেন না।",
            "weed ও সম্ভাব্য vector নিয়ন্ত্রণ করুন।",
            "রোগমুক্ত planting material ব্যবহার করুন।",
        ],
        "keywords": ["মোজাইক ভাইরাস", "mosaic virus", "ছোপ ছোপ দাগ"],
    },

    # =========================================================================
    # 🍎 আপেল — Apple
    # =========================================================================
    "apple_scab": {
        "crop": "Apple",
        "crop_bn": "আপেল",
        "disease_en": "Apple Scab",
        "condition_name_bn": "Apple Scab",
        "is_healthy": False,
        "primary_solution": "infected leaf/fruit residue এবং fungal spread কমানো।",
        "guidance": [
            "আক্রান্ত পাতা সংগ্রহ করে নষ্ট করুন।",
            "আক্রান্ত ফল অপসারণ করুন।",
            "গাছের canopy খুব ঘন হতে দেবেন না।",
            "pruning করে airflow বাড়ান।",
            "প্রয়োজন হলে অনুমোদিত fungicide ব্যবহার করুন।",
        ],
        "keywords": ["আপেল স্ক্যাব", "apple scab", "খসখসে দাগ"],
    },
    "apple_black_rot": {
        "crop": "Apple",
        "crop_bn": "আপেল",
        "disease_en": "Black Rot",
        "condition_name_bn": "Black Rot",
        "is_healthy": False,
        "primary_solution": "আক্রান্ত fruit, branch এবং plant debris অপসারণ।",
        "guidance": [
            "আক্রান্ত ফল দ্রুত সরান।",
            "dead branch ছাঁটাই করুন।",
            "orchard sanitation বজায় রাখুন।",
            "গাছের ক্ষত/আঘাত কমানোর চেষ্টা করুন।",
            "প্রয়োজন হলে অনুমোদিত fungicide ব্যবহার করুন।",
        ],
        "keywords": ["ব্ল্যাক রট", "black rot", "কালো পচা"],
    },
    "apple_cedar_apple_rust": {
        "crop": "Apple",
        "crop_bn": "আপেল",
        "disease_en": "Cedar Apple Rust",
        "condition_name_bn": "Cedar Apple Rust",
        "is_healthy": False,
        "primary_solution": "disease cycle এবং infected tissue কমানো।",
        "guidance": [
            "আক্রান্ত পাতার লক্ষণ পর্যবেক্ষণ করুন।",
            "সম্ভব হলে disease source শনাক্ত করুন।",
            "orchard sanitation বজায় রাখুন।",
            "resistant variety ব্যবহার করুন।",
            "প্রয়োজন হলে অনুমোদিত fungicide ব্যবহার করুন।",
        ],
        "keywords": ["সিডার আপেল রাস্ট", "cedar apple rust", "কমলা স্পট"],
    },

    # =========================================================================
    # 🫐 ব্লুবেরি — Blueberry
    # =========================================================================
    "blueberry_healthy": {
        "crop": "Blueberry",
        "crop_bn": "ব্লুবেরি",
        "disease_en": "Healthy",
        "condition_name_bn": "Healthy Blueberry",
        "is_healthy": True,
        "primary_solution": "কোনো রোগের লক্ষণ শনাক্ত হয়নি।",
        "guidance": [
            "নিয়মিত পাতার রং ও গাছের growth পর্যবেক্ষণ করুন।",
            "সঠিক পানি ব্যবস্থাপনা করুন।",
            "প্রয়োজন অনুযায়ী balanced nutrition দিন।",
            "নতুন রোগের লক্ষণ দেখা দিলে পুনরায় পরীক্ষা করুন।",
        ],
        "keywords": ["healthy", "সুস্থ"],
    },

    # =========================================================================
    # 🍒 চেরি — Cherry
    # =========================================================================
    "cherry_powdery_mildew": {
        "crop": "Cherry",
        "crop_bn": "চেরি",
        "disease_en": "Powdery Mildew",
        "condition_name_bn": "Powdery Mildew",
        "is_healthy": False,
        "primary_solution": "infected foliage কমানো এবং humidity/airflow management।",
        "guidance": [
            "আক্রান্ত পাতা/অংশ সরিয়ে ফেলুন।",
            "canopy অতিরিক্ত ঘন হতে দেবেন না।",
            "pruning করে airflow বাড়ান।",
            "অতিরিক্ত nitrogen এড়িয়ে চলুন।",
            "প্রয়োজন হলে অনুমোদিত fungicide ব্যবহার করুন।",
        ],
        "keywords": ["পাউডারি মিলডিউ", "powdery mildew", "সাদা গুঁড়া"],
    },

    # =========================================================================
    # 🍇 আঙুর — Grape
    # =========================================================================
    "grape_black_rot": {
        "crop": "Grape",
        "crop_bn": "আঙুর",
        "disease_en": "Black Rot",
        "condition_name_bn": "Black Rot",
        "is_healthy": False,
        "primary_solution": "আক্রান্ত fruit ও foliage সরিয়ে fungal source কমানো।",
        "guidance": [
            "আক্রান্ত ফল দ্রুত সরান।",
            "আক্রান্ত পাতা/ডাল পর্যবেক্ষণ করুন।",
            "vineyard sanitation বজায় রাখুন।",
            "canopy management করুন।",
            "প্রয়োজন হলে অনুমোদিত fungicide ব্যবহার করুন।",
        ],
        "keywords": ["ব্ল্যাক রট", "black rot", "আঙুর পচা"],
    },
    "grape_esca_black_measles": {
        "crop": "Grape",
        "crop_bn": "আঙুর",
        "disease_en": "Esca (Black Measles)",
        "condition_name_bn": "Esca / Black Measles",
        "is_healthy": False,
        "primary_solution": "আক্রান্ত কাঠ/গাছের অংশ শনাক্ত ও ব্যবস্থাপনা।",
        "guidance": [
            "আক্রান্ত vine নিয়মিত পর্যবেক্ষণ করুন।",
            "dead/seriously infected wood ছাঁটাই করুন।",
            "pruning tools disinfect করুন।",
            "vineyard sanitation বজায় রাখুন।",
            "গুরুতর আক্রান্ত গাছ আলাদা ব্যবস্থাপনার আওতায় আনুন।",
        ],
        "keywords": ["esca", "black measles", "এসকা", "কালো দাগ"],
    },
    "grape_isariopsis_leaf_spot": {
        "crop": "Grape",
        "crop_bn": "আঙুর",
        "disease_en": "Isariopsis Leaf Spot",
        "condition_name_bn": "Isariopsis Leaf Spot",
        "is_healthy": False,
        "primary_solution": "আক্রান্ত leaf tissue কমানো এবং fungal spread নিয়ন্ত্রণ।",
        "guidance": [
            "আক্রান্ত পাতা অপসারণ করুন।",
            "canopy airflow বাড়ান।",
            "vineyard sanitation বজায় রাখুন।",
            "প্রয়োজন হলে অনুমোদিত fungicide ব্যবহার করুন।",
        ],
        "keywords": ["isariopsis", "আইসারিওপসিস", "পাতার দাগ"],
    },

    # =========================================================================
    # 🍊 কমলা — Orange
    # =========================================================================
    "orange_citrus_greening": {
        "crop": "Orange",
        "crop_bn": "কমলা",
        "disease_en": "Citrus Greening",
        "condition_name_bn": "Citrus Greening",
        "is_healthy": False,
        "primary_solution": "infected tree management এবং psyllid vector control।",
        "guidance": [
            "আক্রান্ত গাছের লক্ষণ নিয়মিত পর্যবেক্ষণ করুন।",
            "disease-free planting material ব্যবহার করুন।",
            "psyllid vector পর্যবেক্ষণ ও নিয়ন্ত্রণ করুন।",
            "আক্রান্ত গাছের বিষয়ে স্থানীয় কৃষি কর্মকর্তার পরামর্শ নিন।",
            "orchard sanitation বজায় রাখুন।",
        ],
        "special_warning": "গুরুত্বপূর্ণ: এটি bacterial disease হওয়ায় সাধারণ fungicide দিয়ে রোগটি নিরাময় করা যায় না।",
        "keywords": ["সাইট্রাস গ্রিনিং", "citrus greening", "হলুদাভ রোগ", "psyllid"],
    },

    # =========================================================================
    # 🍑 পিচ — Peach
    # =========================================================================
    "peach_bacterial_spot": {
        "crop": "Peach",
        "crop_bn": "পিচ",
        "disease_en": "Bacterial Spot",
        "condition_name_bn": "Bacterial Spot",
        "is_healthy": False,
        "primary_solution": "infected foliage/fruit এবং bacterial spread কমানো।",
        "guidance": [
            "আক্রান্ত পাতা ও ফল সরিয়ে ফেলুন।",
            "অতিরিক্ত leaf wetness কমান।",
            "airflow বাড়ান।",
            "pruning tools পরিষ্কার রাখুন।",
            "রোগমুক্ত planting material ব্যবহার করুন।",
            "প্রয়োজন হলে অনুমোদিত bacterial disease management ব্যবহার করুন।",
        ],
        "keywords": ["bacterial spot", "পিচ দাগ"],
    },

    # =========================================================================
    # 🫑 ক্যাপসিকাম — Bell Pepper
    # =========================================================================
    "pepper_bacterial_spot": {
        "crop": "Bell Pepper",
        "crop_bn": "ক্যাপসিকাম",
        "disease_en": "Bacterial Spot",
        "condition_name_bn": "Bacterial Spot",
        "is_healthy": False,
        "primary_solution": "bacterial spread কমানো এবং infected plant material management।",
        "guidance": [
            "আক্রান্ত পাতা/ফল অপসারণ করুন।",
            "ওপর থেকে পানি ছিটানো এড়িয়ে চলুন।",
            "healthy seed/seedling ব্যবহার করুন।",
            "garden tools পরিষ্কার রাখুন।",
            "crop residue সরিয়ে ফেলুন।",
            "প্রয়োজন হলে অনুমোদিত bacterial disease management ব্যবহার করুন।",
        ],
        "keywords": ["bacterial spot", "ক্যাপসিকাম দাগ", "মরিচ দাগ"],
    },

    # =========================================================================
    # 🫐 রাস্পবেরি — Raspberry
    # =========================================================================
    "raspberry_healthy": {
        "crop": "Raspberry",
        "crop_bn": "রাস্পবেরি",
        "disease_en": "Healthy",
        "condition_name_bn": "Healthy Raspberry",
        "is_healthy": True,
        "primary_solution": "বর্তমানে রোগের লক্ষণ শনাক্ত হয়নি।",
        "guidance": [
            "নিয়মিত পাতার পরিবর্তন পর্যবেক্ষণ করুন।",
            "পর্যাপ্ত sunlight ও airflow নিশ্চিত করুন।",
            "পানি ও nutrition সঠিকভাবে পরিচালনা করুন।",
            "নতুন symptoms দেখা দিলে পুনরায় পরীক্ষা করুন।",
        ],
        "keywords": ["healthy", "সুস্থ"],
    },

    # =========================================================================
    # 🌱 সয়াবিন — Soybean
    # =========================================================================
    "soybean_healthy": {
        "crop": "Soybean",
        "crop_bn": "সয়াবিন",
        "disease_en": "Healthy",
        "condition_name_bn": "Healthy Soybean",
        "is_healthy": True,
        "primary_solution": "বর্তমানে রোগের লক্ষণ শনাক্ত হয়নি।",
        "guidance": [
            "নিয়মিত field inspection করুন।",
            "পাতায় spots, discoloration বা wilting দেখা দিলে পুনরায় পরীক্ষা করুন।",
            "সুষম nutrition বজায় রাখুন।",
            "পানি নিষ্কাশন ভালো রাখুন।",
        ],
        "keywords": ["healthy", "সুস্থ"],
    },

    # =========================================================================
    # 🎃 স্কোয়াশ — Squash
    # =========================================================================
    "squash_powdery_mildew": {
        "crop": "Squash",
        "crop_bn": "স্কোয়াশ",
        "disease_en": "Powdery Mildew",
        "condition_name_bn": "Powdery Mildew",
        "is_healthy": False,
        "primary_solution": "আক্রান্ত foliage কমানো এবং canopy airflow বৃদ্ধি।",
        "guidance": [
            "আক্রান্ত পাতা সরিয়ে ফেলুন।",
            "গাছের মধ্যে পর্যাপ্ত spacing রাখুন।",
            "airflow বাড়ান।",
            "অতিরিক্ত nitrogen এড়িয়ে চলুন।",
            "প্রয়োজন হলে অনুমোদিত fungicide ব্যবহার করুন।",
        ],
        "keywords": ["পাউডারি মিলডিউ", "powdery mildew", "সাদা গুঁড়া"],
    },

    # =========================================================================
    # 🍓 স্ট্রবেরি — Strawberry
    # =========================================================================
    "strawberry_leaf_scorch": {
        "crop": "Strawberry",
        "crop_bn": "স্ট্রবেরি",
        "disease_en": "Leaf Scorch",
        "condition_name_bn": "Leaf Scorch",
        "is_healthy": False,
        "primary_solution": "আক্রান্ত leaf tissue কমানো এবং plant stress নিয়ন্ত্রণ।",
        "guidance": [
            "আক্রান্ত পাতা অপসারণ করুন।",
            "পুরোনো ও মৃত leaf material পরিষ্কার করুন।",
            "অতিরিক্ত আর্দ্রতা ও দীর্ঘসময় leaf wetness কমান।",
            "পর্যাপ্ত airflow নিশ্চিত করুন।",
            "প্রয়োজন হলে অনুমোদিত fungicide ব্যবহার করুন।",
        ],
        "keywords": ["লিফ স্কর্চ", "leaf scorch", "পাতা পোড়া"],
    },
}


def get_crop_disease_knowledge(crop: str, disease: str) -> Dict[str, Any]:
    """Retrieves authoritative agronomic guidance for a specific (crop, disease) tuple.

    Handles both explicit condition mappings and healthy class defaults.
    """
    clean_crop = (crop or "").strip().lower()
    clean_dis = (disease or "").strip().lower()

    is_healthy = "healthy" in clean_dis or clean_dis == "সুস্থ ও নিরোগ গাছ"

    # 1. Match direct keys in REVIEWED_CONDITIONS
    for key, data in REVIEWED_CONDITIONS.items():
        cond_crop = data.get("crop", "").lower()
        cond_dis = data.get("disease_en", "").lower()

        crop_match = (
            cond_crop == clean_crop or
            clean_crop in cond_crop or
            data.get("crop_bn", "").lower() in clean_crop
        )

        if crop_match:
            if is_healthy and data.get("is_healthy"):
                return data
            if not is_healthy and (cond_dis in clean_dis or clean_dis in cond_dis):
                return data

    # 2. Match based on keywords
    for key, data in REVIEWED_CONDITIONS.items():
        cond_crop = data.get("crop", "").lower()
        if cond_crop == clean_crop or clean_crop in cond_crop:
            for kw in data.get("keywords", []):
                if kw.lower() in clean_dis:
                    return data

    # 3. Healthy Fallback for any crop
    if is_healthy:
        return {
            "crop": crop,
            "crop_bn": crop,
            "disease_en": "Healthy",
            "condition_name_bn": "সুস্থ গাছ",
            "is_healthy": True,
            "primary_solution": "কোনো ক্ষতিকর রোগের লক্ষণ শনাক্ত হয়নি। গাছ সুস্থ রয়েছে।",
            "guidance": HEALTHY_GENERAL_GUIDANCE,
            "avoid": None,
            "prevention": None,
            "special_warning": None,
        }

    # 4. General fallback for unmapped condition
    return {
        "crop": crop,
        "crop_bn": crop,
        "disease_en": disease,
        "condition_name_bn": disease,
        "is_healthy": False,
        "primary_solution": f"{crop} ফসলের পাতায় রোগের বিস্তার কমানো এবং গাছের সুষম পুষ্টি ও পানি ব্যবস্থাপনা নিশ্চিত করা।",
        "guidance": [
            "আক্রান্ত পাতা ও ডালপালা সাবধানে অপসারণ করে ধ্বংস করুন।",
            "জমির পানি নিষ্কাশন ও আর্দ্রতা নিয়ন্ত্রণ করুন।",
            "সঠিক বালাই ব্যবস্থাপনার জন্য স্থানীয় উপ-সহকারী কৃষি কর্মকর্তা (SAAO)-এর সাথে পরামর্শ করুন।",
        ],
        "avoid": "অতিরিক্ত নাইট্রোজেন সার ও দীর্ঘমেয়াদী জলাবদ্ধতা।",
        "prevention": "রোগমুক্ত ও প্রত্যায়িত বীজ ব্যবহার এবং নিয়মিত মাঠ পরিদর্শন।",
        "special_warning": None,
    }


def lookup_reviewed_condition(crop_type: str, symptoms: Optional[str]) -> Optional[Dict[str, Any]]:
    """Legacy compatibility helper."""
    clean_crop = (crop_type or "").strip().lower()
    supported_crops_lower = [c["id"].lower() for c in SUPPORTED_CROPS] + [c["name_bn"].lower() for c in SUPPORTED_CROPS]
    if clean_crop and not any(clean_crop == sc or clean_crop in sc or sc in clean_crop for sc in supported_crops_lower):
        return None
    return get_crop_disease_knowledge(crop_type, symptoms or "")

