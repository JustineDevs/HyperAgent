"""Deployment service implementation"""
from typing import Dict, Any, List, Optional
import logging
import asyncio
from web3 import Web3
from eth_account import Account
from hyperagent.core.agent_system import ServiceInterface
from hyperagent.blockchain.networks import NetworkManager
from hyperagent.blockchain.alith_client import AlithClient
from hyperagent.blockchain.eigenda_client import EigenDAClient
from hyperagent.core.config import settings

logger = logging.getLogger(__name__)


class DeploymentService(ServiceInterface):
    """On-chain smart contract deployment service"""
    
    def __init__(self, network_manager: NetworkManager,
                 alith_client: AlithClient,
                 eigenda_client: EigenDAClient,
                 use_alith_autonomous: bool = False,
                 use_pef: bool = False):
        """
        Initialize deployment service
        
        Args:
            network_manager: Network manager for Web3 operations
            alith_client: Alith client for optional autonomous deployment
            eigenda_client: EigenDA client for Mantle deployments
            use_alith_autonomous: If True, use Alith tool calling for autonomous deployment
            use_pef: If True, use Hyperion PEF for parallel batch deployments
        """
        self.network_manager = network_manager
        self.alith_client = alith_client
        self.eigenda_client = eigenda_client
        self.use_alith_autonomous = use_alith_autonomous
        self.use_pef = use_pef
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy contract to blockchain
        
        Concept: Build, sign, send, and confirm transaction
        Logic:
            1. Validate deployment requirements (if enabled)
            2. Optionally use Alith autonomous deployment (if enabled)
            3. Otherwise: Get Web3 instance, build transaction, estimate gas, sign, send
            4. Wait for confirmation
            5. Return deployment details
        """
        compiled = input_data.get("compiled_contract")
        network = input_data.get("network")
        private_key = input_data.get("private_key") or settings.private_key
        
        # Validate deployment requirements if enabled
        if settings.enable_deployment_validation:
            try:
                validation_result = await self.validate_deployment_requirements(
                    network,
                    private_key
                )
                logger.info(f"Deployment validation passed: {validation_result}")
            except ValueError as e:
                logger.error(f"Deployment validation failed: {e}")
                raise ValueError(f"Deployment validation failed: {e}")
        
        # Optionally use Alith autonomous deployment
        if self.use_alith_autonomous and self.alith_client.is_sdk_available():
            return await self._deploy_via_alith(compiled, network, private_key)
        
        # Standard manual deployment
        if not private_key:
            raise ValueError("Private key required for deployment")
        
        source_code = input_data.get("source_code")
        constructor_args = input_data.get("constructor_args", [])
        return await self._deploy_manual_with_retry(compiled, network, private_key, source_code, constructor_args)
    
    async def validate(self, data: Dict[str, Any]) -> bool:
        """Validate deployment input"""
        return bool(data.get("compiled_contract") and data.get("network"))
    
    async def _deploy_via_alith(
        self,
        compiled: Dict[str, Any],
        network: str,
        private_key: str
    ) -> Dict[str, Any]:
        """
        Deploy contract using Alith autonomous agent with tool calling
        
        Concept: Use Alith agent to autonomously deploy contract
        Logic:
            1. Initialize deployment agent with tools
            2. Agent calls deploy_contract tool
            3. Tool handler executes deployment
            4. Return results
        """
        try:
            from hyperagent.blockchain.alith_tools import (
                get_deployment_tools,
                AlithToolHandler
            )
            
            # Initialize tool handler
            tool_handler = AlithToolHandler(
                network_manager=self.network_manager,
                eigenda_client=self.eigenda_client,
                private_key=private_key
            )
            
            # Get deployment tools
            tools = get_deployment_tools()
            
            # Initialize or get deployment agent
            agent_name = "autonomous_deployer"
            if agent_name not in self.alith_client.list_agents():
                await self.alith_client.initialize_agent(
                    name=agent_name,
                    preamble="You are an autonomous smart contract deployment agent. Use the deploy_contract tool to deploy contracts to the blockchain."
                )
            
            # Execute agent with tools
            bytecode = compiled.get("bytecode", "")
            abi = compiled.get("abi", [])
            
            prompt = f"Deploy this contract to {network}. Bytecode: {bytecode[:100]}..."
            
            result = await self.alith_client.execute_agent_with_tools(
                agent_name=agent_name,
                prompt=prompt,
                tools=tools,
                context={
                    "bytecode": bytecode,
                    "abi": abi,
                    "network": network
                },
                tool_handler=tool_handler
            )
            
            # Extract deployment result from tool execution
            if result.get("success") and result.get("tool_results"):
                for tool_result in result["tool_results"]:
                    if tool_result.get("tool") == "deploy_contract":
                        deploy_result = tool_result.get("result", {})
                        if deploy_result.get("success"):
                            return {
                                "status": "success",
                                "contract_address": deploy_result.get("contract_address"),
                                "transaction_hash": deploy_result.get("transaction_hash"),
                                "block_number": deploy_result.get("block_number"),
                                "gas_used": deploy_result.get("gas_used"),
                                "eigenda_commitment": deploy_result.get("eigenda_commitment"),
                                "deployment_method": "alith_autonomous"
                            }
                        else:
                            raise ValueError(f"Alith deployment failed: {deploy_result.get('error')}")
            
            # Fallback to manual deployment if Alith didn't execute tool
            logger.warning("Alith agent did not execute deploy_contract tool, falling back to manual deployment")
            return await self._deploy_manual(compiled, network, private_key)
            
        except Exception as e:
            logger.error(f"Alith autonomous deployment failed: {e}, falling back to manual", exc_info=True)
            return await self._deploy_manual(compiled, network, private_key)
    
    async def validate_deployment_requirements(
        self,
        network: str,
        private_key: str
    ) -> Dict[str, Any]:
        """
        Validate deployment requirements before attempting deployment
        
        Checks:
        1. RPC endpoint is reachable
        2. Wallet has sufficient balance
        3. Network chain ID matches
        4. Gas price is reasonable
        
        Args:
            network: Target network name
            private_key: Private key for deployment
        
        Returns:
            Validation result dictionary
        
        Raises:
            ValueError: If validation fails
        """
        w3 = self.network_manager.get_web3(network)
        account = Account.from_key(private_key)
        
        # Check RPC connectivity
        try:
            latest_block = w3.eth.get_block('latest')
        except Exception as e:
            raise ValueError(f"RPC endpoint unreachable for {network}: {e}")
        
        # Check wallet balance
        balance = w3.eth.get_balance(account.address)
        if balance == 0:
            raise ValueError(
                f"Wallet {account.address} has zero balance. "
                f"Please fund the wallet before deployment."
            )
        
        # Check minimum balance
        min_balance_wei = w3.to_wei(settings.min_wallet_balance_eth, 'ether')
        if balance < min_balance_wei:
            balance_eth = float(w3.from_wei(balance, 'ether'))
            logger.warning(
                f"Wallet balance low: {balance_eth} ETH. "
                f"Minimum recommended: {settings.min_wallet_balance_eth} ETH"
            )
        
        # Verify chain ID
        network_config = self.network_manager.get_network_config(network)
        expected_chain_id = network_config.get("chain_id")
        actual_chain_id = w3.eth.chain_id
        
        if expected_chain_id and actual_chain_id != expected_chain_id:
            logger.warning(
                f"Chain ID mismatch: expected {expected_chain_id}, got {actual_chain_id}"
            )
        
        return {
            "rpc_connected": True,
            "wallet_address": account.address,
            "balance_wei": balance,
            "balance_eth": float(w3.from_wei(balance, 'ether')),
            "chain_id": actual_chain_id,
            "latest_block": latest_block['number'],
            "validation_passed": True
        }
    
    async def _deploy_manual_with_retry(
        self,
        compiled: Dict[str, Any],
        network: str,
        private_key: str,
        source_code: Optional[str] = None,
        constructor_args: Optional[List[Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Deploy with automatic retry on network failures
        
        Args:
            compiled: Compiled contract data
            network: Target network
            private_key: Private key
            source_code: Optional source code
            constructor_args: Optional constructor arguments
            max_retries: Maximum retry attempts
        
        Returns:
            Deployment result
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await self._deploy_manual(compiled, network, private_key, source_code, constructor_args)
            except (ConnectionError, TimeoutError, ValueError) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"Deployment failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    import asyncio
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Deployment failed after {max_retries} attempts: {e}")
                    raise
        
        # Should not reach here, but just in case
        raise last_exception or ValueError("Deployment failed")
    
    async def _deploy_manual(
        self,
        compiled: Dict[str, Any],
        network: str,
        private_key: str,
        source_code: Optional[str] = None,
        constructor_args: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Manual deployment (original implementation)
        
        This is the fallback method when Alith autonomous deployment is not used or fails
        """
        # Get Web3 instance
        w3 = self.network_manager.get_web3(network)
        account = Account.from_key(private_key)
        
        # Build contract
        contract = w3.eth.contract(
            abi=compiled.get("abi", []),
            bytecode=compiled.get("bytecode", "0x")
        )
        
        # Extract constructor ABI to determine if arguments are required
        constructor_abi = None
        constructor_inputs = []
        for item in compiled.get("abi", []):
            if item.get("type") == "constructor":
                constructor_abi = item
                constructor_inputs = item.get("inputs", [])
                break
        
        logger.debug(f"Constructor ABI found: {constructor_abi is not None}, inputs: {len(constructor_inputs)}")
        logger.debug(f"Constructor args provided: {constructor_args is not None}, count: {len(constructor_args) if constructor_args else 0}")
        
        # Validate constructor arguments
        needs_args = len(constructor_inputs) > 0
        
        if needs_args:
            # Constructor requires arguments
            if constructor_args is None:
                expected_types = [inp.get("type", "unknown") for inp in constructor_inputs]
                raise ValueError(
                    f"Constructor requires {len(constructor_inputs)} arguments but none provided. "
                    f"Expected types: {expected_types}. "
                    f"Please ensure constructor_args are generated and passed correctly."
                )
            elif len(constructor_args) == 0:
                expected_types = [inp.get("type", "unknown") for inp in constructor_inputs]
                raise ValueError(
                    f"Constructor requires {len(constructor_inputs)} arguments but empty list provided. "
                    f"Expected types: {expected_types}. "
                    f"Please check constructor value generation in GenerationAgent."
                )
            elif len(constructor_args) != len(constructor_inputs):
                expected_types = [inp.get("type", "unknown") for inp in constructor_inputs]
                raise ValueError(
                    f"Constructor argument count mismatch: expected {len(constructor_inputs)}, got {len(constructor_args)}. "
                    f"Expected types: {expected_types}. "
                    f"Provided values: {constructor_args}. "
                    f"Please verify constructor_args generation matches constructor signature."
                )
            # Validation passed - use constructor with args
            logger.debug(f"Using constructor with {len(constructor_args)} arguments: {constructor_args}")
            constructor = contract.constructor(*constructor_args)
        else:
            # Constructor doesn't require arguments
            if constructor_args and len(constructor_args) > 0:
                logger.warning(f"Constructor doesn't require arguments but {len(constructor_args)} provided. Ignoring.")
            logger.debug("Using constructor without arguments")
            constructor = contract.constructor()
        
        # Estimate gas
        try:
            gas_estimate = constructor.estimate_gas({
                "from": account.address
            })
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Gas estimation failed: {e}")
            
            # Provide detailed error message for constructor argument issues
            if "Incorrect argument count" in error_msg or "Expected" in error_msg:
                expected_types = [inp.get("type", "unknown") for inp in constructor_inputs] if constructor_inputs else []
                provided_count = len(constructor_args) if constructor_args else 0
                raise ValueError(
                    f"Gas estimation failed due to constructor argument mismatch: {error_msg}. "
                    f"Constructor requires {len(constructor_inputs)} arguments ({expected_types}), "
                    f"but {provided_count} were provided. "
                    f"Constructor args received: {constructor_args}. "
                    f"Please check that constructor_args are correctly generated and passed through the pipeline."
                )
            raise ValueError(f"Gas estimation failed: {e}")
        
        # Get gas price (EIP-1559 support)
        network_config = self.network_manager.get_network_config(network)
        chain_id = network_config.get("chain_id")
        
        try:
            # Try EIP-1559 first
            fee_data = w3.eth.fee_history(1, "latest")
            base_fee = fee_data["baseFeePerGas"][0]
            max_priority_fee = w3.to_wei(2, "gwei")
            gas_price = base_fee + max_priority_fee
        except Exception:
            # Fallback to legacy gas price
            gas_price = w3.eth.gas_price
        
        # Build transaction
        tx = constructor.build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": int(gas_estimate * 1.2),  # 20% buffer
            "gasPrice": gas_price,
            "chainId": chain_id
        })
        
        # Sign and send
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        logger.info(f"Deployment transaction sent: {tx_hash.hex()}")
        
        # Wait for confirmation
        receipt = w3.eth.wait_for_transaction_receipt(
            tx_hash,
            timeout=300,
            poll_latency=2
        )
        
        # Calculate costs
        total_cost_wei = receipt["gasUsed"] * gas_price
        total_cost_eth = w3.from_wei(total_cost_wei, "ether")
        
        # Enhanced EigenDA integration (with feature check)
        # Note: EigenDA storage is done asynchronously to avoid blocking status updates
        # The deployment is considered successful immediately after on-chain confirmation
        eigenda_commitment = None
        eigenda_metadata_stored = False
        
        # Return deployment result immediately (EigenDA storage happens in background if needed)
        deployment_result = {
            "status": "success",
            "contract_address": receipt["contractAddress"],
            "deployer_address": account.address,
            "transaction_hash": tx_hash.hex(),
            "block_number": receipt["blockNumber"],
            "gas_used": receipt["gasUsed"],
            "gas_price": gas_price,
            "total_cost_wei": total_cost_wei,
            "total_cost_eth": float(total_cost_eth),
            "eigenda_commitment": None,  # Will be set by background task
            "eigenda_metadata_stored": False,  # Will be set by background task
            "deployment_method": "manual"
        }
        
        # Store EigenDA metadata in background (non-blocking)
        # This allows the workflow status to update immediately
        from hyperagent.blockchain.network_features import (
            NetworkFeatureManager,
            NetworkFeature
        )
        
        if (NetworkFeatureManager.supports_feature(network, NetworkFeature.EIGENDA) 
            and self.eigenda_client):
            # Run EigenDA storage in background task to avoid blocking
            # This allows deployment to return immediately while EigenDA storage happens async
            try:
                # Create background task (non-blocking)
                # The task will run in the background and update deployment_result when complete
                asyncio.create_task(self._store_eigenda_metadata_async(
                    network=network,
                    source_code=source_code,
                    compiled=compiled,
                    receipt=receipt,
                    tx_hash=tx_hash,
                    account_address=account.address,
                    deployment_result=deployment_result
                ))
                logger.debug("EigenDA metadata storage scheduled in background")
            except RuntimeError as e:
                # No event loop available or other runtime error, skip EigenDA storage (non-critical)
                logger.warning(f"Could not schedule EigenDA background storage: {e}. Deployment still successful.")
        else:
            logger.debug(f"EigenDA not available for {network}, skipping data availability storage")
        
        return deployment_result
    
    async def _store_eigenda_metadata_async(
        self,
        network: str,
        source_code: Optional[str],
        compiled: Dict[str, Any],
        receipt: Dict[str, Any],
        tx_hash: Any,
        account_address: str,
        deployment_result: Dict[str, Any]
    ):
        """
        Store EigenDA metadata asynchronously (non-blocking)
        
        This allows the deployment to return immediately while EigenDA storage
        happens in the background. The result is updated when storage completes.
        """
        try:
            eigenda_commitment = None
            eigenda_metadata_stored = False
            
            # Store full contract metadata (ABI, source code, deployment info)
            if source_code:
                eigenda_commitment = await self.eigenda_client.store_contract_metadata(
                    contract_address=receipt["contractAddress"],
                    abi=compiled.get("abi", []),
                    source_code=source_code,
                    deployment_info={
                        "transaction_hash": tx_hash.hex(),
                        "block_number": receipt["blockNumber"],
                        "gas_used": receipt["gasUsed"],
                        "network": network,
                        "deployer_address": account_address
                    }
                )
                eigenda_metadata_stored = True
            else:
                # Fallback to bytecode-only storage if source code not available
                bytecode = compiled.get("bytecode", "")
                if isinstance(bytecode, str):
                    bytecode = bytecode.replace("0x", "")
                    bytecode_bytes = bytes.fromhex(bytecode)
                else:
                    bytecode_bytes = bytecode if bytecode else b""
                
                if bytecode_bytes:
                    eigenda_result = await self.eigenda_client.submit_blob(bytecode_bytes)
                    eigenda_commitment = eigenda_result.get("commitment")
            
            # Update deployment result (though it's already returned, this is for logging)
            deployment_result["eigenda_commitment"] = eigenda_commitment
            deployment_result["eigenda_metadata_stored"] = eigenda_metadata_stored
            logger.info(f"EigenDA metadata stored for contract {receipt['contractAddress']}: {eigenda_commitment}")
        except Exception as e:
            logger.warning(f"EigenDA metadata storage failed (non-blocking): {e}")
            # Don't fail deployment if EigenDA storage fails
    
    async def deploy_batch(
        self,
        contracts: List[Dict[str, Any]],
        network: str,
        use_pef: Optional[bool] = None,
        max_parallel: int = 10,
        private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deploy multiple contracts in parallel using PEF
        
        Concept: Use Hyperion PEF for parallel batch deployment
        Logic:
            1. Initialize PEF manager if use_pef=True and network is Hyperion
            2. Analyze dependencies
            3. Deploy independent contracts in parallel
            4. Return batch results
        
        Args:
            contracts: List of contract dictionaries with compiled_contract
            network: Target network
            use_pef: Override instance use_pef setting (defaults to self.use_pef)
            max_parallel: Maximum parallel deployments per batch
            private_key: Private key for deployment
        
        Returns:
            Batch deployment results with success/failure status for each contract
        """
        use_pef_flag = use_pef if use_pef is not None else self.use_pef
        
        # Check if PEF is available (with graceful fallback)
        from hyperagent.blockchain.network_features import (
            NetworkFeatureManager,
            NetworkFeature
        )
        
        if use_pef_flag:
            if NetworkFeatureManager.supports_feature(network, NetworkFeature.PEF):
                # Use PEF for parallel batch deployment
                from hyperagent.blockchain.hyperion_pef import HyperionPEFManager
                pef_manager = HyperionPEFManager(self.network_manager)
                return await pef_manager.deploy_batch(
                    contracts=contracts,
                    network=network,
                    max_parallel=max_parallel,
                    private_key=private_key or settings.private_key
                )
            else:
                logger.warning(
                    f"PEF requested but not available for {network}. "
                    f"Falling back to sequential batch deployment."
                )
                # Fallback to sequential deployment
                return await self._deploy_sequential_batch(contracts, network, private_key)
        else:
            # Sequential deployment requested
            return await self._deploy_sequential_batch(contracts, network, private_key)
    
    async def _deploy_sequential_batch(
        self,
        contracts: List[Dict[str, Any]],
        network: str,
        private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deploy contracts sequentially (fallback when PEF not available)
        
        Args:
            contracts: List of contract dictionaries
            network: Target network
            private_key: Private key for deployment
        
        Returns:
            Batch deployment results
        """
        from datetime import datetime
        start_time = datetime.now()
        
        deployments = []
        for contract in contracts:
            contract_name = contract.get("contract_name", "unknown")
            try:
                result = await self.process({
                    "compiled_contract": contract.get("compiled_contract"),
                    "network": network,
                    "private_key": private_key
                })
                
                if result.get("status") == "success":
                    deployments.append({
                        "contract_name": contract_name,
                        "status": "success",
                        "contract_address": result.get("contract_address"),
                        "transaction_hash": result.get("transaction_hash"),
                        "block_number": result.get("block_number"),
                        "gas_used": result.get("gas_used"),
                        "error": None
                    })
                else:
                    deployments.append({
                        "contract_name": contract_name,
                        "status": "failed",
                        "error": result.get("error", "Unknown error"),
                        "contract_address": None,
                        "transaction_hash": None
                    })
            except Exception as e:
                logger.error(f"Sequential deployment failed for {contract_name}: {e}")
                deployments.append({
                    "contract_name": contract_name,
                    "status": "failed",
                    "error": str(e),
                    "contract_address": None,
                    "transaction_hash": None
                })
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        success_count = len([d for d in deployments if d["status"] == "success"])
        
        return {
            "success": success_count > 0,
            "deployments": deployments,
            "total_time": total_time,
            "parallel_count": 0,  # Sequential, no parallel execution
            "success_count": success_count,
            "failed_count": len(deployments) - success_count,
            "batches_deployed": 1
        }
    
    async def on_error(self, error: Exception) -> None:
        """Handle service-specific errors"""
        logger.error(f"Deployment service error: {error}", exc_info=error)

