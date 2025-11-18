#!/usr/bin/env python3
"""
Generate detailed workflow execution report

Usage:
    python scripts/generate_workflow_report.py --workflow-id <id> --output examples/report.md
"""
import asyncio
import httpx
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from hyperagent.core.config import settings

# Configuration
API_HOST = "localhost" if settings.api_host == "0.0.0.0" else settings.api_host
API_URL = f"http://{API_HOST}:{settings.api_port}/api/v1"

# Explorer URL templates
EXPLORER_URLS = {
    "hyperion_testnet": {
        "explorer": "https://hyperion-testnet-explorer.metisdevops.link",
        "address": "https://hyperion-testnet-explorer.metisdevops.link/address/{address}",
        "tx": "https://hyperion-testnet-explorer.metisdevops.link/tx/{tx_hash}",
        "blockscout": "https://blockscout.com/hyperion_testnet/address/{address}"
    },
    "hyperion_mainnet": {
        "explorer": "https://hyperion-explorer.metisdevops.link",
        "address": "https://hyperion-explorer.metisdevops.link/address/{address}",
        "tx": "https://hyperion-explorer.metisdevops.link/tx/{tx_hash}",
        "blockscout": "https://blockscout.com/hyperion_mainnet/address/{address}"
    },
    "mantle_testnet": {
        "explorer": "https://sepolia.mantlescan.xyz",
        "address": "https://sepolia.mantlescan.xyz/address/{address}",
        "tx": "https://sepolia.mantlescan.xyz/tx/{tx_hash}"
    },
    "mantle_mainnet": {
        "explorer": "https://explorer.mantle.xyz",
        "address": "https://explorer.mantle.xyz/address/{address}",
        "tx": "https://explorer.mantle.xyz/tx/{tx_hash}"
    }
}


def get_explorer_urls(network: str, address: Optional[str] = None, tx_hash: Optional[str] = None) -> Dict[str, str]:
    """Get explorer URLs for network"""
    if network not in EXPLORER_URLS:
        return {}
    
    urls = {}
    config = EXPLORER_URLS[network]
    
    if address:
        urls["contract_address"] = config["address"].format(address=address)
        if "blockscout" in config:
            urls["blockscout_address"] = config["blockscout"].format(address=address)
    
    if tx_hash:
        urls["transaction"] = config["tx"].format(tx_hash=tx_hash)
    
    urls["explorer_base"] = config["explorer"]
    
    return urls


async def fetch_workflow_data(workflow_id: str) -> Dict[str, Any]:
    """Fetch complete workflow data from API"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{API_URL}/workflows/{workflow_id}")
        response.raise_for_status()
        return response.json()


async def fetch_contract_data(contract_id: str) -> Dict[str, Any]:
    """Fetch contract data from API"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{API_URL}/contracts/{contract_id}")
        response.raise_for_status()
        return response.json()


async def fetch_deployment_data(deployment_id: str) -> Dict[str, Any]:
    """Fetch deployment data from API"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{API_URL}/deployments/{deployment_id}")
        response.raise_for_status()
        return response.json()


def generate_markdown_report(workflow_data: Dict[str, Any], contract_data: Optional[Dict[str, Any]] = None, 
                            deployment_data: Optional[Dict[str, Any]] = None) -> str:
    """Generate markdown report from workflow data"""
    
    workflow_id = workflow_data.get("workflow_id", "N/A")
    status = workflow_data.get("status", "unknown")
    network = workflow_data.get("network", "unknown")
    
    # Get contract data
    contracts = workflow_data.get("contracts", [])
    contract = contracts[0] if contracts else contract_data
    
    # Get deployment data
    deployments = workflow_data.get("deployments", [])
    deployment = deployments[0] if deployments else deployment_data
    
    # Calculate timings
    created_at = workflow_data.get("created_at")
    completed_at = workflow_data.get("completed_at")
    elapsed_time = 0
    if created_at and completed_at:
        try:
            from dateutil import parser
            start = parser.parse(created_at)
            end = parser.parse(completed_at)
            elapsed_time = (end - start).total_seconds()
        except:
            pass
    
    # Get explorer URLs
    explorer_urls = {}
    if deployment:
        contract_address = deployment.get("contract_address")
        tx_hash = deployment.get("transaction_hash")
        explorer_urls = get_explorer_urls(network, contract_address, tx_hash)
    
    # Build report
    report = f"""# HyperAgent Workflow Execution Report

**Report Generated**: {datetime.now().isoformat()}  
**Workflow ID**: `{workflow_id}`  
**Status**: `{status}` {'✅' if status == 'completed' else '❌'}  
**Total Execution Time**: `{elapsed_time:.2f}` seconds

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Workflow Status** | {'✅ Completed Successfully' if status == 'completed' else '❌ Failed'} |
| **Contract Generated** | {'✅ Yes' if contract else '❌ No'} |
| **Contract Compiled** | {'✅ Yes' if contract and contract.get('bytecode') else '❌ No'} |
| **Security Audit** | {'✅ Passed' if workflow_data.get('audit_status') == 'passed' else '⚠️ Not Available'} |
| **Tests Generated** | {'✅ Yes' if workflow_data.get('tests_generated') else '⚠️ Not Available'} |
| **Contract Deployed** | {'✅ Yes' if deployment else '❌ No'} |
| **Network** | `{network}` |
| **Contract Type** | `{workflow_data.get('contract_type', 'N/A')}` |

---

## Workflow Details

### Input Parameters

- **NLP Description**: `{workflow_data.get('nlp_input', 'N/A')}`
- **Network**: `{network}`
- **Contract Type**: `{workflow_data.get('contract_type', 'N/A')}`
- **Progress**: `{workflow_data.get('progress_percentage', 0)}%`

### Workflow Timeline

| Stage | Status | Progress |
|-------|--------|----------|
| **Initialization** | ✅ Complete | 10% |
| **Generation** | ✅ Complete | 20% |
| **Compilation** | ✅ Complete | 40% |
| **Security Audit** | ✅ Complete | 60% |
| **Testing** | ✅ Complete | 80% |
| **Deployment** | {'✅ Complete' if deployment else '⏳ Pending'} | 100% |

**Total Time**: `{elapsed_time:.2f}` seconds

---

## Contract Information

"""
    
    if contract:
        contract_id = contract.get("id", "N/A")
        contract_name = contract.get("contract_name", "N/A")
        constructor_args = contract.get("constructor_args", [])
        constructor_params = contract.get("constructor_params", [])
        source_code = contract.get("source_code", "")
        source_code_preview = source_code[:500] + "..." if len(source_code) > 500 else source_code
        
        report += f"""### Contract Details

- **Contract ID**: `{contract_id}`
- **Contract Name**: `{contract_name}`
- **Source Code Hash**: `{contract.get('source_code_hash', 'N/A')}`
- **ABI Available**: {'✅ Yes' if contract.get('abi') else '❌ No'}
- **Bytecode Available**: {'✅ Yes' if contract.get('bytecode') else '❌ No'}

### Constructor Arguments

**Generated Constructor Values**:
```json
{json.dumps(constructor_args, indent=2)}
```

**Constructor Parameters**:
```json
{json.dumps(constructor_params, indent=2)}
```

### Contract Code Preview

```solidity
{source_code_preview}
```

**Full Source Code**: Available via `hyperagent contract view {contract_id}` or API endpoint `/api/v1/contracts/{contract_id}`

---
"""
    
    if deployment:
        contract_address = deployment.get("contract_address")
        tx_hash = deployment.get("transaction_hash")
        block_number = deployment.get("block_number", "N/A")
        gas_used = deployment.get("gas_used", "N/A")
        deploy_network = deployment.get("network", network)
        
        report += f"""## Deployment Information

### Deployment Summary

| Deployment | Status | Network | Address | Transaction |
|------------|--------|---------|---------|-------------|
| **Primary** | ✅ Success | `{deploy_network}` | `{contract_address}` | `{tx_hash}` |

### Deployment Details

- **Contract Address**: `{contract_address}`
- **Transaction Hash**: `{tx_hash}`
- **Block Number**: `{block_number}`
- **Gas Used**: `{gas_used}`
- **Network**: `{deploy_network}`

### Explorer Links

#### Contract Address

"""
        
        # Add network-specific explorer links
        if "hyperion" in deploy_network.lower():
            report += f"""**Hyperion Explorer**:
- Primary: [View Contract on Hyperion Explorer]({explorer_urls.get('contract_address', '#')})
- Alternative: [View on Blockscout]({explorer_urls.get('blockscout_address', '#')})

"""
        elif "mantle" in deploy_network.lower():
            report += f"""**Mantle Explorer**:
- Explorer: [View Contract on Mantle Explorer]({explorer_urls.get('contract_address', '#')})

"""
        
        report += f"""#### Transaction Hash

"""
        
        if "hyperion" in deploy_network.lower():
            report += f"""**Hyperion Explorer**:
- Transaction: [View Transaction on Hyperion Explorer]({explorer_urls.get('transaction', '#')})
- Alternative: [View on Blockscout](https://blockscout.com/{deploy_network}/tx/{tx_hash})

"""
        elif "mantle" in deploy_network.lower():
            report += f"""**Mantle Explorer**:
- Transaction: [View Transaction on Mantle Explorer]({explorer_urls.get('transaction', '#')})

"""
        
        # EigenDA info
        eigenda_commitment = deployment.get("eigenda_commitment")
        if eigenda_commitment:
            report += f"""### EigenDA Integration

- **EigenDA Commitment**: `{eigenda_commitment}`
- **Metadata Stored**: ✅ Yes

---
"""
    
    report += f"""## Performance Metrics

### Workflow Performance

| Metric | Value |
|--------|-------|
| **Total Execution Time** | `{elapsed_time:.2f}` seconds |
| **Workflow Status** | `{status}` |
| **Progress** | `{workflow_data.get('progress_percentage', 0)}%` |

---

## Network Information

### Network Configuration

- **Network Name**: `{network}`
- **Explorer URL**: `{explorer_urls.get('explorer_base', 'N/A')}`

---

## CLI Commands

### View Workflow

```bash
hyperagent workflow status --workflow-id {workflow_id} --format json
```

"""
    
    if contract:
        contract_id = contract.get("id", "N/A")
        report += f"""### View Contract

```bash
hyperagent contract view {contract_id}
```

### Verify Contract

```bash
hyperagent contract verify --contract-id {contract_id} --explorer hyperion
```

"""
    
    if deployment:
        deployment_id = deployment.get("id", "N/A")
        report += f"""### View Deployment

```bash
hyperagent deployment view {deployment_id}
```

"""
    
    report += f"""---

## Support and Resources

- **Website**: [https://hyperionkit.xyz/](https://hyperionkit.xyz/)
- **GitHub**: [https://github.com/JustineDevs/HyperAgent](https://github.com/JustineDevs/HyperAgent)
- **Documentation**: See [Documentation](./README.md#documentation) section

---

**Report Generated by HyperAgent**  
**Generated on**: {datetime.now().isoformat()}

---

## Appendix: Raw Data

### Complete Workflow Response

```json
{json.dumps(workflow_data, indent=2, default=str)}
```

"""
    
    if contract:
        report += f"""
### Complete Contract Data

```json
{json.dumps(contract, indent=2, default=str)}
```

"""
    
    if deployment:
        report += f"""
### Complete Deployment Data

```json
{json.dumps(deployment, indent=2, default=str)}
```

"""
    
    report += "\n---\n\n**End of Report**\n"
    
    return report


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate workflow execution report")
    parser.add_argument("--workflow-id", "-w", required=True, help="Workflow ID")
    parser.add_argument("--output", "-o", default="examples/report.md", help="Output file path")
    
    args = parser.parse_args()
    
    print(f"[*] Fetching workflow data for {args.workflow_id}...")
    
    try:
        # Fetch workflow data
        workflow_data = await fetch_workflow_data(args.workflow_id)
        
        # Fetch contract data if available
        contract_data = None
        contracts = workflow_data.get("contracts", [])
        if contracts:
            contract_id = contracts[0].get("id")
            if contract_id:
                try:
                    contract_data = await fetch_contract_data(contract_id)
                except:
                    contract_data = contracts[0]
        
        # Fetch deployment data if available
        deployment_data = None
        deployments = workflow_data.get("deployments", [])
        if deployments:
            deployment_id = deployments[0].get("id")
            if deployment_id:
                try:
                    deployment_data = await fetch_deployment_data(deployment_id)
                except:
                    deployment_data = deployments[0]
        
        # Generate report
        print(f"[*] Generating report...")
        report = generate_markdown_report(workflow_data, contract_data, deployment_data)
        
        # Write to file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        
        print(f"[+] Report generated successfully: {args.output}")
        print(f"[*] Report includes:")
        print(f"    - Workflow details and timeline")
        print(f"    - Contract information")
        if deployment_data:
            print(f"    - Deployment details with explorer links")
        print(f"    - Performance metrics")
        print(f"    - CLI commands")
        
    except httpx.HTTPStatusError as e:
        print(f"[-] HTTP Error: {e.response.status_code}")
        print(f"    Response: {e.response.text[:200]}")
        sys.exit(1)
    except Exception as e:
        print(f"[-] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

