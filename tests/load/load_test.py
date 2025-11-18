"""Load testing utilities for HyperAgent"""
import asyncio
import aiohttp
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import statistics


@dataclass
class LoadTestResult:
    """Load test result metrics"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float
    requests_per_second: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float


class LoadTester:
    """
    Load Tester
    
    Concept: Stress testing for API endpoints
    Logic: Send concurrent requests, measure performance
    Usage: Identify bottlenecks and capacity limits
    """
    
    def __init__(self, base_url: str, auth_token: str = None):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.results: List[Dict[str, Any]] = []
    
    async def run_load_test(
        self,
        endpoint: str,
        method: str = "GET",
        payload: Dict = None,
        concurrent_users: int = 10,
        total_requests: int = 100,
        duration_seconds: int = None
    ) -> LoadTestResult:
        """
        Run load test
        
        Args:
            endpoint: API endpoint to test
            method: HTTP method
            payload: Request payload (for POST/PUT)
            concurrent_users: Number of concurrent requests
            total_requests: Total requests to send
            duration_seconds: Optional duration limit
        
        Returns:
            LoadTestResult with performance metrics
        """
        print(f"[*] Starting load test: {method} {endpoint}")
        print(f"[*] Concurrent users: {concurrent_users}")
        print(f"[*] Total requests: {total_requests}")
        
        start_time = time.time()
        self.results = []
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrent_users)
        
        # Create tasks
        tasks = []
        for i in range(total_requests):
            task = self._make_request(
                semaphore,
                endpoint,
                method,
                payload
            )
            tasks.append(task)
        
        # Execute all requests
        await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Calculate metrics
        return self._calculate_metrics(total_time)
    
    async def _make_request(
        self,
        semaphore: asyncio.Semaphore,
        endpoint: str,
        method: str,
        payload: Dict = None
    ):
        """Make single HTTP request"""
        async with semaphore:
            url = f"{self.base_url}{endpoint}"
            headers = {}
            
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            start = time.time()
            try:
                async with aiohttp.ClientSession() as session:
                    if method == "GET":
                        async with session.get(url, headers=headers) as response:
                            status = response.status
                            await response.read()
                    elif method == "POST":
                        async with session.post(
                            url,
                            json=payload,
                            headers=headers
                        ) as response:
                            status = response.status
                            await response.read()
                    else:
                        raise ValueError(f"Unsupported method: {method}")
                    
                    response_time = time.time() - start
                    
                    self.results.append({
                        "status": status,
                        "response_time": response_time,
                        "success": 200 <= status < 300,
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception as e:
                response_time = time.time() - start
                self.results.append({
                    "status": 0,
                    "response_time": response_time,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
    
    def _calculate_metrics(self, total_time: float) -> LoadTestResult:
        """Calculate performance metrics from results"""
        if not self.results:
            return LoadTestResult(
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                total_time=0,
                requests_per_second=0,
                avg_response_time=0,
                min_response_time=0,
                max_response_time=0,
                p50_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                error_rate=0
            )
        
        response_times = [r["response_time"] for r in self.results]
        successful = sum(1 for r in self.results if r["success"])
        failed = len(self.results) - successful
        
        sorted_times = sorted(response_times)
        
        return LoadTestResult(
            total_requests=len(self.results),
            successful_requests=successful,
            failed_requests=failed,
            total_time=total_time,
            requests_per_second=len(self.results) / total_time if total_time > 0 else 0,
            avg_response_time=statistics.mean(response_times),
            min_response_time=min(response_times),
            max_response_time=max(response_times),
            p50_response_time=sorted_times[len(sorted_times) // 2] if sorted_times else 0,
            p95_response_time=sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0,
            p99_response_time=sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0,
            error_rate=(failed / len(self.results)) * 100 if self.results else 0
        )
    
    def print_report(self, result: LoadTestResult):
        """Print load test report"""
        print("\n" + "=" * 60)
        print("[*] Load Test Results")
        print("=" * 60)
        print(f"Total Requests: {result.total_requests}")
        print(f"Successful: {result.successful_requests}")
        print(f"Failed: {result.failed_requests}")
        print(f"Error Rate: {result.error_rate:.2f}%")
        print(f"\nPerformance Metrics:")
        print(f"  Requests/Second: {result.requests_per_second:.2f}")
        print(f"  Avg Response Time: {result.avg_response_time:.3f}s")
        print(f"  Min Response Time: {result.min_response_time:.3f}s")
        print(f"  Max Response Time: {result.max_response_time:.3f}s")
        print(f"  P50 (Median): {result.p50_response_time:.3f}s")
        print(f"  P95: {result.p95_response_time:.3f}s")
        print(f"  P99: {result.p99_response_time:.3f}s")
        print("=" * 60)


async def main():
    """Example load test"""
    import os
    
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    auth_token = os.getenv("AUTH_TOKEN")
    
    tester = LoadTester(base_url, auth_token)
    
    # Test health endpoint
    result = await tester.run_load_test(
        endpoint="/api/v1/health",
        method="GET",
        concurrent_users=50,
        total_requests=500
    )
    
    tester.print_report(result)


if __name__ == "__main__":
    asyncio.run(main())

