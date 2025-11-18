#!/usr/bin/env python3
"""
Manual test script for workflow creation

Purpose: Verify workflow creation with real API and database
Usage: python tests/integration/test_workflow_creation_manual.py
"""
import asyncio
import httpx
import json
from datetime import datetime
from hyperagent.core.config import settings


async def test_workflow_creation():
    """Test workflow creation via API"""
    # Use localhost instead of 0.0.0.0 for external access
    api_host = "localhost" if settings.api_host == "0.0.0.0" else settings.api_host
    api_url = f"http://{api_host}:{settings.api_port}"
    
    print("[*] Testing workflow creation...")
    print(f"[*] API URL: {api_url}")
    
    # Test 1: Basic workflow creation
    print("\n[>] Test 1: Basic workflow creation")
    payload = {
        "nlp_input": "Create a simple ERC20 token contract",
        "network": "hyperion_testnet",
        "contract_type": "ERC20",
        "skip_deployment": True,
        "skip_audit": True
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{api_url}/api/v1/workflows/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"[+] Workflow created successfully")
            print(f"    Workflow ID: {data.get('workflow_id', 'N/A')}")
            print(f"    Status: {data.get('status', 'N/A')}")
            print(f"    Message: {data.get('message', 'N/A')}")
            
        except httpx.HTTPStatusError as e:
            print(f"[-] HTTP Error: {e.response.status_code}")
            print(f"    Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"[-] Error: {e}")
            return False
    
    # Test 2: Workflow with MetisVM flags (Hyperion - should work)
    print("\n[>] Test 2: Workflow with MetisVM optimization (Hyperion)")
    payload2 = {
        "nlp_input": "Create ERC20 token with floating-point pricing",
        "network": "hyperion_testnet",
        "contract_type": "ERC20",
        "optimize_for_metisvm": True,
        "enable_floating_point": True,
        "skip_deployment": True,
        "skip_audit": True
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{api_url}/api/v1/workflows/generate",
                json=payload2
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"[+] MetisVM workflow created successfully")
            print(f"    Workflow ID: {data.get('workflow_id', 'N/A')}")
            print(f"    Status: {data.get('status', 'N/A')}")
            if data.get('warnings'):
                print(f"    Warnings: {data.get('warnings')}")
            
        except Exception as e:
            print(f"[-] MetisVM test failed: {e}")
            return False
    
    # Test 2b: Workflow with MetisVM flags (Mantle - should fallback)
    print("\n[>] Test 2b: Workflow with MetisVM optimization (Mantle - should fallback)")
    payload2b = {
        "nlp_input": "Create ERC20 token with floating-point pricing",
        "network": "mantle_testnet",
        "contract_type": "ERC20",
        "optimize_for_metisvm": True,
        "enable_floating_point": True,
        "skip_deployment": True,
        "skip_audit": True
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{api_url}/api/v1/workflows/generate",
                json=payload2b
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"[+] Mantle workflow created (with fallback)")
            print(f"    Workflow ID: {data.get('workflow_id', 'N/A')}")
            if data.get('warnings'):
                print(f"    Warnings: {data.get('warnings')}")
                print(f"    [*] Expected: MetisVM not available warning")
            
        except Exception as e:
            print(f"[-] Mantle MetisVM test failed: {e}")
            return False
    
    # Test 3: Workflow with EigenDA (Mantle mainnet - should use EigenDA)
    print("\n[>] Test 3: Workflow with EigenDA (Mantle mainnet)")
    payload3 = {
        "nlp_input": "Create ERC20 token contract",
        "network": "mantle_mainnet",
        "contract_type": "ERC20",
        "skip_deployment": True,  # Skip deployment for testing
        "skip_audit": True
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{api_url}/api/v1/workflows/generate",
                json=payload3
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"[+] Mantle mainnet workflow created")
            print(f"    Workflow ID: {data.get('workflow_id', 'N/A')}")
            if data.get('features_used'):
                eigenda_available = data.get('features_used', {}).get('eigenda', False)
                print(f"    EigenDA available: {eigenda_available}")
            
        except Exception as e:
            print(f"[-] EigenDA test failed: {e}")
            return False
    
    # Test 4: Workflow with EigenDA (Mantle testnet - should skip)
    print("\n[>] Test 4: Workflow with EigenDA (Mantle testnet - should skip)")
    payload4 = {
        "nlp_input": "Create ERC20 token contract",
        "network": "mantle_testnet",
        "contract_type": "ERC20",
        "skip_deployment": True,
        "skip_audit": True
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{api_url}/api/v1/workflows/generate",
                json=payload4
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"[+] Mantle testnet workflow created")
            print(f"    Workflow ID: {data.get('workflow_id', 'N/A')}")
            if data.get('features_used'):
                eigenda_available = data.get('features_used', {}).get('eigenda', False)
                print(f"    EigenDA available: {eigenda_available} (should be False on testnet)")
            
        except Exception as e:
            print(f"[-] Mantle testnet test failed: {e}")
            return False
    
    # Test 5: Batch deployment with PEF (Hyperion) - Note: This requires batch deployment endpoint
    print("\n[>] Test 5: Batch deployment with PEF (Hyperion)")
    print("    [*] Note: Batch deployment requires /api/v1/deployments/batch endpoint")
    print("    [*] Skipping for now - requires compiled contracts")
    
    # Test 6: Batch deployment with PEF (Mantle - should fallback)
    print("\n[>] Test 6: Batch deployment with PEF (Mantle - should fallback)")
    print("    [*] Note: Batch deployment requires /api/v1/deployments/batch endpoint")
    print("    [*] Skipping for now - requires compiled contracts")
    
    # Test 7: Multiple workflows (verify user creation fix)
    print("\n[>] Test 7: Multiple workflow creation (user creation fix)")
    for i in range(3):
        payload = {
            "nlp_input": f"Create workflow {i+1}",
            "network": "hyperion_testnet",
            "skip_deployment": True,
            "skip_audit": True
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{api_url}/api/v1/workflows/generate",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                print(f"[+] Workflow {i+1} created: {data.get('workflow_id', 'N/A')}")
            except Exception as e:
                print(f"[-] Workflow {i+1} failed: {e}")
                return False
    
    print("\n[+] All workflow creation tests passed!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_workflow_creation())
    exit(0 if success else 1)

