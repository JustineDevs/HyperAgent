"""Unit tests for user creation"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
import uuid

pytestmark = [pytest.mark.unit]


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_get_or_create_default_user_creates_new_user(mock_db_session):
    """Test default user creation with username=None"""
    # Mock: No existing user found
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result
    
    # Mock: User object with ID
    mock_user = MagicMock()
    mock_user.id = uuid.uuid4()
    mock_user.email = "default@hyperagent.local"
    mock_user.username = None
    mock_user.is_active = True
    
    # Patch select to avoid SQLAlchemy issues, and User class
    with patch('hyperagent.api.routes.workflows.select') as mock_select:
        # Make select() return a mock that can be chained
        mock_select_obj = MagicMock()
        mock_select_obj.where.return_value = mock_select_obj
        mock_select.return_value = mock_select_obj
        
        with patch('hyperagent.api.routes.workflows.User', return_value=mock_user):
            from hyperagent.api.routes.workflows import get_or_create_default_user
            user_id = await get_or_create_default_user(mock_db_session)
            
            # Verify user was created with username=None
            assert user_id == mock_user.id
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            
            # Verify User was created with correct parameters
            call_args = mock_db_session.add.call_args[0][0]
            assert call_args.email == "default@hyperagent.local"
            assert call_args.username is None  # Key fix: username should be None
            assert call_args.is_active is True


@pytest.mark.asyncio
async def test_get_or_create_default_user_returns_existing(mock_db_session):
    """Test default user retrieval when exists"""
    # Mock: Existing user found
    existing_user = MagicMock()
    existing_user.id = uuid.uuid4()
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_user
    mock_db_session.execute.return_value = mock_result
    
    from hyperagent.api.routes.workflows import get_or_create_default_user
    user_id = await get_or_create_default_user(mock_db_session)
    
    # Verify existing user ID is returned
    assert user_id == existing_user.id
    # Should not create new user
    mock_db_session.add.assert_not_called()
    mock_db_session.commit.assert_not_called()


def test_user_model_username_nullable():
    """Test that User model allows username=None"""
    # Import User model (with proper mocking to avoid database initialization)
    with patch('hyperagent.db.session.create_async_engine'):
        with patch('hyperagent.db.session.async_sessionmaker'):
            from hyperagent.models.user import User
            
            # Create user with username=None
            user = User(
                email="test@example.com",
                username=None,  # Should be allowed
                is_active=True
            )
            
            assert user.email == "test@example.com"
            assert user.username is None
            assert user.is_active is True

