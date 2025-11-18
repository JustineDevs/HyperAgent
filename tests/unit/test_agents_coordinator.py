"""Unit tests for Coordinator Agent"""
import pytest

pytestmark = [pytest.mark.unit]
from unittest.mock import AsyncMock, MagicMock
from hyperagent.agents.coordinator import CoordinatorAgent
from hyperagent.architecture.soa import ServiceRegistry
from hyperagent.events.event_bus import EventBus
from hyperagent.events.event_types import EventType


@pytest.fixture
def mock_service_registry():
    """Mock service registry"""
    registry = MagicMock(spec=ServiceRegistry)
    registry.get_service.return_value = AsyncMock()
    return registry


@pytest.fixture
def mock_event_bus():
    """Mock event bus"""
    return AsyncMock(spec=EventBus)


@pytest.mark.asyncio
async def test_coordinator_execute_workflow(mock_service_registry, mock_event_bus):
    """Test workflow execution"""
    coordinator = CoordinatorAgent(mock_service_registry, mock_event_bus)
    
    workflow_id = "test-workflow-123"
    nlp_input = "Create ERC20 token"
    network = "hyperion_testnet"
    
    # Mock service execution
    mock_service = AsyncMock()
    mock_service.execute.return_value = {"status": "success", "result": "test"}
    mock_service_registry.get_service.return_value = mock_service
    
    result = await coordinator.execute_workflow(workflow_id, nlp_input, network)
    
    assert "status" in result
    assert mock_event_bus.publish.called


@pytest.mark.asyncio
async def test_coordinator_error_handling(mock_service_registry, mock_event_bus):
    """Test error handling in coordinator"""
    coordinator = CoordinatorAgent(mock_service_registry, mock_event_bus)
    
    # Simulate service error
    mock_service = AsyncMock()
    mock_service.execute.side_effect = Exception("Service error")
    mock_service_registry.get_service.return_value = mock_service
    
    workflow_id = "test-workflow-123"
    
    with pytest.raises(Exception):
        await coordinator.execute_workflow(workflow_id, "test", "hyperion_testnet")
    
    # Verify error event was published
    assert mock_event_bus.publish.called


@pytest.mark.asyncio
async def test_coordinator_on_error(mock_service_registry, mock_event_bus):
    """Test error callback"""
    coordinator = CoordinatorAgent(mock_service_registry, mock_event_bus)
    
    error = Exception("Test error")
    await coordinator.on_error(error)
    
    # Should handle error gracefully
    assert True  # No exception raised


@pytest.mark.asyncio
async def test_coordinator_workflow_stages(mock_service_registry, mock_event_bus):
    """Test workflow stage progression"""
    coordinator = CoordinatorAgent(mock_service_registry, mock_event_bus)
    
    # Track published events
    published_events = []
    
    async def capture_event(event):
        published_events.append(event.type)
    
    mock_event_bus.publish.side_effect = capture_event
    
    workflow_id = "test-workflow-123"
    
    # Mock successful service execution
    mock_service = AsyncMock()
    mock_service.execute.return_value = {"status": "success"}
    mock_service_registry.get_service.return_value = mock_service
    
    try:
        await coordinator.execute_workflow(workflow_id, "test", "hyperion_testnet")
    except Exception:
        pass  # May fail due to missing services
    
    # Should publish workflow events
    assert len(published_events) > 0

