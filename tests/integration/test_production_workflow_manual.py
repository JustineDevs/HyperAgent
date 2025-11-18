"""Production workflow test script - Test real-world scenarios"""
import asyncio
import httpx
import sys
import time
from typing import Dict, Any

# Configuration
API_URL = "http://localhost:8000/api/v1"
MAX_WAIT_TIME = 600  # 10 minutes max wait


def print_progress_bar(progress: int, stage: str = "", width: int = 40):
    """Print Unicode progress bar (Windows-safe)"""
    import platform
    if platform.system() == "Windows":
        filled_char = "#"
        empty_char = "-"
    else:
        filled_char = "█"
        empty_char = "░"
    
    filled = int((progress / 100) * width)
    empty = width - filled
    bar = filled_char * filled + empty_char * empty
    percent = int(progress)
    print(f"\r[...] [{stage:12}] |{bar}| {percent:3}%", end="", flush=True)


async def test_workflow(description: str, network: str, contract_type: str = "Custom") -> Dict[str, Any]:
    """Test a complete workflow"""
    print(f"\n[*] Testing: {description}")
    print(f"[*] Network: {network}")
    print(f"[*] Type: {contract_type}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create workflow
        response = await client.post(
            f"{API_URL}/workflows/generate",
            json={
                "nlp_input": description,
                "network": network,
                "contract_type": contract_type
            }
        )
        response.raise_for_status()
        workflow_data = response.json()
        workflow_id = workflow_data.get("workflow_id")
        
        print(f"[+] Workflow created: {workflow_id}")
        
        # Monitor progress
        start_time = time.time()
        last_progress = -1
        last_stage = ""
        
        stage_map = {
            "created": "Initializing",
            "generating": "Generating",
            "compiling": "Compiling",
            "auditing": "Auditing",
            "testing": "Testing",
            "deploying": "Deploying",
            "completed": "Completed",
            "failed": "Failed"
        }
        
        while time.time() - start_time < MAX_WAIT_TIME:
            status_response = await client.get(
                f"{API_URL}/workflows/{workflow_id}",
                timeout=10.0
            )
            status_response.raise_for_status()
            status_data = status_response.json()
            
            status = status_data.get("status")
            progress = status_data.get("progress_percentage", 0)
            stage = stage_map.get(status, status.title() if status else "Unknown")
            
            # Update progress bar
            if progress != last_progress or stage != last_stage:
                print_progress_bar(progress, stage)
                last_progress = progress
                last_stage = stage
            
            if status == "completed":
                print()  # New line
                print(f"[+] Workflow completed successfully!")
                
                # Get full workflow data
                full_data = await client.get(f"{API_URL}/workflows/{workflow_id}")
                full_data.raise_for_status()
                return full_data.json()
            
            elif status == "failed":
                print()  # New line
                error = status_data.get("error_message", "Unknown error")
                print(f"[-] Workflow failed: {error}")
                return {"status": "failed", "error": error, "workflow_id": workflow_id}
            
            await asyncio.sleep(2)
        
        print()  # New line
        print(f"[-] Workflow timeout after {MAX_WAIT_TIME}s")
        return {"status": "timeout", "workflow_id": workflow_id}


async def main():
    """Run production workflow tests"""
    print("=" * 70)
    print("Production Workflow Test Suite")
    print("=" * 70)
    
    tests = [
        {
            "name": "Simple ERC20 Token",
            "description": "Create a simple ERC20 token with 1 million supply",
            "network": "hyperion_testnet",
            "contract_type": "ERC20"
        },
        {
            "name": "ERC721 NFT with Constructor",
            "description": "Create an ERC721 NFT contract with name and symbol constructor parameters",
            "network": "hyperion_testnet",
            "contract_type": "ERC721"
        },
        {
            "name": "Complex Contract",
            "description": "Create a contract with multiple constructor parameters including arrays and mappings",
            "network": "hyperion_testnet",
            "contract_type": "Custom"
        }
    ]
    
    results = []
    
    for test in tests:
        try:
            result = await test_workflow(
                test["description"],
                test["network"],
                test["contract_type"]
            )
            results.append({
                "test": test["name"],
                "status": result.get("status", "unknown"),
                "workflow_id": result.get("workflow_id"),
                "error": result.get("error")
            })
        except Exception as e:
            print(f"\n[-] Test '{test['name']}' failed with exception: {e}")
            results.append({
                "test": test["name"],
                "status": "exception",
                "error": str(e)
            })
        
        # Wait between tests
        await asyncio.sleep(5)
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    for result in results:
        status_icon = "[+]" if result["status"] == "completed" else "[-]"
        print(f"{status_icon} {result['test']}: {result['status']}")
        if result.get("workflow_id"):
            print(f"    Workflow ID: {result['workflow_id']}")
        if result.get("error"):
            print(f"    Error: {result['error']}")
    
    # Count successes
    success_count = sum(1 for r in results if r["status"] == "completed")
    print(f"\n[*] Passed: {success_count}/{len(results)}")
    
    if success_count == len(results):
        print("[+] All tests passed!")
        return 0
    else:
        print("[-] Some tests failed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n[*] Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] Fatal error: {e}")
        sys.exit(1)

