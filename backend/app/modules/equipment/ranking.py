"""Equipment ranking engine and geospatial distance calculation.

Strictly enforces AGENTS.md Rule 15:
ranking_score = (0.65 * normalized_price_score) + (0.35 * normalized_distance_score)
Lower scores rank higher (best value & closest distance).

Enforces:
- Filters unavailable/paused listings before ranking.
- Compares only identical equipment type and compatible pricing unit.
- Prevents division by zero when min == max.
- Returns transparent breakdown components (price_score, distance_score, ranking_score).
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional
from app.core.errors import ShikhorException
from app.modules.equipment.models import Equipment, PriceUnit


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two coordinates in kilometers."""
    R = 6371.0  # Earth's mean radius in km

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


@dataclass
class RankingBreakdown:
    price_score: float
    distance_score: float
    ranking_score: float
    distance_km: float


@dataclass
class RankedEquipmentItem:
    equipment: Equipment
    distance_km: float
    price_score: float
    distance_score: float
    ranking_score: float


def rank_equipment_candidates(
    candidates: List[Equipment],
    user_lat: float,
    user_lon: float,
    target_unit: PriceUnit,
    max_radius_km: Optional[float] = None,
) -> List[RankedEquipmentItem]:
    """Applies the approved 65/35 ranking formula across filtered candidates."""
    if not candidates:
        return []

    # 1. Validate pricing unit consistency (Rule 15: Never compare incompatible units)
    filtered: List[tuple[Equipment, float]] = []
    for item in candidates:
        if item.price_unit != target_unit:
            continue
        if not item.is_available or item.is_paused:
            continue

        distance = calculate_haversine_distance(user_lat, user_lon, item.latitude, item.longitude)
        effective_radius = max_radius_km or item.service_radius_km
        if distance > effective_radius:
            continue

        filtered.append((item, distance))

    if not filtered:
        return []

    # 2. Extract min & max bounds for normalization
    prices = [item.price_amount for item, _ in filtered]
    distances = [dist for _, dist in filtered]

    min_price = min(prices)
    max_price = max(prices)

    min_distance = min(distances)
    max_distance = max(distances)

    # 3. Compute normalized scores with zero-division protection
    ranked_items: List[RankedEquipmentItem] = []
    for item, dist in filtered:
        # Normalized price score: 0 = lowest price, 1 = highest price
        if max_price == min_price:
            price_score = 0.0
        else:
            price_score = (item.price_amount - min_price) / (max_price - min_price)

        # Normalized distance score: 0 = nearest, 1 = farthest in radius
        if max_distance == min_distance:
            distance_score = 0.0
        else:
            distance_score = (dist - min_distance) / (max_distance - min_distance)

        # Approved formula: 65% price + 35% distance
        ranking_score = round((0.65 * price_score) + (0.35 * distance_score), 4)

        ranked_items.append(
            RankedEquipmentItem(
                equipment=item,
                distance_km=dist,
                price_score=round(price_score, 4),
                distance_score=round(distance_score, 4),
                ranking_score=ranking_score,
            )
        )

    # 4. Sort by ranking_score ascending (lower score = higher rank)
    ranked_items.sort(key=lambda x: (x.ranking_score, x.distance_km, x.equipment.price_amount))
    return ranked_items
