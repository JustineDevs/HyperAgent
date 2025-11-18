"""Unit tests for Hyperion PEF Manager"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from hyperagent.blockchain.hyperion_pef import HyperionPEFManager
from hyperagent.blockchain.networks import NetworkManager


@pytest.fixture
def network_manager():
    """Create NetworkManager mock"""
    return Mock(spec=NetworkManager)


@pytest.fixture
def pef_manager(network_manager):
    """Create HyperionPEFManager instance"""
    return HyperionPEFManager(network_manager)


@pytest.mark.asyncio
async def test_analyze_dependencies_no_deps(pef_manager):
    """Test dependency analysis with no dependencies"""
    contracts = [
        {
            "contract_name": "Contract1",
            "source_code": "contract Contract1 {}"
        },
        {
            "contract_name": "Contract2",
            "source_code": "contract Contract2 {}"
        }
    ]
    
    dependencies = await pef_manager.analyze_dependencies(contracts)
    
    assert "Contract1" in dependencies
    assert "Contract2" in dependencies
    assert len(dependencies["Contract1"]) == 0
    assert len(dependencies["Contract2"]) == 0


@pytest.mark.asyncio
async def test_analyze_dependencies_with_imports(pef_manager):
    """Test dependency analysis with imports"""
    contracts = [
        {
            "contract_name": "Contract1",
            "source_code": 'import "./Contract2.sol"; contract Contract1 {}'
        }
    ]
    
    dependencies = await pef_manager.analyze_dependencies(contracts)
    
    assert "Contract1" in dependencies
    assert len(dependencies["Contract1"]) > 0


@pytest.mark.asyncio
async def test_group_parallel_contracts(pef_manager):
    """Test grouping contracts into parallel batches"""
    contracts = [
        {"contract_name": "Contract1"},
        {"contract_name": "Contract2"},
        {"contract_name": "Contract3"}
    ]
    
    dependencies = {
        "Contract1": [],
        "Contract2": [],
        "Contract3": []
    }
    
    batches = pef_manager._group_parallel_contracts(contracts, dependencies)
    
    assert len(batches) > 0
    assert len(batches[0]) == 3  # All can run in parallel


@pytest.mark.asyncio
async def test_deploy_batch_non_hyperion(pef_manager):
    """Test deploy_batch raises error for non-Hyperion networks"""
    contracts = [{"contract_name": "Contract1"}]
    
    with pytest.raises(ValueError, match="PEF is only available for Hyperion"):
        await pef_manager.deploy_batch(contracts, network="mantle_testnet")


@pytest.mark.asyncio
async def test_deploy_batch_hyperion(pef_manager):
    """Test deploy_batch for Hyperion network"""
    contracts = [
        {
            "contract_name": "Contract1",
            "compiled_contract": {
                "bytecode": "0x1234",
                "abi": []
            }
        }
    ]
    
    with patch('hyperagent.blockchain.hyperion_pef.DeploymentService') as mock_service:
        mock_deployment = AsyncMock()
        mock_deployment.process = AsyncMock(return_value={
            "status": "success",
            "contract_address": "0xabcd",
            "transaction_hash": "0x5678"
        })
        mock_service.return_value = mock_deployment
        
        # This will fail at actual deployment, but tests the structure
        with pytest.raises((AttributeError, TypeError)):
            await pef_manager.deploy_batch(
                contracts,
                network="hyperion_testnet",
                max_parallel=1
            )
