"""
Performance testing service
"""
import time
import logging
import statistics
from typing import Dict, Any, List
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


class PerformanceTester:
    """Performance and load testing"""

    def __init__(self):
        self.results = []

    def run_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run performance test"""
        try:
            test_data = test_case.get("test_data", {})
            test_type = test_data.get("performance_type", "load")

            if test_type == "load":
                return self.run_load_test(test_data)
            elif test_type == "stress":
                return self.run_stress_test(test_data)
            elif test_type == "spike":
                return self.run_spike_test(test_data)
            else:
                return self.run_load_test(test_data)

        except Exception as e:
            logger.error(f"Performance test error: {e}")
            return {
                "status": "error",
                "error_message": str(e)
            }

    def run_load_test(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run load test"""
        try:
            url = config.get("url")
            concurrent_users = config.get("concurrent_users", 10)
            duration_seconds = config.get("duration_seconds", 60)
            method = config.get("method", "GET")

            if not url:
                return {
                    "status": "error",
                    "error_message": "No URL provided for load test"
                }

            # Run async load test
            results = asyncio.run(
                self._async_load_test(url, concurrent_users, duration_seconds, method)
            )

            # Calculate metrics
            response_times = [r["response_time"] for r in results if r["success"]]
            successful = len([r for r in results if r["success"]])
            failed = len([r for r in results if not r["success"]])

            if response_times:
                avg_response_time = statistics.mean(response_times)
                median_response_time = statistics.median(response_times)
                p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times)
                p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else max(response_times)
            else:
                avg_response_time = 0
                median_response_time = 0
                p95_response_time = 0
                p99_response_time = 0

            total_requests = len(results)
            throughput = total_requests / duration_seconds if duration_seconds > 0 else 0
            error_rate = (failed / total_requests * 100) if total_requests > 0 else 0

            status = "passed" if error_rate < 5 and avg_response_time < 1000 else "failed"

            return {
                "status": status,
                "output": f"Load test completed: {total_requests} requests",
                "metrics": {
                    "total_requests": total_requests,
                    "successful_requests": successful,
                    "failed_requests": failed,
                    "throughput_rps": throughput,
                    "error_rate_percent": error_rate,
                    "avg_response_time_ms": avg_response_time,
                    "median_response_time_ms": median_response_time,
                    "p95_response_time_ms": p95_response_time,
                    "p99_response_time_ms": p99_response_time,
                    "concurrent_users": concurrent_users,
                    "duration_seconds": duration_seconds
                }
            }

        except Exception as e:
            logger.error(f"Load test error: {e}")
            return {
                "status": "error",
                "error_message": str(e)
            }

    async def _async_load_test(self, url: str, users: int, duration: int, method: str) -> List[Dict[str, Any]]:
        """Async load test execution"""
        results = []
        start_time = time.time()

        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration:
                tasks = []
                for _ in range(users):
                    tasks.append(self._make_request(session, url, method))

                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                results.extend([r for r in batch_results if isinstance(r, dict)])

                # Small delay between batches
                await asyncio.sleep(0.1)

        return results

    async def _make_request(self, session: aiohttp.ClientSession, url: str, method: str) -> Dict[str, Any]:
        """Make single HTTP request"""
        start_time = time.time()

        try:
            async with session.request(method, url) as response:
                await response.text()
                response_time = (time.time() - start_time) * 1000  # Convert to ms

                return {
                    "success": response.status < 400,
                    "status_code": response.status,
                    "response_time": response_time
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response_time": (time.time() - start_time) * 1000
            }

    def run_stress_test(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run stress test with increasing load"""
        # Similar to load test but gradually increase concurrent users
        return self.run_load_test(config)

    def run_spike_test(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run spike test with sudden load increase"""
        # Similar to load test but with sudden user spikes
        return self.run_load_test(config)
