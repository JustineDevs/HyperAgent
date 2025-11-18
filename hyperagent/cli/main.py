"""HyperAgent CLI - ASCII-based command interface"""
import asyncio
import click
import httpx
import sys
import time
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
import platform

from hyperagent.cli.formatters import (
    CLIStyle, print_banner, format_workflow_status, format_workflow_list,
    format_contract_code, format_audit_report, format_deployment_confirmation,
    format_test_results, format_error, format_success, format_unicode_progress_bar,
    format_progress_bar_windows_safe, get_stage_name, handle_api_error
)
from hyperagent.core.config import settings

console = Console()


def get_api_url() -> str:
    """Get API URL, converting 0.0.0.0 to localhost for external access"""
    api_host = "localhost" if settings.api_host == "0.0.0.0" else settings.api_host
    return f"http://{api_host}:{settings.api_port}"


def create_progress_columns():
    """Create progress columns, avoiding Unicode spinner on Windows"""
    if platform.system() == "Windows":
        return [TextColumn("[progress.description]{task.description}")]
    else:
        return [SpinnerColumn(), TextColumn("[progress.description]{task.description}")]


def monitor_workflow_progress(workflow_id: str, api_url: str, poll_interval: int = 2, output_format: str = 'table'):
    """Monitor workflow progress with real-time Unicode progress bar"""
    last_progress = -1
    last_stage = ""
    start_time = time.time()
    
    console.print(f"\n{CLIStyle.INFO} Monitoring workflow progress...")
    console.print(f"{CLIStyle.INFO} Press Ctrl+C to stop monitoring\n")
    
    try:
        while True:
            # Poll API
            async def get_status_async():
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{api_url}/api/v1/workflows/{workflow_id}")
                    response.raise_for_status()
                    return response.json()
            
            status_data = asyncio.run(get_status_async())
            status = status_data.get("status", "unknown")
            progress = status_data.get("progress_percentage", 0)
            stage = get_stage_name(status)
            
            # Update progress bar if changed (Windows-safe)
            if progress != last_progress or stage != last_stage:
                # Use Windows-safe version directly on Windows to avoid encoding issues
                if platform.system() == "Windows":
                    progress_bar = format_progress_bar_windows_safe(
                        progress, stage=stage, label="Workflow"
                    )
                    progress_prefix = "[...]"
                else:
                    try:
                        progress_bar = format_unicode_progress_bar(
                            progress, stage=stage, label="Workflow"
                        )
                        progress_prefix = CLIStyle.WAIT
                    except UnicodeEncodeError:
                        # Fallback to ASCII on other platforms if encoding fails
                        progress_bar = format_progress_bar_windows_safe(
                            progress, stage=stage, label="Workflow"
                        )
                        progress_prefix = "[...]"
                
                # Use sys.stdout.write for better Windows compatibility
                try:
                    sys.stdout.write(f"\r{progress_prefix} {progress_bar}")
                    sys.stdout.flush()
                except UnicodeEncodeError:
                    # Final fallback: ASCII only
                    progress_bar_ascii = format_progress_bar_windows_safe(
                        progress, stage=stage, label="Workflow"
                    )
                    sys.stdout.write(f"\r[...] {progress_bar_ascii}")
                    sys.stdout.flush()
                
                last_progress = progress
                last_stage = stage
            
            # Check completion
            if status in ["completed", "failed"]:
                sys.stdout.write("\n")
                if status == "completed":
                    elapsed = time.time() - start_time
                    console.print(f"\n{CLIStyle.SUCCESS} Workflow completed in {elapsed:.1f}s")
                    
                    # Show final status in requested format
                    if output_format == 'json':
                        import json
                        console.print(json.dumps(status_data, indent=2, default=str))
                    elif output_format == 'yaml':
                        try:
                            import yaml
                            console.print(yaml.dump(status_data, default_flow_style=False, allow_unicode=True))
                        except ImportError:
                            pass
                    elif output_format == 'compact':
                        console.print(f"{status_data.get('workflow_id', 'N/A')} | {status_data.get('status', 'N/A')} | {status_data.get('progress_percentage', 0)}%")
                    else:
                        format_workflow_status(status_data)
                else:
                    error = status_data.get("error_message", "Unknown error")
                    console.print(f"\n{CLIStyle.ERROR} Workflow failed: {error}")
                break
            
            time.sleep(poll_interval)
            
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        console.print(f"\n{CLIStyle.WARNING} Monitoring stopped by user")
    except httpx.RequestError as e:
        sys.stdout.write("\n")
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health"])
    except httpx.HTTPStatusError as e:
        sys.stdout.write("\n")
        handle_api_error(e, f"workflow {workflow_id}")
    except Exception as e:
        sys.stdout.write("\n")
        format_error("Error monitoring workflow", str(e))


@click.group()
@click.version_option(version="1.0.0")
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--debug', '-d', is_flag=True, help='Debug mode')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), help='Log level')
@click.pass_context
def cli(ctx, verbose, debug, log_level):
    """HyperAgent: AI Agent for Smart Contract Generation & Deployment"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug
    ctx.obj['log_level'] = log_level or ('DEBUG' if debug else ('INFO' if verbose else 'WARNING'))
    
    # Configure logging if verbose or debug
    if debug or verbose:
        import logging
        logging.basicConfig(
            level=getattr(logging, ctx.obj['log_level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )


@cli.group()
def workflow():
    """Workflow management commands"""
    pass


@workflow.command()
@click.option('--description', '-d', help='NLP description of contract (required if not interactive)')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode')
@click.option('--watch', '-w', is_flag=True, help='Watch progress in real-time')
@click.option('--follow', '-f', is_flag=True, help='Follow progress (alias for --watch)')
@click.option('--network', '-n', type=click.Choice(['hyperion_testnet', 'hyperion_mainnet', 'mantle_testnet', 'mantle_mainnet']), default='hyperion_testnet', help='Target blockchain')
@click.option('--type', '-t', type=click.Choice(['ERC20', 'ERC721', 'ERC1155', 'Custom']), default='Custom', help='Contract type')
@click.option('--name', help='Workflow name (optional)')
@click.option('--no-audit', is_flag=True, help='Skip security audit')
@click.option('--no-deploy', is_flag=True, help='Skip deployment')
@click.option('--optimize-metisvm', is_flag=True, help='Optimize for MetisVM (Hyperion only)')
@click.option('--enable-fp', is_flag=True, help='Enable floating-point operations')
@click.option('--enable-ai', is_flag=True, help='Enable AI inference support')
@click.option('--confirm-steps', is_flag=True, help='Confirm each step')
def create(description: Optional[str], interactive: bool, watch: bool, follow: bool, network: str, type: str, name: Optional[str], no_audit: bool, no_deploy: bool, optimize_metisvm: bool, enable_fp: bool, enable_ai: bool, confirm_steps: bool):
    """[>] Create workflow to generate and deploy smart contract"""
    print_banner()
    
    # Interactive mode
    if interactive:
        from hyperagent.cli.interactive import run_interactive_prompts
        description, network, type, options = run_interactive_prompts()
        no_audit = options.get("skip_audit", False)
        no_deploy = options.get("skip_deployment", False)
        optimize_metisvm = options.get("optimize_metisvm", False)
        enable_fp = options.get("enable_fp", False)
        enable_ai = options.get("enable_ai", False)
    elif not description:
        format_error("Description required", "Use --description or --interactive", 
                    suggestions=["Use --description to provide description directly",
                                "Use --interactive for guided workflow creation"])
        return
    
    # Step-by-step confirmation
    if confirm_steps:
        if not click.confirm(f"{CLIStyle.INFO} Step 1: Generate contract?", default=True):
            return
        if not click.confirm(f"{CLIStyle.INFO} Step 2: Run security audit?", default=True):
            no_audit = True
        if not click.confirm(f"{CLIStyle.INFO} Step 3: Deploy to blockchain?", default=True):
            no_deploy = True
    
    console.print(f"\n{CLIStyle.INFO} Creating workflow...")
    console.print(f"{CLIStyle.INFO} Network: {network}")
    console.print(f"{CLIStyle.INFO} Contract Type: {type}")
    console.print(f"{CLIStyle.INFO} Description: {description[:60]}...")
    
    try:
        # Call API to create workflow
        api_url = get_api_url()
        
        async def create_workflow_async():
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{api_url}/api/v1/workflows/generate",
                    json={
                        "nlp_input": description,
                        "network": network,
                        "contract_type": type,
                        "name": name,
                        "skip_audit": no_audit,
                        "skip_deployment": no_deploy,
                        "optimize_for_metisvm": optimize_metisvm,
                        "enable_floating_point": enable_fp,
                        "enable_ai_inference": enable_ai
                    }
                )
                response.raise_for_status()
                return response.json()
        
        with Progress(
            *create_progress_columns(),
            console=console
        ) as progress:
            task = progress.add_task(f"{CLIStyle.WAIT} Creating workflow...", total=None)
            result = asyncio.run(create_workflow_async())
            progress.update(task, completed=True)
        
        workflow_id = result.get("workflow_id")
        status = result.get("status")
        
        if watch or follow:
            monitor_workflow_progress(workflow_id, api_url)
        else:
            format_success(
                f"Workflow created: {workflow_id}",
                f"Status: {status}\nUse 'hyperagent workflow status --workflow-id {workflow_id}' to check progress"
            )
        
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health",
                                "Verify API URL in configuration",
                                "Check network connectivity"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, "workflow creation")
    except Exception as e:
        format_error("Failed to create workflow", str(e))


@workflow.command()
@click.option('--workflow-id', '-w', required=True, help='Workflow ID')
@click.option('--watch', is_flag=True, help='Watch progress continuously')
@click.option('--follow', is_flag=True, help='Follow progress (alias for --watch)')
@click.option('--poll-interval', type=int, default=2, help='Polling interval in seconds (default: 2)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml', 'compact']), default='table', help='Output format')
def status(workflow_id: str, watch: bool, follow: bool, poll_interval: int, format: str):
    """[*] Check workflow status"""
    try:
        api_url = get_api_url()
        
        async def get_status_async():
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{api_url}/api/v1/workflows/{workflow_id}")
                response.raise_for_status()
                return response.json()
        
        if watch or follow:
            monitor_workflow_progress(workflow_id, api_url, poll_interval, format)
        else:
            status_data = asyncio.run(get_status_async())
            
            if format == 'json':
                import json
                console.print(json.dumps(status_data, indent=2, default=str))
            elif format == 'yaml':
                try:
                    import yaml
                    console.print(yaml.dump(status_data, default_flow_style=False, allow_unicode=True))
                except ImportError:
                    format_error("YAML format requires PyYAML", "Install with: pip install pyyaml")
            elif format == 'compact':
                console.print(f"{status_data.get('workflow_id', 'N/A')} | {status_data.get('status', 'N/A')} | {status_data.get('progress_percentage', 0)}%")
            else:
                format_workflow_status(status_data)
        
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health",
                                "Verify API URL in configuration"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, f"workflow {workflow_id}")
    except Exception as e:
        format_error("Failed to get workflow status", str(e))


@workflow.command()
@click.option('--workflow-id', '-w', required=True, help='Workflow ID to cancel')
def cancel(workflow_id: str):
    """[!] Cancel running workflow"""
    try:
        api_url = get_api_url()
        
        async def cancel_workflow_async():
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{api_url}/api/v1/workflows/{workflow_id}/cancel")
                response.raise_for_status()
                return response.json()
        
        result = asyncio.run(cancel_workflow_async())
        format_success(f"Workflow cancelled: {workflow_id}")
        
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, f"workflow {workflow_id}")
    except Exception as e:
        format_error("Failed to cancel workflow", str(e))


@workflow.command()
@click.option('--status-filter', '-s', type=click.Choice(['created', 'generating', 'auditing', 'testing', 'deploying', 'completed', 'failed']), help='Filter by status')
@click.option('--search', help='Search in description/name')
@click.option('--network', '-n', help='Filter by network')
@click.option('--limit', '-l', type=int, default=10, help='Number of workflows to display')
@click.option('--format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def list(status_filter: Optional[str], search: Optional[str], network: Optional[str], limit: int, format: str):
    """[*] List workflows with filters"""
    try:
        api_url = get_api_url()
        
        async def get_workflows_async():
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {"limit": limit}
                if status_filter:
                    params["status"] = status_filter
                if search:
                    params["search"] = search
                if network:
                    params["network"] = network
                
                # Try to call workflows list endpoint
                response = await client.get(f"{api_url}/api/v1/workflows", params=params)
                if response.status_code == 200:
                    return response.json()
                else:
                    # Fallback if endpoint not implemented
                    return {"workflows": []}
        
        workflows_data = asyncio.run(get_workflows_async())
        workflows = workflows_data.get("workflows", [])
        
        if format == 'json':
            import json
            console.print(json.dumps(workflows, indent=2, default=str))
        else:
            if not workflows:
                console.print(f"{CLIStyle.INFO} No workflows found")
                if status_filter or search or network:
                    console.print(f"{CLIStyle.INFO} Try removing filters or check API endpoint availability")
            else:
                format_workflow_list(workflows)
        
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, "workflow list")
    except Exception as e:
        format_error("Failed to list workflows", str(e))


# ============================================================================
# COMMAND GROUP: CONTRACT
# ============================================================================

@cli.group()
def contract():
    """Contract management commands"""
    pass


@contract.command()
@click.option('--contract-id', '-c', required=True, help='Contract ID')
@click.option('--format', '-f', type=click.Choice(['code', 'abi', 'both']), default='code', help='Output format')
def view(contract_id: str, format: str):
    """[*] View contract code or ABI"""
    try:
        api_url = get_api_url()
        
        async def get_contract_async():
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{api_url}/api/v1/contracts/{contract_id}")
                response.raise_for_status()
                return response.json()
        
        contract_data = asyncio.run(get_contract_async())
        
        if format in ['code', 'both']:
            source_code = contract_data.get("source_code")
            if source_code:
                format_contract_code(source_code)
            else:
                console.print(f"{CLIStyle.WARNING} Contract code not available")
        
        if format in ['abi', 'both']:
            abi = contract_data.get("abi")
            if abi:
                import json
                console.print("\n[bold blue]ABI:[/bold blue]")
                console.print(json.dumps(abi, indent=2))
            else:
                console.print(f"{CLIStyle.WARNING} ABI not available")
        
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, f"contract {contract_id}")
    except Exception as e:
        format_error("Failed to get contract", str(e))


@contract.command()
@click.option('--file', '-f', type=click.File('r'), help='Solidity file to audit')
@click.option('--contract-id', '-c', help='Contract ID to audit')
@click.option('--level', '-l', type=click.Choice(['basic', 'standard', 'comprehensive']), default='standard', help='Audit depth')
def audit(file: Optional[click.File], contract_id: Optional[str], level: str):
    """[SEC] Run security audit on contract"""
    if not file and not contract_id:
        format_error("Either --file or --contract-id must be provided",
                    suggestions=["Provide --file with path to Solidity file",
                                "Or provide --contract-id of existing contract"])
        return
    
    console.print(f"{CLIStyle.INFO} Running {level} security audit...")
    
    try:
        api_url = get_api_url()
        contract_code = None
        
        if file:
            contract_code = file.read()
        elif contract_id:
            # Fetch contract source code from API
            async def get_contract_async():
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{api_url}/api/v1/contracts/{contract_id}")
                    response.raise_for_status()
                    return response.json()
            
            contract_data = asyncio.run(get_contract_async())
            contract_code = contract_data.get("source_code")
            
            if not contract_code:
                format_error("Contract source code not found",
                            suggestions=["Verify contract ID is correct",
                                        "Contract may not have source code stored"])
                return
        
        # Call audit API
        async def audit_async():
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{api_url}/api/v1/contracts/audit",
                    json={
                        "contract_code": contract_code,
                        "audit_level": level
                    }
                )
                response.raise_for_status()
                return response.json()
        
        audit_result = asyncio.run(audit_async())
        format_audit_report(audit_result)
        
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, f"contract audit")
    except Exception as e:
        format_error("Failed to run audit", str(e))


@contract.command()
@click.option('--contract-id', '-c', required=True, help='Contract ID to test')
@click.option('--framework', '-f', type=click.Choice(['foundry', 'hardhat']), default='foundry', help='Test framework')
def test(contract_id: str, framework: str):
    """[TEST] Run tests on contract"""
    console.print(f"{CLIStyle.INFO} Running tests with {framework}...")
    console.print(f"{CLIStyle.WAIT} Test API endpoint not yet implemented")
    # TODO: Implement when test endpoint is available


# ============================================================================
# COMMAND GROUP: DEPLOYMENT
# ============================================================================

@cli.group()
def deployment():
    """Deployment management commands"""
    pass


@deployment.command()
@click.option('--contract-id', '-c', required=True, help='Contract ID to deploy')
@click.option('--network', '-n', type=click.Choice(['hyperion_testnet', 'hyperion_mainnet', 'mantle_testnet', 'mantle_mainnet']), required=True, help='Target network')
@click.option('--private-key', '-k', help='Private key for deployment (or use config)')
@click.option('--constructor-args', help='Constructor arguments as JSON array (e.g., \'[1000000, "0x123..."]\')')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def deploy(contract_id: str, network: str, private_key: Optional[str], constructor_args: Optional[str], confirm: bool):
    """[>] Deploy contract to blockchain"""
    if not confirm:
        if not click.confirm(f"Deploy contract {contract_id} to {network}?"):
            return
    
    console.print(f"{CLIStyle.INFO} Deploying contract to {network}...")
    
    try:
        api_url = get_api_url()
        
        # Fetch contract data from API
        async def get_contract_async():
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{api_url}/api/v1/contracts/{contract_id}")
                response.raise_for_status()
                return response.json()
        
        contract_data = asyncio.run(get_contract_async())
        
        # Get compiled contract (bytecode and ABI)
        compiled_contract = {
            "bytecode": contract_data.get("bytecode", ""),
            "abi": contract_data.get("abi", [])
        }
        
        if not compiled_contract.get("bytecode"):
            format_error("Contract bytecode not found",
                        suggestions=["Contract may not be compiled",
                                    "Verify contract ID is correct"])
            return
        
        # Parse constructor args if provided
        constructor_args_list = []
        if constructor_args:
            try:
                import json
                constructor_args_list = json.loads(constructor_args)
            except json.JSONDecodeError:
                format_error("Invalid constructor arguments format",
                            suggestions=["Use JSON array format: '[value1, value2]'",
                                        "Example: '[1000000, \"0x123...\"]'"])
                return
        
        # Use private key from config if not provided
        deploy_private_key = private_key or settings.private_key
        if not deploy_private_key:
            format_error("Private key required",
                        suggestions=["Provide --private-key option",
                                    "Or set PRIVATE_KEY in environment/config"])
            return
        
        # Deploy contract
        async def deploy_async():
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{api_url}/api/v1/deployments/deploy",
                    json={
                        "compiled_contract": compiled_contract,
                        "network": network,
                        "private_key": deploy_private_key,
                        "constructor_args": constructor_args_list
                    }
                )
                response.raise_for_status()
                return response.json()
        
        with Progress(
            *create_progress_columns(),
            console=console
        ) as progress:
            task = progress.add_task(f"{CLIStyle.WAIT} Deploying contract...", total=None)
            deployment_result = asyncio.run(deploy_async())
            progress.update(task, completed=True)
        
        # Display deployment result
        format_deployment_confirmation(deployment_result)
        
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, f"contract deployment")
    except Exception as e:
        format_error("Failed to deploy contract", str(e))


@deployment.command()
@click.option('--contracts-file', '-f', type=click.File('r'), required=True, help='JSON file with contracts to deploy')
@click.option('--network', '-n', type=click.Choice(['hyperion_testnet', 'hyperion_mainnet', 'mantle_testnet', 'mantle_mainnet']), required=True, help='Target network')
@click.option('--use-pef', is_flag=True, default=True, help='Use Hyperion PEF for parallel deployment (Hyperion only)')
@click.option('--max-parallel', type=int, default=10, help='Maximum parallel deployments')
@click.option('--private-key', '-k', help='Private key for deployment (or use config)')
def batch(contracts_file: click.File, network: str, use_pef: bool, max_parallel: int, private_key: Optional[str]):
    """[>] Deploy multiple contracts in parallel using PEF"""
    import json
    
    try:
        contracts_data = json.load(contracts_file)
        contracts = contracts_data.get("contracts", [])
        
        if not contracts:
            format_error("No contracts found in file", "File must contain 'contracts' array")
            return
        
        console.print(f"{CLIStyle.INFO} Deploying {len(contracts)} contracts to {network}...")
        if use_pef and network.startswith("hyperion"):
            console.print(f"{CLIStyle.INFO} Using PEF for parallel deployment (max: {max_parallel})")
        else:
            console.print(f"{CLIStyle.INFO} Using sequential deployment")
        
        api_url = get_api_url()
        
        async def deploy_batch_async():
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{api_url}/api/v1/deployments/batch",
                    json={
                        "contracts": contracts,
                        "use_pef": use_pef,
                        "max_parallel": max_parallel,
                        "private_key": private_key
                    }
                )
                response.raise_for_status()
                return response.json()
        
        with Progress(
            *create_progress_columns(),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"{CLIStyle.WAIT} Deploying batch...", total=None)
            result = asyncio.run(deploy_batch_async())
            progress.update(task, completed=True)
        
        # Display results
        console.print(f"\n{CLIStyle.SUCCESS} Batch deployment completed")
        console.print(f"{CLIStyle.INFO} Total time: {result.get('total_time', 0):.2f}s")
        console.print(f"{CLIStyle.INFO} Success: {result.get('success_count', 0)}")
        console.print(f"{CLIStyle.INFO} Failed: {result.get('failed_count', 0)}")
        console.print(f"{CLIStyle.INFO} Parallel count: {result.get('parallel_count', 0)}")
        
        # Display individual results
        for deployment in result.get("deployments", []):
            if deployment["status"] == "success":
                console.print(f"{CLIStyle.SUCCESS} {deployment['contract_name']}: {deployment.get('contract_address', 'N/A')}")
            else:
                console.print(f"{CLIStyle.ERROR} {deployment['contract_name']}: {deployment.get('error', 'Unknown error')}")
        
    except json.JSONDecodeError as e:
        format_error("Invalid JSON file", str(e),
                    suggestions=["Check JSON syntax",
                                "Ensure file contains 'contracts' array",
                                "Validate JSON with: python -m json.tool <file>"])
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, "batch deployment")
    except Exception as e:
        format_error("Failed to deploy batch", str(e))


@deployment.command()
@click.option('--deployment-id', '-d', required=True, help='Deployment ID')
def verify(deployment_id: str):
    """[*] Verify deployment status"""
    try:
        api_url = get_api_url()
        
        async def get_deployment_async():
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{api_url}/api/v1/deployments/{deployment_id}")
                response.raise_for_status()
                return response.json()
        
        deployment_data = asyncio.run(get_deployment_async())
        format_deployment_confirmation(deployment_data)
        
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, f"deployment {deployment_id}")
    except Exception as e:
        format_error("Failed to get deployment", str(e))


@deployment.command()
@click.option('--deployment-id', '-d', help='Deployment ID')
@click.option('--contract-address', '-a', help='Contract address (if not using deployment-id)')
@click.option('--function', '-f', required=True, help='Function name to call')
@click.option('--args', help='Function arguments as JSON array')
@click.option('--network', '-n', type=click.Choice(['hyperion_testnet', 'hyperion_mainnet', 'mantle_testnet', 'mantle_mainnet']), help='Network (if not using deployment-id)')
@click.option('--value', '-v', help='ETH value to send (for payable functions)')
def interact(deployment_id: Optional[str], contract_address: Optional[str], function: str, args: Optional[str], network: Optional[str], value: Optional[str]):
    """[*] Interact with deployed contract"""
    if not deployment_id and not contract_address:
        format_error("Either --deployment-id or --contract-address must be provided",
                    suggestions=["Provide --deployment-id of existing deployment",
                                "Or provide --contract-address and --network"])
        return
    
    console.print(f"{CLIStyle.INFO} Calling {function} on contract...")
    
    try:
        api_url = get_api_url()
        contract_addr = contract_address
        deploy_network = network
        
        if deployment_id:
            # Fetch deployment data
            async def get_deployment_async():
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{api_url}/api/v1/deployments/{deployment_id}")
                    response.raise_for_status()
                    return response.json()
            
            deployment_data = asyncio.run(get_deployment_async())
            contract_addr = deployment_data.get("contract_address")
            deploy_network = deployment_data.get("network")
            
            if not contract_addr:
                format_error("Contract address not found",
                            suggestions=["Verify deployment ID is correct"])
                return
        
        if not contract_addr or not deploy_network:
            format_error("Contract address and network required",
                        suggestions=["Provide both --contract-address and --network",
                                    "Or use --deployment-id"])
            return
        
        # Parse function arguments
        function_args = []
        if args:
            try:
                import json
                function_args = json.loads(args)
            except json.JSONDecodeError:
                format_error("Invalid function arguments format",
                            suggestions=["Use JSON array format: '[value1, value2]'",
                                        "Example: '[\"0x123...\", 1000]'"])
                return
        
        console.print(f"{CLIStyle.INFO} Contract: {contract_addr}")
        console.print(f"{CLIStyle.INFO} Network: {deploy_network}")
        console.print(f"{CLIStyle.INFO} Function: {function}")
        if function_args:
            console.print(f"{CLIStyle.INFO} Arguments: {function_args}")
        if value:
            console.print(f"{CLIStyle.INFO} Value: {value} ETH")
        
        console.print(f"\n{CLIStyle.WARNING} Contract interaction API not yet implemented")
        console.print(f"{CLIStyle.INFO} Use Web3.py or ethers.js to interact with contract directly")
        if deployment_id:
            console.print(f"{CLIStyle.INFO} Contract ABI available via: hyperagent contract view {deployment_data.get('contract_id', '')}")
        
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, f"deployment {deployment_id or 'interaction'}")
    except Exception as e:
        format_error("Failed to interact with contract", str(e))


# ============================================================================
# COMMAND GROUP: SYSTEM
# ============================================================================

@cli.group()
def system():
    """System commands"""
    pass


@system.command()
def health():
    """[*] Check system health"""
    console.print(f"{CLIStyle.INFO} Checking system health...")
    
    try:
        api_url = get_api_url()
        
        async def check_health_async():
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{api_url}/api/v1/health/")
                response.raise_for_status()
                return response.json()
        
        health_data = asyncio.run(check_health_async())
        
        status = health_data.get("status", "unknown")
        if status == "healthy":
            console.print(f"{CLIStyle.SUCCESS} API: Healthy")
        else:
            console.print(f"{CLIStyle.WARNING} API: {status}")
        
    except httpx.RequestError:
        console.print(f"{CLIStyle.ERROR} API: Not reachable")
    except Exception as e:
        console.print(f"{CLIStyle.ERROR} Health check failed: {e}")


@system.command()
def version():
    """[*] Display version information"""
    console.print(f"HyperAgent v1.0.0")
    console.print(f"Python: 3.10+")
    console.print(f"Web3: Enabled (Hyperion + Mantle)")
    console.print(f"LLM: Gemini (OpenAI Fallback)")


@system.command()
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish']), required=True, help='Shell type')
def install_completion(shell: str):
    """[*] Install shell completion"""
    import os
    from pathlib import Path
    
    script_path = Path(__file__).parent.parent.parent / "scripts" / "completion" / f"{shell}.sh"
    
    if not script_path.exists():
        format_error(f"Completion script not found: {script_path}")
        return
    
    console.print(f"{CLIStyle.INFO} Installation instructions for {shell}:")
    console.print()
    
    if shell == "bash":
        console.print(f"  Add to ~/.bashrc:")
        console.print(f"    source {script_path.absolute()}")
        console.print()
        console.print(f"  Or run:")
        console.print(f"    echo 'source {script_path.absolute()}' >> ~/.bashrc")
    elif shell == "zsh":
        console.print(f"  Add to ~/.zshrc:")
        console.print(f"    source {script_path.absolute()}")
        console.print()
        console.print(f"  Or run:")
        console.print(f"    echo 'source {script_path.absolute()}' >> ~/.zshrc")
    elif shell == "fish":
        fish_completions = Path.home() / ".config" / "fish" / "completions"
        fish_completions.mkdir(parents=True, exist_ok=True)
        target = fish_completions / "hyperagent.fish"
        
        try:
            import shutil
            shutil.copy(script_path, target)
            format_success(f"Completion installed to {target}")
            console.print(f"{CLIStyle.INFO} Restart your shell or run: source {target}")
        except Exception as e:
            format_error(f"Failed to install completion: {e}",
                        suggestions=[f"Manually copy {script_path} to {target}"])


@cli.group()
def network():
    """Network information and compatibility commands"""
    pass


@network.command()
def list():
    """[*] List all supported networks"""
    from hyperagent.blockchain.network_features import NetworkFeatureManager, NetworkFeature
    
    console.print(f"\n{CLIStyle.INFO} Supported Networks:\n")
    
    for network_name in NetworkFeatureManager.list_networks():
        config = NetworkFeatureManager.get_network_config(network_name)
        features = NetworkFeatureManager.get_features(network_name)
        
        # Count available features
        available = sum(1 for f, supported in features.items() if supported)
        total = len(features)
        
        console.print(f"  {CLIStyle.SUCCESS}{network_name}")
        console.print(f"    Chain ID: {config.get('chain_id', 'N/A')}")
        console.print(f"    Currency: {config.get('currency', 'N/A')}")
        console.print(f"    Features: {available}/{total} available\n")


@network.command()
@click.argument('network_name')
def info(network_name: str):
    """[*] Show network features and capabilities"""
    from hyperagent.blockchain.network_features import (
        NetworkFeatureManager,
        NetworkFeature,
        NETWORK_FEATURES
    )
    
    if network_name not in NETWORK_FEATURES:
        console.print(f"{CLIStyle.ERROR} Network '{network_name}' not found")
        console.print(f"{CLIStyle.INFO} Use 'hyperagent network list' to see available networks")
        return
    
    config = NetworkFeatureManager.get_network_config(network_name)
    features = NetworkFeatureManager.get_features(network_name)
    
    console.print(f"\n{CLIStyle.INFO} Network: {network_name}")
    console.print(f"  Chain ID: {config.get('chain_id', 'N/A')}")
    console.print(f"  Currency: {config.get('currency', 'N/A')}")
    console.print(f"  RPC URL: {config.get('rpc_url', 'N/A')}")
    console.print(f"  Explorer: {config.get('explorer', 'N/A')}")
    
    console.print(f"\n{CLIStyle.INFO} Available Features:")
    feature_names = {
        NetworkFeature.PEF: "PEF (Parallel Execution Framework)",
        NetworkFeature.METISVM: "MetisVM Optimizations",
        NetworkFeature.EIGENDA: "EigenDA",
        NetworkFeature.BATCH_DEPLOYMENT: "Batch Deployment",
        NetworkFeature.FLOATING_POINT: "Floating-Point Operations",
        NetworkFeature.AI_INFERENCE: "AI Inference"
    }
    
    for feature, supported in features.items():
        status = CLIStyle.SUCCESS + "[+]" if supported else CLIStyle.ERROR + "[-]"
        console.print(f"  {status} {feature_names.get(feature, feature.value)}")
    
    # Show fallbacks
    console.print(f"\n{CLIStyle.INFO} Fallbacks:")
    for feature in NetworkFeature:
        if not features.get(feature, False):
            fallback = NetworkFeatureManager.get_fallback_strategy(network_name, feature)
            if fallback:
                console.print(f"  - {feature_names.get(feature, feature.value)}: {fallback}")


@network.command()
@click.argument('network_name')
def features(network_name: str):
    """[*] Show available features for a network"""
    from hyperagent.blockchain.network_features import (
        NetworkFeatureManager,
        NetworkFeature,
        NETWORK_FEATURES
    )
    
    if network_name not in NETWORK_FEATURES:
        console.print(f"{CLIStyle.ERROR} Network '{network_name}' not found")
        return
    
    features = NetworkFeatureManager.get_features(network_name)
    
    console.print(f"\n{CLIStyle.INFO} Features for {network_name}:\n")
    
    feature_descriptions = {
        NetworkFeature.PEF: "Parallel Execution Framework - 10-50x faster batch deployments",
        NetworkFeature.METISVM: "MetisVM optimizations - floating-point, AI inference, GPU acceleration",
        NetworkFeature.EIGENDA: "EigenDA data availability - cost-efficient metadata storage",
        NetworkFeature.BATCH_DEPLOYMENT: "Batch deployment support - deploy multiple contracts",
        NetworkFeature.FLOATING_POINT: "Floating-point operations - native decimal support",
        NetworkFeature.AI_INFERENCE: "On-chain AI inference - run ML models on-chain"
    }
    
    for feature, supported in features.items():
        status = "Available" if supported else "Not Available"
        style = CLIStyle.SUCCESS if supported else CLIStyle.WARNING
        console.print(f"  {style}{feature.value}: {status}")
        if feature_descriptions.get(feature):
            console.print(f"    {feature_descriptions[feature]}")


@network.command()
@click.argument('network_name')
def test(network_name: str):
    """[*] Test network connectivity and features"""
    from hyperagent.blockchain.network_features import NetworkFeatureManager, NetworkFeature
    from hyperagent.blockchain.networks import NetworkManager
    from rich.table import Table
    
    console.print(f"\n{CLIStyle.INFO} Testing network: {network_name}\n")
    
    table = Table(title="Network Test Results")
    table.add_column("Test", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    # Test 1: Network exists
    try:
        config = NetworkFeatureManager.get_network_config(network_name)
        table.add_row("Network Configuration", "[green][+] Found[/green]", f"Chain ID: {config.get('chain_id', 'N/A')}")
    except:
        table.add_row("Network Configuration", "[red][-] Not Found[/red]", "Network not in registry")
        console.print(table)
        return
    
    # Test 2: RPC connectivity
    try:
        network_manager = NetworkManager()
        w3 = network_manager.get_web3(network_name)
        block_number = w3.eth.block_number
        table.add_row("RPC Connectivity", "[green][+] Connected[/green]", f"Latest block: {block_number}")
    except Exception as e:
        table.add_row("RPC Connectivity", "[red][-] Failed[/red]", str(e)[:50])
    
    # Test 3: Feature availability
    features = NetworkFeatureManager.get_features(network_name)
    available = sum(1 for f, supported in features.items() if supported)
    total = len(features)
    table.add_row("Features", f"[green][+] {available}/{total}[/green]", f"{available} features available")
    
    # Test 4: Wallet balance (if private key configured)
    if settings.private_key:
        try:
            from eth_account import Account
            account = Account.from_key(settings.private_key)
            balance = w3.eth.get_balance(account.address)
            balance_eth = w3.from_wei(balance, 'ether')
            table.add_row("Wallet Balance", "[green][+] Funded[/green]" if balance > 0 else "[yellow][!] Zero[/yellow]", 
                         f"{balance_eth:.6f} ETH")
        except Exception as e:
            table.add_row("Wallet Balance", "[red][-] Error[/red]", str(e)[:50])
    else:
        table.add_row("Wallet Balance", "[yellow][!] Not Configured[/yellow]", "PRIVATE_KEY not set")
    
    console.print(table)


# ============================================================================
# COMMAND GROUP: CONFIG
# ============================================================================

@cli.group()
def config():
    """Configuration management commands"""
    pass


@config.command()
def show():
    """[*] Show current configuration"""
    from rich.table import Table
    
    def mask_sensitive(value: Optional[str]) -> str:
        """Mask sensitive configuration values"""
        if not value:
            return "Not set"
        if len(value) > 10:
            return value[:4] + "..." + value[-4:]
        return "***"
    
    table = Table(title="HyperAgent Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Source", style="yellow")
    
    config_items = [
        ("API Host", settings.api_host, "env"),
        ("API Port", settings.api_port, "env"),
        ("Database URL", mask_sensitive(settings.database_url), "env"),
        ("Gemini API Key", mask_sensitive(settings.gemini_api_key), "env"),
        ("OpenAI API Key", mask_sensitive(settings.openai_api_key), "env"),
        ("Private Key", mask_sensitive(settings.private_key), "env"),
        ("Default Network", getattr(settings, 'default_network', 'N/A'), "env"),
    ]
    
    for name, value, source in config_items:
        table.add_row(name, str(value), source)
    
    console.print(table)


@config.command()
def validate():
    """[*] Validate configuration"""
    from rich.table import Table
    
    table = Table(title="Configuration Validation")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Message", style="yellow")
    
    # Check required settings
    checks = [
        ("Database URL", settings.database_url, "Required for data persistence"),
        ("Gemini API Key", settings.gemini_api_key, "Required for LLM generation"),
        ("Private Key", settings.private_key, "Required for deployments"),
    ]
    
    for name, value, message in checks:
        if value:
            table.add_row(name, "[green][+] Set[/green]", "OK")
        else:
            table.add_row(name, "[red][-] Missing[/red]", message)
    
    # Test API connectivity
    try:
        api_url = get_api_url()
        async def test_api():
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{api_url}/api/v1/health/")
                return response.status_code == 200
        
        if asyncio.run(test_api()):
            table.add_row("API Connectivity", "[green][+] Connected[/green]", "API is reachable")
        else:
            table.add_row("API Connectivity", "[red][-] Failed[/red]", "API not responding")
    except:
        table.add_row("API Connectivity", "[red][-] Failed[/red]", "Cannot connect to API")
    
    console.print(table)


# ============================================================================
# COMMAND GROUP: TEMPLATE
# ============================================================================

@cli.group()
def template():
    """Template management commands"""
    pass


@template.command()
@click.option('--search', '-s', help='Search query')
@click.option('--format', type=click.Choice(['table', 'json']), default='table')
def list(search: Optional[str], format: str):
    """[*] List available templates"""
    try:
        api_url = get_api_url()
        
        async def get_templates_async():
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{api_url}/api/v1/templates"
                if search:
                    url += f"?search={search}"
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        
        templates_data = asyncio.run(get_templates_async())
        # API returns a list directly, not a dict
        if type(templates_data).__name__ == 'list':
            templates = templates_data
        elif type(templates_data).__name__ == 'dict':
            templates = templates_data.get("templates", [])
        else:
            templates = []
        
        if format == 'json':
            import json
            console.print(json.dumps(templates, indent=2, default=str))
        else:
            from rich.table import Table
            table = Table(title="Contract Templates")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Description", style="yellow")
            
            for template in templates:
                table.add_row(
                    template.get("name", "N/A"),
                    template.get("contract_type", "N/A"),
                    template.get("description", "N/A")[:50] + "..." if len(template.get("description", "")) > 50 else template.get("description", "N/A")
                )
            console.print(table)
        
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, "template list")
    except Exception as e:
        format_error("Failed to list templates", str(e))


@template.command()
@click.argument('name')
@click.option('--format', type=click.Choice(['code', 'json', 'both']), default='code')
def show(name: str, format: str):
    """[*] Show template details"""
    try:
        api_url = get_api_url()
        
        async def get_template_async():
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{api_url}/api/v1/templates/{name}")
                response.raise_for_status()
                return response.json()
        
        template_data = asyncio.run(get_template_async())
        
        if format in ['code', 'both']:
            template_code = template_data.get("template_code")
            if template_code:
                format_contract_code(template_code)
            else:
                console.print(f"{CLIStyle.WARNING} Template code not available")
        
        if format in ['json', 'both']:
            import json
            console.print("\n[bold blue]Template Metadata:[/bold blue]")
            console.print(json.dumps(template_data, indent=2, default=str))
        
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, f"template {name}")
    except Exception as e:
        format_error("Failed to get template", str(e))


@template.command()
@click.option('--query', '-q', required=True, help='Search query')
def search(query: str):
    """[?] Search templates"""
    try:
        api_url = get_api_url()
        
        async def search_templates_async():
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Search endpoint uses POST, not GET
                response = await client.post(
                    f"{api_url}/api/v1/templates/search",
                    json={"query": query}
                )
                response.raise_for_status()
                return response.json()
        
        results = asyncio.run(search_templates_async())
        # API returns a list directly, not a dict
        if type(results).__name__ == 'list':
            templates = results
        elif type(results).__name__ == 'dict':
            templates = results.get("templates", [])
        else:
            templates = []
        
        from rich.table import Table
        table = Table(title=f"Search Results: '{query}'")
        table.add_column("Name", style="cyan")
        table.add_column("Similarity", style="green")
        table.add_column("Type", style="yellow")
        
        for template in templates:
            similarity = template.get("similarity", 0)
            table.add_row(
                template.get("name", "N/A"),
                f"{similarity:.2%}" if similarity else "N/A",
                template.get("contract_type", "N/A")
            )
        console.print(table)
        
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, "template search")
    except Exception as e:
        format_error("Failed to search templates", str(e))


# ============================================================================
# COMMAND GROUP: EXPORT/IMPORT
# ============================================================================

@workflow.command()
@click.option('--workflow-id', '-w', required=True)
@click.option('--output', '-o', type=click.Path(), help='Output file (default: stdout)')
@click.option('--format', type=click.Choice(['json', 'yaml']), default='json')
def export(workflow_id: str, output: Optional[str], format: str):
    """[>] Export workflow to file"""
    try:
        api_url = get_api_url()
        
        async def get_workflow_data():
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get workflow
                workflow_resp = await client.get(f"{api_url}/api/v1/workflows/{workflow_id}")
                workflow_resp.raise_for_status()
                workflow_data = workflow_resp.json()
                
                # Get contracts
                contracts_resp = await client.get(f"{api_url}/api/v1/workflows/{workflow_id}/contracts")
                contracts_data = contracts_resp.json() if contracts_resp.status_code == 200 else {"contracts": []}
                
                # Get deployments
                deployments_resp = await client.get(f"{api_url}/api/v1/workflows/{workflow_id}/deployments")
                deployments_data = deployments_resp.json() if deployments_resp.status_code == 200 else {"deployments": []}
                
                return {
                    "workflow": workflow_data,
                    "contracts": contracts_data.get("contracts", []),
                    "deployments": deployments_data.get("deployments", [])
                }
        
        data = asyncio.run(get_workflow_data())
        
        if format == 'json':
            import json
            output_str = json.dumps(data, indent=2, default=str)
        else:
            try:
                import yaml
                output_str = yaml.dump(data, default_flow_style=False, allow_unicode=True)
            except ImportError:
                format_error("YAML format requires PyYAML", "Install with: pip install pyyaml")
                return
        
        if output:
            with open(output, 'w') as f:
                f.write(output_str)
            format_success(f"Workflow exported to {output}")
        else:
            console.print(output_str)
        
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, f"workflow {workflow_id}")
    except Exception as e:
        format_error("Failed to export workflow", str(e))


@contract.command()
@click.option('--contract-id', '-c', required=True)
@click.option('--output', '-o', type=click.Path(), required=True, help='Output file')
def export(contract_id: str, output: str):
    """[>] Export contract code"""
    try:
        api_url = get_api_url()
        
        async def get_contract_async():
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{api_url}/api/v1/contracts/{contract_id}")
                response.raise_for_status()
                return response.json()
        
        contract_data = asyncio.run(get_contract_async())
        source_code = contract_data.get("source_code")
        
        if source_code:
            with open(output, 'w') as f:
                f.write(source_code)
            format_success(f"Contract exported to {output}")
        else:
            format_error("Contract code not available")
        
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, f"contract {contract_id}")
    except Exception as e:
        format_error("Failed to export contract", str(e))


@contract.command()
@click.option('--contract-id', '-c', help='Contract ID to verify')
@click.option('--address', '-a', help='Contract address (if not using contract-id)')
@click.option('--network', '-n', help='Network (if not using contract-id)')
@click.option('--explorer', '-e', type=click.Choice(['etherscan', 'blockscout', 'hyperion', 'mantle']), default='blockscout', help='Explorer to use')
def verify(contract_id: Optional[str], address: Optional[str], network: Optional[str], explorer: str):
    """[*] Verify contract on blockchain explorer"""
    if not contract_id and not address:
        format_error("Either --contract-id or --address must be provided",
                    suggestions=["Provide --contract-id of existing contract",
                                "Or provide --address and --network"])
        return
    
    try:
        api_url = get_api_url()
        
        if contract_id:
            # Fetch contract and deployment data
            async def get_contract_data_async():
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Get contract
                    contract_response = await client.get(f"{api_url}/api/v1/contracts/{contract_id}")
                    contract_response.raise_for_status()
                    contract_data = contract_response.json()
                    
                    # Get deployments for this contract
                    deployments_response = await client.get(
                        f"{api_url}/api/v1/contracts/{contract_id}/deployments"
                    )
                    deployments = []
                    if deployments_response.status_code == 200:
                        deployments = deployments_response.json()
                    
                    return contract_data, deployments
            
            contract_data, deployments = asyncio.run(get_contract_data_async())
            
            if not deployments:
                format_error("No deployments found for contract",
                            suggestions=["Contract may not be deployed yet",
                                        "Deploy contract first: hyperagent deployment deploy"])
                return
            
            # Display verification info
            console.print(f"\n{CLIStyle.INFO} Contract Verification Info:")
            console.print(f"  Contract: {contract_data.get('contract_name', 'N/A')}")
            console.print(f"  Source Code Hash: {contract_data.get('source_code_hash', 'N/A')}")
            
            for deployment in deployments:
                contract_address = deployment.get("contract_address")
                tx_hash = deployment.get("transaction_hash")
                deploy_network = deployment.get("network", "unknown")
                
                console.print(f"\n  Deployment on {deploy_network}:")
                console.print(f"    Address: {contract_address}")
                console.print(f"    Transaction: {tx_hash}")
                
                # Generate explorer URL
                explorer_urls = {
                    "blockscout": f"https://blockscout.com/{deploy_network}/address/{contract_address}",
                    "etherscan": f"https://etherscan.io/address/{contract_address}",
                    "hyperion": f"https://hyperion-testnet-explorer.metisdevops.link/address/{contract_address}",
                    "mantle": f"https://explorer.mantle.xyz/address/{contract_address}"
                }
                
                if explorer in explorer_urls:
                    console.print(f"    Explorer: {explorer_urls[explorer]}")
                else:
                    console.print(f"    {CLIStyle.WARNING} Explorer URL not configured for {explorer}")
        else:
            # Direct address verification
            if not network:
                format_error("Network required when using --address",
                            suggestions=["Provide --network option"])
                return
            
            console.print(f"\n{CLIStyle.INFO} Contract Verification Info:")
            console.print(f"  Address: {address}")
            console.print(f"  Network: {network}")
            
            # Generate explorer URL
            explorer_urls = {
                "blockscout": f"https://blockscout.com/{network}/address/{address}",
                "etherscan": f"https://etherscan.io/address/{address}",
                "hyperion": f"https://hyperion-testnet-explorer.metisdevops.link/address/{address}",
                "mantle": f"https://explorer.mantle.xyz/address/{address}"
            }
            
            if explorer in explorer_urls:
                console.print(f"  Explorer: {explorer_urls[explorer]}")
            else:
                console.print(f"  {CLIStyle.WARNING} Explorer URL not configured for {explorer}")
        
        console.print(f"\n{CLIStyle.INFO} Note: Automatic verification submission not yet implemented")
        console.print(f"{CLIStyle.INFO} Use explorer website to submit source code for verification")
        
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, f"contract verification")
    except Exception as e:
        format_error("Failed to get verification info", str(e))


# ============================================================================
# COMMAND GROUP: QUICK ACTIONS
# ============================================================================

@cli.group()
def quick():
    """Quick action commands"""
    pass


@quick.command()
@click.argument('description')
@click.option('--network', '-n', default='hyperion_testnet', help='Network')
@click.option('--watch', '-w', is_flag=True, help='Watch progress')
def create(description: str, network: str, watch: bool):
    """[>] Quick workflow creation with defaults"""
    # Quick workflow creation - reuse the workflow create logic
    print_banner()
    
    console.print(f"\n{CLIStyle.INFO} Quick workflow creation...")
    console.print(f"{CLIStyle.INFO} Network: {network}")
    console.print(f"{CLIStyle.INFO} Description: {description[:60]}...")
    
    try:
        api_url = get_api_url()
        
        async def create_workflow_async():
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{api_url}/api/v1/workflows/generate",
                    json={
                        "nlp_input": description,
                        "network": network,
                        "contract_type": "Custom",
                        "skip_audit": False,
                        "skip_deployment": False,
                        "optimize_for_metisvm": False,
                        "enable_floating_point": False,
                        "enable_ai_inference": False
                    }
                )
                response.raise_for_status()
                return response.json()
        
        with Progress(
            *create_progress_columns(),
            console=console
        ) as progress:
            task = progress.add_task(f"{CLIStyle.WAIT} Creating workflow...", total=None)
            result = asyncio.run(create_workflow_async())
            progress.update(task, completed=True)
        
        workflow_id = result.get("workflow_id")
        
        if watch:
            monitor_workflow_progress(workflow_id, api_url)
        else:
            format_success(
                f"Workflow created: {workflow_id}",
                f"Status: {result.get('status')}\nUse 'hyperagent workflow status --workflow-id {workflow_id}' to check progress"
            )
        
    except httpx.RequestError as e:
        format_error("Failed to connect to API", str(e),
                    suggestions=["Check if API server is running: hyperagent system health"])
    except httpx.HTTPStatusError as e:
        handle_api_error(e, "quick workflow creation")
    except Exception as e:
        format_error("Failed to create workflow", str(e))


# ============================================================================
# COMMAND GROUP: STATS
# ============================================================================

@cli.group()
def stats():
    """Statistics and analytics"""
    pass


@stats.command()
def show():
    """[*] Show usage statistics"""
    try:
        api_url = get_api_url()
        
        async def get_stats_async():
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try to get stats from API if endpoint exists
                try:
                    response = await client.get(f"{api_url}/api/v1/stats")
                    if response.status_code == 200:
                        return response.json()
                except:
                    pass
                return None
        
        stats_data = asyncio.run(get_stats_async())
        
        if stats_data:
            from rich.table import Table
            table = Table(title="Usage Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in stats_data.items():
                table.add_row(key.replace('_', ' ').title(), str(value))
            console.print(table)
        else:
            console.print(f"{CLIStyle.INFO} Statistics endpoint not available")
            console.print(f"{CLIStyle.INFO} Query database directly for statistics")
        
    except Exception as e:
        format_error("Failed to get statistics", str(e))


if __name__ == '__main__':
    cli()

