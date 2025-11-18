#!/usr/bin/env python3
"""
Test API endpoints for network features

Purpose: Verify network API endpoints work correctly
Usage: python tests/integration/test_api_endpoints_manual.py
"""
import asyncio
import httpx
import json
from hyperagent.core.config import settings


async def test_api_endpoints():
    """Test network API endpoints"""
    api_host = "localhost" if settings.api_host == "0.0.0.0" else settings.api_host
    api_url = f"http://{api_host}:{settings.api_port}"
    
    print("[*] Testing Network API Endpoints...")
    print(f"[*] API URL: {api_url}\n")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test 1: List all networks
        print("[>] Test 1: GET /api/v1/networks")
        try:
            response = await client.get(f"{api_url}/api/v1/networks")
            response.raise_for_status()
            data = response.json()
            
            print(f"[+] Success: Retrieved {len(data)} networks")
            for network in data:
                print(f"    - {network.get('network', 'N/A')}: {sum(1 for v in network.get('features', {}).values() if v)}/{len(network.get('features', {}))} features")
            
        except httpx.RequestError as e:
            print(f"[-] Connection error: {e}")
            print(f"    [*] Make sure API server is running: docker-compose up -d")
            return False
        except httpx.HTTPStatusError as e:
            print(f"[-] HTTP Error: {e.response.status_code}")
            print(f"    Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"[-] Error: {e}")
            return False
        
        # Test 2: Get network features
        print("\n[>] Test 2: GET /api/v1/networks/hyperion_testnet/features")
        try:
            response = await client.get(f"{api_url}/api/v1/networks/hyperion_testnet/features")
            response.raise_for_status()
            data = response.json()
            
            print(f"[+] Success: Retrieved features for {data.get('network', 'N/A')}")
            print(f"    Chain ID: {data.get('chain_id', 'N/A')}")
            print(f"    Features:")
            for feature, supported in data.get('features', {}).items():
                status = "[+]" if supported else "[-]"
                print(f"      {status} {feature}: {supported}")
            
        except Exception as e:
            print(f"[-] Error: {e}")
            return False
        
        # Test 3: Get compatibility report
        print("\n[>] Test 3: GET /api/v1/networks/mantle_mainnet/compatibility")
        try:
            response = await client.get(f"{api_url}/api/v1/networks/mantle_mainnet/compatibility")
            response.raise_for_status()
            data = response.json()
            
            print(f"[+] Success: Compatibility report for {data.get('network', 'N/A')}")
            print(f"    Supports PEF: {data.get('supports_pef', False)}")
            print(f"    Supports MetisVM: {data.get('supports_metisvm', False)}")
            print(f"    Supports EigenDA: {data.get('supports_eigenda', False)}")
            if data.get('recommendations'):
                print(f"    Recommendations:")
                for rec in data.get('recommendations', []):
                    print(f"      - {rec}")
            
        except Exception as e:
            print(f"[-] Error: {e}")
            return False
        
        # Test 4: Test unknown network (should return 404)
        print("\n[>] Test 4: GET /api/v1/networks/unknown_network/features (should 404)")
        try:
            response = await client.get(f"{api_url}/api/v1/networks/unknown_network/features")
            if response.status_code == 404:
                print(f"[+] Success: Correctly returned 404 for unknown network")
            else:
                print(f"[-] Unexpected status: {response.status_code}")
                return False
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"[+] Success: Correctly returned 404 for unknown network")
            else:
                print(f"[-] Unexpected status: {e.response.status_code}")
                return False
        except Exception as e:
            print(f"[-] Error: {e}")
            return False
    
    print("\n[+] All API endpoint tests passed!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_api_endpoints())
    exit(0 if success else 1)

