"""Integration tests for PEF batch deployment"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from hyperagent.blockchain.hyperion_pef import HyperionPEFManager
from hyperagent.blockchain.networks import NetworkManager
from hyperagent.core.services.deployment_service import DeploymentService
from hyperagent.blockchain.alith_client import AlithClient
from hyperagent.blockchain.eigenda_client import EigenDAClient
from hyperagent.core.config import settings

pytestmark = [pytest.mark.integration]


@pytest.fixture
def network_manager():
    """NetworkManager fixture"""
    return NetworkManager()


@pytest.fixture
def pef_manager(network_manager):
    """HyperionPEFManager fixture"""
    return HyperionPEFManager(network_manager)


@pytest.fixture
def mock_deployment_service():
    """Mock DeploymentService for testing"""
    service = MagicMock(spec=DeploymentService)
    service.process = AsyncMock(return_value={
        "status": "success",
        "contract_address": "0xContract",
        "transaction_hash": "0xTxHash",
        "block_number": 12345,
        "gas_used": 100000
    })
    return service


@pytest.mark.asyncio
async def test_pef_batch_deployment_mocked(pef_manager, mock_deployment_service):
    """Test PEF batch deployment with mocked deployment service"""
    contracts = [
        {
            "contract_name": "Contract1",
            "compiled_contract": {"bytecode": "0x123", "abi": []},
            "source_code": "pragma solidity ^0.8.27; contract Contract1 {}"
        },
        {
            "contract_name": "Contract2",
            "compiled_contract": {"bytecode": "0x456", "abi": []},
            "source_code": "pragma solidity ^0.8.27; contract Contract2 {}"
        }
    ]
    
    # Mock the deployment service creation
    with patch('hyperagent.blockchain.hyperion_pef.DeploymentService') as mock_service_class:
        mock_service_class.return_value = mock_deployment_service
        
        # Mock settings (AlithClient and EigenDAClient are not imported in hyperion_pef)
        with patch('hyperagent.core.config.settings') as mock_settings:
            
            mock_settings.private_key = "test_key"
            
            result = await pef_manager.deploy_batch(
                contracts=contracts,
                network="hyperion_testnet",
                max_parallel=10,
                private_key="test_key"
            )
            
            assert result["success"] is True
            assert len(result["deployments"]) == 2
            assert result["parallel_count"] == 2
            assert result["success_count"] == 2
            assert all(d["status"] == "success" for d in result["deployments"])


@pytest.mark.asyncio
async def test_pef_dependency_analysis(pef_manager):
    """Test dependency analysis for contracts"""
    contracts = [
        {
            "contract_name": "Contract1",
            "source_code": "pragma solidity ^0.8.27; contract Contract1 {}"
        },
        {
            "contract_name": "Contract2",
            "source_code": 'pragma solidity ^0.8.27; import "./Contract1.sol"; contract Contract2 {}'
        }
    ]
    
    dependencies = await pef_manager.analyze_dependencies(contracts)
    
    assert "Contract1" in dependencies
    assert "Contract2" in dependencies
    # Contract2 depends on Contract1
    assert len(dependencies["Contract2"]) > 0


@pytest.mark.asyncio
async def test_pef_group_parallel_contracts(pef_manager):
    """Test grouping contracts for parallel execution"""
    contracts = [
        {"contract_name": "Contract1", "compiled_contract": {"bytecode": "0x123"}},
        {"contract_name": "Contract2", "compiled_contract": {"bytecode": "0x456"}},
        {"contract_name": "Contract3", "compiled_contract": {"bytecode": "0x789"}}
    ]
    
    dependencies = {
        "Contract1": [],
        "Contract2": [],
        "Contract3": []
    }
    
    batches = pef_manager._group_parallel_contracts(contracts, dependencies)
    
    assert len(batches) > 0
    # All contracts are independent, should be in same batch
    assert len(batches[0]) == 3


@pytest.mark.asyncio
@pytest.mark.requires_api
async def test_pef_batch_deployment_real_network(pef_manager):
    """
    Test PEF batch deployment on real Hyperion testnet
    
    Note: This test requires:
    - Real network connection
    - Private key with testnet funds
    - Actual contract bytecode
    """
    # Skip if no testnet access
    pytest.skip("Requires real network connection and testnet funds")
    
    contracts = [
        {
            "contract_name": "TestContract1",
            "compiled_contract": {
                "bytecode": "0x608060405234801561001057600080fd5b50610150806100206000396000f3fe6080604052348015600f57600080fd5b506004361060325760003560e01c80632e64cec11460375780636057361d146051575b600080fd5b603d6069565b6040516048919060c2565b60405180910390f35b6067600480360381019060639190608f565b6072565b005b60008054905090565b8060008190555050565b600080fd5b6000819050919050565b6089816078565b8114609357600080fd5b50565b60006020828403121560a057600080fd5b600060ac84828501608f565b91505092915050565b6000819050919050565b60c68160b5565b82525050565b600060208201905060df600083018460bf565b9291505056fea2646970667358221220d6c4e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e64736f6c63430008070033",
                "abi": []
            },
            "source_code": "pragma solidity ^0.8.27; contract TestContract1 { uint256 public value; }"
        }
    ]
    
    result = await pef_manager.deploy_batch(
        contracts=contracts,
        network="hyperion_testnet",
        max_parallel=5,
        private_key=settings.private_key
    )
    
    assert result["success"] is True
    assert result["success_count"] > 0

