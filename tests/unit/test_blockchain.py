"""Unit tests for blockchain components"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from hyperagent.blockchain.networks import NetworkManager
from hyperagent.blockchain.alith_client import AlithClient
from hyperagent.blockchain.eigenda_client import EigenDAClient
from hyperagent.blockchain.web3_manager import Web3Manager
from hyperagent.blockchain.wallet import WalletManager

pytestmark = [pytest.mark.unit]


@pytest.fixture
def mock_network_manager():
    """Mock network manager"""
    manager = MagicMock(spec=NetworkManager)
    manager.get_web3.return_value = MagicMock()
    manager.get_network_config.return_value = {
        "chain_id": 133717,
        "rpc_url": "https://testnet.example.com"
    }
    return manager


@pytest.mark.asyncio
async def test_alith_client_initialize_agent():
    """Test Alith client agent initialization"""
    client = AlithClient()
    
    result = await client.initialize_agent(
        name="test_agent",
        model="gpt-4",
        tools=["code_generation"]
    )
    
    assert result["status"] == "initialized"
    assert result["agent_name"] == "test_agent"
    assert "agent_id" in result


@pytest.mark.asyncio
async def test_alith_client_agent_reuse():
    """Test agent reuse in Alith client"""
    client = AlithClient()
    
    # Initialize agent
    result1 = await client.initialize_agent("test_agent")
    agent_id1 = result1["agent_id"]
    
    # Initialize again (should reuse)
    result2 = await client.initialize_agent("test_agent")
    
    assert result2["status"] == "reused"
    assert result2["agent_id"] == agent_id1


@pytest.mark.asyncio
async def test_alith_client_model_selection():
    """Test smart model selection (Gemini-first, OpenAI fallback)"""
    from hyperagent.core.config import settings
    
    client = AlithClient()
    
    # Test auto-selection
    with patch.object(settings, 'gemini_api_key', 'test_gemini_key'):
        with patch.object(settings, 'openai_api_key', None):
            model = client._select_model()
            assert model == "gemini-pro"
    
    # Test OpenAI fallback
    with patch.object(settings, 'gemini_api_key', None):
        with patch.object(settings, 'openai_api_key', 'test_openai_key'):
            model = client._select_model()
            assert model == "gpt-4"
    
    # Test error when no keys
    with patch.object(settings, 'gemini_api_key', None):
        with patch.object(settings, 'openai_api_key', None):
            with pytest.raises(ValueError, match="No LLM API key configured"):
                client._select_model()


@pytest.mark.asyncio
async def test_alith_client_tool_calling():
    """Test tool calling functionality"""
    client = AlithClient()
    
    # Initialize agent
    await client.initialize_agent("test_agent")
    
    # Mock tool handler
    from hyperagent.blockchain.alith_tools import get_deployment_tools
    tools = get_deployment_tools()
    
    # Mock agent response with tool calls
    mock_agent = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "I will deploy the contract"
    mock_response.tool_calls = [
        {"name": "deploy_contract", "parameters": {"bytecode": "0x123", "network": "hyperion_testnet"}}
    ]
    mock_agent.prompt_with_tools.return_value = mock_response
    
    client._agents["test_agent"]["agent"] = mock_agent
    client.sdk_available = True
    
    # Mock tool handler
    mock_tool_handler = AsyncMock()
    mock_tool_handler.execute_tool.return_value = {"success": True, "contract_address": "0xContract"}
    
    result = await client.execute_agent_with_tools(
        agent_name="test_agent",
        prompt="Deploy this contract",
        tools=tools,
        tool_handler=mock_tool_handler
    )
    
    assert result["success"] is True
    assert "tool_calls" in result
    assert len(result["tool_results"]) > 0


@pytest.mark.asyncio
async def test_alith_client_web3_agent():
    """Test Web3 agent initialization"""
    client = AlithClient()
    
    result = await client.initialize_web3_agent(
        name="web3_test_agent",
        network="hyperion_testnet"
    )
    
    assert result["status"] in ["initialized", "initialized_fallback"]
    assert result["agent_name"] == "web3_test_agent"
    assert result["network"] == "hyperion_testnet"
    assert "web3_enabled" in result


@pytest.mark.asyncio
async def test_alith_client_orchestration():
    """Test multi-agent workflow orchestration"""
    client = AlithClient()
    
    # Initialize test agents
    await client.initialize_agent("generator")
    await client.initialize_agent("auditor")
    
    # Mock execute_agent to return predictable results
    async def mock_execute(agent_name, prompt, context=None):
        if agent_name == "generator":
            return "contract_code_here"
        elif agent_name == "auditor":
            return "audit_passed"
        return "result"
    
    client.execute_agent = mock_execute
    
    workflow_steps = [
        {
            "agent": "generator",
            "task": "generate",
            "depends_on": [],
            "prompt": "Generate contract",
            "parallel": False
        },
        {
            "agent": "auditor",
            "task": "audit",
            "depends_on": ["generate"],
            "prompt": "Audit contract",
            "parallel": False
        }
    ]
    
    result = await client.orchestrate_workflow(workflow_steps)
    
    assert result["status"] == "completed"
    assert "generate" in result["results"]
    assert "audit" in result["results"]
    assert result["results"]["generate"] == "contract_code_here"
    assert result["results"]["audit"] == "audit_passed"


@pytest.mark.asyncio
async def test_eigenda_client_submit_blob():
    """Test EigenDA blob submission"""
    client = EigenDAClient(
        disperser_url="https://disperser.eigenda.xyz",
        use_authenticated=False
    )
    
    # Mock HTTP response for submission
    with patch("httpx.AsyncClient") as mock_client:
        # Mock submission response
        mock_submit_response = MagicMock()
        mock_submit_response.status_code = 200
        mock_submit_response.json.return_value = {
            "request_id": "test_request_123"
        }
        
        # Mock status polling response
        mock_status_response = MagicMock()
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {
            "status": "confirmed",
            "commitment": "0x123",
            "batch_header": {},
            "blob_index": 1
        }
        
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_client_instance.post.return_value = mock_submit_response
        mock_client_instance.get.return_value = mock_status_response
        
        # Create large enough blob (128 KiB minimum)
        test_data = b"0" * (128 * 1024)
        result = await client.submit_blob(test_data)
        
        assert "commitment" in result
        assert result["commitment"] == "0x123"


@pytest.mark.asyncio
async def test_eigenda_client_verify_availability():
    """Test EigenDA availability verification"""
    client = EigenDAClient(
        disperser_url="https://disperser.eigenda.xyz",
        use_authenticated=False
    )
    
    # Mock HTTP response for retrieval
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": "0x" + ("00" * 128 * 1024)  # Mock blob data
        }
        
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        is_available = await client.verify_availability("0x123")
        
        assert is_available is True


@pytest.mark.asyncio
async def test_web3_manager_send_transaction(mock_network_manager):
    """Test Web3Manager transaction sending"""
    manager = Web3Manager(mock_network_manager)
    
    # Mock Web3 instance
    mock_w3 = mock_network_manager.get_web3.return_value
    mock_w3.eth.gas_price = 20000000000
    mock_w3.eth.get_transaction_count.return_value = 0
    mock_w3.eth.send_raw_transaction.return_value = b"0x123"
    mock_w3.eth.wait_for_transaction_receipt.return_value = {
        "blockNumber": 12345,
        "gasUsed": 100000,
        "status": 1
    }
    
    tx = {
        "from": "0xAddress",
        "to": "0xRecipient",
        "value": 0,
        "data": "0x"
    }
    
    private_key = "0x" + "1" * 64
    
    result = await manager.send_transaction(
        "hyperion_testnet",
        tx,
        private_key,
        wait_for_confirmation=True
    )
    
    assert "tx_hash" in result
    assert "receipt" in result


@pytest.mark.asyncio
async def test_wallet_manager_add_wallet():
    """Test wallet manager add wallet"""
    from cryptography.fernet import Fernet
    
    # Generate encryption key
    key = Fernet.generate_key().decode()
    
    manager = WalletManager(key, MagicMock())
    
    private_key = "0x" + "a" * 64
    
    manager.add_wallet("test_wallet", private_key, {"description": "Test wallet"})
    
    # Verify wallet was added
    wallets = manager.list_wallets()
    assert len(wallets) == 1
    assert wallets[0]["name"] == "test_wallet"


@pytest.mark.asyncio
async def test_wallet_manager_get_account():
    """Test wallet manager get account"""
    from cryptography.fernet import Fernet
    from eth_account import Account
    
    # Generate encryption key
    key = Fernet.generate_key().decode()
    
    manager = WalletManager(key, MagicMock())
    
    # Create test account
    test_account = Account.create()
    private_key = test_account.key.hex()
    
    manager.add_wallet("test_wallet", private_key)
    
    # Get account
    account = manager.get_account("test_wallet")
    
    assert account.address == test_account.address


@pytest.mark.asyncio
async def test_wallet_manager_get_balance(mock_network_manager):
    """Test wallet manager balance checking"""
    from cryptography.fernet import Fernet
    from eth_account import Account
    
    # Generate encryption key
    key = Fernet.generate_key().decode()
    
    manager = WalletManager(key, mock_network_manager)
    
    # Create test account
    test_account = Account.create()
    private_key = test_account.key.hex()
    
    manager.add_wallet("test_wallet", private_key)
    
    # Mock Web3 balance
    mock_w3 = mock_network_manager.get_web3.return_value
    mock_w3.eth.get_balance.return_value = 1000000000000000000  # 1 ETH in Wei
    mock_w3.from_wei = lambda x, unit: x / 10**18 if unit == "ether" else x
    
    balance = await manager.get_balance("hyperion_testnet", "test_wallet")
    
    assert balance == 1.0  # 1 ETH

