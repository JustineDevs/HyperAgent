#!/usr/bin/env python3
"""
Complete real-world end-to-end test

Tests the full workflow with constructor argument generation:
1. Create workflow with NLP description
2. Verify constructor args are generated correctly
3. Monitor progress through all stages
4. Verify deployment (if wallet funded)
5. Check contract on explorer

Usage: python tests/integration/test_real_world_complete_manual.py
"""
import asyncio
import httpx
import json
import time
import sys
from typing import Dict, Any, Optional
from hyperagent.core.config import settings

# Configuration
API_HOST = "localhost" if settings.api_host == "0.0.0.0" else settings.api_host
API_URL = f"http://{API_HOST}:{settings.api_port}/api/v1"
MAX_WAIT_TIME = 600  # 10 minutes


def print_progress_bar(progress: int, stage: str = "", width: int = 40):
    """Print progress bar (Windows-safe)"""
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


async def test_complete_workflow(
    description: str,
    network: str = "hyperion_testnet",
    contract_type: str = "Custom",
    verify_constructor_args: bool = True
) -> Dict[str, Any]:
    """
    Test complete workflow with constructor argument generation
    
    Args:
        description: NLP description of contract
        network: Target network
        contract_type: Contract type
        verify_constructor_args: Whether to verify constructor args are generated
        
    Returns:
        Workflow result dictionary
    """
    print("\n" + "=" * 70)
    print("Real-World Complete Workflow Test")
    print("=" * 70)
    print(f"[*] Description: {description}")
    print(f"[*] Network: {network}")
    print(f"[*] Contract Type: {contract_type}")
    print()
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Step 1: Create workflow
        print("[>] Step 1: Creating workflow...")
        try:
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
            
            if not workflow_id:
                print("[-] No workflow_id in response")
                return {"status": "error", "error": "No workflow_id"}
            
            print(f"[+] Workflow created: {workflow_id}")
            print()
            
        except httpx.HTTPStatusError as e:
            print(f"[-] Failed to create workflow: {e.response.status_code}")
            print(f"    Response: {e.response.text[:200]}")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            print(f"[-] Error creating workflow: {e}")
            return {"status": "error", "error": str(e)}
        
        # Step 2: Monitor workflow progress
        print("[>] Step 2: Monitoring workflow progress...")
        print("    This may take 1-5 minutes...")
        print()
        
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
            try:
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
                
                # Check completion
                if status == "completed":
                    print()  # New line
                    elapsed = time.time() - start_time
                    print(f"[+] Workflow completed in {elapsed:.1f}s")
                    print()
                    
                    # Step 3: Verify constructor arguments
                    if verify_constructor_args:
                        print("[>] Step 3: Verifying constructor arguments...")
                        
                        # Get full workflow data
                        full_response = await client.get(f"{API_URL}/workflows/{workflow_id}")
                        full_response.raise_for_status()
                        full_data = full_response.json()
                        
                        # Check contracts
                        contracts = full_data.get("contracts", [])
                        if contracts:
                            contract = contracts[0]
                            constructor_args = contract.get("constructor_args", [])
                            constructor_params = contract.get("constructor_params", [])
                            
                            print(f"    Constructor Parameters: {len(constructor_params)}")
                            for i, param in enumerate(constructor_params):
                                print(f"      {i+1}. {param.get('name', 'N/A')} ({param.get('type', 'N/A')})")
                            
                            print(f"    Constructor Values: {len(constructor_args)}")
                            if constructor_args:
                                print(f"      Values: {constructor_args}")
                                print(f"[+] Constructor arguments generated successfully!")
                            else:
                                print(f"      [!] No constructor values found")
                                if constructor_params:
                                    print(f"      [!] Warning: Parameters found but no values generated")
                        else:
                            print("    [!] No contracts found in workflow")
                        
                        print()
                    
                    # Step 4: Check deployments
                    print("[>] Step 4: Checking deployments...")
                    deployments = full_data.get("deployments", [])
                    if deployments:
                        for i, deployment in enumerate(deployments):
                            contract_address = deployment.get("contract_address")
                            tx_hash = deployment.get("transaction_hash")
                            deploy_network = deployment.get("network", "unknown")
                            
                            print(f"    Deployment {i+1}:")
                            print(f"      Address: {contract_address}")
                            print(f"      Transaction: {tx_hash}")
                            print(f"      Network: {deploy_network}")
                            
                            # Generate explorer URL
                            if "hyperion" in deploy_network.lower():
                                explorer_url = f"https://hyperion-testnet-explorer.metisdevops.link/address/{contract_address}"
                            elif "mantle" in deploy_network.lower():
                                explorer_url = f"https://explorer.mantle.xyz/address/{contract_address}"
                            else:
                                explorer_url = f"https://blockscout.com/{deploy_network}/address/{contract_address}"
                            
                            print(f"      Explorer: {explorer_url}")
                            print()
                    else:
                        print("    [!] No deployments found")
                        print("    [*] Deployment may have been skipped or failed")
                        print()
                    
                    return {
                        "status": "success",
                        "workflow_id": workflow_id,
                        "elapsed_time": elapsed,
                        "contracts": contracts,
                        "deployments": deployments
                    }
                
                elif status == "failed":
                    print()  # New line
                    error = status_data.get("error_message", "Unknown error")
                    print(f"[-] Workflow failed: {error}")
                    return {
                        "status": "failed",
                        "workflow_id": workflow_id,
                        "error": error
                    }
                
                await asyncio.sleep(2)
                
            except httpx.RequestError as e:
                print(f"\n[-] Request error: {e}")
                return {"status": "error", "error": str(e)}
            except Exception as e:
                print(f"\n[-] Error: {e}")
                return {"status": "error", "error": str(e)}
        
        print()  # New line
        print(f"[-] Workflow timeout after {MAX_WAIT_TIME}s")
        return {
            "status": "timeout",
            "workflow_id": workflow_id
        }


async def main():
    """Run complete real-world tests"""
    print("=" * 70)
    print("HyperAgent Real-World Complete Test Suite")
    print("=" * 70)
    print()
    
    tests = [
        {
            "name": "Simple ERC20 Token",
            "description": "Create a simple ERC20 token with name 'MyToken', symbol 'MTK', and initial supply of 1 million",
            "network": "hyperion_testnet",
            "contract_type": "ERC20"
        },
        {
            "name": "ERC721 NFT with Constructor",
            "description": "Create an ERC721 NFT contract with name 'MyNFT' and symbol 'MNFT'",
            "network": "hyperion_testnet",
            "contract_type": "ERC721"
        },
        {
            "name": "Storage Contract",
            "description": "Create a simple storage contract that can store and retrieve a number",
            "network": "hyperion_testnet",
            "contract_type": "Custom"
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\n{'=' * 70}")
        print(f"Test: {test['name']}")
        print(f"{'=' * 70}")
        
        try:
            result = await test_complete_workflow(
                test["description"],
                test["network"],
                test["contract_type"],
                verify_constructor_args=True
            )
            results.append({
                "test": test["name"],
                **result
            })
        except Exception as e:
            print(f"\n[-] Test '{test['name']}' failed with exception: {e}")
            results.append({
                "test": test["name"],
                "status": "exception",
                "error": str(e)
            })
        
        # Wait between tests
        if test != tests[-1]:
            print("\n[*] Waiting 5 seconds before next test...")
            await asyncio.sleep(5)
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    success_count = 0
    for result in results:
        status_icon = "[+]" if result["status"] == "success" else "[-]"
        print(f"{status_icon} {result['test']}: {result['status']}")
        
        if result.get("workflow_id"):
            print(f"    Workflow ID: {result['workflow_id']}")
        
        if result.get("elapsed_time"):
            print(f"    Time: {result['elapsed_time']:.1f}s")
        
        if result.get("contracts"):
            print(f"    Contracts: {len(result['contracts'])}")
        
        if result.get("deployments"):
            print(f"    Deployments: {len(result['deployments'])}")
        
        if result.get("error"):
            print(f"    Error: {result['error']}")
        
        if result["status"] == "success":
            success_count += 1
        
        print()
    
    print(f"[*] Passed: {success_count}/{len(results)}")
    
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
        import traceback
        traceback.print_exc()
        sys.exit(1)

