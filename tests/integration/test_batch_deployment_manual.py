#!/usr/bin/env python3
"""
Manual test script for PEF batch deployment

Purpose: Test PEF batch deployment via API
Usage: python tests/integration/test_batch_deployment_manual.py
"""
import asyncio
import httpx
import json
from hyperagent.core.config import settings


async def test_batch_deployment():
    """Test PEF batch deployment via API"""
    # Use localhost instead of 0.0.0.0 for external access
    api_host = "localhost" if settings.api_host == "0.0.0.0" else settings.api_host
    api_url = f"http://{api_host}:{settings.api_port}"
    
    print("[*] Testing PEF batch deployment...")
    print(f"[*] API URL: {api_url}")
    
    # Try to load contracts from example file, fallback to inline
    import os
    example_file = "examples/batch_deployment_example.json"
    if os.path.exists(example_file):
        print(f"[*] Loading contracts from {example_file}")
        with open(example_file, 'r') as f:
            example_data = json.load(f)
            contracts = example_data.get("contracts", [])
    else:
        print("[!] Example file not found, using inline contracts")
        contracts = [
        {
            "contract_name": "TestContract1",
            "compiled_contract": {
                "bytecode": "0x608060405234801561001057600080fd5b50610150806100206000396000f3fe6080604052348015600f57600080fd5b506004361060325760003560e01c80632e64cec11460375780636057361d146051575b600080fd5b603d6069565b6040516048919060c2565b60405180910390f35b6067600480360381019060639190608f565b6072565b005b60008054905090565b8060008190555050565b600080fd5b6000819050919050565b6089816078565b8114609357600080fd5b50565b60006020828403121560a057600080fd5b600060ac84828501608f565b91505092915050565b6000819050919050565b60c68160b5565b82525050565b600060208201905060df600083018460bf565b9291505056fea2646970667358221220d6c4e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e64736f6c63430008070033",
                "abi": []
            },
            "source_code": "pragma solidity ^0.8.27; contract TestContract1 { uint256 public value; }"
        },
        {
            "contract_name": "TestContract2",
            "compiled_contract": {
                "bytecode": "0x608060405234801561001057600080fd5b50610150806100206000396000f3fe6080604052348015600f57600080fd5b506004361060325760003560e01c80632e64cec11460375780636057361d146051575b600080fd5b603d6069565b6040516048919060c2565b60405180910390f35b6067600480360381019060639190608f565b6072565b005b60008054905090565b8060008190555050565b600080fd5b6000819050919050565b6089816078565b8114609357600080fd5b50565b60006020828403121560a057600080fd5b600060ac84828501608f565b91505092915050565b6000819050919050565b60c68160b5565b82525050565b600060208201905060df600083018460bf565b9291505056fea2646970667358221220d6c4e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e64736f6c63430008070033",
                "abi": []
            },
            "source_code": "pragma solidity ^0.8.27; contract TestContract2 { uint256 public count; }"
        }
        ]
    
    # Ensure all contracts have network field
    for contract in contracts:
        if "network" not in contract:
            contract["network"] = "hyperion_testnet"
    
    payload = {
        "contracts": contracts,
        "network": "hyperion_testnet",
        "use_pef": True,
        "max_parallel": 2
    }
    
    print(f"\n[>] Deploying {len(contracts)} contracts in parallel...")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(
                f"{api_url}/api/v1/deployments/batch",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"[+] Batch deployment completed")
            print(f"    Success: {data.get('success', False)}")
            print(f"    Total time: {data.get('total_time', 0):.2f}s")
            print(f"    Success count: {data.get('success_count', 0)}")
            print(f"    Failed count: {data.get('failed_count', 0)}")
            print(f"    Parallel count: {data.get('parallel_count', 0)}")
            
            # Verify response structure matches BatchDeploymentResponse
            assert "deployments" in data, "Response should include 'deployments' field"
            assert "success" in data, "Response should include 'success' field"
            assert "total_time" in data, "Response should include 'total_time' field"
            assert "parallel_count" in data, "Response should include 'parallel_count' field"
            
            # Display individual results
            for deployment in data.get("deployments", []):
                status = "[+]" if deployment.get("status") == "success" else "[-]"
                contract_name = deployment.get('contract_name', 'N/A')
                if deployment.get("status") == "success":
                    address = deployment.get('contract_address', 'N/A')
                    tx_hash = deployment.get('transaction_hash', 'N/A')
                    print(f"    {status} {contract_name}: {address} (tx: {tx_hash[:10]}...)")
                else:
                    error = deployment.get('error', 'N/A')
                    print(f"    {status} {contract_name}: {error}")
            
            # Test error handling - network mismatch
            print("\n[*] Testing error handling: network mismatch...")
            error_payload = {
                "contracts": [
                    {"contract_name": "Contract1", "network": "hyperion_testnet", "compiled_contract": {"bytecode": "0x123", "abi": []}},
                    {"contract_name": "Contract2", "network": "mantle_testnet", "compiled_contract": {"bytecode": "0x456", "abi": []}}
                ],
                "network": "hyperion_testnet",
                "use_pef": True
            }
            try:
                error_response = await client.post(
                    f"{api_url}/api/v1/deployments/batch",
                    json=error_payload
                )
                if error_response.status_code == 400:
                    print(f"[+] Error handling works: {error_response.json().get('detail', 'Network mismatch detected')}")
                else:
                    print(f"[!] Expected 400 for network mismatch, got {error_response.status_code}")
            except Exception as e:
                print(f"[!] Error handling test failed: {e}")
            
            return data.get("success", False)
            
        except httpx.HTTPStatusError as e:
            print(f"[-] HTTP Error: {e.response.status_code}")
            print(f"    Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"[-] Error: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = asyncio.run(test_batch_deployment())
    exit(0 if success else 1)

