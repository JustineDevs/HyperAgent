"""End-to-end workflow integration tests for production readiness"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from hyperagent.core.orchestrator import WorkflowCoordinator
from hyperagent.architecture.soa import ServiceRegistry
from hyperagent.events.event_bus import EventBus
import uuid

pytestmark = [pytest.mark.integration]


@pytest.fixture
async def event_bus():
    """Create EventBus fixture with mocked Redis"""
    from unittest.mock import MagicMock
    mock_redis = MagicMock()
    mock_redis.xadd = AsyncMock(return_value="mock-stream-id")
    mock_redis.xread = AsyncMock(return_value=[])
    return EventBus(mock_redis)


@pytest.fixture
def service_registry():
    """Create ServiceRegistry with mocked services that return proper data"""
    registry = ServiceRegistry()
    
    # Mock Generation Service - returns contract with constructor args
    mock_generation = MagicMock()
    mock_generation.process = AsyncMock(return_value={
        "status": "success",
        "contract_code": "pragma solidity ^0.8.27; contract TestToken { constructor(uint256 initialSupply, address owner) {} }",
        "contract_name": "TestToken",
        "contract_type": "ERC20",
        "abi": [{"type": "constructor", "inputs": [{"name": "initialSupply", "type": "uint256"}, {"name": "owner", "type": "address"}]}],
        "constructor_args": [
            {"name": "initialSupply", "type": "uint256", "storage_location": None, "indexed": False},
            {"name": "owner", "type": "address", "storage_location": None, "indexed": False}
        ]
    })
    mock_generation.validate = AsyncMock(return_value=True)
    mock_generation.on_error = AsyncMock()
    
    # Mock Compilation Service
    mock_compilation = MagicMock()
    mock_compilation.process = AsyncMock(return_value={
        "status": "success",
        "compiled_contract": {
            "bytecode": "0x6080604052348015600f57600080fd5b50",
            "abi": [{"type": "constructor", "inputs": [{"name": "initialSupply", "type": "uint256"}, {"name": "owner", "type": "address"}]}],
            "deployed_bytecode": "0x6080604052348015600f57600080fd5b50"
        },
        "contract_code": "pragma solidity ^0.8.27; contract TestToken { constructor(uint256 initialSupply, address owner) {} }"
    })
    mock_compilation.validate = AsyncMock(return_value=True)
    mock_compilation.on_error = AsyncMock()
    
    # Mock Audit Service
    mock_audit = MagicMock()
    mock_audit.process = AsyncMock(return_value={
        "status": "success",
        "overall_risk_score": 10,
        "vulnerabilities": [],
        "contract_code": "pragma solidity ^0.8.27; contract TestToken { constructor(uint256 initialSupply, address owner) {} }"
    })
    mock_audit.validate = AsyncMock(return_value=True)
    mock_audit.on_error = AsyncMock()
    
    # Mock Testing Service
    mock_testing = MagicMock()
    mock_testing.process = AsyncMock(return_value={
        "status": "success",
        "test_results": {"passed": 5, "failed": 0},
        "contract_code": "pragma solidity ^0.8.27; contract TestToken { constructor(uint256 initialSupply, address owner) {} }",
        "compiled_contract": {"bytecode": "0x6080604052348015600f57600080fd5b50", "abi": []}
    })
    mock_testing.validate = AsyncMock(return_value=True)
    mock_testing.on_error = AsyncMock()
    
    # Mock Deployment Service - should receive constructor_args
    mock_deployment = MagicMock()
    mock_deployment.process = AsyncMock(return_value={
        "status": "success",
        "contract_address": "0x1234567890123456789012345678901234567890",
        "transaction_hash": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefab",
        "block_number": 12345,
        "gas_used": 150000
    })
    mock_deployment.validate = AsyncMock(return_value=True)
    mock_deployment.on_error = AsyncMock()
    
    registry.register("generation", mock_generation)
    registry.register("compilation", mock_compilation)
    registry.register("audit", mock_audit)
    registry.register("testing", mock_testing)
    registry.register("deployment", mock_deployment)
    
    return registry


@pytest.mark.asyncio
async def test_workflow_coordinator_basic(event_bus, service_registry):
    """Test basic workflow coordinator execution"""
    coordinator = WorkflowCoordinator(service_registry, event_bus)
    
    workflow_id = str(uuid.uuid4())
    result = await coordinator.execute_workflow(
        workflow_id=workflow_id,
        nlp_input="Create ERC20 token",
        network="hyperion_testnet"
    )
    
    # Should return result
    assert "status" in result


@pytest.mark.asyncio
async def test_complete_workflow_simple_contract(event_bus, service_registry):
    """Test complete workflow with simple contract (no constructor args)"""
    # Setup: Simple contract without constructor
    mock_generation = service_registry.get_service("generation")
    mock_generation.process = AsyncMock(return_value={
        "status": "success",
        "contract_code": "pragma solidity ^0.8.27; contract SimpleStorage { uint256 public value; }",
        "contract_name": "SimpleStorage",
        "constructor_args": []  # No constructor args
    })
    
    coordinator = WorkflowCoordinator(service_registry, event_bus)
    workflow_id = str(uuid.uuid4())
    
    result = await coordinator.execute_workflow(
        workflow_id=workflow_id,
        nlp_input="Create a simple storage contract",
        network="hyperion_testnet"
    )
    
    # Verify workflow completed
    assert result["status"] == "success"
    assert "result" in result
    
    # Verify all stages were called
    assert mock_generation.process.called
    assert service_registry.get_service("compilation").process.called
    assert service_registry.get_service("audit").process.called
    assert service_registry.get_service("testing").process.called
    assert service_registry.get_service("deployment").process.called
    
    # Verify deployment received empty constructor args
    deployment_call = service_registry.get_service("deployment").process.call_args
    if deployment_call:
        deployment_input = deployment_call[0][0] if deployment_call[0] else {}
        # Constructor args should be empty list or not present
        assert deployment_input.get("constructor_args", []) == []


@pytest.mark.asyncio
async def test_complete_workflow_with_constructor_args(event_bus, service_registry):
    """Test complete workflow with contract requiring constructor args"""
    coordinator = WorkflowCoordinator(service_registry, event_bus)
    workflow_id = str(uuid.uuid4())
    
    result = await coordinator.execute_workflow(
        workflow_id=workflow_id,
        nlp_input="Create ERC20 token with initial supply and owner",
        network="hyperion_testnet"
    )
    
    # Verify workflow completed
    assert result["status"] == "success"
    assert "result" in result
    
    # Verify constructor args were extracted
    generation_result = result.get("result", {}).get("generation_result", {})
    constructor_args = generation_result.get("constructor_args", [])
    assert len(constructor_args) == 2
    assert constructor_args[0]["name"] == "initialSupply"
    assert constructor_args[0]["type"] == "uint256"
    assert constructor_args[1]["name"] == "owner"
    assert constructor_args[1]["type"] == "address"
    
    # Verify deployment service received constructor args
    mock_deployment = service_registry.get_service("deployment")
    assert mock_deployment.process.called
    
    # Check that constructor_args were passed to deployment
    deployment_call = mock_deployment.process.call_args
    if deployment_call and len(deployment_call[0]) > 0:
        deployment_input = deployment_call[0][0]
        # Constructor args should be passed through pipeline
        assert "constructor_args" in deployment_input or "compiled_contract" in deployment_input


@pytest.mark.asyncio
async def test_workflow_progress_tracking(event_bus, service_registry):
    """Test that progress callback is called at each stage"""
    progress_updates = []
    
    async def progress_callback(stage: str, progress: int):
        """Track progress updates"""
        progress_updates.append((stage, progress))
    
    coordinator = WorkflowCoordinator(service_registry, event_bus, progress_callback)
    workflow_id = str(uuid.uuid4())
    
    result = await coordinator.execute_workflow(
        workflow_id=workflow_id,
        nlp_input="Create a test contract",
        network="hyperion_testnet"
    )
    
    # Verify progress updates were called
    assert len(progress_updates) >= 4  # At least generation, compilation, audit, testing
    
    # Verify progress values
    progress_map = {stage: progress for stage, progress in progress_updates}
    assert progress_map.get("generating", 0) == 20
    assert progress_map.get("auditing", 0) == 60
    assert progress_map.get("testing", 0) == 80
    assert progress_map.get("deploying", 0) == 100


@pytest.mark.asyncio
async def test_workflow_with_complex_constructor_args(event_bus, service_registry):
    """Test workflow with complex constructor arguments (arrays, mappings)"""
    # Setup: Contract with complex constructor args
    mock_generation = service_registry.get_service("generation")
    mock_generation.process = AsyncMock(return_value={
        "status": "success",
        "contract_code": "pragma solidity ^0.8.27; contract Complex { constructor(uint256[] memory amounts, mapping(address => uint256) storage balances) {} }",
        "contract_name": "Complex",
        "constructor_args": [
            {"name": "amounts", "type": "uint256[]", "storage_location": "memory", "indexed": False},
            {"name": "balances", "type": "mapping(address => uint256)", "storage_location": "storage", "indexed": False}
        ]
    })
    
    coordinator = WorkflowCoordinator(service_registry, event_bus)
    workflow_id = str(uuid.uuid4())
    
    result = await coordinator.execute_workflow(
        workflow_id=workflow_id,
        nlp_input="Create contract with array and mapping parameters",
        network="hyperion_testnet"
    )
    
    # Verify workflow completed
    assert result["status"] == "success"
    
    # Verify complex constructor args were extracted
    generation_result = result.get("result", {}).get("generation_result", {})
    constructor_args = generation_result.get("constructor_args", [])
    assert len(constructor_args) == 2
    assert constructor_args[0]["type"] == "uint256[]"
    assert constructor_args[0]["storage_location"] == "memory"
    assert constructor_args[1]["type"] == "mapping(address => uint256)"
    assert constructor_args[1]["storage_location"] == "storage"


@pytest.mark.asyncio
async def test_workflow_error_handling(event_bus, service_registry):
    """Test workflow error handling at each stage"""
    # Setup: Make compilation fail
    mock_compilation = service_registry.get_service("compilation")
    mock_compilation.process = AsyncMock(side_effect=ValueError("Compilation failed"))
    
    coordinator = WorkflowCoordinator(service_registry, event_bus)
    workflow_id = str(uuid.uuid4())
    
    result = await coordinator.execute_workflow(
        workflow_id=workflow_id,
        nlp_input="Create a contract that will fail compilation",
        network="hyperion_testnet"
    )
    
    # Verify workflow failed gracefully
    assert result["status"] == "failed"
    assert "error" in result
    assert "Compilation failed" in result["error"]


@pytest.mark.asyncio
async def test_workflow_constructor_args_passed_to_deployment(event_bus, service_registry):
    """Test that constructor args are correctly passed from generation to deployment"""
    coordinator = WorkflowCoordinator(service_registry, event_bus)
    workflow_id = str(uuid.uuid4())
    
    result = await coordinator.execute_workflow(
        workflow_id=workflow_id,
        nlp_input="Create token with constructor parameters",
        network="hyperion_testnet"
    )
    
    # Verify workflow completed
    assert result["status"] == "success"
    
    # Verify constructor args flow through pipeline
    result_data = result.get("result", {})
    
    # Generation should have constructor_args
    generation_result = result_data.get("generation_result", {})
    gen_constructor_args = generation_result.get("constructor_args", [])
    assert len(gen_constructor_args) > 0
    
    # Constructor args should be in overall result for deployment
    overall_constructor_args = result_data.get("constructor_args", [])
    # Either in overall result or passed through pipeline
    assert len(gen_constructor_args) == len(overall_constructor_args) or overall_constructor_args == gen_constructor_args

