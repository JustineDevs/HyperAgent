"""Integration tests for database operations"""
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.requires_db]
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from hyperagent.models import Base
from hyperagent.models.workflow import Workflow, WorkflowStatus
from hyperagent.models.contract import GeneratedContract
import uuid
from datetime import datetime


@pytest.fixture
async def db_session():
    """Create test database session"""
    # Use test database URL
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


@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_workflow_creation(db_session: AsyncSession):
    """Test workflow creation in database"""
    workflow = Workflow(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Test Workflow",
        description="Test description",
        nlp_input="Create ERC20 token",
        network="hyperion_testnet",
        is_testnet=True,
        status=WorkflowStatus.CREATED.value,
        progress_percentage=0
    )
    
    db_session.add(workflow)
    await db_session.commit()
    await db_session.refresh(workflow)
    
    assert workflow.id is not None
    assert workflow.status == WorkflowStatus.CREATED.value
    assert workflow.network == "hyperion_testnet"


@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_workflow_status_update(db_session: AsyncSession):
    """Test workflow status update"""
    workflow = Workflow(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Test Workflow",
        nlp_input="Create token",
        network="hyperion_testnet",
        status=WorkflowStatus.CREATED.value
    )
    
    db_session.add(workflow)
    await db_session.commit()
    
    # Update status
    workflow.status = WorkflowStatus.GENERATING.value
    workflow.progress_percentage = 25
    await db_session.commit()
    await db_session.refresh(workflow)
    
    assert workflow.status == WorkflowStatus.GENERATING.value
    assert workflow.progress_percentage == 25


@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_contract_creation(db_session: AsyncSession):
    """Test contract creation with workflow relationship"""
    workflow = Workflow(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Test Workflow",
        nlp_input="Create token",
        network="hyperion_testnet",
        status=WorkflowStatus.CREATED.value
    )
    
    db_session.add(workflow)
    await db_session.commit()
    
    contract = GeneratedContract(
        id=uuid.uuid4(),
        workflow_id=workflow.id,
        contract_name="TestToken",
        contract_type="ERC20",
        source_code="pragma solidity 0.8.27; contract TestToken {}",
        solidity_version="0.8.27"
    )
    
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)
    
    assert contract.id is not None
    assert contract.workflow_id == workflow.id
    assert contract.contract_name == "TestToken"


@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_workflow_contract_relationship(db_session: AsyncSession):
    """Test workflow-contract relationship"""
    workflow = Workflow(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Test Workflow",
        nlp_input="Create token",
        network="hyperion_testnet",
        status=WorkflowStatus.CREATED.value
    )
    
    db_session.add(workflow)
    await db_session.commit()
    
    contract = GeneratedContract(
        id=uuid.uuid4(),
        workflow_id=workflow.id,
        contract_name="TestToken",
        source_code="contract TestToken {}"
    )
    
    db_session.add(contract)
    await db_session.commit()
    
    # Test relationship
    await db_session.refresh(workflow)
    assert len(workflow.contracts) == 1
    assert workflow.contracts[0].id == contract.id

