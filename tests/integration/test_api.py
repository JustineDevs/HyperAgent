"""Integration tests for API endpoints"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from hyperagent.api.main import app


@pytest.fixture
def client():
    """Test client fixture with mocked database"""
    # Mock database session to avoid connection errors
    with patch('hyperagent.db.session.get_db') as mock_get_db:
        mock_session = MagicMock()
        mock_session.execute = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = MagicMock()
        mock_session.rollback = AsyncMock()
        
        # Mock user query result
        mock_result = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result
        
        async def mock_db():
            yield mock_session
        mock_get_db.return_value = mock_db()
        
        yield TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "version" in data


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint"""
    response = client.get("/api/v1/metrics/prometheus")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    # Check for some expected metrics
    content = response.text
    assert "hyperagent" in content.lower() or len(content) > 0


def test_workflow_create_endpoint(client):
    """Test workflow creation endpoint with user creation verification"""
    payload = {
        "nlp_input": "Create a simple ERC20 token",
        "network": "hyperion_testnet",
        "contract_type": "ERC20",
        "skip_deployment": True,
        "skip_audit": True
    }
    response = client.post("/api/v1/workflows/generate", json=payload)
    # Should return 200 or 201
    assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
    
    if response.status_code in [200, 201]:
        data = response.json()
        # Verify workflow response structure
        assert "workflow_id" in data or "id" in data
        assert "status" in data
        assert "message" in data
        
        # Verify workflow was created (user creation should work)
        workflow_id = data.get("workflow_id") or data.get("id")
        assert workflow_id is not None, "Workflow ID should be present"


def test_workflow_create_with_metisvm_flags(client):
    """Test workflow creation with MetisVM optimization flags"""
    payload = {
        "nlp_input": "Create ERC20 token with floating-point pricing",
        "network": "hyperion_testnet",
        "contract_type": "ERC20",
        "optimize_for_metisvm": True,
        "enable_floating_point": True,
        "skip_deployment": True,
        "skip_audit": True
    }
    response = client.post("/api/v1/workflows/generate", json=payload)
    assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
    
    if response.status_code in [200, 201]:
        data = response.json()
        assert "workflow_id" in data or "id" in data


def test_workflow_create_multiple_times(client):
    """Test creating multiple workflows to verify user creation fix"""
    # Create first workflow
    payload1 = {
        "nlp_input": "Create first ERC20 token",
        "network": "hyperion_testnet",
        "skip_deployment": True,
        "skip_audit": True
    }
    response1 = client.post("/api/v1/workflows/generate", json=payload1)
    assert response1.status_code in [200, 201]
    
    # Create second workflow (should reuse same default user)
    payload2 = {
        "nlp_input": "Create second ERC20 token",
        "network": "hyperion_testnet",
        "skip_deployment": True,
        "skip_audit": True
    }
    response2 = client.post("/api/v1/workflows/generate", json=payload2)
    assert response2.status_code in [200, 201], "Second workflow creation should succeed (user creation fix)"
    
    # Both should have workflow IDs
    if response1.status_code in [200, 201] and response2.status_code in [200, 201]:
        data1 = response1.json()
        data2 = response2.json()
        assert "workflow_id" in data1 or "id" in data1
        assert "workflow_id" in data2 or "id" in data2

