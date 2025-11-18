"""Unit tests for enhanced EigenDA client"""
import pytest
from unittest.mock import AsyncMock, patch
from hyperagent.blockchain.eigenda_client import EigenDAClient, EigenDAError


@pytest.fixture
def eigenda_client():
    """Create EigenDAClient instance"""
    return EigenDAClient(
        disperser_url="https://disperser.eigenda.xyz",
        use_authenticated=False
    )


@pytest.mark.asyncio
async def test_batch_submit_success(eigenda_client):
    """Test successful batch submission"""
    blobs = [b"blob1", b"blob2", b"blob3"]
    
    with patch.object(eigenda_client, 'submit_blob', new_callable=AsyncMock) as mock_submit:
        mock_submit.return_value = {"commitment": "0x1234"}
        
        result = await eigenda_client.batch_submit(blobs)
        
        assert result["count"] == 3
        assert result["success_count"] == 3
        assert len(result["commitments"]) == 3
        assert mock_submit.call_count == 3


@pytest.mark.asyncio
async def test_batch_submit_with_errors(eigenda_client):
    """Test batch submission with some failures"""
    blobs = [b"blob1", b"blob2"]
    
    with patch.object(eigenda_client, 'submit_blob', new_callable=AsyncMock) as mock_submit:
        mock_submit.side_effect = [
            {"commitment": "0x1234"},
            EigenDAError("Submission failed")
        ]
        
        result = await eigenda_client.batch_submit(blobs)
        
        assert result["success_count"] == 1
        assert result["failed_count"] == 1
        assert len(result["errors"]) == 1


@pytest.mark.asyncio
async def test_store_contract_metadata(eigenda_client):
    """Test storing contract metadata"""
    contract_address = "0xabcd"
    abi = [{"type": "function", "name": "test"}]
    source_code = "contract Test {}"
    deployment_info = {"tx_hash": "0x1234", "block_number": 100}
    
    with patch.object(eigenda_client, 'submit_blob', new_callable=AsyncMock) as mock_submit:
        mock_submit.return_value = {"commitment": "0x5678"}
        
        commitment = await eigenda_client.store_contract_metadata(
            contract_address, abi, source_code, deployment_info
        )
        
        assert commitment == "0x5678"
        assert mock_submit.called
        # Verify metadata was serialized correctly
        call_args = mock_submit.call_args[0][0]
        assert isinstance(call_args, bytes)


@pytest.mark.asyncio
async def test_retrieve_contract_metadata(eigenda_client):
    """Test retrieving contract metadata"""
    commitment = "0x5678"
    metadata_json = '{"contract_address": "0xabcd", "abi": []}'
    
    with patch.object(eigenda_client, 'retrieve_blob', new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = metadata_json.encode('utf-8')
        
        metadata = await eigenda_client.retrieve_contract_metadata(commitment)
        
        assert metadata["contract_address"] == "0xabcd"
        assert "abi" in metadata
