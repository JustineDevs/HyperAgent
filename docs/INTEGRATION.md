# EigenDA & Alith SDK Integration Guide

**Generated**: 2025-01-27  
**Purpose**: Complete integration guide for EigenDA and Alith SDKs in HyperAgent  
**Status**: ✅ **COMPLETED**

---

## Implementation Summary

**Status**: ✅ **COMPLETE**

Complete implementation of EigenDA and Alith SDK integrations based on official documentation and best practices.

### Files Modified

1. **`hyperagent/blockchain/eigenda_client.py`** ✅
   - Complete REST API v1 implementation
   - Blob serialization validation
   - Authentication support (ECDSA signing)
   - Status polling mechanism
   - Error handling and retry logic

2. **`hyperagent/blockchain/alith_client.py`** ✅
   - Full Alith SDK integration
   - Agent pool management
   - Fallback mode support
   - SDK availability detection

3. **`hyperagent/core/config.py`** ✅
   - Added EigenDA configuration settings
   - Added boolean validator for `eigenda_use_authenticated`

4. **`hyperagent/core/services/deployment_service.py`** ✅
   - Updated EigenDA blob submission
   - Improved bytecode conversion
   - Better error handling

### Key Features Implemented

**EigenDA Integration**:
- ✅ REST API v1 Integration (DisperseBlob, GetBlobStatus, RetrieveBlob)
- ✅ Blob Serialization (automatic padding, size validation)
- ✅ Authentication (ECDSA signing)
- ✅ Status Polling (automatic until confirmed)
- ✅ Error Handling (exponential backoff, retry logic)

**Alith SDK Integration**:
- ✅ SDK Detection (automatic availability detection)
- ✅ Agent Management (initialization, pool management)
- ✅ Smart Model Selection (Gemini primary, OpenAI fallback)
- ✅ Tool Calling Support (autonomous deployment)
- ✅ Web3 Integration (network-specific agents)
- ✅ Multi-Agent Orchestration (workflow coordination)
- ✅ Error Handling (fallback mode support)

---

## Overview

This document provides comprehensive instructions for integrating and using EigenDA (Data Availability) and Alith (Decentralized AI Agent Framework) SDKs in the HyperAgent platform.

---

## EigenDA Integration

### What is EigenDA?

EigenDA is a secure, high-throughput, decentralized data availability service built on Ethereum using EigenLayer restaking primitives. It provides cost-efficient data storage for Layer 2 networks like Mantle.

**Official Documentation**: https://docs.eigencloud.xyz/products/eigenda/api/disperser-v1-API/overview  
**GitHub Repository**: https://github.com/Layr-Labs/eigenda

### Integration Method

HyperAgent uses the **REST API** integration method (recommended approach):

- **Endpoint**: `https://disperser.eigenda.xyz` (Mainnet)
- **API Version**: v1
- **Authentication**: Optional (authenticated endpoint for production)

### Installation

No additional Python package installation required. The implementation uses `httpx` for REST API calls, which is already in `requirements.txt`.

**Note**: There is an unofficial Python SDK (`powerloom-eigenda`) available, but we use the REST API directly for better control and compatibility.

### Configuration

Add to `.env`:

```bash
# EigenDA Configuration
# Mainnet: https://disperser.eigenda.xyz
# Testnet: (check EigenDA docs for testnet endpoint)
EIGENDA_DISPERSER_URL=https://disperser.eigenda.xyz
EIGENDA_USE_AUTHENTICATED=true

# Private key for authenticated requests (uses PRIVATE_KEY if not set separately)
# PRIVATE_KEY=your_ethereum_private_key_here
```

### Usage

#### Initialize EigenDA Client

```python
from hyperagent.blockchain.eigenda_client import EigenDAClient
from hyperagent.core.config import settings

# Initialize with settings
client = EigenDAClient(
    disperser_url=settings.eigenda_disperser_url,
    private_key=settings.private_key,
    use_authenticated=settings.eigenda_use_authenticated
)
```

#### Submit Blob to EigenDA

```python
# Prepare blob data (must be 128 KiB - 16 MiB, multiple of 32 bytes)
blob_data = contract_bytecode  # bytes

# Submit blob
result = await client.submit_blob(blob_data)

# Result contains:
# {
#     "commitment": "0x...",  # KZG commitment hash
#     "batch_header": {...},  # Batch header information
#     "blob_index": 123,      # Index in batch
#     "data_hash": "0x...",   # SHA256 hash
#     "request_id": "...",    # Request ID for status tracking
#     "submitted_at": "..."   # ISO timestamp
# }
```

#### Check Blob Status

```python
# Get status using request_id
status = await client.get_blob_status(request_id)

# Status values: pending, processing, confirmed, failed
```

#### Retrieve Blob

```python
# Retrieve blob using commitment hash
blob_data = await client.retrieve_blob(commitment)
```

#### Verify Availability

```python
# Check if blob is still available
is_available = await client.verify_availability(commitment)
```

### Blob Serialization Requirements

- **Minimum Size**: 128 KiB (131,072 bytes)
- **Maximum Size**: 16 MiB (16,777,216 bytes)
- **Alignment**: Must be multiple of 32 bytes (for BN254 field element compatibility)
- **Automatic Padding**: The client automatically pads blobs to meet alignment requirements

### API Endpoints Used

1. **DisperseBlob** (Unauthenticated)
   - Endpoint: `POST /v1/disperser/disperse-blob`
   - Use: Testing, rate-limited by IP

2. **DisperseBlobAuthenticated** (Authenticated)
   - Endpoint: `POST /v1/disperser/disperse-blob-authenticated`
   - Use: Production deployments
   - Requires: ECDSA signature with private key

3. **GetBlobStatus**
   - Endpoint: `GET /v1/disperser/blob-status/{request_id}`
   - Use: Poll blob status until confirmed

4. **RetrieveBlob**
   - Endpoint: `GET /v1/disperser/retrieve-blob/{commitment}`
   - Use: Fetch blob data using commitment

### Rate Limits

EigenDA enforces rate limits:

- **Data Rate Limit**: Total data posted within fixed interval (e.g., 10 minutes)
- **Blob Rate Limit**: Number of blobs posted within timeframe

Exceeding limits results in rate limit errors. The client implements automatic retry with exponential backoff.

### Integration in Deployment Service

EigenDA is automatically integrated when deploying to Mantle networks:

```python
# In DeploymentService.process()
if network.startswith("mantle"):
    eigenda_result = await self.eigenda_client.submit_blob(bytecode_bytes)
    eigenda_commitment = eigenda_result.get("commitment")
    # Store commitment in deployment record
```

---

## Alith SDK Integration

### What is Alith?

Alith is a decentralized AI agent framework for Web3, offering high-performance inference, Web3 integration, Data Anchoring Tokens (DATs), and Trusted Execution Environment (TEE) support.

**Official Documentation**: https://alith.lazai.network/docs/get-started  
**Installation**: `pip install alith -U`

### Installation

```bash
pip install alith -U
```

Or add to `requirements.txt`:

```
alith>=0.1.0
```

### Configuration

No API key required! Alith SDK does not require an API key for basic operations.

**Note**: TEE (Trusted Execution Environment) is optional and will be initialized automatically if available. The system will continue to work without TEE for basic agent functionality.

### Usage

#### Initialize Alith Client

```python
from hyperagent.blockchain.alith_client import AlithClient

# Initialize (no API key needed)
client = AlithClient()

# Check if SDK is available
if client.is_sdk_available():
    print("Alith SDK is ready")
else:
    print("Alith SDK not installed - using fallback mode")
```

#### Create and Use Agent

```python
# Initialize agent
agent_config = await client.initialize_agent(
    name="contract_generator",
    model="gpt-4",  # or "gemini-pro"
    tools=["code_generation", "security_analysis"],
    preamble="You are an expert Solidity smart contract developer."
)

# Execute agent
response = await client.execute_agent(
    agent_name="contract_generator",
    prompt="Generate an ERC20 token contract with a fixed supply of 1 million tokens.",
    context={
        "network": "hyperion_testnet",
        "solidity_version": "0.8.27"
    }
)

print(response)  # Agent's response
```

#### Agent Pool Management

```python
# List all initialized agents
agents = client.list_agents()
print(agents)  # ['contract_generator', 'audit_agent', ...]

# Stop and remove agent
await client.stop_agent("contract_generator")
```

### Model Configuration

Alith supports multiple LLM providers. Set API keys as environment variables:

**OpenAI**:
```bash
export OPENAI_API_KEY=<your_key>
```

**Gemini** (default in HyperAgent):
```bash
export GEMINI_API_KEY=<your_key>
```

### Fallback Mode

If Alith SDK is not installed, the client operates in fallback mode:

- Agents are created as placeholders
- Execution returns placeholder responses
- Full functionality requires SDK installation

### Tool Calling Support

Alith agents can autonomously call tools for blockchain operations:

```python
from hyperagent.blockchain.alith_client import AlithClient
from hyperagent.blockchain.alith_tools import get_deployment_tools, AlithToolHandler
from hyperagent.blockchain.networks import NetworkManager

# Initialize components
client = AlithClient()
network_manager = NetworkManager()
tool_handler = AlithToolHandler(network_manager=network_manager)

# Get deployment tools
tools = get_deployment_tools()

# Initialize agent with tools
await client.initialize_agent(
    name="autonomous_deployer",
    preamble="You are an autonomous deployment agent. Use tools to deploy contracts."
)

# Execute agent with tools
result = await client.execute_agent_with_tools(
    agent_name="autonomous_deployer",
    prompt="Deploy this contract to hyperion_testnet",
    tools=tools,
    context={
        "bytecode": "0x6080604052...",
        "abi": [...],
        "network": "hyperion_testnet"
    },
    tool_handler=tool_handler
)

# Agent will autonomously call deploy_contract tool
print(result["tool_calls"])  # Tools agent decided to use
print(result["tool_results"])  # Results from tool execution
```

### Web3 Agent Integration

Initialize agents with built-in Web3 capabilities:

```python
# Initialize Web3-enabled agent
result = await client.initialize_web3_agent(
    name="web3_agent",
    network="hyperion_testnet",
    private_key="your_private_key"  # Optional, uses settings if not provided
)

# Agent can now interact with blockchain directly
# (depends on Alith SDK's Web3 API implementation)
```

### Multi-Agent Orchestration

Coordinate multiple agents in a workflow:

```python
# Define workflow steps with dependencies
workflow_steps = [
    {
        "agent": "contract_generator",
        "task": "generate_contract",
        "depends_on": [],
        "prompt": "Generate an ERC20 token contract",
        "parallel": False
    },
    {
        "agent": "auditor",
        "task": "audit_contract",
        "depends_on": ["generate_contract"],
        "prompt": "Audit the generated contract for security issues",
        "parallel": False
    },
    {
        "agent": "deployer",
        "task": "deploy_contract",
        "depends_on": ["audit_contract"],
        "prompt": "Deploy the audited contract to testnet",
        "parallel": False
    }
]

# Execute workflow
result = await client.orchestrate_workflow(
    workflow_steps=workflow_steps,
    context={"network": "hyperion_testnet"}
)

# Access results from each step
print(result["results"]["generate_contract"])
print(result["results"]["audit_contract"])
print(result["results"]["deploy_contract"])
```

### Smart Model Selection

AlithClient automatically selects the best model:

- **Primary**: Gemini (if `GEMINI_API_KEY` is set)
- **Fallback**: OpenAI GPT-4 (if `OPENAI_API_KEY` is set)

```python
# Auto-selects model based on available API keys
await client.initialize_agent(name="smart_agent")
# Will use "gemini-pro" if Gemini key available, else "gpt-4"
```

### Integration in HyperAgent

Alith can be used to enhance contract generation agents:

```python
# In GenerationAgent or custom agent
from hyperagent.blockchain.alith_client import AlithClient

alith_client = AlithClient()

# Use Alith agent for enhanced generation
if alith_client.is_sdk_available():
    response = await alith_client.execute_agent(
        agent_name="enhanced_generator",
        prompt=nlp_input,
        context={"contract_type": contract_type, "network": network}
    )
```

### Autonomous Deployment

Enable autonomous deployment using Alith tool calling:

```python
from hyperagent.core.services.deployment_service import DeploymentService

# Initialize with autonomous deployment enabled
deployment_service = DeploymentService(
    network_manager=network_manager,
    alith_client=alith_client,
    eigenda_client=eigenda_client,
    use_alith_autonomous=True  # Enable autonomous deployment
)

# Agent will autonomously deploy the contract
result = await deployment_service.process({
    "compiled_contract": compiled,
    "network": "hyperion_testnet"
})
```

---

## LLM Provider Configuration

### Default: Gemini (Primary)

Gemini is the **default** LLM provider in HyperAgent:

```python
# In hyperagent/llm/provider.py
class GeminiProvider(LLMProvider):
    """Google Gemini Provider - PRIMARY"""
    # ... implementation
```

### Fallback: OpenAI

OpenAI is used as a **fallback** when Gemini is unavailable:

```python
# In hyperagent/llm/provider.py
class OpenAIProvider(LLMProvider):
    """OpenAI provider (fallback)"""
    # ... implementation
```

### Configuration Priority

1. **Primary**: Gemini (required in `.env`)
2. **Fallback**: OpenAI (optional, used if Gemini fails)

```bash
# Required - Primary LLM
GEMINI_API_KEY=your_gemini_api_key

# Optional - Fallback LLM
OPENAI_API_KEY=your_openai_api_key
```

---

## Error Handling

### EigenDA Errors

```python
from hyperagent.blockchain.eigenda_client import EigenDAError

try:
    result = await eigenda_client.submit_blob(data)
except EigenDAError as e:
    # Handle EigenDA-specific errors
    logger.error(f"EigenDA error: {e}")
except Exception as e:
    # Handle other errors
    logger.error(f"Unexpected error: {e}")
```

### Alith Errors

```python
from hyperagent.blockchain.alith_client import AlithError

try:
    response = await alith_client.execute_agent("agent_name", "prompt")
except AlithError as e:
    # Handle Alith-specific errors
    logger.error(f"Alith error: {e}")
except Exception as e:
    # Handle other errors
    logger.error(f"Unexpected error: {e}")
```

---

## Testing

### Unit Tests

Unit tests are available in `tests/unit/test_blockchain.py`:

```bash
pytest tests/unit/test_blockchain.py -v
```

### Integration Testing

For integration testing with actual EigenDA network:

1. Set `EIGENDA_USE_AUTHENTICATED=false` for testing (uses unauthenticated endpoint)
2. Use testnet endpoint if available
3. Ensure blob data meets size requirements (128 KiB minimum)

---

## Troubleshooting

### EigenDA Issues

**Problem**: "Blob too small" error  
**Solution**: Ensure blob is at least 128 KiB. The client will pad smaller blobs, but very small blobs may fail.

**Problem**: "Rate limit exceeded"  
**Solution**: Implement exponential backoff. The client already includes retry logic.

**Problem**: "Authentication failed"  
**Solution**: Verify private key is correct and account has sufficient balance for payments.

### Alith Issues

**Problem**: "Alith SDK not available"  
**Solution**: Install SDK: `pip install alith -U`

**Problem**: "Agent execution failed"  
**Solution**: Check API key is set correctly and model provider API keys are configured.

**Problem**: "ImportError: No module named 'alith'"  
**Solution**: Install the SDK and verify it's in your Python environment.

---

## Best Practices

### EigenDA

1. **Use Authenticated Endpoint** for production deployments
2. **Monitor Blob Status** until confirmed before proceeding
3. **Store Commitments** in database for later retrieval
4. **Handle Rate Limits** gracefully with retry logic
5. **Validate Blob Size** before submission

### Alith

1. **Reuse Agents** from the agent pool when possible
2. **Set Appropriate Preambles** for agent behavior
3. **Provide Context** for better agent responses
4. **Handle Fallback Mode** gracefully if SDK unavailable
5. **Monitor API Usage** and rate limits

---

## References

- **EigenDA Documentation**: https://docs.eigencloud.xyz/products/eigenda/
- **EigenDA Disperser API**: https://docs.eigencloud.xyz/products/eigenda/api/disperser-v1-API/overview
- **EigenDA GitHub**: https://github.com/Layr-Labs/eigenda
- **Alith Documentation**: https://alith.lazai.network/docs/get-started
- **Alith Installation**: `pip install alith -U`

---

## Implementation Files

- `hyperagent/blockchain/eigenda_client.py` - EigenDA REST API client
- `hyperagent/blockchain/alith_client.py` - Alith SDK wrapper
- `hyperagent/core/config.py` - Configuration settings
- `hyperagent/core/services/deployment_service.py` - Deployment service with EigenDA integration
- `hyperagent/agents/deployment.py` - Deployment agent with EigenDA integration

---

**Last Updated**: 2025-01-27

