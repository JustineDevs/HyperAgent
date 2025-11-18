"""Unit tests for network feature detection"""
import pytest
from hyperagent.blockchain.network_features import (
    NetworkFeatureManager,
    NetworkFeature,
    NETWORK_FEATURES
)


class TestNetworkFeatureManager:
    """Test NetworkFeatureManager functionality"""
    
    def test_get_features_hyperion_testnet(self):
        """Test feature detection for Hyperion testnet"""
        features = NetworkFeatureManager.get_features("hyperion_testnet")
        
        assert features[NetworkFeature.PEF] is True
        assert features[NetworkFeature.METISVM] is True
        assert features[NetworkFeature.EIGENDA] is False
        assert features[NetworkFeature.BATCH_DEPLOYMENT] is True
        assert features[NetworkFeature.FLOATING_POINT] is True
        assert features[NetworkFeature.AI_INFERENCE] is True
    
    def test_get_features_mantle_mainnet(self):
        """Test feature detection for Mantle mainnet"""
        features = NetworkFeatureManager.get_features("mantle_mainnet")
        
        assert features[NetworkFeature.PEF] is False
        assert features[NetworkFeature.METISVM] is False
        assert features[NetworkFeature.EIGENDA] is True  # Only mainnet
        assert features[NetworkFeature.BATCH_DEPLOYMENT] is True
        assert features[NetworkFeature.FLOATING_POINT] is False
        assert features[NetworkFeature.AI_INFERENCE] is False
    
    def test_get_features_mantle_testnet(self):
        """Test feature detection for Mantle testnet"""
        features = NetworkFeatureManager.get_features("mantle_testnet")
        
        assert features[NetworkFeature.EIGENDA] is False  # Disabled on testnet
    
    def test_get_features_unknown_network(self):
        """Test feature detection for unknown network"""
        features = NetworkFeatureManager.get_features("unknown_network")
        
        # Should return basic features only
        assert features[NetworkFeature.PEF] is False
        assert features[NetworkFeature.METISVM] is False
        assert features[NetworkFeature.EIGENDA] is False
        assert features[NetworkFeature.BATCH_DEPLOYMENT] is True  # Basic sequential
        assert features[NetworkFeature.FLOATING_POINT] is False
        assert features[NetworkFeature.AI_INFERENCE] is False
    
    def test_supports_feature(self):
        """Test supports_feature method"""
        assert NetworkFeatureManager.supports_feature("hyperion_testnet", NetworkFeature.PEF) is True
        assert NetworkFeatureManager.supports_feature("mantle_testnet", NetworkFeature.PEF) is False
        assert NetworkFeatureManager.supports_feature("mantle_mainnet", NetworkFeature.EIGENDA) is True
        assert NetworkFeatureManager.supports_feature("mantle_testnet", NetworkFeature.EIGENDA) is False
    
    def test_get_network_config(self):
        """Test get_network_config method"""
        config = NetworkFeatureManager.get_network_config("hyperion_testnet")
        
        assert config["chain_id"] == 133717
        assert "rpc_url" in config
        assert "explorer" in config
        assert "currency" in config
    
    def test_get_network_config_unknown(self):
        """Test get_network_config for unknown network"""
        config = NetworkFeatureManager.get_network_config("unknown_network")
        assert config == {}
    
    def test_list_networks(self):
        """Test list_networks method"""
        networks = NetworkFeatureManager.list_networks()
        
        assert "hyperion_testnet" in networks
        assert "hyperion_mainnet" in networks
        assert "mantle_testnet" in networks
        assert "mantle_mainnet" in networks
        assert len(networks) >= 4
    
    def test_register_network(self):
        """Test custom network registration"""
        # Register a test network
        NetworkFeatureManager.register_network(
            network_name="test_network",
            chain_id=99999,
            rpc_url="https://rpc.test.network",
            features={
                NetworkFeature.PEF: False,
                NetworkFeature.METISVM: False,
                NetworkFeature.EIGENDA: False,
                NetworkFeature.BATCH_DEPLOYMENT: True,
                NetworkFeature.FLOATING_POINT: False,
                NetworkFeature.AI_INFERENCE: False
            },
            explorer="https://explorer.test.network",
            currency="TEST"
        )
        
        # Verify registration
        assert "test_network" in NetworkFeatureManager.list_networks()
        config = NetworkFeatureManager.get_network_config("test_network")
        assert config["chain_id"] == 99999
        assert config["currency"] == "TEST"
        
        # Clean up (remove test network)
        if "test_network" in NETWORK_FEATURES:
            del NETWORK_FEATURES["test_network"]
    
    def test_get_fallback_strategy(self):
        """Test fallback strategy retrieval"""
        fallback = NetworkFeatureManager.get_fallback_strategy("mantle_testnet", NetworkFeature.PEF)
        assert fallback == "sequential_deployment"
        
        fallback = NetworkFeatureManager.get_fallback_strategy("hyperion_testnet", NetworkFeature.METISVM)
        assert fallback == "standard_compilation"
        
        fallback = NetworkFeatureManager.get_fallback_strategy("mantle_testnet", NetworkFeature.EIGENDA)
        assert fallback == "skip_data_availability"


class TestNetworkFeatureEnum:
    """Test NetworkFeature enum"""
    
    def test_feature_values(self):
        """Test feature enum values"""
        assert NetworkFeature.PEF.value == "pef"
        assert NetworkFeature.METISVM.value == "metisvm"
        assert NetworkFeature.EIGENDA.value == "eigenda"
        assert NetworkFeature.BATCH_DEPLOYMENT.value == "batch_deployment"
        assert NetworkFeature.FLOATING_POINT.value == "floating_point"
        assert NetworkFeature.AI_INFERENCE.value == "ai_inference"

