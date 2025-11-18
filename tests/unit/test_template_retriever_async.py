"""Unit tests for TemplateRetriever async session validation"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from hyperagent.rag.template_retriever import TemplateRetriever
from hyperagent.llm.provider import LLMProvider


class TestTemplateRetrieverAsyncSession:
    """Test async session validation in TemplateRetriever"""
    
    @pytest.mark.asyncio
    async def test_template_retriever_valid_async_session(self):
        """Test that TemplateRetriever accepts valid async session"""
        # Create mock async session
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        
        # Create mock LLM provider
        mock_llm = Mock(spec=LLMProvider)
        
        # Should not raise exception
        retriever = TemplateRetriever(mock_llm, mock_session)
        assert retriever.db_session == mock_session
        assert retriever.llm_provider == mock_llm
    
    def test_template_retriever_invalid_session_type(self):
        """Test that TemplateRetriever rejects invalid session types"""
        mock_llm = Mock(spec=LLMProvider)
        
        # Test with string (invalid)
        with pytest.raises(TypeError, match="db_session must be an async session"):
            TemplateRetriever(mock_llm, "invalid_session")
        
        # Test with None
        with pytest.raises(TypeError, match="db_session must be an async session"):
            TemplateRetriever(mock_llm, None)
        
        # Test with sync session (no execute method)
        sync_session = Mock()
        del sync_session.execute
        with pytest.raises(TypeError, match="db_session must be an async session"):
            TemplateRetriever(mock_llm, sync_session)
    
    def test_template_retriever_sync_session_rejected(self):
        """Test that sync sessions are rejected"""
        import inspect
        from sqlalchemy.orm import Session
        
        mock_llm = Mock(spec=LLMProvider)
        
        # Create a mock sync session
        sync_session = Mock(spec=Session)
        # Make execute NOT a coroutine function
        sync_session.execute = Mock()  # Regular function, not async
        
        with pytest.raises(TypeError, match="db_session.execute must be an async method"):
            TemplateRetriever(mock_llm, sync_session)

