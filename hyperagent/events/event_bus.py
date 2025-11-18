"""Event bus implementation using Redis Streams"""
import json
import uuid
from typing import Dict, List, Callable, Optional, AsyncGenerator, Any
from datetime import datetime
import redis.asyncio as redis
from hyperagent.events.event_types import Event, EventType


class EventBus:
    """
    Event Bus Pattern
    
    Concept: Central hub for event publishing/subscribing
    Logic: Publishers send events, subscribers receive via Redis Streams
    Benefits: Decoupling, scalability, persistence
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self._handlers: Dict[EventType, List[Callable[..., Any]]] = {}
    
    async def publish(self, event: Event) -> None:
        """
        Publish event to Redis Stream
        
        Logic Flow:
        1. Serialize event to JSON
        2. Store in Redis Stream with event type as key
        3. Notify local subscribers
        4. Return immediately (async)
        """
        # Store in Redis Stream
        stream_key = f"events:{event.type.value}"
        await self.redis.xadd(
            stream_key,
            {"data": json.dumps(event.to_dict())},
            id="*"  # Auto-generate ID
        )
        
        # Notify local handlers
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                try:
                    await handler(event)
                except Exception as e:
                    # Log error but don't fail
                    print(f"Handler error: {e}")
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """
        Subscribe to event type
        
        Example:
            async def on_generation_complete(event: Event):
                print(f"Contract generated: {event.data['contract_code']}")
            
            event_bus.subscribe(EventType.GENERATION_COMPLETED, on_generation_complete)
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def consume_stream(self, event_type: EventType, 
                           consumer_group: str = "default") -> AsyncGenerator[Event, None]:
        """
        Consume events from Redis Stream
        
        Logic: Read events from stream, process, acknowledge
        Use Case: Background workers processing events
        """
        stream_key = f"events:{event_type.value}"
        
        # Create consumer group if not exists
        try:
            await self.redis.xgroup_create(
                stream_key, consumer_group, id="0", mkstream=True
            )
        except redis.ResponseError:
            pass  # Group already exists
        
        while True:
            # Read events
            messages = await self.redis.xreadgroup(
                consumer_group,
                "worker-1",
                {stream_key: ">"},
                count=10,
                block=1000
            )
            
            for stream, events in messages:
                for event_id, event_data in events:
                    # Process event
                    event_dict = json.loads(event_data[b"data"])
                    # Reconstruct Event object
                    event = Event(
                        id=event_dict["id"],
                        type=EventType(event_dict["type"]),
                        workflow_id=event_dict["workflow_id"],
                        timestamp=datetime.fromisoformat(event_dict["timestamp"]),
                        data=event_dict["data"],
                        source_agent=event_dict["source_agent"],
                        metadata=event_dict.get("metadata")
                    )
                    
                    # Acknowledge
                    await self.redis.xack(stream_key, consumer_group, event_id)
                    
                    yield event

