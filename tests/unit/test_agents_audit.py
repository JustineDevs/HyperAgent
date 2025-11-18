"""Unit tests for Audit Agent"""
import pytest

pytestmark = [pytest.mark.unit]
from unittest.mock import AsyncMock, MagicMock
from hyperagent.agents.audit import AuditAgent
from hyperagent.security.audit import SecurityAuditor
from hyperagent.events.event_bus import EventBus


@pytest.fixture
def mock_security_auditor():
    """Mock security auditor"""
    auditor = AsyncMock(spec=SecurityAuditor)
    auditor.run_slither.return_value = {
        "status": "success",
        "vulnerabilities": [
            {"severity": "high", "title": "Reentrancy", "tool": "slither"}
        ],
        "summary": {
            "total": 1,
            "by_severity": {"high": 1, "medium": 0, "low": 0}
        }
    }
    auditor.run_mythril.return_value = {
        "status": "success",
        "vulnerabilities": [],
        "summary": {"total": 0}
    }
    auditor.run_echidna.return_value = {
        "status": "success",
        "vulnerabilities": []
    }
    return auditor


@pytest.fixture
def mock_event_bus():
    """Mock event bus"""
    return AsyncMock(spec=EventBus)


@pytest.mark.asyncio
async def test_audit_agent_process_success(mock_security_auditor, mock_event_bus):
    """Test successful audit execution"""
    agent = AuditAgent(mock_security_auditor, mock_event_bus)
    
    input_data = {
        "contract_code": "pragma solidity 0.8.27; contract Test {}",
        "contract_path": "/tmp/test.sol",
        "workflow_id": "test-workflow-123",
        "audit_level": "standard"
    }
    
    result = await agent.process(input_data)
    
    assert result["status"] == "success"
    assert "vulnerabilities" in result
    assert "overall_risk_score" in result
    assert mock_security_auditor.run_slither.called
    assert mock_event_bus.publish.called


@pytest.mark.asyncio
async def test_audit_agent_validation(mock_security_auditor, mock_event_bus):
    """Test input validation"""
    agent = AuditAgent(mock_security_auditor, mock_event_bus)
    
    # Valid input
    valid_data = {"contract_code": "contract Test {}"}
    assert await agent.validate(valid_data) is True
    
    # Invalid input
    invalid_data = {}
    assert await agent.validate(invalid_data) is False


@pytest.mark.asyncio
async def test_audit_agent_risk_scoring(mock_security_auditor, mock_event_bus):
    """Test risk score calculation"""
    agent = AuditAgent(mock_security_auditor, mock_event_bus)
    
    # High severity vulnerabilities
    mock_security_auditor.run_slither.return_value = {
        "status": "success",
        "vulnerabilities": [
            {"severity": "critical", "title": "Critical Issue"},
            {"severity": "high", "title": "High Issue"}
        ],
        "summary": {"by_severity": {"critical": 1, "high": 1}}
    }
    
    input_data = {
        "contract_code": "contract Test {}",
        "workflow_id": "test-123"
    }
    
    result = await agent.process(input_data)
    
    # Risk score should be high
    assert result["overall_risk_score"] > 30
    assert result["audit_status"] in ["warning", "failed"]


@pytest.mark.asyncio
async def test_audit_agent_error_handling(mock_security_auditor, mock_event_bus):
    """Test error handling"""
    agent = AuditAgent(mock_security_auditor, mock_event_bus)
    
    # Simulate audit tool error
    mock_security_auditor.run_slither.side_effect = Exception("Slither error")
    
    input_data = {
        "contract_code": "contract Test {}",
        "workflow_id": "test-123"
    }
    
    with pytest.raises(Exception):
        await agent.process(input_data)

