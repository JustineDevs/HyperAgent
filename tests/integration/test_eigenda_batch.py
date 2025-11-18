"""Integration tests for EigenDA batch operations"""
import pytest
from unittest.mock import AsyncMock, patch
from hyperagent.blockchain.eigenda_client import EigenDAClient, EigenDAError

pytestmark = [pytest.mark.integration, pytest.mark.requires_api]


@pytest.fixture
def eigenda_client():
    """EigenDAClient fixture"""
    return EigenDAClient(
        disperser_url="https://disperser.eigenda.xyz",
        private_key=None,
        use_authenticated=False
    )


@pytest.mark.asyncio
async def test_eigenda_batch_metadata_storage_mocked(eigenda_client):
    """Test batch metadata storage with mocked EigenDA"""
    contract_metadata = [
        {
            "contract_address": "0xContract1",
            "abi": [{"type": "function", "name": "test1"}],
            "source_code": "contract Contract1 {}",
            "deployment_info": {"tx_hash": "0xTx1", "block_number": 123}
        },
        {
            "contract_address": "0xContract2",
            "abi": [{"type": "function", "name": "test2"}],
            "source_code": "contract Contract2 {}",
            "deployment_info": {"tx_hash": "0xTx2", "block_number": 124}
        }
    ]
    
    # Mock submit_blob to return commitments
    with patch.object(eigenda_client, 'submit_blob') as mock_submit:
        mock_submit.side_effect = [
            {"commitment": "0xCommit1"},
            {"commitment": "0xCommit2"}
        ]
        
        commitments = []
        for metadata in contract_metadata:
            commitment = await eigenda_client.store_contract_metadata(
                metadata["contract_address"],
                metadata["abi"],
                metadata["source_code"],
                metadata["deployment_info"]
            )
            commitments.append(commitment)
        
        assert len(commitments) == 2
        assert commitments[0] == "0xCommit1"
        assert commitments[1] == "0xCommit2"


@pytest.mark.asyncio
async def test_eigenda_batch_submit_multiple_blobs(eigenda_client):
    """Test batch submission of multiple blobs"""
    blobs = [
        b"blob_data_1" * 1000,  # Simulate blob data
        b"blob_data_2" * 1000,
        b"blob_data_3" * 1000
    ]
    
    # Mock submit_blob
    with patch.object(eigenda_client, 'submit_blob') as mock_submit:
        mock_submit.side_effect = [
            {"commitment": f"0xCommit{i}"} for i in range(1, 4)
        ]
        
        result = await eigenda_client.batch_submit(blobs)
        
        assert result["count"] == 3
        assert result["success_count"] == 3
        assert result["failed_count"] == 0
        assert len(result["commitments"]) == 3


@pytest.mark.asyncio
async def test_eigenda_metadata_retrieval_mocked(eigenda_client):
    """Test retrieving contract metadata from EigenDA"""
    commitment = "0xMetadataCommitment"
    expected_metadata = {
        "contract_address": "0xContract",
        "abi": [{"type": "function"}],
        "source_code": "contract Test {}",
        "deployment_info": {"tx_hash": "0xTx", "block_number": 123},
        "timestamp": "2025-01-27T00:00:00",
        "version": "1.0"
    }
    
    # Mock retrieve_blob
    with patch.object(eigenda_client, 'retrieve_blob') as mock_retrieve:
        import json
        mock_retrieve.return_value = json.dumps(expected_metadata).encode('utf-8')
        
        metadata = await eigenda_client.retrieve_contract_metadata(commitment)
        
        assert metadata["contract_address"] == expected_metadata["contract_address"]
        assert metadata["abi"] == expected_metadata["abi"]
        assert metadata["source_code"] == expected_metadata["source_code"]


@pytest.mark.asyncio
@pytest.mark.requires_api
async def test_eigenda_batch_submit_real_network(eigenda_client):
    """
    Test batch submission on real EigenDA network
    
    Note: This test requires:
    - Real network connection
    - Valid blob data (128 KiB - 16 MiB, multiple of 32 bytes)
    """
    # Skip if no network access
    pytest.skip("Requires real network connection and valid blob data")
    
    # Create test blobs (must meet size requirements)
    blobs = [
        b"0" * (128 * 1024),  # 128 KiB minimum
        b"1" * (128 * 1024)
    ]
    
    result = await eigenda_client.batch_submit(blobs)
    
    assert result["success_count"] > 0
    assert len(result["commitments"]) > 0

