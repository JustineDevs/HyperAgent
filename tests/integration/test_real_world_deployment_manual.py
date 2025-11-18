#!/usr/bin/env python3
"""
Real-world end-to-end deployment test

Tests complete workflow: Generation → Compilation → Audit → Testing → Deployment
Verifies contract is deployed on-chain and visible on explorer

Usage: python tests/integration/test_real_world_deployment_manual.py
"""
import asyncio
import httpx
import json
import time
from hyperagent.core.config import settings

async def test_real_world_deployment():
    """Test complete workflow with on-chain deployment"""
    api_host = "localhost" if settings.api_host == "0.0.0.0" else settings.api_host
    api_url = f"http://{api_host}:{settings.api_port}"
    
    print("[*] Real-World End-to-End Deployment Test")
    print(f"[*] API URL: {api_url}")
    print(f"[*] Network: hyperion_testnet")
    print()
    
    # Step 1: Create workflow
    print("[>] Step 1: Creating workflow...")
    payload = {
        "nlp_input": "Create a simple storage contract that can store and retrieve a number",
        "network": "hyperion_testnet",
        "contract_type": "Custom",
        "skip_audit": False,
        "skip_testing": False,
        "skip_deployment": False  # Enable deployment!
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(
                f"{api_url}/api/v1/workflows/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            workflow_id = data.get("workflow_id")
            
            if not workflow_id:
                print("[-] No workflow_id in response")
                print(f"    Response: {json.dumps(data, indent=2)}")
                return False
            
            print(f"[+] Workflow created: {workflow_id}")
            print(f"    Status: {data.get('status')}")
            if data.get('warnings'):
                print(f"    Warnings: {data.get('warnings')}")
            
            # Step 2: Monitor workflow progress with Unicode progress bar
            print("\n[>] Step 2: Monitoring workflow progress...")
            print("    This may take 1-3 minutes...")
            max_wait = 300  # 5 minutes max
            start_time = time.time()
            last_progress = -1
            last_stage = ""
            
            def print_progress_bar(progress: int, stage: str = "", width: int = 40):
                """Print Unicode progress bar"""
                filled = int((progress / 100) * width)
                empty = width - filled
                bar = "█" * filled + "░" * empty
                percent = int(progress)
                print(f"\r[...] [{stage:12}] |{bar}| {percent:3}%", end="", flush=True)
            
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
            
            while time.time() - start_time < max_wait:
                try:
                    status_response = await client.get(
                        f"{api_url}/api/v1/workflows/{workflow_id}",
                        timeout=10.0
                    )
                    status_response.raise_for_status()
                    status_data = status_response.json()
                    status = status_data.get("status")
                    progress = status_data.get("progress_percentage", 0)
                    stage = stage_map.get(status, status.title() if status else "Unknown")
                    
                    # Update progress bar if changed
                    if progress != last_progress or stage != last_stage:
                        print_progress_bar(progress, stage)
                        last_progress = progress
                        last_stage = stage
                    
                    if status == "completed":
                        print()  # New line after progress bar
                        print("\n[+] Workflow completed successfully!")
                        break
                    elif status == "failed":
                        print()  # New line after progress bar
                        print("\n[-] Workflow failed!")
                        error = status_data.get("error_message", status_data.get("error", "Unknown error"))
                        print(f"    Error: {error}")
                        if status_data.get("error_details"):
                            print(f"    Details: {status_data.get('error_details')}")
                        return False
                    
                    await asyncio.sleep(2)  # Check every 2 seconds
                except httpx.TimeoutException:
                    print("\n    [*] Timeout checking status, retrying...")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"\n    [!] Error checking status: {e}")
                    await asyncio.sleep(2)
            else:
                print()  # New line after progress bar
                print("\n[-] Workflow timeout after 5 minutes!")
                print(f"    Last status: {last_stage}")
                return False
            
            # Step 3: Get deployment details
            print("\n[>] Step 3: Retrieving deployment details...")
            try:
                contracts_response = await client.get(
                    f"{api_url}/api/v1/workflows/{workflow_id}/contracts",
                    timeout=10.0
                )
                contracts_response.raise_for_status()
                contracts_data = contracts_response.json()
                
                deployments_response = await client.get(
                    f"{api_url}/api/v1/workflows/{workflow_id}/deployments",
                    timeout=10.0
                )
                deployments_response.raise_for_status()
                deployments_data = deployments_response.json()
                
                if deployments_data.get("deployments"):
                    deployment = deployments_data["deployments"][0]
                    contract_address = deployment.get("contract_address")
                    tx_hash = deployment.get("transaction_hash")
                    block_number = deployment.get("block_number")
                    gas_used = deployment.get("gas_used")
                    
                    print(f"[+] Contract deployed successfully!")
                    print(f"    Address: {contract_address}")
                    print(f"    Transaction: {tx_hash}")
                    print(f"    Block: {block_number}")
                    if gas_used:
                        print(f"    Gas Used: {gas_used:,}")
                    
                    print(f"\n[*] Verify on explorer:")
                    print(f"    Address: https://hyperion-testnet-explorer.metisdevops.link/address/{contract_address}")
                    print(f"    Transaction: https://hyperion-testnet-explorer.metisdevops.link/tx/{tx_hash}")
                    
                    # Step 4: Verify contract details
                    if contracts_data.get("contracts"):
                        contract = contracts_data["contracts"][0]
                        contract_name = contract.get("contract_name", "Unknown")
                        print(f"\n[*] Contract Details:")
                        print(f"    Name: {contract_name}")
                        print(f"    Source Code Hash: {contract.get('source_code_hash', 'N/A')[:20]}...")
                    
                    return True
                else:
                    print("[-] No deployment found in workflow")
                    print(f"    Response: {json.dumps(deployments_data, indent=2)}")
                    return False
                    
            except httpx.HTTPStatusError as e:
                print(f"[-] HTTP Error retrieving deployment: {e.response.status_code}")
                print(f"    Response: {e.response.text}")
                return False
            except Exception as e:
                print(f"[-] Error retrieving deployment: {e}")
                return False
                
        except httpx.HTTPStatusError as e:
            print(f"[-] HTTP Error: {e.response.status_code}")
            print(f"    Response: {e.response.text}")
            return False
        except httpx.ConnectError:
            print(f"[-] Connection error: Cannot connect to {api_url}")
            print(f"    [*] Make sure API server is running: docker-compose up -d")
            return False
        except Exception as e:
            print(f"[-] Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("HyperAgent Real-World Deployment Test")
    print("=" * 60)
    print()
    print("[*] Prerequisites:")
    print("    1. Docker services running (docker-compose up -d)")
    print("    2. Wallet funded with testnet tokens")
    print("    3. PRIVATE_KEY set in .env file")
    print("    4. GEMINI_API_KEY set in .env file")
    print()
    
    success = asyncio.run(test_real_world_deployment())
    
    print()
    print("=" * 60)
    if success:
        print("[+] Test PASSED - Contract deployed successfully!")
        print("    Verify on explorer to confirm deployment")
    else:
        print("[-] Test FAILED - Check errors above")
        print("    Common issues:")
        print("    - Wallet not funded (get testnet tokens from faucet)")
        print("    - PRIVATE_KEY not set in .env")
        print("    - API server not running")
        print("    - Network connectivity issues")
    print("=" * 60)
    
    exit(0 if success else 1)

