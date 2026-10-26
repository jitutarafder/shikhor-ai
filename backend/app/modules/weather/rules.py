"""Agronomic rule engine translating weather facts into practical farming activity plans.

Strictly complies with:
- AGENTS.md Rule 20: Product recommendations are structurally distinguishable from provider facts.
- Reviewed agricultural practices for Bangladesh rice, vegetables, and machinery.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple
from app.integrations.weather.provider import RawDailyForecast, RawWeatherFact


class ActivityType(str, Enum):
    SPRAYING = "spraying"
    HARVESTING = "harvesting"
    IRRIGATION = "irrigation"
    MACHINERY = "machinery"


class SuitabilityLevel(str, Enum):
    SUITABLE = "suitable"        # অনুকূল
    CAUTION = "caution"          # সতর্কতা
    UNFAVORABLE = "unfavorable"  # অনুপযুক্ত


@dataclass
class ActivityRecommendation:
    activity_type: ActivityType
    title_bn: str
    suitability: SuitabilityLevel
    reason_summary_bn: str
    guidance_bn: str
    risk_factors: List[str]


@dataclass
class MachineryWeatherWarning:
    warning_level: str  # "warning" | "alert" | "info"
    title_bn: str
    message_bn: str
    affected_equipment: List[str]


def evaluate_spraying_activity(
    fact: RawWeatherFact, daily: Optional[RawDailyForecast] = None
) -> ActivityRecommendation:
    """Evaluates suitability for pesticide, fungicide, or foliar fertilizer spraying."""
    risks: List[str] = []

    # 1. Wind speed constraints (Drift hazard above 15 km/h)
    if fact.wind_speed_kmh > 15.0 or (daily and daily.wind_speed_max_kmh > 20.0):
        risks.append("উচ্চ বাতাসের গতিবেগ (বাতাসে ওষুধ উড়ে যাওয়ার ও পার্শ্ববর্তী এলাকায় বিষাক্ততার ঝুঁকি)")
        return ActivityRecommendation(
            activity_type=ActivityType.SPRAYING,
            title_bn="বালাইনাশক ও ভিটামিন স্প্রে",
            suitability=SuitabilityLevel.UNFAVORABLE,
            reason_summary_bn="বাতাসের বেগ বেশি (১৫ কিমি/ঘণ্টার অধিক)। স্প্রে করলে বাতাসের তোড়ে ওষুধ উড়ে যাবে এবং কার্যকারিতা নষ্ট হবে।",
            guidance_bn="বাতাস শান্ত হওয়া পর্যন্ত (১০ কিমি/ঘণ্টার নিচে) স্প্রে স্থগিত রাখুন।",
            risk_factors=risks,
        )

    # 2. Rain constraints (Wash-off hazard)
    rain_prob = daily.precipitation_probability_max if daily else fact.precipitation_probability
    rain_sum = daily.precipitation_sum_mm if daily else fact.precipitation_mm

    if rain_prob >= 40 or rain_sum >= 2.0 or fact.precipitation_mm > 0.5:
        risks.append("বৃষ্টিপাতের ঝুঁকি (ওষুধ ধুয়ে যাওয়ার সম্ভাবনা)")
        return ActivityRecommendation(
            activity_type=ActivityType.SPRAYING,
            title_bn="বালাইনাশক ও ভিটামিন স্প্রে",
            suitability=SuitabilityLevel.UNFAVORABLE,
            reason_summary_bn="বৃষ্টির উচ্চ সম্ভাবনা রয়েছে। স্প্রে করার পর বৃষ্টি হলে রাসায়নিক ধুয়ে যাবে এবং কৃষক আর্থিক ক্ষতির মুখে পড়বেন।",
            guidance_bn="বৃষ্টিপাত থেমে আকাশ পরিষ্কার ও রোদ না ওঠা পর্যন্ত স্প্রে স্থগিত রাখুন।",
            risk_factors=risks,
        )

    # 3. High Temperature constraint (Rapid evaporation / leaf scorch)
    if fact.temperature_c >= 34.0:
        risks.append("তীব্র রোদ ও উচ্চ তাপমাত্রা (দ্রুত বাষ্পীভবন ও পাতার ক্ষতি)")
        return ActivityRecommendation(
            activity_type=ActivityType.SPRAYING,
            title_bn="বালাইনাশক ও ভিটামিন স্প্রে",
            suitability=SuitabilityLevel.CAUTION,
            reason_summary_bn="তাপমাত্রা ৩৪° সেলসিয়াসের বেশি। তীব্র রোদে স্প্রে করলে ওষুধ দ্রুত শুকিয়ে বাষ্পীভূত হয় এবং পাতা পুড়ে যেতে পারে।",
            guidance_bn="দুপুরের কড়া রোদে স্প্রে করবেন না। সকাল ৯টার পূর্বে অথবা বিকাল ৪টার পরে স্প্রে সম্পন্ন করুন।",
            risk_factors=risks,
        )

    # 4. Favorable condition
    return ActivityRecommendation(
        activity_type=ActivityType.SPRAYING,
        title_bn="বালাইনাশক ও ভিটামিন স্প্রে",
        suitability=SuitabilityLevel.SUITABLE,
        reason_summary_bn="বাতাস শান্ত এবং বৃষ্টির ঝুঁকি নেই।",
        guidance_bn="স্প্রে করার জন্য চমৎকার ও অনুকূল আবহাওয়া। নিরাপত্তা মাস্ক ও গ্লাভস পরিধান করে স্প্রে করুন।",
        risk_factors=[],
    )


def evaluate_harvesting_activity(
    fact: RawWeatherFact, daily: Optional[RawDailyForecast] = None
) -> ActivityRecommendation:
    """Evaluates suitability for crop harvesting and threshing (ধান কাটা ও মাড়াই)."""
    risks: List[str] = []
    rain_prob = daily.precipitation_probability_max if daily else fact.precipitation_probability
    rain_sum = daily.precipitation_sum_mm if daily else fact.precipitation_mm

    # 1. Heavy rain / high rain probability
    if rain_prob >= 50 or rain_sum >= 5.0:
        risks.append("বৃষ্টিপাত ও স্যাঁতসেঁতে আবহাওয়া (ফসল পচন ও অঙ্কুরোদগমের ঝুঁকি)")
        return ActivityRecommendation(
            activity_type=ActivityType.HARVESTING,
            title_bn="ফসল কর্তন ও মাড়াই",
            suitability=SuitabilityLevel.UNFAVORABLE,
            reason_summary_bn="বৃষ্টির তীব্র পূর্বাভাস রয়েছে। পাকা ধান বা ফসল কেটে ভিজলে দানা কালো হওয়া ও ছত্রাক সংক্রমণের ঝুঁকি রয়েছে।",
            guidance_bn="বৃষ্টি কেটে যাওয়ার আগে নতুন করে ফসল কাটা শুরু করবেন না। পূর্বের কাটা ফসল দ্রুত ত্রিপল দিয়ে ঢেকে নিরাপদ স্থানে রাখুন।",
            risk_factors=risks,
        )

    # 2. Moderate rain or high humidity caution
    if rain_prob >= 25 or rain_sum >= 1.0 or fact.relative_humidity > 85:
        risks.append("আংশিক বৃষ্টির সম্ভাবনা ও বাতাসে উচ্চ আর্দ্রতা")
        return ActivityRecommendation(
            activity_type=ActivityType.HARVESTING,
            title_bn="ফসল কর্তন ও মাড়াই",
            suitability=SuitabilityLevel.CAUTION,
            reason_summary_bn="আংশিক মেঘলা ও বৃষ্টির সামান্য সম্ভাবনা রয়েছে।",
            guidance_bn="ফসল কাটলে সাথে সাথে মাড়াই করে শুকানোর প্রস্তুতি রাখুন এবং জমিতে ফেলে রাখবেন না।",
            risk_factors=risks,
        )

    # 3. Favorable
    return ActivityRecommendation(
        activity_type=ActivityType.HARVESTING,
        title_bn="ফসল কর্তন ও মাড়াই",
        suitability=SuitabilityLevel.SUITABLE,
        reason_summary_bn="আকাশ পরিষ্কার ও রোদোজ্জ্বল। মাড়াই ও রোদে শুকানোর আদর্শ পরিবেশ।",
        guidance_bn="পাকা ফসল কর্তন ও ধান মাড়াইয়ের উপযুক্ত সময়।",
        risk_factors=[],
    )


def evaluate_irrigation_activity(
    fact: RawWeatherFact, daily: Optional[RawDailyForecast] = None
) -> ActivityRecommendation:
    """Evaluates suitability for field irrigation (সেচ প্রদান)."""
    risks: List[str] = []
    rain_prob = daily.precipitation_probability_max if daily else fact.precipitation_probability
    rain_sum = daily.precipitation_sum_mm if daily else fact.precipitation_mm

    # 1. Rain forecasted >= 10mm -> Pause irrigation (saves cost, avoids waterlogging)
    if rain_sum >= 8.0 or rain_prob >= 60:
        risks.append("আসন্ন বৃষ্টিপাত (অতিরিক্ত সেচ দিলে জলাবদ্ধতা ও খরচ অপচয়ের ঝুঁকি)")
        return ActivityRecommendation(
            activity_type=ActivityType.IRRIGATION,
            title_bn="জমিতে সেচ প্রদান",
            suitability=SuitabilityLevel.UNFAVORABLE,
            reason_summary_bn="শীঘ্রই পর্যাপ্ত বৃষ্টির জোরালো সম্ভাবনা রয়েছে। এখন সেচ দিলে জ্বালানি ও বিদ্যুৎ অপচয় হবে এবং জমিতে জলাবদ্ধতা তৈরি হতে পারে।",
            guidance_bn="কৃত্রিম সেচ সাময়িক বন্ধ রাখুন। বৃষ্টির পর মাটির রস দেখে পরবর্তী সিদ্ধান্ত নিন।",
            risk_factors=risks,
        )

    # 2. Moderate rain warning
    if rain_sum >= 3.0 or rain_prob >= 35:
        risks.append("মাঝারি বৃষ্টির সম্ভাবনা")
        return ActivityRecommendation(
            activity_type=ActivityType.IRRIGATION,
            title_bn="জমিতে সেচ প্রদান",
            suitability=SuitabilityLevel.CAUTION,
            reason_summary_bn="সামান্য বৃষ্টির পূর্বাভাস রয়েছে।",
            guidance_bn="মাটি শুষ্ক থাকলে শুধুমাত্র হালকা সেচ দিন। গভীর সেচ দেওয়া থেকে বিরত থাকুন।",
            risk_factors=risks,
        )

    # 3. Dry weather -> Suitable for irrigation
    return ActivityRecommendation(
        activity_type=ActivityType.IRRIGATION,
        title_bn="জমিতে সেচ প্রদান",
        suitability=SuitabilityLevel.SUITABLE,
        reason_summary_bn="শুষ্ক আবহাওয়া ও বৃষ্টির সম্ভাবনা কম। মাটির আর্দ্রতা ধরে রাখতে সেচ প্রয়োজন।",
        guidance_bn="ফসলের বৃদ্ধির স্তর বিবেচনা করে রুটিন অনুযায়ী পরিমিত সেচ প্রদান করুন।",
        risk_factors=[],
    )


def evaluate_machinery_activity(
    fact: RawWeatherFact, daily: Optional[RawDailyForecast] = None
) -> Tuple[ActivityRecommendation, Optional[MachineryWeatherWarning]]:
    """Evaluates machinery operations (ট্রাক্টর, হার্ভেস্টার, পাওয়ার টিলার)."""
    risks: List[str] = []
    rain_sum = daily.precipitation_sum_mm if daily else fact.precipitation_mm

    # 1. Thunderstorms / Gales (Safety danger to operators)
    if fact.weather_code in [95, 96, 99]:
        risks.append("বজ্রপাত ও তীব্র ঝড়ের ঝুঁকি")
        rec = ActivityRecommendation(
            activity_type=ActivityType.MACHINERY,
            title_bn="ভারী কৃষিযন্ত্র চালনা",
            suitability=SuitabilityLevel.UNFAVORABLE,
            reason_summary_bn="বজ্রবিদ্যুৎসহ ঝড়বৃষ্টির আশঙ্কা। খোলা মাঠে ধাতব কৃষিযন্ত্র পরিচালনা প্রাণঘাতী হতে পারে।",
            guidance_bn="মাঠে ট্রাক্টর বা কম্বাইন হার্ভেস্টার চালানো অবিলম্বে বন্ধ রাখুন এবং নিরাপদ আশ্রয়ে অবস্থান নিন।",
            risk_factors=risks,
        )
        warning = MachineryWeatherWarning(
            warning_level="alert",
            title_bn="বজ্রপাতের সতর্কতা: যন্ত্র চালনা স্থগিত রাখুন",
            message_bn="খোলা মাঠে ট্রাক্টর বা হার্ভেস্টার পরিচালনা অত্যন্ত বিপজ্জনক। আবহাওয়া শান্ত না হওয়া পর্যন্ত কাজ বন্ধ রাখুন।",
            affected_equipment=["tractor", "harvester", "power_tiller", "sprayer"],
        )
        return rec, warning

    # 2. Mud hazard from heavy rain
    if rain_sum >= 12.0 or fact.precipitation_mm >= 5.0:
        risks.append("জলাবদ্ধতা ও অতিরিক্ত কাদা (ভারী যন্ত্র আটকে যাওয়ার ঝুঁকি)")
        rec = ActivityRecommendation(
            activity_type=ActivityType.MACHINERY,
            title_bn="ভারী কৃষিযন্ত্র চালনা",
            suitability=SuitabilityLevel.UNFAVORABLE,
            reason_summary_bn="ভারী বৃষ্টির কারণে মাঠের মাটি নরম ও পিচ্ছিল হয়ে চাকা দেবে যাওয়ার উচ্চ ঝুঁকি রয়েছে।",
            guidance_bn="জমির পানি নিষ্কাশন ও মাটি কিছুটা শক্ত হওয়া পর্যন্ত ভারী যন্ত্র ভাড়া নেওয়া বা চালানো থেকে বিরত থাকুন।",
            risk_factors=risks,
        )
        warning = MachineryWeatherWarning(
            warning_level="warning",
            title_bn="কাদামাটিতে চাকা দেবে যাওয়ার ঝুঁকি",
            message_bn="ভারী বৃষ্টির পর জমিতে ট্রাক্টর বা হার্ভেস্টার নামালে চাকা আটকে ক্ষতি হতে পারে। জমি শুকাতে সময় দিন।",
            affected_equipment=["tractor", "harvester"],
        )
        return rec, warning

    # 3. Normal / Favorable conditions
    rec = ActivityRecommendation(
        activity_type=ActivityType.MACHINERY,
        title_bn="ভারী কৃষিযন্ত্র চালনা",
        suitability=SuitabilityLevel.SUITABLE,
        reason_summary_bn="মাটি শুষ্ক ও শক্ত এবং আবহাওয়া অনুকূল।",
        guidance_bn="জমি চাষ, ফসল কাটা বা মাড়াইয়ের কাজে ট্রাক্টর ও হার্ভেস্টার নিরাপদে ব্যবহার করা যাবে।",
        risk_factors=[],
    )
    return rec, None


def generate_all_activity_plans(
    fact: RawWeatherFact, daily: Optional[RawDailyForecast] = None
) -> Tuple[List[ActivityRecommendation], List[MachineryWeatherWarning]]:
    """Evaluates all agricultural activities for given facts."""
    recs: List[ActivityRecommendation] = []
    warnings: List[MachineryWeatherWarning] = []

    # 1. Spraying
    recs.append(evaluate_spraying_activity(fact, daily))

    # 2. Harvesting
    recs.append(evaluate_harvesting_activity(fact, daily))

    # 3. Irrigation
    recs.append(evaluate_irrigation_activity(fact, daily))

    # 4. Machinery
    mach_rec, mach_warn = evaluate_machinery_activity(fact, daily)
    recs.append(mach_rec)
    if mach_warn:
        warnings.append(mach_warn)

    return recs, warnings
