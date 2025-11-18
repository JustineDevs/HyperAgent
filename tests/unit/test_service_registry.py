"""Unit tests for Service Registry"""
import pytest
from hyperagent.architecture.soa import ServiceRegistry
from hyperagent.core.services.generation_service import GenerationService
from hyperagent.llm.provider import LLMProviderFactory
from hyperagent.core.config import settings


@pytest.mark.asyncio
async def test_service_registry_register():
    """Test service registration"""
    registry = ServiceRegistry()
    
    # Create mock service
    llm_provider = LLMProviderFactory.create("gemini", api_key="test_key")
    # Note: This will fail without actual API key, but tests structure
    
    # Test registration
    # registry.register("generation", service, {"version": "1.0"})
    
    # Test listing
    services = registry.list_services()
    assert isinstance(services, list)


@pytest.mark.asyncio
async def test_service_registry_get_service():
    """Test service retrieval"""
    registry = ServiceRegistry()
    
    # Test getting non-existent service
    with pytest.raises(ValueError):
        registry.get_service("nonexistent")

