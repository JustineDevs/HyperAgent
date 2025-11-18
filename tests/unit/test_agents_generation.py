"""Unit tests for Generation Agent"""
import pytest

pytestmark = [pytest.mark.unit]
from unittest.mock import AsyncMock, MagicMock, patch
from hyperagent.agents.generation import GenerationAgent
from hyperagent.events.event_bus import EventBus
from hyperagent.events.event_types import EventType
from hyperagent.llm.provider import LLMProvider


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider"""
    provider = AsyncMock(spec=LLMProvider)
    provider.generate.return_value = """
    pragma solidity 0.8.27;
    
    contract TestToken {
        string public name = "Test Token";
        uint256 public totalSupply = 1000000;
        
        function transfer(address to, uint256 amount) public returns (bool) {
            return true;
        }
    }
    """
    return provider


@pytest.fixture
def mock_template_retriever():
    """Mock template retriever"""
    retriever = AsyncMock()
    retriever.retrieve_and_generate.return_value = "contract TestToken {}"
    retriever.retrieve_templates.return_value = [
        {"template_code": "contract ERC20 {}", "similarity": 0.9}
    ]
    return retriever


@pytest.fixture
def mock_event_bus():
    """Mock event bus"""
    return AsyncMock(spec=EventBus)


@pytest.mark.asyncio
async def test_generation_agent_process_success(mock_llm_provider, mock_template_retriever, mock_event_bus):
    """Test successful contract generation"""
    agent = GenerationAgent(mock_llm_provider, mock_template_retriever, mock_event_bus)
    
    input_data = {
        "nlp_description": "Create an ERC20 token with 1 million supply",
        "contract_type": "ERC20",
        "workflow_id": "test-workflow-123",
        "network": "hyperion_testnet"
    }
    
    result = await agent.process(input_data)
    
    assert result["status"] == "success"
    assert "contract_code" in result
    assert "contract_type" in result
    assert mock_event_bus.publish.called
    assert mock_llm_provider.generate.called


@pytest.mark.asyncio
async def test_generation_agent_validation(mock_llm_provider, mock_template_retriever, mock_event_bus):
    """Test input validation"""
    agent = GenerationAgent(mock_llm_provider, mock_template_retriever, mock_event_bus)
    
    # Valid input
    valid_data = {
        "nlp_description": "Create a token",
        "contract_type": "ERC20"
    }
    assert await agent.validate(valid_data) is True
    
    # Invalid input (missing description)
    invalid_data = {
        "contract_type": "ERC20"
    }
    assert await agent.validate(invalid_data) is False


@pytest.mark.asyncio
async def test_generation_agent_error_handling(mock_llm_provider, mock_template_retriever, mock_event_bus):
    """Test error handling"""
    agent = GenerationAgent(mock_llm_provider, mock_template_retriever, mock_event_bus)
    
    # Simulate LLM error
    mock_llm_provider.generate.side_effect = Exception("LLM API error")
    
    input_data = {
        "nlp_description": "Create token",
        "contract_type": "ERC20",
        "workflow_id": "test-123"
    }
    
    with pytest.raises(Exception):
        await agent.process(input_data)
    
    # Verify error event was published
    assert mock_event_bus.publish.called


@pytest.mark.asyncio
async def test_generation_agent_on_error(mock_llm_provider, mock_template_retriever, mock_event_bus):
    """Test error callback"""
    agent = GenerationAgent(mock_llm_provider, mock_template_retriever, mock_event_bus)
    
    error = Exception("Test error")
    await agent.on_error(error)
    
    # Should handle error gracefully
    assert True  # No exception raised

