"""
Concurrency and Load Testing Tool for Shikhor AI Backend (MongoDB + Cloudinary)
================================================================================
Simulates realistic concurrent agricultural users hitting core application flows:
  - Authentication (Login / Token Verification)
  - User Profile (/auth/me)
  - AI Crop Disease Vision Model Inference (/crop-cases/predict)
  - Crop Cases Read & History (/crop-cases)
  - Equipment 2dsphere Geospatial Search & 65/35 Ranking (/equipment/search)
  - Messaging & Conversations (/messages/conversations)
  - Health & Baseline DB Check (/health, /health/readiness)

Measures:
  - Requests / Second (RPS)
  - Mean, Median (p50), p95, p99, Min, Max Latencies (ms)
  - Error Rates (4xx, 5xx, Network/Timeout)
  - Bottleneck identification per endpoint
"""

import asyncio
import io
import json
import logging
import os
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

import httpx

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
API_PREFIX = "/api/v1"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("shikhor.load_test")


@dataclass
class RequestMetric:
    endpoint: str
    method: str
    status_code: int
    duration_ms: float
    error: Optional[str] = None


@dataclass
class TierResult:
    concurrency: int
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    requests_per_second: float
    error_rate_pct: float
    status_counts: Dict[int, int] = field(default_factory=dict)
    endpoint_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    overall_latency: Dict[str, float] = field(default_factory=dict)
    cpu_percent_approx: float = 0.0
    memory_mb_approx: float = 0.0


def calculate_percentiles(latencies: List[float]) -> Dict[str, float]:
    if not latencies:
        return {"min": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0, "max": 0}
    sorted_lat = sorted(latencies)
    n = len(sorted_lat)

    def p(pct: float) -> float:
        idx = int((pct / 100.0) * n)
        idx = min(idx, n - 1)
        return sorted_lat[idx]

    return {
        "min": round(sorted_lat[0], 2),
        "avg": round(sum(sorted_lat) / n, 2),
        "p50": round(p(50), 2),
        "p95": round(p(95), 2),
        "p99": round(p(99), 2),
        "max": round(sorted_lat[-1], 2),
    }


def create_sample_leaf_bytes() -> bytes:
    """Creates a synthetic 224x224 RGB image in-memory for AI vision inference testing."""
    img = Image.new("RGB", (224, 224), color=(34, 139, 34))  # Forest green leaf
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


class ConcurrencyLoadTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.leaf_image_bytes = create_sample_leaf_bytes()

    async def setup_auth(self) -> bool:
        """Obtains an auth token from the running backend to perform authenticated flows."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.post(
                    f"{self.base_url}{API_PREFIX}/auth/login",
                    json={"phone": "01711223344", "password": "Password123#Strong"},
                )
                if res.status_code == 200:
                    data = res.json()
                    self.token = data.get("accessToken")
                    logger.info("Authenticated successfully as test user")
                    return True
                else:
                    logger.warning("Auth setup failed with status %d: %s", res.status_code, res.text)
                    return False
            except Exception as e:
                logger.error("Error setting up auth for load test: %s", e)
                return False

    async def execute_user_action(
        self, client: httpx.AsyncClient, action_type: str, headers: Dict[str, str]
    ) -> RequestMetric:
        """Executes a single user endpoint action and records high-precision timing."""
        start = time.perf_counter()
        status_code = 0
        error_msg = None

        try:
            if action_type == "health":
                res = await client.get(f"{self.base_url}{API_PREFIX}/health")
                status_code = res.status_code

            elif action_type == "readiness":
                res = await client.get(f"{self.base_url}{API_PREFIX}/health/readiness")
                status_code = res.status_code

            elif action_type == "get_profile":
                res = await client.get(f"{self.base_url}{API_PREFIX}/auth/me", headers=headers)
                status_code = res.status_code

            elif action_type == "list_crop_cases":
                res = await client.get(f"{self.base_url}{API_PREFIX}/crop-cases", headers=headers)
                status_code = res.status_code

            elif action_type == "search_equipment":
                res = await client.get(
                    f"{self.base_url}{API_PREFIX}/equipment?equipmentType=tractor&priceUnit=per_hour&latitude=25.62&longitude=88.63&maxRadiusKm=30",
                    headers=headers,
                )
                status_code = res.status_code

            elif action_type == "list_conversations":
                res = await client.get(
                    f"{self.base_url}{API_PREFIX}/conversations", headers=headers
                )
                status_code = res.status_code

            elif action_type == "ai_crop_prediction":
                files = {"file": ("leaf.jpg", self.leaf_image_bytes, "image/jpeg")}
                data = {"crop": "rice"}
                res = await client.post(
                    f"{self.base_url}{API_PREFIX}/crop-disease/predict",
                    files=files,
                    data=data,
                    headers=headers,
                )
                status_code = res.status_code

            elif action_type == "login_request":
                res = await client.post(
                    f"{self.base_url}{API_PREFIX}/auth/login",
                    json={"phone": "01711223344", "password": "Password123#Strong"},
                )
                status_code = res.status_code

            else:
                raise ValueError(f"Unknown action: {action_type}")

        except httpx.TimeoutException:
            status_code = 504
            error_msg = "TIMEOUT"
        except httpx.ConnectError:
            status_code = 503
            error_msg = "CONNECT_ERROR"
        except Exception as e:
            status_code = 500
            error_msg = str(e)

        duration_ms = (time.perf_counter() - start) * 1000.0
        return RequestMetric(
            endpoint=action_type,
            method="POST" if "prediction" in action_type or "login" in action_type else "GET",
            status_code=status_code,
            duration_ms=duration_ms,
            error=error_msg,
        )

    async def user_worker(
        self,
        worker_id: int,
        stop_event: asyncio.Event,
        action_weights: List[Tuple[str, int]],
        results: List[RequestMetric],
        client: httpx.AsyncClient,
    ):
        """Simulates a concurrent user session executing weighted agricultural tasks continuously."""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        import random

        actions, weights = zip(*action_weights)

        while not stop_event.is_set():
            # Pick a realistic action based on real traffic weighting
            action = random.choices(actions, weights=weights, k=1)[0]
            metric = await self.execute_user_action(client, action, headers)
            results.append(metric)

            # Realistic micro-think time (0ms to 25ms between actions in stress test)
            await asyncio.sleep(0.01)

    async def run_tier(
        self,
        concurrency: int,
        duration_seconds: float,
        action_weights: List[Tuple[str, int]],
    ) -> TierResult:
        """Runs a concurrent load test tier at specified user concurrency."""
        logger.info(">>> Starting Concurrency Tier: %d Concurrent Users (Duration: %.1fs)...", concurrency, duration_seconds)

        limits = httpx.Limits(max_connections=concurrency * 2 + 50, max_keepalive_connections=concurrency + 20)
        timeout = httpx.Timeout(20.0, connect=10.0)

        results: List[RequestMetric] = []
        stop_event = asyncio.Event()

        start_time = time.perf_counter()

        async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
            workers = [
                asyncio.create_task(
                    self.user_worker(i, stop_event, action_weights, results, client)
                )
                for i in range(concurrency)
            ]

            await asyncio.sleep(duration_seconds)
            stop_event.set()
            await asyncio.gather(*workers, return_exceptions=True)

        total_elapsed = time.perf_counter() - start_time
        total_reqs = len(results)
        successful_reqs = sum(1 for r in results if 200 <= r.status_code < 400)
        failed_reqs = total_reqs - successful_reqs
        rps = round(total_reqs / total_elapsed, 2) if total_elapsed > 0 else 0
        error_pct = round((failed_reqs / total_reqs) * 100.0, 2) if total_reqs > 0 else 0.0

        # Status breakdown
        status_counts: Dict[int, int] = defaultdict(int)
        for r in results:
            status_counts[r.status_code] += 1

        # Per endpoint latencies
        endpoint_data: Dict[str, List[float]] = defaultdict(list)
        endpoint_errors: Dict[str, int] = defaultdict(int)
        for r in results:
            endpoint_data[r.endpoint].append(r.duration_ms)
            if not (200 <= r.status_code < 400):
                endpoint_errors[r.endpoint] += 1

        endpoint_metrics: Dict[str, Dict[str, Any]] = {}
        for ep, lats in endpoint_data.items():
            pcts = calculate_percentiles(lats)
            ep_total = len(lats)
            ep_errs = endpoint_errors[ep]
            endpoint_metrics[ep] = {
                "count": ep_total,
                "rps": round(ep_total / total_elapsed, 2),
                "error_count": ep_errs,
                "error_rate_pct": round((ep_errs / ep_total) * 100.0, 2) if ep_total > 0 else 0.0,
                **pcts,
            }

        overall_latencies = calculate_percentiles([r.duration_ms for r in results])

        logger.info(
            "--- Tier %d Users Completed: %d reqs in %.2fs | RPS: %.2f | Avg: %.2fms | p95: %.2fms | Errors: %d (%.2f%%) ---",
            concurrency,
            total_reqs,
            total_elapsed,
            rps,
            overall_latencies["avg"],
            overall_latencies["p95"],
            failed_reqs,
            error_pct,
        )

        return TierResult(
            concurrency=concurrency,
            duration_seconds=round(total_elapsed, 2),
            total_requests=total_reqs,
            successful_requests=successful_reqs,
            failed_requests=failed_reqs,
            requests_per_second=rps,
            error_rate_pct=error_pct,
            status_counts=dict(status_counts),
            endpoint_metrics=endpoint_metrics,
            overall_latency=overall_latencies,
        )


async def main():
    print("=" * 80)
    print("        SHIKHOR AI - REALISTIC CONCURRENCY & LOAD TESTING SUITE")
    print("=" * 80)

    tester = ConcurrencyLoadTester(BASE_URL)
    auth_ok = await tester.setup_auth()
    if not auth_ok:
        logger.warning("Could not setup authenticated test user; proceeding with public & auth endpoints.")

    # Weighted realistic user actions:
    # 25% User Profile, 20% Equipment 65/35 search, 20% Crop Cases Read,
    # 15% Messaging, 10% AI Disease Leaf Inference, 5% Login, 5% Health
    action_weights = [
        ("get_profile", 25),
        ("search_equipment", 20),
        ("list_crop_cases", 20),
        ("list_conversations", 15),
        ("ai_crop_prediction", 10),
        ("login_request", 5),
        ("readiness", 5),
    ]

    concurrency_tiers = [10, 25, 50, 100, 200]
    tier_duration = 10.0  # 10s per tier for crisp, reproducible measurement

    all_results: List[TierResult] = []

    for c in concurrency_tiers:
        tier_res = await tester.run_tier(c, tier_duration, action_weights)
        all_results.append(tier_res)
        # 1s cooldown between stages
        await asyncio.sleep(1.0)

    # Isolated Endpoint Stress Test at 50 concurrency to pinpoint individual endpoint saturation
    print("\n" + "=" * 80)
    print("       ISOLATED ENDPOINT SATURATION BENCHMARK (50 Concurrent Users)")
    print("=" * 80)
    endpoint_stress_results = {}
    isolated_endpoints = [
        ("get_profile", "User Profile (/auth/me)"),
        ("search_equipment", "Equipment 2dsphere + 65/35 Ranking (/equipment)"),
        ("list_crop_cases", "Crop Cases Read (/crop-cases)"),
        ("list_conversations", "Conversations (/conversations)"),
        ("ai_crop_prediction", "AI Disease Vision Inference (/crop-disease/predict)"),
        ("login_request", "Argon2id Login Authentication (/auth/login)"),
    ]

    for ep_key, ep_label in isolated_endpoints:
        logger.info("Testing isolated endpoint: %s ...", ep_label)
        res = await tester.run_tier(
            concurrency=50,
            duration_seconds=6.0,
            action_weights=[(ep_key, 100)],
        )
        endpoint_stress_results[ep_key] = {
            "label": ep_label,
            "rps": res.requests_per_second,
            "avg_ms": res.overall_latency["avg"],
            "p50_ms": res.overall_latency["p50"],
            "p95_ms": res.overall_latency["p95"],
            "p99_ms": res.overall_latency["p99"],
            "error_rate_pct": res.error_rate_pct,
        }
        await asyncio.sleep(0.5)

    # Print Final Summary Tables
    print("\n" + "=" * 90)
    print("                          CONCURRENCY LOAD TEST SUMMARY")
    print("=" * 90)
    print(f"{'Users':<8} | {'Total Req':<10} | {'RPS':<10} | {'Avg (ms)':<10} | {'p50 (ms)':<10} | {'p95 (ms)':<10} | {'p99 (ms)':<10} | {'Error %':<8}")
    print("-" * 90)
    for r in all_results:
        print(
            f"{r.concurrency:<8} | "
            f"{r.total_requests:<10} | "
            f"{r.requests_per_second:<10.2f} | "
            f"{r.overall_latency['avg']:<10.2f} | "
            f"{r.overall_latency['p50']:<10.2f} | "
            f"{r.overall_latency['p95']:<10.2f} | "
            f"{r.overall_latency['p99']:<10.2f} | "
            f"{r.error_rate_pct:<8.2f}%"
        )
    print("=" * 90)

    print("\n" + "=" * 105)
    print("                      ISOLATED ENDPOINT PERFORMANCE & BOTTLENECK BREAKDOWN")
    print("=" * 105)
    print(f"{'Endpoint':<42} | {'RPS':<10} | {'Avg (ms)':<10} | {'p50 (ms)':<10} | {'p95 (ms)':<10} | {'p99 (ms)':<10} | {'Error %':<8}")
    print("-" * 105)
    for ep_key, data in endpoint_stress_results.items():
        print(
            f"{data['label']:<42} | "
            f"{data['rps']:<10.2f} | "
            f"{data['avg_ms']:<10.2f} | "
            f"{data['p50_ms']:<10.2f} | "
            f"{data['p95_ms']:<10.2f} | "
            f"{data['p99_ms']:<10.2f} | "
            f"{data['error_rate_pct']:<8.2f}%"
        )
    print("=" * 105)

    # Save summary report artifact
    report_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "backend": "FastAPI + MongoDB Atlas + Cloudinary",
        "concurrency_tiers": [
            {
                "concurrency": r.concurrency,
                "total_requests": r.total_requests,
                "successful_requests": r.successful_requests,
                "failed_requests": r.failed_requests,
                "rps": r.requests_per_second,
                "error_rate_pct": r.error_rate_pct,
                "latency": r.overall_latency,
                "status_counts": r.status_counts,
                "endpoints": r.endpoint_metrics,
            }
            for r in all_results
        ],
        "endpoint_stress_benchmarks": endpoint_stress_results,
    }

    report_path = os.path.join(os.path.dirname(__file__), "load_test_results.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    logger.info("Saved load test raw metrics to %s", report_path)


if __name__ == "__main__":
    asyncio.run(main())
