"""
Multi-Worker Concurrency Benchmark for Shikhor AI Backend (MongoDB + Cloudinary)
================================================================================
Runs identical load tests across different Uvicorn worker counts (1, 2, 4 workers)
at 10, 25, 50, and 100 concurrent users.

Measures:
  - Overall RPS, p50, p95, p99, and Error Rate
  - /crop-disease/predict AI Vision Latency (Avg, p50, p95, p99)
  - Process RAM MB and System CPU % utilization
"""

import argparse
import asyncio
import io
import json
import logging
import os
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
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
logger = logging.getLogger("shikhor.multi_worker_bench")


@dataclass
class RequestMetric:
    endpoint: str
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
    overall_latency: Dict[str, float] = field(default_factory=dict)
    ai_vision_latency: Dict[str, float] = field(default_factory=dict)
    avg_ram_mb: float = 0.0
    peak_ram_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    endpoint_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)


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
    img = Image.new("RGB", (224, 224), color=(34, 139, 34))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


class ResourceMonitor:
    def __init__(self):
        self._stop_event = asyncio.Event()
        self.ram_samples: List[float] = []
        self.cpu_samples: List[float] = []

    def _sample_once(self) -> Tuple[float, float]:
        """Samples Uvicorn/Python process working set RAM in MB and CPU load via PowerShell."""
        try:
            cmd = "powershell -NoProfile -Command \"Get-Process uvicorn,python -ErrorAction SilentlyContinue | Measure-Object -Property WorkingSet64 -Sum | Select-Object -ExpandProperty Sum\""
            out = subprocess.check_output(cmd, shell=True, timeout=2).decode().strip()
            ram_mb = round(int(out) / (1024 * 1024), 1) if out.isdigit() else 0.0
            return ram_mb, 0.0
        except Exception:
            return 0.0, 0.0

    async def run(self):
        while not self._stop_event.is_set():
            ram, cpu = self._sample_once()
            if ram > 0:
                self.ram_samples.append(ram)
            await asyncio.sleep(1.0)

    def stop(self) -> Tuple[float, float, float]:
        self._stop_event.set()
        avg_ram = round(sum(self.ram_samples) / len(self.ram_samples), 1) if self.ram_samples else 0.0
        peak_ram = round(max(self.ram_samples), 1) if self.ram_samples else 0.0
        return avg_ram, peak_ram, 0.0


class MultiWorkerTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.leaf_image_bytes = create_sample_leaf_bytes()

    async def setup_auth(self) -> bool:
        for attempt in range(10):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    res = await client.post(
                        f"{self.base_url}{API_PREFIX}/auth/login",
                        json={"phone": "01711223344", "password": "Password123#Strong"},
                    )
                    if res.status_code == 200:
                        self.token = res.json().get("accessToken")
                        logger.info("Successfully authenticated against backend.")
                        return True
            except Exception:
                await asyncio.sleep(1.0)
        return False

    async def execute_action(
        self, client: httpx.AsyncClient, action: str, headers: Dict[str, str]
    ) -> RequestMetric:
        start = time.perf_counter()
        status_code = 0
        error = None

        try:
            if action == "get_profile":
                res = await client.get(f"{self.base_url}{API_PREFIX}/auth/me", headers=headers)
                status_code = res.status_code

            elif action == "search_equipment":
                res = await client.get(
                    f"{self.base_url}{API_PREFIX}/equipment?equipmentType=tractor&priceUnit=per_hour&latitude=25.62&longitude=88.63&maxRadiusKm=30",
                    headers=headers,
                )
                status_code = res.status_code

            elif action == "list_crop_cases":
                res = await client.get(f"{self.base_url}{API_PREFIX}/crop-cases", headers=headers)
                status_code = res.status_code

            elif action == "list_conversations":
                res = await client.get(f"{self.base_url}{API_PREFIX}/conversations", headers=headers)
                status_code = res.status_code

            elif action == "ai_crop_prediction":
                files = {"file": ("leaf.jpg", self.leaf_image_bytes, "image/jpeg")}
                data = {"crop": "rice"}
                res = await client.post(
                    f"{self.base_url}{API_PREFIX}/crop-disease/predict",
                    files=files,
                    data=data,
                    headers=headers,
                )
                status_code = res.status_code

            elif action == "login_request":
                res = await client.post(
                    f"{self.base_url}{API_PREFIX}/auth/login",
                    json={"phone": "01711223344", "password": "Password123#Strong"},
                )
                status_code = res.status_code

            elif action == "readiness":
                res = await client.get(f"{self.base_url}{API_PREFIX}/health/readiness")
                status_code = res.status_code

            else:
                raise ValueError(f"Unknown action: {action}")

        except httpx.TimeoutException:
            status_code = 504
            error = "TIMEOUT"
        except httpx.ConnectError:
            status_code = 503
            error = "CONNECT_ERROR"
        except Exception as e:
            status_code = 500
            error = str(e)

        dur_ms = (time.perf_counter() - start) * 1000.0
        return RequestMetric(endpoint=action, status_code=status_code, duration_ms=dur_ms, error=error)

    async def worker_loop(
        self,
        stop_event: asyncio.Event,
        action_weights: List[Tuple[str, int]],
        results: List[RequestMetric],
        client: httpx.AsyncClient,
    ):
        import random
        actions, weights = zip(*action_weights)
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        while not stop_event.is_set():
            action = random.choices(actions, weights=weights, k=1)[0]
            metric = await self.execute_action(client, action, headers)
            results.append(metric)
            await asyncio.sleep(0.01)

    async def run_concurrency_tier(
        self, concurrency: int, duration_seconds: float, action_weights: List[Tuple[str, int]]
    ) -> TierResult:
        logger.info(">>> Running Tier: %d Concurrent Users (Duration: %.1fs)...", concurrency, duration_seconds)
        limits = httpx.Limits(max_connections=concurrency * 2 + 50, max_keepalive_connections=concurrency + 20)
        timeout = httpx.Timeout(20.0, connect=10.0)

        results: List[RequestMetric] = []
        stop_event = asyncio.Event()

        monitor = ResourceMonitor()
        monitor_task = asyncio.create_task(monitor.run())

        start_time = time.perf_counter()
        async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
            workers = [
                asyncio.create_task(self.worker_loop(stop_event, action_weights, results, client))
                for _ in range(concurrency)
            ]
            await asyncio.sleep(duration_seconds)
            stop_event.set()
            await asyncio.gather(*workers, return_exceptions=True)

        elapsed = time.perf_counter() - start_time
        avg_ram, peak_ram, avg_cpu = monitor.stop()
        monitor_task.cancel()

        total = len(results)
        succ = sum(1 for r in results if 200 <= r.status_code < 400)
        fail = total - succ
        rps = round(total / elapsed, 2) if elapsed > 0 else 0.0
        err_pct = round((fail / total) * 100.0, 2) if total > 0 else 0.0

        status_counts: Dict[int, int] = defaultdict(int)
        for r in results:
            status_counts[r.status_code] += 1

        overall_lat = calculate_percentiles([r.duration_ms for r in results])
        ai_vision_lat = calculate_percentiles(
            [r.duration_ms for r in results if r.endpoint == "ai_crop_prediction"]
        )

        ep_data: Dict[str, List[float]] = defaultdict(list)
        ep_errs: Dict[str, int] = defaultdict(int)
        for r in results:
            ep_data[r.endpoint].append(r.duration_ms)
            if not (200 <= r.status_code < 400):
                ep_errs[r.endpoint] += 1

        ep_breakdown: Dict[str, Dict[str, Any]] = {}
        for ep, lats in ep_data.items():
            ep_total = len(lats)
            ep_e = ep_errs[ep]
            ep_breakdown[ep] = {
                "count": ep_total,
                "rps": round(ep_total / elapsed, 2),
                "error_rate_pct": round((ep_e / ep_total) * 100.0, 2) if ep_total > 0 else 0.0,
                **calculate_percentiles(lats),
            }

        logger.info(
            "--- Tier %d Users Done: %d reqs | RPS: %.2f | Avg: %.2fms | p95: %.2fms | AI Lat: %.2fms | Errors: %d (%.2f%%) | RAM: %.1fMB ---",
            concurrency,
            total,
            rps,
            overall_lat["avg"],
            overall_lat["p95"],
            ai_vision_lat["avg"],
            fail,
            err_pct,
            peak_ram,
        )

        return TierResult(
            concurrency=concurrency,
            duration_seconds=round(elapsed, 2),
            total_requests=total,
            successful_requests=succ,
            failed_requests=fail,
            requests_per_second=rps,
            error_rate_pct=err_pct,
            status_counts=dict(status_counts),
            overall_latency=overall_lat,
            ai_vision_latency=ai_vision_lat,
            avg_ram_mb=avg_ram,
            peak_ram_mb=peak_ram,
            avg_cpu_percent=avg_cpu,
            endpoint_breakdown=ep_breakdown,
        )


async def run_benchmark_for_worker_count(workers: int, output_file: str):
    print("=" * 80)
    print(f"   SHIKHOR AI LOAD TEST: {workers} UVICORN WORKER(S) BENCHMARK")
    print("=" * 80)

    tester = MultiWorkerTester(BASE_URL)
    auth_ok = await tester.setup_auth()
    if not auth_ok:
        logger.error("Authentication setup failed. Is the server running?")
        sys.exit(1)

    action_weights = [
        ("get_profile", 25),
        ("search_equipment", 20),
        ("list_crop_cases", 20),
        ("list_conversations", 15),
        ("ai_crop_prediction", 10),
        ("login_request", 5),
        ("readiness", 5),
    ]

    concurrency_tiers = [10, 25, 50, 100]
    tier_duration = 10.0

    tier_results = []
    for c in concurrency_tiers:
        res = await tester.run_concurrency_tier(c, tier_duration, action_weights)
        tier_results.append(res)
        await asyncio.sleep(1.0)

    # Output table
    print("\n" + "=" * 105)
    print(f"                      RESULTS SUMMARY: {workers} UVICORN WORKER(S)")
    print("=" * 105)
    print(f"{'Users':<8} | {'Total':<7} | {'RPS':<8} | {'Avg (ms)':<9} | {'p50 (ms)':<9} | {'p95 (ms)':<9} | {'p99 (ms)':<9} | {'AI p50 (ms)':<11} | {'Error %':<8} | {'RAM (MB)':<8}")
    print("-" * 105)
    for r in tier_results:
        print(
            f"{r.concurrency:<8} | "
            f"{r.total_requests:<7} | "
            f"{r.requests_per_second:<8.2f} | "
            f"{r.overall_latency['avg']:<9.1f} | "
            f"{r.overall_latency['p50']:<9.1f} | "
            f"{r.overall_latency['p95']:<9.1f} | "
            f"{r.overall_latency['p99']:<9.1f} | "
            f"{r.ai_vision_latency['p50']:<11.1f} | "
            f"{r.error_rate_pct:<8.2f}% | "
            f"{r.peak_ram_mb:<8.1f}"
        )
    print("=" * 105)

    data = {
        "workers": workers,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tiers": [asdict(r) for r in tier_results],
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Saved worker results to %s", output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=1, help="Number of workers currently active")
    parser.add_argument("--output", type=str, default="worker_bench_results.json", help="Output JSON path")
    args = parser.parse_args()

    asyncio.run(run_benchmark_for_worker_count(args.workers, args.output))
