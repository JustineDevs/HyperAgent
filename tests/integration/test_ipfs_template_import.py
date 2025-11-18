"""Integration tests for IPFS template import"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from hyperagent.api.routes.templates import import_template_from_ipfs, IPFSImportRequest
from hyperagent.models.template import ContractTemplate
from hyperagent.core.config import settings


class TestIPFSTemplateImport:
    """Test IPFS template import functionality"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock async database session"""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = Mock()
        return session
    
    @pytest.fixture
    def sample_template_code(self):
        """Sample Solidity template code"""
        return """pragma solidity ^0.8.30;

contract SimpleStorage {
    uint256 public storedData;
    
    constructor(uint256 _initialValue) {
        storedData = _initialValue;
    }
    
    function set(uint256 _value) public {
        storedData = _value;
    }
    
    function get() public view returns (uint256) {
        return storedData;
    }
}"""
    
    @pytest.mark.asyncio
    async def test_import_template_from_ipfs_success(
        self, mock_db_session, sample_template_code
    ):
        """Test successful template import from IPFS"""
        # Mock IPFS hash
        ipfs_hash = "QmTestHash123456789"
        
        # Mock PinataManager
        mock_pinata = AsyncMock()
        mock_pinata.retrieve_template = AsyncMock(return_value=sample_template_code)
        mock_pinata.verify_template_integrity = AsyncMock(return_value=True)
        
        # Mock LLM provider for embedding
        mock_embedding = [0.1] * 1536  # 1536-dim embedding
        
        with patch('hyperagent.api.routes.templates.PinataManager', return_value=mock_pinata):
            with patch('hyperagent.api.routes.templates.LLMProviderFactory') as mock_factory:
                mock_llm = AsyncMock()
                mock_llm.embed = AsyncMock(return_value=mock_embedding)
                mock_factory.create = Mock(return_value=mock_llm)
                
                # Mock database query (no existing template)
                mock_result = AsyncMock()
                mock_result.scalar_one_or_none = Mock(return_value=None)
                mock_db_session.execute = AsyncMock(return_value=mock_result)
                
                # Mock settings
                with patch.object(settings, 'pinata_jwt', 'test_jwt'):
                    with patch.object(settings, 'gemini_api_key', 'test_key'):
                        with patch.object(settings, 'gemini_model', 'gemini-2.5-flash'):
                            request = IPFSImportRequest(
                                ipfs_hash=ipfs_hash,
                                name="SimpleStorage",
                                contract_type="Storage",
                                description="Simple storage contract",
                                verify_integrity=True
                            )
                            
                            # Should not raise exception
                            result = await import_template_from_ipfs(request, mock_db_session)
                            
                            # Verify Pinata was called
                            mock_pinata.retrieve_template.assert_called_once_with(ipfs_hash)
                            mock_pinata.verify_template_integrity.assert_called_once()
                            
                            # Verify embedding was generated
                            mock_llm.embed.assert_called_once()
                            
                            # Verify database operations
                            mock_db_session.add.assert_called_once()
                            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_import_template_invalid_ipfs_hash(self, mock_db_session):
        """Test import fails with invalid IPFS hash format"""
        request = IPFSImportRequest(
            ipfs_hash="invalid_hash",
            verify_integrity=True
        )
        
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException, match="Invalid IPFS hash format"):
            await import_template_from_ipfs(request, mock_db_session)
    
    @pytest.mark.asyncio
    async def test_import_template_not_found_on_ipfs(self, mock_db_session):
        """Test import fails when template not found on IPFS"""
        ipfs_hash = "QmTestHash123456789"
        
        mock_pinata = AsyncMock()
        mock_pinata.retrieve_template = AsyncMock(
            side_effect=Exception("Template not found")
        )
        
        with patch('hyperagent.api.routes.templates.PinataManager', return_value=mock_pinata):
            with patch.object(settings, 'pinata_jwt', 'test_jwt'):
                request = IPFSImportRequest(ipfs_hash=ipfs_hash)
                
                from fastapi import HTTPException
                
                with pytest.raises(HTTPException, match="Template not found on IPFS"):
                    await import_template_from_ipfs(request, mock_db_session)
    
    @pytest.mark.asyncio
    async def test_import_template_integrity_verification_failure(
        self, mock_db_session, sample_template_code
    ):
        """Test import fails when integrity verification fails"""
        ipfs_hash = "QmTestHash123456789"
        
        mock_pinata = AsyncMock()
        mock_pinata.retrieve_template = AsyncMock(return_value=sample_template_code)
        mock_pinata.verify_template_integrity = AsyncMock(return_value=False)
        
        with patch('hyperagent.api.routes.templates.PinataManager', return_value=mock_pinata):
            with patch.object(settings, 'pinata_jwt', 'test_jwt'):
                request = IPFSImportRequest(
                    ipfs_hash=ipfs_hash,
                    verify_integrity=True
                )
                
                from fastapi import HTTPException
                
                with pytest.raises(HTTPException, match="integrity verification failed"):
                    await import_template_from_ipfs(request, mock_db_session)

