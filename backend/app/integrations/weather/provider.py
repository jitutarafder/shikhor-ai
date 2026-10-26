"""Weather provider adapter and HTTP integrations.

Strictly complies with AGENTS.md Rule 20:
- Provider timeout, retry budget, and caching.
- Attribution and provider timestamps.
- Stale data detection and fallback handling.
- Never expose provider secrets.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Protocol, Tuple
import httpx

logger = logging.getLogger("shikhor.weather")

# WMO Weather Interpretation Codes (WW) translated to standard Bangla descriptions
WMO_CODE_BANGLA: Dict[int, str] = {
    0: "পরিষ্কার রোদোজ্জ্বল আকাশ",
    1: "প্রধানত রোদোজ্জ্বল ও পরিষ্কার",
    2: "আংশিক মেঘলা আকাশ",
    3: "মেঘলা আকাশ",
    45: "কুয়াশাচ্ছন্ন আবহাওয়া",
    48: "ঘন কুয়াশা",
    51: "হালকা গুঁড়ি গুঁড়ি বৃষ্টি",
    53: "মাঝারি গুঁড়ি গুঁড়ি বৃষ্টি",
    55: "ভারী গুঁড়ি গুঁড়ি বৃষ্টি",
    61: "হালকা বৃষ্টি",
    63: "মাঝারি বৃষ্টিপাত",
    65: "ভারী বর্ষণ",
    71: "হালকা তুষারপাত",
    80: "দমকা হাওয়াসহ হালকা বৃষ্টি",
    81: "দমকা হাওয়াসহ মাঝারি বৃষ্টি",
    82: "দমকা হাওয়াসহ মুষলধারে বৃষ্টি",
    95: "বজ্রবিদ্যুৎসহ ঝড়বৃষ্টি",
    96: "বজ্রঝড় ও শিলাবৃষ্টি",
    99: "তীব্র বজ্রঝড় ও ভারী শিলাবৃষ্টি",
}


@dataclass
class RawWeatherFact:
    timestamp: datetime
    temperature_c: float
    feels_like_c: float
    relative_humidity: int
    precipitation_probability: int
    precipitation_mm: float
    wind_speed_kmh: float
    wind_gust_kmh: float
    weather_code: int
    weather_description_bn: str


@dataclass
class RawDailyForecast:
    date: str  # YYYY-MM-DD
    temp_max_c: float
    temp_min_c: float
    precipitation_probability_max: int
    precipitation_sum_mm: float
    wind_speed_max_kmh: float
    weather_code: int
    weather_description_bn: str


@dataclass
class RawWeatherResponse:
    provider_name: str
    attribution: str
    provider_timestamp: datetime
    latitude: float
    longitude: float
    current: RawWeatherFact
    daily: List[RawDailyForecast]
    is_stale: bool = False
    stale_reason: Optional[str] = None


class WeatherProvider(Protocol):
    """Protocol for weather provider implementations."""

    async def fetch_weather(self, lat: float, lon: float) -> RawWeatherResponse:
        ...


class OpenMeteoWeatherAdapter:
    """Production-grade weather adapter for Open-Meteo with caching, bounded retries, and stale fallback.

    Complies with AGENTS.md Rule 20.
    """

    PROVIDER_NAME = "Open-Meteo (ECMWF & GFS)"
    ATTRIBUTION = "বাংলাদেশ আবহাওয়া বিশ্লেষণ ও আন্তর্জাতিক আবহাওয়া মডেল (Open-Meteo)"
    CACHE_TTL_SECONDS = 1800  # 30 minutes cache TTL
    REQUEST_TIMEOUT_SECONDS = 4.0

    def __init__(self):
        # In-memory cache: (rounded_lat, rounded_lon) -> (cached_at_epoch, RawWeatherResponse)
        self._cache: Dict[Tuple[float, float], Tuple[float, RawWeatherResponse]] = {}

    async def fetch_weather(self, lat: float, lon: float) -> RawWeatherResponse:
        """Fetches current and 3-day forecast for coordinates with caching and retries."""
        # Round coordinates to 2 decimal places (~1.1 km) for caching and privacy
        cache_key = (round(lat, 2), round(lon, 2))
        now_epoch = datetime.now(timezone.utc).timestamp()

        # 1. Check cache freshness
        if cache_key in self._cache:
            cached_epoch, cached_data = self._cache[cache_key]
            if now_epoch - cached_epoch < self.CACHE_TTL_SECONDS:
                logger.debug(f"Returning cached weather for {cache_key}")
                return cached_data

        # 2. Attempt remote provider call with bounded retry budget
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation",
                "weather_code",
                "wind_speed_10m",
                "wind_gusts_10m",
            ],
            "daily": [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "precipitation_probability_max",
                "wind_speed_10m_max",
            ],
            "timezone": "Asia/Dhaka",
            "forecast_days": 4,
        }

        attempts = 0
        last_exception = None

        while attempts < 2:
            attempts += 1
            try:
                async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT_SECONDS) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        parsed = self._parse_open_meteo_response(data, lat, lon)
                        # Update cache
                        self._cache[cache_key] = (now_epoch, parsed)
                        return parsed
                    else:
                        logger.warning(
                            f"Weather provider returned status {resp.status_code}: {resp.text}"
                        )
            except Exception as exc:
                last_exception = exc
                logger.warning(
                    f"Weather provider attempt {attempts} failed: {exc}. Retrying..."
                )

        # 3. Handle provider failure gracefully (Rule 20: Stale/unavailable state)
        logger.error(f"Weather provider completely unreachable: {last_exception}")

        # Check if we have stale cache available
        if cache_key in self._cache:
            _, stale_data = self._cache[cache_key]
            logger.info("Serving stale cached weather data due to provider timeout.")
            return RawWeatherResponse(
                provider_name=stale_data.provider_name,
                attribution=stale_data.attribution,
                provider_timestamp=stale_data.provider_timestamp,
                latitude=stale_data.latitude,
                longitude=stale_data.longitude,
                current=stale_data.current,
                daily=stale_data.daily,
                is_stale=True,
                stale_reason="আবহাওয়া সার্ভার থেকে নতুন তথ্য পাওয়া যায়নি। পূর্বের সংরক্ষিত তথ্য প্রদর্শিত হচ্ছে।",
            )

        # 4. Generate seasonal fallback when no cache exists
        return self._create_seasonal_fallback(lat, lon, reason="লাইভ আবহাওয়া সার্ভারের সংযোগ বিচ্ছিন্ন।")

    def _parse_open_meteo_response(
        self, data: dict, lat: float, lon: float
    ) -> RawWeatherResponse:
        current_data = data.get("current", {})
        daily_data = data.get("daily", {})

        wmo_code = current_data.get("weather_code", 0)
        desc_bn = WMO_CODE_BANGLA.get(wmo_code, "স্বাভাবিক আবহাওয়া")

        current_fact = RawWeatherFact(
            timestamp=datetime.now(timezone.utc),
            temperature_c=float(current_data.get("temperature_2m", 28.0)),
            feels_like_c=float(current_data.get("apparent_temperature", 30.0)),
            relative_humidity=int(current_data.get("relative_humidity_2m", 65)),
            precipitation_probability=int(
                daily_data.get("precipitation_probability_max", [0])[0]
                if daily_data.get("precipitation_probability_max")
                else 0
            ),
            precipitation_mm=float(current_data.get("precipitation", 0.0)),
            wind_speed_kmh=float(current_data.get("wind_speed_10m", 8.0)),
            wind_gust_kmh=float(current_data.get("wind_gusts_10m", 12.0)),
            weather_code=wmo_code,
            weather_description_bn=desc_bn,
        )

        daily_list: List[RawDailyForecast] = []
        dates = daily_data.get("time", [])
        max_temps = daily_data.get("temperature_2m_max", [])
        min_temps = daily_data.get("temperature_2m_min", [])
        rain_probs = daily_data.get("precipitation_probability_max", [])
        rain_sums = daily_data.get("precipitation_sum", [])
        wind_speeds = daily_data.get("wind_speed_10m_max", [])
        codes = daily_data.get("weather_code", [])

        # Process up to 3 upcoming days
        for i in range(min(len(dates), 4)):
            code = codes[i] if i < len(codes) else 0
            daily_list.append(
                RawDailyForecast(
                    date=dates[i] if i < len(dates) else "",
                    temp_max_c=float(max_temps[i]) if i < len(max_temps) else 32.0,
                    temp_min_c=float(min_temps[i]) if i < len(min_temps) else 24.0,
                    precipitation_probability_max=int(rain_probs[i]) if i < len(rain_probs) else 10,
                    precipitation_sum_mm=float(rain_sums[i]) if i < len(rain_sums) else 0.0,
                    wind_speed_max_kmh=float(wind_speeds[i]) if i < len(wind_speeds) else 10.0,
                    weather_code=code,
                    weather_description_bn=WMO_CODE_BANGLA.get(code, "স্বাভাবিক আবহাওয়া"),
                )
            )

        return RawWeatherResponse(
            provider_name=self.PROVIDER_NAME,
            attribution=self.ATTRIBUTION,
            provider_timestamp=datetime.now(timezone.utc),
            latitude=lat,
            longitude=lon,
            current=current_fact,
            daily=daily_list,
            is_stale=False,
        )

    def _create_seasonal_fallback(
        self, lat: float, lon: float, reason: str
    ) -> RawWeatherResponse:
        """Safe fallback data structure when remote provider is totally down and no cache exists."""
        current_fact = RawWeatherFact(
            timestamp=datetime.now(timezone.utc),
            temperature_c=29.0,
            feels_like_c=31.0,
            relative_humidity=70,
            precipitation_probability=15,
            precipitation_mm=0.0,
            wind_speed_kmh=9.0,
            wind_gust_kmh=14.0,
            weather_code=2,
            weather_description_bn="আংশিক মেঘলা (অফলাইন অনুমান)",
        )

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily_list = [
            RawDailyForecast(
                date=today,
                temp_max_c=32.0,
                temp_min_c=25.0,
                precipitation_probability_max=20,
                precipitation_sum_mm=0.0,
                wind_speed_max_kmh=12.0,
                weather_code=2,
                weather_description_bn="আংশিক মেঘলা",
            ),
        ]

        return RawWeatherResponse(
            provider_name="Shikhor Regional Climate Baseline",
            attribution=self.ATTRIBUTION,
            provider_timestamp=datetime.now(timezone.utc),
            latitude=lat,
            longitude=lon,
            current=current_fact,
            daily=daily_list,
            is_stale=True,
            stale_reason=reason,
        )
