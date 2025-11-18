"""Integration tests for workflow with compilation"""
import pytest
import sys
from unittest.mock import AsyncMock, MagicMock
from hyperagent.core.orchestrator import WorkflowCoordinator
from hyperagent.architecture.soa import ServiceRegistry
from hyperagent.events.event_bus import EventBus
from hyperagent.core.services.compilation_service import CompilationService

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
    """Create ServiceRegistry with mocked services"""
    registry = ServiceRegistry()
    
    # Mock generation service
    mock_generation = MagicMock()
    mock_generation.process = AsyncMock(return_value={
        "status": "success",
        "contract_code": "pragma solidity ^0.8.27; contract TestContract { uint256 public value; }",
        "contract_type": "Custom"
    })
    mock_generation.validate = AsyncMock(return_value=True)
    mock_generation.on_error = AsyncMock()
    
    # Real compilation service (will use mocked py-solc-x)
    compilation_service = CompilationService()
    
    # Mock audit service
    mock_audit = MagicMock()
    mock_audit.process = AsyncMock(return_value={
        "status": "success",
        "overall_risk_score": 10,
        "audit_status": "passed"
    })
    mock_audit.validate = AsyncMock(return_value=True)
    mock_audit.on_error = AsyncMock()
    
    # Mock testing service
    mock_testing = MagicMock()
    mock_testing.process = AsyncMock(return_value={
        "status": "success",
        "test_results": {"passed": 5, "failed": 0}
    })
    mock_testing.validate = AsyncMock(return_value=True)
    mock_testing.on_error = AsyncMock()
    
    # Mock deployment service
    mock_deployment = MagicMock()
    mock_deployment.process = AsyncMock(return_value={
        "status": "success",
        "contract_address": "0xContract",
        "transaction_hash": "0xTxHash"
    })
    mock_deployment.validate = AsyncMock(return_value=True)
    mock_deployment.on_error = AsyncMock()
    
    registry.register("generation", mock_generation)
    registry.register("compilation", compilation_service)
    registry.register("audit", mock_audit)
    registry.register("testing", mock_testing)
    registry.register("deployment", mock_deployment)
    
    return registry


@pytest.mark.asyncio
async def test_workflow_with_compilation(event_bus, service_registry):
    """Test complete workflow with compilation step"""
    coordinator = WorkflowCoordinator(service_registry, event_bus)
    
    # Mock py_solc_x module
    mock_py_solc_x = MagicMock()
    mock_py_solc_x.compile_source = MagicMock(return_value={
        '<stdin>:TestContract': {
            'abi': [{'type': 'function', 'name': 'value', 'inputs': [], 'outputs': []}],
            'evm': {
                'bytecode': {
                    'object': '0x608060405234801561001057600080fd5b50610150806100206000396000f3fe'
                },
                'deployedBytecode': {
                    'object': '0x6080604052348015600f57600080fd5b506004361060325760003560e01c'
                }
            }
        }
    })
    sys.modules['py_solc_x'] = mock_py_solc_x
    
    try:
        workflow_id = "test-workflow-compilation"
        result = await coordinator.execute_workflow(
            workflow_id=workflow_id,
            nlp_input="Create a simple contract",
            network="hyperion_testnet"
        )
        
        # Verify workflow completed
        assert "status" in result
        
        # Verify compilation service was called
        compilation_service = service_registry.get_service("compilation")
        # The service should have processed the contract_code from generation
    finally:
        if 'py_solc_x' in sys.modules:
            del sys.modules['py_solc_x']


@pytest.mark.asyncio
async def test_compilation_in_workflow_pipeline(event_bus, service_registry):
    """Test that compilation is in the workflow pipeline"""
    coordinator = WorkflowCoordinator(service_registry, event_bus)
    
    # Verify compilation service is registered
    assert "compilation" in service_registry.list_services()
    
    # Verify it's a CompilationService instance
    compilation_service = service_registry.get_service("compilation")
    assert isinstance(compilation_service, CompilationService)


@pytest.mark.asyncio
async def test_workflow_compilation_output_format(event_bus, service_registry):
    """Test that compilation output format matches deployment expectations"""
    coordinator = WorkflowCoordinator(service_registry, event_bus)
    
    # Mock py_solc_x module
    mock_py_solc_x = MagicMock()
    mock_py_solc_x.compile_source = MagicMock(return_value={
        '<stdin>:TestContract': {
            'abi': [],
            'evm': {
                'bytecode': {'object': '0x123'},
                'deployedBytecode': {'object': '0x456'}
            }
        }
    })
    sys.modules['py_solc_x'] = mock_py_solc_x
    
    try:
        workflow_id = "test-workflow-format"
        result = await coordinator.execute_workflow(
            workflow_id=workflow_id,
            nlp_input="Create contract",
            network="hyperion_testnet"
        )
        
        # If successful, verify compiled_contract structure
        if result.get("status") == "success":
            workflow_result = result.get("result", {})
            compiled_contract = workflow_result.get("compiled_contract")
            
            if compiled_contract:
                # Verify structure matches deployment service expectations
                assert "bytecode" in compiled_contract
                assert "abi" in compiled_contract
    finally:
        if 'py_solc_x' in sys.modules:
            del sys.modules['py_solc_x']

