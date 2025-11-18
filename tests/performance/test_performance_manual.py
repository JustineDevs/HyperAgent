#!/usr/bin/env python3
"""
Performance testing script for HyperAgent

Tests:
1. Concurrent workflow creation
2. Response times
3. Resource usage
4. Throughput

Usage: python tests/performance/test_performance_manual.py
"""
import asyncio
import httpx
import time
import statistics
from typing import List, Dict, Any
from hyperagent.core.config import settings

API_HOST = "localhost" if settings.api_host == "0.0.0.0" else settings.api_host
API_URL = f"http://{API_HOST}:{settings.api_port}/api/v1"


async def create_workflow(client: httpx.AsyncClient, description: str) -> Dict[str, Any]:
    """Create a single workflow and measure time"""
    start_time = time.time()
    try:
        response = await client.post(
            f"{API_URL}/workflows/generate",
            json={
                "nlp_input": description,
                "network": "hyperion_testnet",
                "contract_type": "Custom"
            },
            timeout=300.0
        )
        response.raise_for_status()
        data = response.json()
        elapsed = time.time() - start_time
        
        return {
            "success": True,
            "workflow_id": data.get("workflow_id"),
            "elapsed_time": elapsed,
            "status_code": response.status_code
        }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "success": False,
            "error": str(e),
            "elapsed_time": elapsed
        }


async def test_concurrent_workflows(count: int = 5) -> Dict[str, Any]:
    """Test concurrent workflow creation"""
    print(f"\n[*] Testing {count} concurrent workflows...")
    
    descriptions = [
        "Create a simple storage contract",
        "Create an ERC20 token with 1 million supply",
        "Create a voting contract",
        "Create a multi-sig wallet",
        "Create a token swap contract"
    ]
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        start_time = time.time()
        
        # Create workflows concurrently
        tasks = [
            create_workflow(client, descriptions[i % len(descriptions)])
            for i in range(count)
        ]
        
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Analyze results
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]
        
        elapsed_times = [r["elapsed_time"] for r in successful]
        
        return {
            "total_workflows": count,
            "successful": len(successful),
            "failed": len(failed),
            "total_time": total_time,
            "avg_time": statistics.mean(elapsed_times) if elapsed_times else 0,
            "min_time": min(elapsed_times) if elapsed_times else 0,
            "max_time": max(elapsed_times) if elapsed_times else 0,
            "throughput": len(successful) / total_time if total_time > 0 else 0,
            "errors": [r.get("error") for r in failed]
        }


async def test_api_response_times() -> Dict[str, Any]:
    """Test API endpoint response times"""
    print("\n[*] Testing API response times...")
    
    endpoints = [
        ("GET", "/health/"),
        ("GET", "/templates"),
        ("GET", "/networks/info/hyperion_testnet"),
    ]
    
    results = {}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for method, endpoint in endpoints:
            times = []
            for _ in range(5):  # 5 requests per endpoint
                start = time.time()
                try:
                    if method == "GET":
                        response = await client.get(f"{API_URL}{endpoint}")
                    else:
                        response = await client.post(f"{API_URL}{endpoint}")
                    response.raise_for_status()
                    elapsed = time.time() - start
                    times.append(elapsed)
                except Exception as e:
                    print(f"  [-] {endpoint}: {e}")
                    times.append(None)
            
            valid_times = [t for t in times if t is not None]
            if valid_times:
                results[endpoint] = {
                    "avg": statistics.mean(valid_times),
                    "min": min(valid_times),
                    "max": max(valid_times),
                    "count": len(valid_times)
                }
    
    return results


async def main():
    """Run performance tests"""
    print("=" * 70)
    print("HyperAgent Performance Test Suite")
    print("=" * 70)
    
    # Test 1: API Response Times
    print("\n[>] Test 1: API Response Times")
    api_results = await test_api_response_times()
    print("\nResults:")
    for endpoint, metrics in api_results.items():
        print(f"  {endpoint}:")
        print(f"    Avg: {metrics['avg']:.3f}s")
        print(f"    Min: {metrics['min']:.3f}s")
        print(f"    Max: {metrics['max']:.3f}s")
    
    # Test 2: Concurrent Workflows
    print("\n[>] Test 2: Concurrent Workflows")
    concurrent_results = await test_concurrent_workflows(count=3)
    print("\nResults:")
    print(f"  Total Workflows: {concurrent_results['total_workflows']}")
    print(f"  Successful: {concurrent_results['successful']}")
    print(f"  Failed: {concurrent_results['failed']}")
    print(f"  Total Time: {concurrent_results['total_time']:.2f}s")
    print(f"  Avg Time per Workflow: {concurrent_results['avg_time']:.2f}s")
    print(f"  Min Time: {concurrent_results['min_time']:.2f}s")
    print(f"  Max Time: {concurrent_results['max_time']:.2f}s")
    print(f"  Throughput: {concurrent_results['throughput']:.2f} workflows/sec")
    
    if concurrent_results['errors']:
        print(f"  Errors: {len(concurrent_results['errors'])}")
        for error in concurrent_results['errors']:
            print(f"    - {error}")
    
    print("\n" + "=" * 70)
    print("Performance Test Complete")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Tests interrupted by user")
    except Exception as e:
        print(f"\n[-] Fatal error: {e}")
        import traceback
        traceback.print_exc()

