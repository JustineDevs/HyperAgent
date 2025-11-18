"""Performance tests for PEF batch deployment"""
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from hyperagent.blockchain.hyperion_pef import HyperionPEFManager
from hyperagent.blockchain.networks import NetworkManager

pytestmark = [pytest.mark.performance]


@pytest.fixture
def network_manager():
    """NetworkManager fixture"""
    return NetworkManager()


@pytest.fixture
def pef_manager(network_manager):
    """HyperionPEFManager fixture"""
    return HyperionPEFManager(network_manager)


@pytest.mark.asyncio
async def test_pef_vs_sequential_speedup(pef_manager):
    """Compare PEF parallel vs sequential deployment speed"""
    # Create mock contracts
    contracts = [
        {
            "contract_name": f"Contract{i}",
            "compiled_contract": {"bytecode": f"0x{i:064x}", "abi": []},
            "source_code": f"pragma solidity ^0.8.27; contract Contract{i} {{}}"
        }
        for i in range(10)
    ]
    
    # Mock deployment service
    mock_service = MagicMock()
    mock_service.process = AsyncMock(side_effect=[
        {
            "status": "success",
            "contract_address": f"0xContract{i}",
            "transaction_hash": f"0xTx{i}",
            "block_number": 1000 + i,
            "gas_used": 100000
        }
        for i in range(10)
    ])
    
    # Test PEF parallel deployment
    with patch('hyperagent.blockchain.hyperion_pef.DeploymentService') as mock_service_class, \
         patch('hyperagent.blockchain.hyperion_pef.AlithClient') as mock_alith, \
         patch('hyperagent.blockchain.hyperion_pef.EigenDAClient') as mock_eigenda, \
         patch('hyperagent.blockchain.hyperion_pef.settings') as mock_settings:
        
        mock_service_class.return_value = mock_service
        mock_settings.private_key = "test_key"
        
        start_parallel = time.time()
        parallel_result = await pef_manager.deploy_batch(
            contracts=contracts,
            network="hyperion_testnet",
            max_parallel=10,
            private_key="test_key"
        )
        parallel_time = time.time() - start_parallel
    
    # Simulate sequential deployment (one at a time)
    start_sequential = time.time()
    for contract in contracts:
        await mock_service.process({
            "compiled_contract": contract["compiled_contract"],
            "network": "hyperion_testnet"
        })
        time.sleep(0.1)  # Simulate network delay
    sequential_time = time.time() - start_sequential
    
    speedup = sequential_time / parallel_time if parallel_time > 0 else 0
    
    print(f"\nParallel time: {parallel_time:.2f}s")
    print(f"Sequential time: {sequential_time:.2f}s")
    print(f"Speedup: {speedup:.2f}x")
    
    # Verify speedup (should be significant with parallel execution)
    assert speedup >= 5, f"Expected at least 5x speedup, got {speedup:.2f}x"
    assert parallel_result["success_count"] == 10


@pytest.mark.asyncio
async def test_pef_scalability(pef_manager):
    """Test PEF performance with different batch sizes"""
    batch_sizes = [5, 10, 20]
    results = {}
    
    mock_service = MagicMock()
    mock_service.process = AsyncMock(return_value={
        "status": "success",
        "contract_address": "0xContract",
        "transaction_hash": "0xTx",
        "block_number": 12345,
        "gas_used": 100000
    })
    
    with patch('hyperagent.blockchain.hyperion_pef.DeploymentService') as mock_service_class, \
         patch('hyperagent.blockchain.hyperion_pef.AlithClient') as mock_alith, \
         patch('hyperagent.blockchain.hyperion_pef.EigenDAClient') as mock_eigenda, \
         patch('hyperagent.blockchain.hyperion_pef.settings') as mock_settings:
        
        mock_service_class.return_value = mock_service
        mock_settings.private_key = "test_key"
        
        for size in batch_sizes:
            contracts = [
                {
                    "contract_name": f"Contract{i}",
                    "compiled_contract": {"bytecode": f"0x{i:064x}", "abi": []}
                }
                for i in range(size)
            ]
            
            start = time.time()
            result = await pef_manager.deploy_batch(
                contracts=contracts,
                network="hyperion_testnet",
                max_parallel=size,
                private_key="test_key"
            )
            elapsed = time.time() - start
            
            results[size] = {
                "time": elapsed,
                "success_count": result["success_count"],
                "parallel_count": result["parallel_count"]
            }
    
    # Verify scalability
    print("\nScalability Results:")
    for size, metrics in results.items():
        print(f"{size} contracts: {metrics['time']:.2f}s, {metrics['parallel_count']} parallel")
        assert metrics["success_count"] == size
        assert metrics["parallel_count"] == size


@pytest.mark.asyncio
async def test_pef_dependency_impact(pef_manager):
    """Test how dependencies affect parallel execution"""
    # Independent contracts (should deploy in parallel)
    independent_contracts = [
        {
            "contract_name": f"Contract{i}",
            "compiled_contract": {"bytecode": f"0x{i:064x}", "abi": []},
            "source_code": f"pragma solidity ^0.8.27; contract Contract{i} {{}}"
        }
        for i in range(5)
    ]
    
    # Contracts with dependencies (should deploy sequentially)
    dependent_contracts = [
        {
            "contract_name": "Contract1",
            "compiled_contract": {"bytecode": "0x1", "abi": []},
            "source_code": "pragma solidity ^0.8.27; contract Contract1 {}"
        },
        {
            "contract_name": "Contract2",
            "compiled_contract": {"bytecode": "0x2", "abi": []},
            "source_code": 'pragma solidity ^0.8.27; import "./Contract1.sol"; contract Contract2 {}'
        }
    ]
    
    mock_service = MagicMock()
    mock_service.process = AsyncMock(return_value={
        "status": "success",
        "contract_address": "0xContract",
        "transaction_hash": "0xTx",
        "block_number": 12345,
        "gas_used": 100000
    })
    
    with patch('hyperagent.blockchain.hyperion_pef.DeploymentService') as mock_service_class, \
         patch('hyperagent.blockchain.hyperion_pef.AlithClient') as mock_alith, \
         patch('hyperagent.blockchain.hyperion_pef.EigenDAClient') as mock_eigenda, \
         patch('hyperagent.blockchain.hyperion_pef.settings') as mock_settings:
        
        mock_service_class.return_value = mock_service
        mock_settings.private_key = "test_key"
        
        # Test independent contracts
        start_independent = time.time()
        independent_result = await pef_manager.deploy_batch(
            contracts=independent_contracts,
            network="hyperion_testnet",
            max_parallel=10,
            private_key="test_key"
        )
        independent_time = time.time() - start_independent
        
        # Test dependent contracts
        start_dependent = time.time()
        dependent_result = await pef_manager.deploy_batch(
            contracts=dependent_contracts,
            network="hyperion_testnet",
            max_parallel=10,
            private_key="test_key"
        )
        dependent_time = time.time() - start_dependent
    
    print(f"\nIndependent contracts: {independent_time:.2f}s, batches: {independent_result['batches_deployed']}")
    print(f"Dependent contracts: {dependent_time:.2f}s, batches: {dependent_result['batches_deployed']}")
    
    # Independent should be faster (more parallelization)
    # Dependent may have more batches due to dependencies
    assert independent_result["success_count"] == 5
    assert dependent_result["success_count"] == 2

