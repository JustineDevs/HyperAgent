"""Network feature and compatibility API endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from hyperagent.db.session import get_db
from hyperagent.blockchain.network_features import (
    NetworkFeatureManager,
    NetworkFeature,
    NETWORK_FEATURES
)

router = APIRouter(prefix="/api/v1/networks", tags=["networks"])


class NetworkFeatureResponse(BaseModel):
    """Network feature response model"""
    network: str
    features: Dict[str, bool]
    fallbacks: Dict[str, str]
    chain_id: Optional[int] = None
    rpc_url: Optional[str] = None
    explorer: Optional[str] = None
    currency: Optional[str] = None


class NetworkCompatibilityResponse(BaseModel):
    """Network compatibility report"""
    network: str
    supports_pef: bool
    supports_metisvm: bool
    supports_eigenda: bool
    supports_batch_deployment: bool
    supports_floating_point: bool
    supports_ai_inference: bool
    fallback_strategies: Dict[str, str]
    recommendations: List[str]


@router.get("", response_model=List[NetworkFeatureResponse])
async def list_networks():
    """
    List all supported networks with their features
    
    Returns:
        List of networks with feature flags and fallback strategies
    """
    networks = []
    
    for network_name in NetworkFeatureManager.list_networks():
        config = NetworkFeatureManager.get_network_config(network_name)
        features = NetworkFeatureManager.get_features(network_name)
        
        # Convert NetworkFeature enum keys to strings
        features_dict = {feature.value: supported for feature, supported in features.items()}
        
        # Build fallback strategies
        fallbacks = {}
        for feature in NetworkFeature:
            if not features.get(feature, False):
                fallback = NetworkFeatureManager.get_fallback_strategy(network_name, feature)
                if fallback:
                    fallbacks[feature.value] = fallback
        
        networks.append(NetworkFeatureResponse(
            network=network_name,
            features=features_dict,
            fallbacks=fallbacks,
            chain_id=config.get("chain_id"),
            rpc_url=config.get("rpc_url"),
            explorer=config.get("explorer"),
            currency=config.get("currency")
        ))
    
    return networks


@router.get("/{network}/features", response_model=NetworkFeatureResponse)
async def get_network_features(network: str):
    """
    Get features for a specific network
    
    Args:
        network: Network name (e.g., "hyperion_testnet")
    
    Returns:
        Network features and fallback strategies
    """
    if network not in NETWORK_FEATURES:
        raise HTTPException(
            status_code=404,
            detail=f"Network '{network}' not found. Use /api/v1/networks to list available networks."
        )
    
    config = NetworkFeatureManager.get_network_config(network)
    features = NetworkFeatureManager.get_features(network)
    
    # Convert NetworkFeature enum keys to strings
    features_dict = {feature.value: supported for feature, supported in features.items()}
    
    # Build fallback strategies
    fallbacks = {}
    for feature in NetworkFeature:
        if not features.get(feature, False):
            fallback = NetworkFeatureManager.get_fallback_strategy(network, feature)
            if fallback:
                fallbacks[feature.value] = fallback
    
    return NetworkFeatureResponse(
        network=network,
        features=features_dict,
        fallbacks=fallbacks,
        chain_id=config.get("chain_id"),
        rpc_url=config.get("rpc_url"),
        explorer=config.get("explorer"),
        currency=config.get("currency")
    )


@router.get("/{network}/compatibility", response_model=NetworkCompatibilityResponse)
async def get_network_compatibility(network: str):
    """
    Get compatibility report for a network
    
    Args:
        network: Network name
    
    Returns:
        Detailed compatibility report with recommendations
    """
    if network not in NETWORK_FEATURES:
        raise HTTPException(
            status_code=404,
            detail=f"Network '{network}' not found"
        )
    
    features = NetworkFeatureManager.get_features(network)
    
    # Build fallback strategies
    fallback_strategies = {}
    for feature in NetworkFeature:
        if not features.get(feature, False):
            fallback = NetworkFeatureManager.get_fallback_strategy(network, feature)
            if fallback:
                fallback_strategies[feature.value] = fallback
    
    # Generate recommendations
    recommendations = []
    if not features.get(NetworkFeature.PEF, False):
        recommendations.append("Use sequential deployment instead of PEF for batch operations")
    if not features.get(NetworkFeature.METISVM, False):
        recommendations.append("MetisVM optimizations not available - contracts will use standard compilation")
    if not features.get(NetworkFeature.EIGENDA, False):
        if network.endswith("_testnet"):
            recommendations.append("EigenDA disabled on testnet for cost optimization")
        else:
            recommendations.append("EigenDA not available - contract metadata will not be stored on data availability layer")
    if not features.get(NetworkFeature.FLOATING_POINT, False):
        recommendations.append("Floating-point operations not supported - use fixed-point math libraries")
    if not features.get(NetworkFeature.AI_INFERENCE, False):
        recommendations.append("On-chain AI inference not available")
    
    return NetworkCompatibilityResponse(
        network=network,
        supports_pef=features.get(NetworkFeature.PEF, False),
        supports_metisvm=features.get(NetworkFeature.METISVM, False),
        supports_eigenda=features.get(NetworkFeature.EIGENDA, False),
        supports_batch_deployment=features.get(NetworkFeature.BATCH_DEPLOYMENT, False),
        supports_floating_point=features.get(NetworkFeature.FLOATING_POINT, False),
        supports_ai_inference=features.get(NetworkFeature.AI_INFERENCE, False),
        fallback_strategies=fallback_strategies,
        recommendations=recommendations
    )

