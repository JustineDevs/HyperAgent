"""Network feature detection and compatibility framework

Concept: Central registry for network-specific capabilities
Logic: Map networks to supported features, enable graceful fallbacks
Benefits: Extensible, clear user messaging, prevents hard errors
"""
from typing import Dict, Any, Optional, List
from enum import Enum


class NetworkFeature(Enum):
    """Network-specific features"""
    PEF = "pef"  # Parallel Execution Framework (Hyperion)
    METISVM = "metisvm"  # MetisVM optimizations (Hyperion)
    EIGENDA = "eigenda"  # EigenDA data availability (Mantle mainnet)
    BATCH_DEPLOYMENT = "batch_deployment"  # Batch deployment support
    FLOATING_POINT = "floating_point"  # Floating-point operations (MetisVM)
    AI_INFERENCE = "ai_inference"  # On-chain AI inference (MetisVM)


NETWORK_FEATURES: Dict[str, Dict[str, Any]] = {
    "hyperion_testnet": {
        "features": {
            NetworkFeature.PEF: True,
            NetworkFeature.METISVM: True,
            NetworkFeature.BATCH_DEPLOYMENT: True,
            NetworkFeature.FLOATING_POINT: True,
            NetworkFeature.AI_INFERENCE: True,
            NetworkFeature.EIGENDA: False
        },
        "chain_id": 133717,
        "rpc_url": "https://hyperion-testnet.metisdevops.link",
        "explorer": "https://hyperion-testnet-explorer.metisdevops.link",
        "currency": "tMETIS"
    },
    "hyperion_mainnet": {
        "features": {
            NetworkFeature.PEF: True,
            NetworkFeature.METISVM: True,
            NetworkFeature.BATCH_DEPLOYMENT: True,
            NetworkFeature.FLOATING_POINT: True,
            NetworkFeature.AI_INFERENCE: True,
            NetworkFeature.EIGENDA: False
        },
        "chain_id": 133718,
        "rpc_url": "https://hyperion.metisdevops.link",
        "explorer": "https://hyperion-explorer.metisdevops.link",
        "currency": "METIS"
    },
    "mantle_testnet": {
        "features": {
            NetworkFeature.PEF: False,
            NetworkFeature.METISVM: False,
            NetworkFeature.BATCH_DEPLOYMENT: True,  # Sequential batch
            NetworkFeature.FLOATING_POINT: False,
            NetworkFeature.AI_INFERENCE: False,
            NetworkFeature.EIGENDA: False  # Cost optimization
        },
        "chain_id": 5003,
        "rpc_url": "https://rpc.sepolia.mantle.xyz",
        "explorer": "https://sepolia.mantlescan.xyz",
        "currency": "MNT"
    },
    "mantle_mainnet": {
        "features": {
            NetworkFeature.PEF: False,
            NetworkFeature.METISVM: False,
            NetworkFeature.BATCH_DEPLOYMENT: True,  # Sequential batch
            NetworkFeature.FLOATING_POINT: False,
            NetworkFeature.AI_INFERENCE: False,
            NetworkFeature.EIGENDA: True  # Only mainnet
        },
        "chain_id": 5000,
        "rpc_url": "https://rpc.mantle.xyz",
        "explorer": "https://mantlescan.xyz",
        "currency": "MNT"
    }
}


class NetworkFeatureManager:
    """
    Manage network feature detection and compatibility
    
    Concept: Centralized feature registry with fallback support
    Logic:
        1. Check network in registry
        2. Return feature map or default (basic features only)
        3. Support custom network registration
    """
    
    @staticmethod
    def get_features(network: str) -> Dict[NetworkFeature, bool]:
        """
        Get feature map for network
        
        Args:
            network: Network name (e.g., "hyperion_testnet")
        
        Returns:
            Dictionary mapping NetworkFeature to bool (supported/not supported)
        """
        if network not in NETWORK_FEATURES:
            # Unknown network - return basic features only
            return {
                NetworkFeature.PEF: False,
                NetworkFeature.METISVM: False,
                NetworkFeature.EIGENDA: False,
                NetworkFeature.BATCH_DEPLOYMENT: True,  # Basic sequential
                NetworkFeature.FLOATING_POINT: False,
                NetworkFeature.AI_INFERENCE: False
            }
        return NETWORK_FEATURES[network]["features"]
    
    @staticmethod
    def supports_feature(network: str, feature: NetworkFeature) -> bool:
        """
        Check if network supports a specific feature
        
        Args:
            network: Network name
            feature: NetworkFeature enum value
        
        Returns:
            True if feature is supported, False otherwise
        """
        features = NetworkFeatureManager.get_features(network)
        return features.get(feature, False)
    
    @staticmethod
    def get_network_config(network: str) -> Dict[str, Any]:
        """
        Get full network configuration
        
        Args:
            network: Network name
        
        Returns:
            Dictionary with features, chain_id, rpc_url, explorer, currency
        """
        return NETWORK_FEATURES.get(network, {})
    
    @staticmethod
    def list_networks() -> List[str]:
        """
        List all registered networks
        
        Returns:
            List of network names
        """
        return list(NETWORK_FEATURES.keys())
    
    @staticmethod
    def register_network(
        network_name: str,
        chain_id: int,
        rpc_url: str,
        features: Dict[NetworkFeature, bool],
        explorer: Optional[str] = None,
        currency: Optional[str] = None
    ):
        """
        Register a custom network with feature flags
        
        Concept: Allow dynamic network registration
        Logic:
            1. Add network to registry
            2. Store feature flags and configuration
            3. Network becomes available immediately
        
        Args:
            network_name: Unique network identifier
            chain_id: Blockchain chain ID
            rpc_url: RPC endpoint URL
            features: Dictionary mapping NetworkFeature to bool
            explorer: Optional block explorer URL
            currency: Optional native currency symbol
        """
        NETWORK_FEATURES[network_name] = {
            "features": features,
            "chain_id": chain_id,
            "rpc_url": rpc_url,
            "explorer": explorer,
            "currency": currency
        }
    
    @staticmethod
    def get_fallback_strategy(network: str, feature: NetworkFeature) -> Optional[str]:
        """
        Get fallback strategy for unavailable feature
        
        Args:
            network: Network name
            feature: Unavailable feature
        
        Returns:
            Fallback strategy description or None
        """
        fallbacks = {
            NetworkFeature.PEF: "sequential_deployment",
            NetworkFeature.METISVM: "standard_compilation",
            NetworkFeature.EIGENDA: "skip_data_availability",
            NetworkFeature.FLOATING_POINT: "fixed_point_math",
            NetworkFeature.AI_INFERENCE: "skip_ai_inference"
        }
        return fallbacks.get(feature)

