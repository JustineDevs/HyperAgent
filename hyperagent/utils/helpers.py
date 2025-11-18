"""Utility helper functions"""
import hashlib
import re
from typing import Optional


def calculate_hash(content: str) -> str:
    """Calculate SHA256 hash of content"""
    return hashlib.sha256(content.encode()).hexdigest()


def extract_solidity_code(text: str) -> Optional[str]:
    """
    Extract Solidity code from LLM response
    
    Logic: Look for code blocks marked with ```solidity or ```sol
    """
    # Pattern to match Solidity code blocks
    pattern = r'```(?:solidity|sol)?\s*\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    
    # If no code block found, try to extract between pragma and last }
    pragma_match = re.search(r'pragma\s+solidity.*?}', text, re.DOTALL)
    if pragma_match:
        return pragma_match.group(0)
    
    return None


def validate_ethereum_address(address: str) -> bool:
    """Validate Ethereum address format"""
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return bool(re.match(pattern, address))


def format_gas_cost(gas_used: int, gas_price: int) -> Dict[str, Any]:
    """Format gas cost in multiple units"""
    cost_wei = gas_used * gas_price
    cost_ether = cost_wei / 1e18
    
    return {
        "wei": cost_wei,
        "ether": cost_ether,
        "gwei": cost_wei / 1e9
    }

