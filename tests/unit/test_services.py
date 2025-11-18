"""Unit tests for core services"""
import pytest

pytestmark = [pytest.mark.unit]
from unittest.mock import AsyncMock, MagicMock
from hyperagent.core.services.generation_service import GenerationService
from hyperagent.core.services.audit_service import AuditService
from hyperagent.core.services.deployment_service import DeploymentService
from hyperagent.llm.provider import LLMProvider
from hyperagent.rag.template_retriever import TemplateRetriever
from hyperagent.security.audit import SecurityAuditor
from hyperagent.blockchain.networks import NetworkManager
from hyperagent.blockchain.alith_client import AlithClient
from hyperagent.blockchain.eigenda_client import EigenDAClient


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider"""
    provider = AsyncMock(spec=LLMProvider)
    provider.generate = AsyncMock(return_value="pragma solidity 0.8.27; contract Test {}")
    return provider


@pytest.fixture
def mock_template_retriever():
    """Mock template retriever"""
    retriever = AsyncMock(spec=TemplateRetriever)
    retriever.retrieve_templates.return_value = [
        {"template_code": "contract ERC20 {}", "similarity": 0.9}
    ]
    return retriever


@pytest.fixture
def mock_security_auditor():
    """Mock security auditor"""
    auditor = AsyncMock(spec=SecurityAuditor)
    auditor.run_slither.return_value = {
        "status": "success",
        "vulnerabilities": [],
        "summary": {"total": 0}
    }
    return auditor


@pytest.fixture
def mock_network_manager():
    """Mock network manager"""
    manager = MagicMock(spec=NetworkManager)
    manager.get_web3.return_value = MagicMock()
    manager.get_network_config.return_value = {"chain_id": 133717}
    return manager


@pytest.mark.asyncio
async def test_generation_service_process(mock_llm_provider, mock_template_retriever):
    """Test generation service"""
    service = GenerationService(mock_llm_provider, mock_template_retriever)
    
    input_data = {
        "nlp_description": "Create ERC20 token",
        "contract_type": "ERC20",
        "network": "hyperion_testnet"
    }
    
    result = await service.process(input_data)
    
    assert result["status"] == "success"
    assert "contract_code" in result
    assert mock_llm_provider.call_llm.called
    assert mock_template_retriever.retrieve_templates.called


@pytest.mark.asyncio
async def test_generation_service_validation(mock_llm_provider, mock_template_retriever):
    """Test generation service validation"""
    service = GenerationService(mock_llm_provider, mock_template_retriever)
    
    # Valid input
    valid_data = {"nlp_description": "Create a token with 1 million supply"}
    assert await service.validate(valid_data) is True
    
    # Invalid input (too short)
    invalid_data = {"nlp_description": "token"}
    assert await service.validate(invalid_data) is False


@pytest.mark.asyncio
async def test_audit_service_process(mock_security_auditor):
    """Test audit service"""
    service = AuditService(mock_security_auditor)
    
    input_data = {
        "contract_code": "pragma solidity 0.8.27; contract Test {}",
        "contract_path": "/tmp/test.sol"
    }
    
    result = await service.process(input_data)
    
    assert result["status"] == "success"
    assert "vulnerabilities" in result
    assert "overall_risk_score" in result
    assert mock_security_auditor.run_slither.called


@pytest.mark.asyncio
async def test_deployment_service_process(mock_network_manager):
    """Test deployment service"""
    alith_client = AsyncMock(spec=AlithClient)
    eigenda_client = AsyncMock(spec=EigenDAClient)
    
    service = DeploymentService(mock_network_manager, alith_client, eigenda_client)
    
    # Mock Web3 transaction
    mock_w3 = mock_network_manager.get_web3.return_value
    mock_w3.eth.contract.return_value.constructor.return_value.estimate_gas.return_value = 100000
    mock_w3.eth.gas_price = 20000000000
    mock_w3.eth.get_transaction_count.return_value = 0
    mock_w3.eth.send_raw_transaction.return_value = b"0x123"
    mock_w3.eth.wait_for_transaction_receipt.return_value = {
        "contractAddress": "0xContract",
        "blockNumber": 12345,
        "gasUsed": 100000
    }
    
    input_data = {
        "compiled_contract": {
            "abi": [],
            "bytecode": "0x6080604052348015600f57600080fd5b50"
        },
        "network": "hyperion_testnet",
        "private_key": "0x" + "1" * 64
    }
    
    result = await service.process(input_data)
    
    assert result["status"] == "success"
    assert "contract_address" in result
    assert "transaction_hash" in result

