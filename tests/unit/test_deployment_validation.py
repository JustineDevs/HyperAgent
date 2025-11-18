"""Unit tests for deployment validation"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from web3 import Web3
from eth_account import Account
from hyperagent.core.services.deployment_service import DeploymentService
from hyperagent.blockchain.networks import NetworkManager
from hyperagent.blockchain.alith_client import AlithClient
from hyperagent.blockchain.eigenda_client import EigenDAClient
from hyperagent.core.config import settings


class TestDeploymentValidation:
    """Test deployment requirement validation"""
    
    @pytest.fixture
    def deployment_service(self):
        """Create DeploymentService instance"""
        network_manager = Mock(spec=NetworkManager)
        alith_client = Mock(spec=AlithClient)
        eigenda_client = Mock(spec=EigenDAClient)
        return DeploymentService(network_manager, alith_client, eigenda_client)
    
    @pytest.fixture
    def mock_web3(self):
        """Create mock Web3 instance"""
        w3 = Mock(spec=Web3)
        w3.eth = Mock()
        w3.to_wei = Web3.to_wei
        w3.from_wei = Web3.from_wei
        return w3
    
    @pytest.mark.asyncio
    async def test_validate_rpc_connectivity_success(self, deployment_service, mock_web3):
        """Test successful RPC connectivity validation"""
        # Setup mocks
        deployment_service.network_manager.get_web3 = Mock(return_value=mock_web3)
        mock_web3.eth.get_block = Mock(return_value={'number': 12345})
        
        # Create test account
        account = Account.create()
        private_key = account.key.hex()
        
        result = await deployment_service.validate_deployment_requirements(
            "hyperion_testnet",
            private_key
        )
        
        assert result["rpc_connected"] is True
        assert result["wallet_address"] == account.address
        assert "balance_wei" in result
        assert "chain_id" in result
    
    @pytest.mark.asyncio
    async def test_validate_rpc_connectivity_failure(self, deployment_service, mock_web3):
        """Test RPC connectivity failure"""
        deployment_service.network_manager.get_web3 = Mock(return_value=mock_web3)
        mock_web3.eth.get_block = Mock(side_effect=ConnectionError("RPC unreachable"))
        
        account = Account.create()
        private_key = account.key.hex()
        
        with pytest.raises(ValueError, match="RPC endpoint unreachable"):
            await deployment_service.validate_deployment_requirements(
                "hyperion_testnet",
                private_key
            )
    
    @pytest.mark.asyncio
    async def test_validate_zero_balance_failure(self, deployment_service, mock_web3):
        """Test validation fails with zero balance"""
        deployment_service.network_manager.get_web3 = Mock(return_value=mock_web3)
        mock_web3.eth.get_block = Mock(return_value={'number': 12345})
        mock_web3.eth.get_balance = Mock(return_value=0)
        mock_web3.eth.chain_id = 133717
        
        deployment_service.network_manager.get_network_config = Mock(
            return_value={"chain_id": 133717}
        )
        
        account = Account.create()
        private_key = account.key.hex()
        
        with pytest.raises(ValueError, match="zero balance"):
            await deployment_service.validate_deployment_requirements(
                "hyperion_testnet",
                private_key
            )
    
    @pytest.mark.asyncio
    async def test_validate_low_balance_warning(self, deployment_service, mock_web3):
        """Test warning for low balance"""
        deployment_service.network_manager.get_web3 = Mock(return_value=mock_web3)
        mock_web3.eth.get_block = Mock(return_value={'number': 12345})
        # Set balance to 0.0005 ETH (below 0.001 minimum)
        mock_web3.eth.get_balance = Mock(return_value=Web3.to_wei(0.0005, 'ether'))
        mock_web3.eth.chain_id = 133717
        
        deployment_service.network_manager.get_network_config = Mock(
            return_value={"chain_id": 133717}
        )
        
        account = Account.create()
        private_key = account.key.hex()
        
        with patch('hyperagent.core.services.deployment_service.logger') as mock_logger:
            result = await deployment_service.validate_deployment_requirements(
                "hyperion_testnet",
                private_key
            )
            
            # Should pass but log warning
            assert result["validation_passed"] is True
            mock_logger.warning.assert_called()

