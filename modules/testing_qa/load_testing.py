"""
Load Testing Module

Provides LoadTester, StressTester, and PerformanceMonitor for load and performance testing.
"""

import asyncio
import logging
import time
import statistics
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
import httpx

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Performance metrics monitor.

    Tracks response times, throughput, and other performance metrics.
    """

    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: Dict[str, List[float]] = {
            "response_times": [],
            "request_rates": [],
            "error_rates": [],
        }
        self.start_time = None
        self.logger = logging.getLogger(__name__)

    def start(self) -> None:
        """Start monitoring."""
        self.start_time = time.time()
        self.metrics = {
            "response_times": [],
            "request_rates": [],
            "error_rates": [],
        }

    def record_response_time(self, response_time_ms: float) -> None:
        """Record response time."""
        self.metrics["response_times"].append(response_time_ms)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get performance statistics.

        Returns:
            Performance metrics
        """
        response_times = self.metrics["response_times"]

        if not response_times:
            return {
                "total_requests": 0,
                "duration_seconds": 0,
            }

        duration = time.time() - self.start_time if self.start_time else 0

        stats = {
            "total_requests": len(response_times),
            "duration_seconds": duration,
            "requests_per_second": len(response_times) / duration if duration > 0 else 0,
            "response_time_ms": {
                "min": min(response_times),
                "max": max(response_times),
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "stdev": statistics.stdev(response_times) if len(response_times) > 1 else 0,
            },
        }

        # Calculate percentiles
        sorted_times = sorted(response_times)
        stats["response_time_ms"]["p50"] = sorted_times[int(len(sorted_times) * 0.50)]
        stats["response_time_ms"]["p95"] = sorted_times[int(len(sorted_times) * 0.95)]
        stats["response_time_ms"]["p99"] = sorted_times[int(len(sorted_times) * 0.99)]

        return stats


class LoadTester:
    """
    Load tester for simulating concurrent users.

    Supports various load patterns and scenarios.
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
    ):
        """
        Initialize load tester.

        Args:
            base_url: Base URL to test
            timeout: Request timeout
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.monitor = PerformanceMonitor()
        self.logger = logging.getLogger(__name__)

    async def run_load_test(
        self,
        endpoint: str,
        method: str = "GET",
        concurrent_users: int = 10,
        total_requests: int = 100,
        ramp_up_time: int = 0,
        headers: Dict[str, str] = None,
        json_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Run load test with concurrent users.

        Args:
            endpoint: Endpoint to test
            method: HTTP method
            concurrent_users: Number of concurrent users
            total_requests: Total number of requests
            ramp_up_time: Ramp-up time in seconds
            headers: Request headers
            json_data: JSON request body

        Returns:
            Load test results
        """
        self.logger.info(
            f"Starting load test: {concurrent_users} users, {total_requests} requests"
        )

        self.monitor.start()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        requests_per_user = total_requests // concurrent_users
        ramp_up_delay = ramp_up_time / concurrent_users if ramp_up_time > 0 else 0

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = []

            for i in range(concurrent_users):
                # Ramp up users gradually
                if ramp_up_delay > 0:
                    await asyncio.sleep(ramp_up_delay)

                task = self._user_scenario(
                    client,
                    url,
                    method,
                    requests_per_user,
                    headers,
                    json_data,
                )
                tasks.append(task)

            # Execute all user scenarios concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        failed = len(results) - successful

        stats = self.monitor.get_statistics()
        stats["concurrent_users"] = concurrent_users
        stats["successful_requests"] = successful * requests_per_user
        stats["failed_requests"] = failed * requests_per_user
        stats["success_rate"] = (successful / len(results) * 100) if results else 0

        self.logger.info(f"Load test completed: {stats['success_rate']:.2f}% success rate")

        return stats

    async def _user_scenario(
        self,
        client: httpx.AsyncClient,
        url: str,
        method: str,
        num_requests: int,
        headers: Dict[str, str] = None,
        json_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Execute single user scenario."""
        success_count = 0
        error_count = 0

        for _ in range(num_requests):
            start_time = time.time()

            try:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=json_data,
                )

                response_time = (time.time() - start_time) * 1000
                self.monitor.record_response_time(response_time)

                if response.status_code < 400:
                    success_count += 1
                else:
                    error_count += 1

            except Exception as e:
                error_count += 1
                self.logger.debug(f"Request error: {e}")

        return {
            "success": success_count > 0,
            "successful_requests": success_count,
            "failed_requests": error_count,
        }


class StressTester:
    """
    Stress tester for finding system limits.

    Gradually increases load to find breaking points.
    """

    def __init__(self, base_url: str):
        """
        Initialize stress tester.

        Args:
            base_url: Base URL to test
        """
        self.base_url = base_url
        self.load_tester = LoadTester(base_url)
        self.logger = logging.getLogger(__name__)

    async def run_stress_test(
        self,
        endpoint: str,
        method: str = "GET",
        start_users: int = 1,
        max_users: int = 100,
        step_size: int = 10,
        requests_per_step: int = 100,
        failure_threshold: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Run stress test with increasing load.

        Args:
            endpoint: Endpoint to test
            method: HTTP method
            start_users: Starting number of users
            max_users: Maximum number of users
            step_size: User increment per step
            requests_per_step: Requests per step
            failure_threshold: Failure rate threshold (%)

        Returns:
            Stress test results
        """
        self.logger.info(
            f"Starting stress test: {start_users} to {max_users} users"
        )

        results = []
        breaking_point = None

        current_users = start_users

        while current_users <= max_users:
            self.logger.info(f"Testing with {current_users} concurrent users")

            result = await self.load_tester.run_load_test(
                endpoint=endpoint,
                method=method,
                concurrent_users=current_users,
                total_requests=requests_per_step,
            )

            result["concurrent_users"] = current_users
            results.append(result)

            # Check if we've hit the breaking point
            failure_rate = 100 - result.get("success_rate", 0)

            if failure_rate >= failure_threshold:
                breaking_point = current_users
                self.logger.warning(
                    f"Breaking point found at {current_users} users "
                    f"({failure_rate:.2f}% failure rate)"
                )
                break

            current_users += step_size

        return {
            "breaking_point_users": breaking_point,
            "max_tested_users": current_users,
            "total_steps": len(results),
            "step_results": results,
        }

    async def run_spike_test(
        self,
        endpoint: str,
        method: str = "GET",
        baseline_users: int = 10,
        spike_users: int = 100,
        spike_duration: int = 60,
    ) -> Dict[str, Any]:
        """
        Run spike test with sudden load increase.

        Args:
            endpoint: Endpoint to test
            method: HTTP method
            baseline_users: Baseline concurrent users
            spike_users: Spike concurrent users
            spike_duration: Spike duration in seconds

        Returns:
            Spike test results
        """
        self.logger.info(
            f"Starting spike test: {baseline_users} -> {spike_users} users"
        )

        # Baseline test
        baseline_result = await self.load_tester.run_load_test(
            endpoint=endpoint,
            method=method,
            concurrent_users=baseline_users,
            total_requests=baseline_users * 10,
        )

        # Spike test
        spike_result = await self.load_tester.run_load_test(
            endpoint=endpoint,
            method=method,
            concurrent_users=spike_users,
            total_requests=spike_users * (spike_duration // 10),
            ramp_up_time=0,  # Immediate spike
        )

        # Recovery test
        recovery_result = await self.load_tester.run_load_test(
            endpoint=endpoint,
            method=method,
            concurrent_users=baseline_users,
            total_requests=baseline_users * 10,
        )

        return {
            "baseline": baseline_result,
            "spike": spike_result,
            "recovery": recovery_result,
            "performance_degradation": (
                (baseline_result["response_time_ms"]["mean"] -
                 spike_result["response_time_ms"]["mean"])
                / baseline_result["response_time_ms"]["mean"] * 100
            ) if baseline_result["response_time_ms"]["mean"] > 0 else 0,
        }
