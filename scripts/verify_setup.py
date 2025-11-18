#!/usr/bin/env python3
"""Setup verification script for HyperAgent enhancements

Verifies that all new components are properly installed and configured.
"""
import sys
import asyncio
from pathlib import Path

def check_imports():
    """Check if all required modules can be imported"""
    print("[*] Checking imports...")
    
    try:
        from hyperagent.blockchain.hyperion_pef import HyperionPEFManager
        print("[+] HyperionPEFManager imported successfully")
    except ImportError as e:
        print(f"[-] Failed to import HyperionPEFManager: {e}")
        return False
    
    try:
        from hyperagent.blockchain.metisvm_optimizer import MetisVMOptimizer
        print("[+] MetisVMOptimizer imported successfully")
    except ImportError as e:
        print(f"[-] Failed to import MetisVMOptimizer: {e}")
        return False
    
    try:
        from hyperagent.blockchain.mantle_sdk import MantleSDKClient
        print("[+] MantleSDKClient imported successfully")
    except ImportError as e:
        print(f"[-] Failed to import MantleSDKClient: {e}")
        return False
    
    try:
        from hyperagent.blockchain.eigenda_client import EigenDAClient
        print("[+] EigenDAClient imported successfully")
    except ImportError as e:
        print(f"[-] Failed to import EigenDAClient: {e}")
        return False
    
    return True


def check_config():
    """Check configuration settings"""
    print("\n[*] Checking configuration...")
    
    try:
        from hyperagent.core.config import settings
        
        # Check required settings
        if not settings.gemini_api_key:
            print("[!] Warning: GEMINI_API_KEY not set")
        else:
            print("[+] GEMINI_API_KEY configured")
        
        if not settings.database_url:
            print("[-] Error: DATABASE_URL not set")
            return False
        else:
            print("[+] DATABASE_URL configured")
        
        # Check optional settings
        if settings.use_mantle_sdk:
            print("[+] USE_MANTLE_SDK enabled")
        else:
            print("[*] USE_MANTLE_SDK disabled (default)")
        
        print(f"[+] Hyperion testnet RPC: {settings.hyperion_testnet_rpc}")
        print(f"[+] Mantle testnet RPC: {settings.mantle_testnet_rpc}")
        print(f"[+] EigenDA disperser: {settings.eigenda_disperser_url}")
        
        return True
    except Exception as e:
        print(f"[-] Configuration check failed: {e}")
        return False


def check_network_connectivity():
    """Check network connectivity to blockchain RPCs"""
    print("\n[*] Checking network connectivity...")
    
    try:
        import httpx
        from hyperagent.core.config import settings
        
        async def check_rpc(url, name):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    # Simple connectivity check
                    response = await client.post(
                        url,
                        json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
                    )
                    if response.status_code == 200:
                        print(f"[+] {name} RPC accessible")
                        return True
                    else:
                        print(f"[-] {name} RPC returned status {response.status_code}")
                        return False
            except Exception as e:
                print(f"[-] {name} RPC not accessible: {e}")
                return False
        
        async def check_all():
            results = await asyncio.gather(
                check_rpc(settings.hyperion_testnet_rpc, "Hyperion Testnet"),
                check_rpc(settings.mantle_testnet_rpc, "Mantle Testnet"),
                return_exceptions=True
            )
            return all(r for r in results if isinstance(r, bool))
        
        return asyncio.run(check_all())
    except Exception as e:
        print(f"[-] Network connectivity check failed: {e}")
        return False


def check_dependencies():
    """Check if external dependencies are available"""
    print("\n[*] Checking dependencies...")
    
    try:
        from alith import Agent
        print("[+] Alith SDK available")
    except ImportError:
        print("[!] Warning: Alith SDK not installed (pip install alith -U)")
    
    try:
        from web3 import Web3
        print("[+] Web3.py available")
    except ImportError:
        print("[-] Error: Web3.py not installed")
        return False
    
    try:
        import httpx
        print("[+] httpx available")
    except ImportError:
        print("[-] Error: httpx not installed")
        return False
    
    return True


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("HyperAgent Setup Verification")
    print("=" * 60)
    
    checks = [
        ("Imports", check_imports),
        ("Configuration", check_config),
        ("Dependencies", check_dependencies),
        ("Network Connectivity", check_network_connectivity)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"[-] {name} check failed with exception: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "[+] PASS" if result else "[-] FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n[+] All checks passed! Setup is complete.")
        return 0
    else:
        print("\n[-] Some checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

