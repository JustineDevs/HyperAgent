#!/usr/bin/env python3
"""
Manual test script for MetisVM optimization

Purpose: Test MetisVM optimization via API
Usage: python tests/integration/test_metisvm_optimization_manual.py
"""
import asyncio
import httpx
from hyperagent.core.config import settings


async def test_metisvm_optimization():
    """Test MetisVM optimization via API"""
    # Use localhost instead of 0.0.0.0 for external access
    api_host = "localhost" if settings.api_host == "0.0.0.0" else settings.api_host
    api_url = f"http://{api_host}:{settings.api_port}"
    
    print("[*] Testing MetisVM optimization...")
    print(f"[*] API URL: {api_url}")
    
    # Test 1: Basic MetisVM optimization
    print("\n[>] Test 1: Basic MetisVM optimization")
    payload1 = {
        "nlp_input": "Create ERC20 token contract",
        "network": "hyperion_testnet",
        "contract_type": "ERC20",
        "optimize_for_metisvm": True,
        "skip_deployment": True,
        "skip_audit": True
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{api_url}/api/v1/workflows/generate",
                json=payload1
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"[+] Workflow created with MetisVM optimization")
            print(f"    Workflow ID: {data.get('workflow_id', 'N/A')}")
            print(f"    Status: {data.get('status', 'N/A')}")
            print(f"    Note: To verify pragma directives, query workflow status endpoint with workflow_id")
            
        except Exception as e:
            print(f"[-] Test 1 failed: {e}")
            return False
    
    # Test 2: MetisVM with floating-point
    print("\n[>] Test 2: MetisVM with floating-point operations")
    payload2 = {
        "nlp_input": "Create ERC20 token with floating-point pricing calculations",
        "network": "hyperion_testnet",
        "contract_type": "ERC20",
        "optimize_for_metisvm": True,
        "enable_floating_point": True,
        "skip_deployment": True,
        "skip_audit": True
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{api_url}/api/v1/workflows/generate",
                json=payload2
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"[+] Workflow created with MetisVM + floating-point")
            print(f"    Workflow ID: {data.get('workflow_id', 'N/A')}")
            print(f"    Expected: Contract should include 'pragma metisvm_floating_point'")
            
        except Exception as e:
            print(f"[-] Test 2 failed: {e}")
            return False
    
    # Test 3: MetisVM with AI inference
    print("\n[>] Test 3: MetisVM with AI inference support")
    payload3 = {
        "nlp_input": "Create smart contract with AI prediction capabilities",
        "network": "hyperion_testnet",
        "contract_type": "Custom",
        "optimize_for_metisvm": True,
        "enable_ai_inference": True,
        "skip_deployment": True,
        "skip_audit": True
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{api_url}/api/v1/workflows/generate",
                json=payload3
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"[+] Workflow created with MetisVM + AI inference")
            print(f"    Workflow ID: {data.get('workflow_id', 'N/A')}")
            print(f"    Expected: Contract should include 'pragma metisvm_ai_quantization'")
            
        except Exception as e:
            print(f"[-] Test 3 failed: {e}")
            return False
    
    # Test 4: All flags enabled
    print("\n[>] Test 4: MetisVM with all optimization flags")
    payload4 = {
        "nlp_input": "Create advanced ERC20 token with floating-point and AI features",
        "network": "hyperion_testnet",
        "contract_type": "ERC20",
        "optimize_for_metisvm": True,
        "enable_floating_point": True,
        "enable_ai_inference": True,
        "skip_deployment": True,
        "skip_audit": True
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{api_url}/api/v1/workflows/generate",
                json=payload4
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"[+] Workflow created with all MetisVM optimizations")
            print(f"    Workflow ID: {data.get('workflow_id', 'N/A')}")
            print(f"    Expected: Contract should include:")
            print(f"      - pragma metisvm")
            print(f"      - pragma metisvm_floating_point")
            print(f"      - pragma metisvm_ai_quantization")
            
        except Exception as e:
            print(f"[-] Test 4 failed: {e}")
            return False
    
    print("\n[+] All MetisVM optimization tests passed!")
    print("[*] Note: To verify pragma directives in generated contracts:")
    print("    1. Query workflow status: GET /api/v1/workflows/{workflow_id}")
    print("    2. Check generated contract_code field for pragma directives")
    print("    3. Verify optimization_report field contains optimization details")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_metisvm_optimization())
    exit(0 if success else 1)

