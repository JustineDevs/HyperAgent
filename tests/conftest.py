"""Pytest configuration and fixtures"""
import pytest
import asyncio
from typing import AsyncGenerator
from hyperagent.core.config import Settings
from hyperagent.cache.redis_manager import RedisManager
from hyperagent.events.event_bus import EventBus
import redis.asyncio as redis


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def redis_client() -> AsyncGenerator[redis.Redis, None]:
    """Redis client fixture"""
    client = await redis.from_url("redis://localhost:6379/0", decode_responses=True)
    yield client
    await client.close()


@pytest.fixture
async def event_bus(redis_client: redis.Redis) -> EventBus:
    """Event bus fixture"""
    return EventBus(redis_client)


@pytest.fixture
def test_settings() -> Settings:
    """Test settings fixture"""
    return Settings(
        app_name="HyperAgent-Test",
        app_version="1.0.0",
        log_level="DEBUG",
        database_url="postgresql://test:test@localhost:5432/hyperagent_test",
        redis_url="redis://localhost:6379/0",
        gemini_api_key="test_key",
        hyperion_testnet_rpc="https://hyperion-testnet.metisdevops.link",
        hyperion_testnet_chain_id=133717
    )


@pytest.fixture
async def db_session():
    """Database session fixture for integration tests"""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from hyperagent.models import Base
    
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost:5432/hyperagent_test",
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def mock_web3():
    """Mock Web3 instance"""
    from unittest.mock import MagicMock
    from web3 import Web3
    
    w3 = MagicMock(spec=Web3)
    w3.eth.gas_price = 20000000000
    w3.eth.get_transaction_count.return_value = 0
    w3.eth.send_raw_transaction.return_value = b"0x123"
    w3.eth.wait_for_transaction_receipt.return_value = {
        "contractAddress": "0xContract",
        "blockNumber": 12345,
        "gasUsed": 100000
    }
    w3.to_wei = lambda x, unit: x * 10**18 if unit == "ether" else x
    w3.from_wei = lambda x, unit: x / 10**18 if unit == "ether" else x
    
    return w3

