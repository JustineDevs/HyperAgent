#!/usr/bin/env python3
"""Verify wallet address from private key"""
import os
from eth_account import Account
from dotenv import load_dotenv

# Load from .env file (private key never in command line)
load_dotenv()

private_key = os.getenv("PRIVATE_KEY", "").strip()
public_address_env = os.getenv("PUBLIC_ADDRESS", "").strip()

if not private_key:
    print("[-] PRIVATE_KEY not found in .env file")
    exit(1)

# Remove 0x prefix if present
if private_key.startswith("0x"):
    private_key = private_key[2:]

try:
    account = Account.from_key(private_key)
    derived_address = account.address
    
    print("[*] Wallet Address Verification")
    print("=" * 60)
    print(f"Derived Address: {derived_address}")
    print(f"Address in .env:  {public_address_env}")
    print()
    
    if public_address_env:
        if derived_address.lower() == public_address_env.lower():
            print("[+] Addresses MATCH - Configuration is correct")
        else:
            print("[-] Addresses DO NOT MATCH!")
            print(f"    Expected: {public_address_env}")
            print(f"    Got:      {derived_address}")
            print()
            print("[*] Action: Update PUBLIC_ADDRESS in .env to:")
            print(f"    PUBLIC_ADDRESS={derived_address}")
    else:
        print(f"[*] Derived address: {derived_address}")
        print("    Add to .env: PUBLIC_ADDRESS=" + derived_address)
    
    print()
    print("=" * 60)
    print(f"[*] Fund this address with testnet tokens:")
    print(f"    {derived_address}")
    print()
    print("[*] Hyperion Testnet Faucet:")
    print("    https://hyperion-testnet-explorer.metisdevops.link")
    print()
    print("[*] Mantle Testnet Faucet:")
    print("    https://faucet.sepolia.mantle.xyz")
    
except Exception as e:
    print(f"[-] Error: {e}")
    print("    Check if private key format is correct (hex, no 0x prefix)")
    exit(1)