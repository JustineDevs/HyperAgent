"""Integration tests for network fallback behavior"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from hyperagent.blockchain.hyperion_pef import HyperionPEFManager
from hyperagent.core.services.generation_service import GenerationService
from hyperagent.core.services.deployment_service import DeploymentService
from hyperagent.blockchain.network_features import NetworkFeature, NetworkFeatureManager


class TestPEFallback:
    """Test PEF fallback behavior"""
    
    @pytest.mark.asyncio
    async def test_pef_fallback_on_non_hyperion(self):
        """Test PEF falls back to sequential on non-Hyperion networks"""
        network_manager = MagicMock()
        pef_manager = HyperionPEFManager(network_manager)
        
        contracts = [
            {"contract_name": "TestContract1", "compiled_contract": {"abi": [], "bytecode": "0x"}},
            {"contract_name": "TestContract2", "compiled_contract": {"abi": [], "bytecode": "0x"}}
        ]
        
        # Mock deployment service
        with patch('hyperagent.blockchain.hyperion_pef.DeploymentService') as mock_deployment:
            mock_service = AsyncMock()
            mock_service.process = AsyncMock(return_value={
                "status": "success",
                "contract_address": "0x123",
                "transaction_hash": "0xabc",
                "block_number": 1,
                "gas_used": 100000
            })
            mock_deployment.return_value = mock_service
            
            # Test on Mantle (should fallback)
            result = await pef_manager.deploy_batch(
                contracts=contracts,
                network="mantle_testnet",
                max_parallel=10,
                private_key="0x" + "1" * 64
            )
            
            # Should use sequential fallback
            assert result["deployment_method"] == "sequential_fallback"
            assert result["parallel_count"] == 0
    
    @pytest.mark.asyncio
    async def test_pef_works_on_hyperion(self):
        """Test PEF works normally on Hyperion networks"""
        network_manager = MagicMock()
        pef_manager = HyperionPEFManager(network_manager)
        
        contracts = [
            {"contract_name": "TestContract1", "compiled_contract": {"abi": [], "bytecode": "0x"}}
        ]
        
        # Mock PEF deployment (should not fallback)
        with patch.object(pef_manager, 'analyze_dependencies') as mock_analyze:
            mock_analyze.return_value = {}
            
            with patch.object(pef_manager, '_group_parallel_contracts') as mock_group:
                mock_group.return_value = [[contracts[0]]]
                
                with patch.object(pef_manager, '_deploy_single_contract') as mock_deploy:
                    mock_deploy.return_value = {
                        "status": "success",
                        "contract_address": "0x123",
                        "transaction_hash": "0xabc",
                        "block_number": 1,
                        "gas_used": 100000
                    }
                    
                    result = await pef_manager.deploy_batch(
                        contracts=contracts,
                        network="hyperion_testnet",
                        max_parallel=10,
                        private_key="0x" + "1" * 64
                    )
                    
                    # Should use PEF (not fallback)
                    assert "deployment_method" not in result or result.get("deployment_method") != "sequential_fallback"


class TestMetisVMFallback:
    """Test MetisVM fallback behavior"""
    
    @pytest.mark.asyncio
    async def test_metisvm_fallback_on_non_hyperion(self):
        """Test MetisVM falls back to standard compilation on non-Hyperion networks"""
        llm_provider = AsyncMock()
        template_retriever = AsyncMock()
        template_retriever.retrieve_and_generate = AsyncMock(return_value="contract code")
        
        service = GenerationService(llm_provider, template_retriever)
        
        input_data = {
            "nlp_description": "Test contract",
            "contract_type": "Custom",
            "network": "mantle_testnet",
            "optimize_for_metisvm": True  # Requested but not available
        }
        
        result = await service.process(input_data)
        
        # Should succeed without optimization
        assert result["status"] == "success"
        assert result["metisvm_optimized"] is False  # Should not be optimized
    
    @pytest.mark.asyncio
    async def test_metisvm_works_on_hyperion(self):
        """Test MetisVM works normally on Hyperion networks"""
        llm_provider = AsyncMock()
        template_retriever = AsyncMock()
        template_retriever.retrieve_and_generate = AsyncMock(return_value="contract code")
        
        service = GenerationService(llm_provider, template_retriever)
        
        input_data = {
            "nlp_description": "Test contract",
            "contract_type": "Custom",
            "network": "hyperion_testnet",
            "optimize_for_metisvm": True
        }
        
        with patch('hyperagent.blockchain.metisvm_optimizer.MetisVMOptimizer') as mock_optimizer:
            mock_opt = MagicMock()
            mock_opt.optimize_for_metisvm.return_value = "optimized code"
            mock_opt.get_optimization_report.return_value = {"optimizations": []}
            mock_optimizer.return_value = mock_opt
            
            result = await service.process(input_data)
            
            # Should be optimized
            assert result["status"] == "success"
            assert result["metisvm_optimized"] is True


class TestEigenDAFallback:
    """Test EigenDA fallback behavior"""
    
    @pytest.mark.asyncio
    async def test_eigenda_skipped_on_non_mantle(self):
        """Test EigenDA is skipped on non-Mantle networks"""
        from hyperagent.blockchain.network_features import NetworkFeatureManager, NetworkFeature
        
        # Test feature check directly
        supports_eigenda = NetworkFeatureManager.supports_feature("hyperion_testnet", NetworkFeature.EIGENDA)
        assert supports_eigenda is False, "EigenDA should not be supported on Hyperion"
        
        # Test that EigenDA client would not be called
        eigenda_client = AsyncMock()
        eigenda_client.store_contract_metadata = AsyncMock()
        
        # Simulate deployment service logic
        network = "hyperion_testnet"
        if NetworkFeatureManager.supports_feature(network, NetworkFeature.EIGENDA) and eigenda_client:
            await eigenda_client.store_contract_metadata("0x123", [], "code", {})
        
        # Verify EigenDA was not called
        eigenda_client.store_contract_metadata.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_eigenda_works_on_mantle_mainnet(self):
        """Test EigenDA works on Mantle mainnet"""
        from hyperagent.blockchain.network_features import NetworkFeatureManager, NetworkFeature
        
        # Test feature check directly
        supports_eigenda = NetworkFeatureManager.supports_feature("mantle_mainnet", NetworkFeature.EIGENDA)
        assert supports_eigenda is True, "EigenDA should be supported on Mantle mainnet"
        
        # Test that EigenDA client would be called
        eigenda_client = AsyncMock()
        eigenda_client.store_contract_metadata = AsyncMock(return_value={
            "commitment": "0xcommitment"
        })
        
        # Simulate deployment service logic
        network = "mantle_mainnet"
        if NetworkFeatureManager.supports_feature(network, NetworkFeature.EIGENDA) and eigenda_client:
            result = await eigenda_client.store_contract_metadata(
                "0x123", [], "code", {}
            )
        
        # Verify EigenDA was called
        eigenda_client.store_contract_metadata.assert_called_once()
        assert result["commitment"] == "0xcommitment"


class TestBatchDeploymentFallback:
    """Test batch deployment fallback behavior"""
    
    @pytest.mark.asyncio
    async def test_batch_deployment_pef_fallback(self):
        """Test batch deployment falls back when PEF not available"""
        network_manager = MagicMock()
        service = DeploymentService(
            network_manager=network_manager,
            alith_client=MagicMock(),
            eigenda_client=MagicMock(),
            use_alith_autonomous=False,
            use_pef=True  # Requested
        )
        
        contracts = [
            {"compiled_contract": {"abi": [], "bytecode": "0x"}, "contract_name": "Test1"},
            {"compiled_contract": {"abi": [], "bytecode": "0x"}, "contract_name": "Test2"}
        ]
        
        # Mock sequential batch deployment
        with patch.object(service, '_deploy_sequential_batch') as mock_seq:
            mock_seq.return_value = {
                "success": True,
                "deployments": [],
                "total_time": 1.0,
                "parallel_count": 0,
                "success_count": 2,
                "failed_count": 0,
                "batches_deployed": 2
            }
            
            result = await service.deploy_batch(
                contracts=contracts,
                network="mantle_testnet",  # No PEF
                use_pef=True,
                max_parallel=10,
                private_key="0x" + "1" * 64
            )
            
            # Should use sequential fallback
            assert result["success"] is True
            mock_seq.assert_called_once()

