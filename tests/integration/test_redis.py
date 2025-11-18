"""Integration tests for Redis operations"""
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.requires_redis]
import redis.asyncio as redis
from hyperagent.cache.redis_manager import RedisManager
from hyperagent.events.event_bus import EventBus
from hyperagent.events.event_types import Event, EventType
from datetime import datetime
import uuid


@pytest.mark.asyncio
@pytest.mark.requires_redis
async def test_redis_manager_set_get(redis_client: redis.Redis):
    """Test Redis cache operations"""
    # RedisManager expects a URL string, not a Redis client
    # Use the redis_client's connection info or create manager with URL
    from hyperagent.core.config import settings
    manager = RedisManager(settings.redis_url)
    
    key = "test:key"
    value = {"test": "data", "number": 123}
    
    await manager.set(key, value, ttl=60)
    result = await manager.get(key)
    
    assert result == value


@pytest.mark.asyncio
@pytest.mark.requires_redis
async def test_redis_manager_workflow_state(redis_client: redis.Redis):
    """Test workflow state caching"""
    from hyperagent.core.config import settings
    manager = RedisManager(settings.redis_url)
    
    workflow_id = "test-workflow-123"
    state = {
        "status": "generating",
        "progress": 50,
        "contract_code": "contract Test {}"
    }
    
    await manager.set_workflow_state(workflow_id, state)
    retrieved_state = await manager.get_workflow_state(workflow_id)
    
    assert retrieved_state == state
    assert retrieved_state["status"] == "generating"
    assert retrieved_state["progress"] == 50


@pytest.mark.asyncio
@pytest.mark.requires_redis
async def test_event_bus_publish_consume(redis_client: redis.Redis):
    """Test event bus publish and consume"""
    event_bus = EventBus(redis_client)
    
    event = Event(
        id=str(uuid.uuid4()),
        type=EventType.WORKFLOW_CREATED,
        workflow_id="test-workflow-123",
        timestamp=datetime.now(),
        data={"test": "data"},
        source_agent="test"
    )
    
    # Publish event
    await event_bus.publish(event)
    
    # Consume event
    consumed_events = []
    async for consumed_event in event_bus.consume_stream(EventType.WORKFLOW_CREATED, "test_group"):
        consumed_events.append(consumed_event)
        if len(consumed_events) >= 1:
            break
    
    assert len(consumed_events) > 0
    assert consumed_events[0].workflow_id == event.workflow_id
    assert consumed_events[0].type == event.type


@pytest.mark.asyncio
@pytest.mark.requires_redis
async def test_event_bus_subscription(redis_client: redis.Redis):
    """Test event bus subscription"""
    event_bus = EventBus(redis_client)
    
    received_events = []
    
    async def handler(event: Event):
        received_events.append(event)
    
    # Subscribe
    event_bus.subscribe(EventType.WORKFLOW_CREATED, handler)
    
    # Publish event
    event = Event(
        id=str(uuid.uuid4()),
        type=EventType.WORKFLOW_CREATED,
        workflow_id="test-workflow-123",
        timestamp=datetime.now(),
        data={},
        source_agent="test"
    )
    
    await event_bus.publish(event)
    
    # Give handler time to process
    import asyncio
    await asyncio.sleep(0.1)
    
    # Handler should have been called
    assert len(received_events) > 0

