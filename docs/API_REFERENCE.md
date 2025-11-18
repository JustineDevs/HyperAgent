# API Reference

**Document Type**: Reference (Technical Specification)  
**Category**: API Documentation  
**Audience**: Developers, Integrators  
**Location**: `docs/API_REFERENCE.md`

Complete API reference for HyperAgent REST API.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, authentication is optional. When enabled, use JWT tokens:

```http
Authorization: Bearer <jwt_token>
```

## API Endpoints

### Health Endpoints

#### GET `/health/`

Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "app_name": "HyperAgent",
  "version": "1.0.0",
  "timestamp": "2025-11-18T10:00:00Z"
}
```

#### GET `/health/detailed`

Detailed health check with service status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-18T10:00:00Z",
  "services": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2
    }
  }
}
```

#### GET `/health/readiness`

Kubernetes readiness probe.

**Response:**
```json
{
  "ready": true,
  "timestamp": "2025-11-18T10:00:00Z"
}
```

#### GET `/health/liveness`

Kubernetes liveness probe.

**Response:**
```json
{
  "alive": true,
  "timestamp": "2025-11-18T10:00:00Z"
}
```

### Workflow Endpoints

#### POST `/workflows/generate`

Create a new workflow for contract generation and deployment.

**Request:**
```json
{
  "nlp_input": "Create an ERC20 token named MyToken with symbol MTK and initial supply 1000000",
  "network": "hyperion_testnet",
  "contract_type": "ERC20",
  "name": "My Token Workflow",
  "skip_audit": false,
  "skip_deployment": false,
  "optimize_for_metisvm": false,
  "enable_floating_point": false,
  "enable_ai_inference": false
}
```

**Response:**
```json
{
  "workflow_id": "abc123-def456-ghi789",
  "status": "generating",
  "progress_percentage": 10,
  "features_used": {
    "metisvm": false,
    "floating_point": false
  }
}
```

**Status Codes:**
- `200` - Workflow created successfully
- `400` - Invalid request
- `500` - Server error

#### GET `/workflows/{workflow_id}`

Get workflow status and details.

**Response:**
```json
{
  "workflow_id": "abc123-def456-ghi789",
  "status": "completed",
  "progress_percentage": 100,
  "created_at": "2025-11-18T10:00:00Z",
  "updated_at": "2025-11-18T10:05:00Z",
  "contracts": [
    {
      "id": "contract-id",
      "contract_code": "pragma solidity...",
      "abi": [...]
    }
  ],
  "deployments": [
    {
      "contract_address": "0x...",
      "transaction_hash": "0x...",
      "block_number": 12345,
      "gas_used": 500000
    }
  ]
}
```

**Status Codes:**
- `200` - Workflow found
- `404` - Workflow not found

### Contract Endpoints

#### POST `/contracts/generate`

Generate contract code from NLP description (without full workflow).

**Request:**
```json
{
  "nlp_description": "Create a simple storage contract",
  "contract_type": "Custom"
}
```

**Response:**
```json
{
  "contract_code": "pragma solidity ^0.8.0; ...",
  "contract_type": "Custom",
  "abi": [...],
  "constructor_args": []
}
```

#### POST `/contracts/audit`

Run security audit on contract code.

**Request:**
```json
{
  "contract_code": "pragma solidity ^0.8.0; ..."
}
```

**Response:**
```json
{
  "vulnerabilities": [
    {
      "severity": "high",
      "title": "Reentrancy vulnerability",
      "description": "...",
      "line": 45
    }
  ],
  "overall_risk_score": 25,
  "audit_status": "passed",
  "critical_count": 0,
  "high_count": 1,
  "medium_count": 0,
  "low_count": 0
}
```

### Deployment Endpoints

#### POST `/deployments/deploy`

Deploy a compiled contract to blockchain.

**Request:**
```json
{
  "compiled_contract": {
    "abi": [...],
    "bytecode": "0x..."
  },
  "network": "hyperion_testnet",
  "private_key": "0x...",
  "constructor_args": []
}
```

**Response:**
```json
{
  "contract_address": "0x1234...",
  "transaction_hash": "0xabcd...",
  "block_number": 12345,
  "gas_used": 500000,
  "eigenda_commitment": "0x..."
}
```

#### POST `/deployments/batch`

Deploy multiple contracts in parallel (Hyperion PEF).

**Request:**
```json
{
  "contracts": [
    {
      "compiled_contract": {...},
      "network": "hyperion_testnet",
      "constructor_args": []
    }
  ],
  "max_parallel": 10
}
```

**Response:**
```json
{
  "total": 5,
  "successful": 4,
  "failed": 1,
  "results": [
    {
      "status": "success",
      "contract_address": "0x...",
      "transaction_hash": "0x..."
    }
  ]
}
```

### Template Endpoints

#### GET `/templates`

List all contract templates.

**Query Parameters:**
- `contract_type` (optional) - Filter by contract type
- `is_active` (optional) - Filter by active status
- `limit` (default: 50) - Number of results
- `offset` (default: 0) - Pagination offset

**Response:**
```json
[
  {
    "id": "template-id",
    "name": "ERC20 Basic",
    "description": "Basic ERC20 token template",
    "contract_type": "ERC20",
    "template_code": "pragma solidity...",
    "version": "1.0.0",
    "is_active": true,
    "tags": ["token", "erc20"],
    "created_at": "2025-11-18T10:00:00Z"
  }
]
```

#### POST `/templates/search`

Search templates using semantic similarity.

**Request:**
```json
{
  "query": "ERC20 token with burn functionality",
  "contract_type": "ERC20",
  "limit": 5,
  "similarity_threshold": 0.7
}
```

**Response:**
```json
[
  {
    "id": "template-id",
    "name": "ERC20 Burn",
    "similarity_score": 0.95,
    ...
  }
]
```

#### GET `/templates/{template_id}`

Get specific template by ID.

**Response:**
```json
{
  "id": "template-id",
  "name": "ERC20 Basic",
  "template_code": "pragma solidity...",
  ...
}
```

#### POST `/templates`

Create a new template.

**Request:**
```json
{
  "name": "My Custom Template",
  "description": "Custom contract template",
  "contract_type": "Custom",
  "template_code": "pragma solidity...",
  "version": "1.0.0",
  "is_active": true,
  "tags": ["custom"],
  "upload_to_ipfs": true
}
```

### Network Endpoints

#### GET `/networks`

List all supported networks with their features.

**Response:**
```json
[
  {
    "network": "hyperion_testnet",
    "features": {
      "pef": true,
      "metisvm": true,
      "eigenda": false,
      "floating_point": true
    },
    "fallbacks": {},
    "chain_id": 133717,
    "rpc_url": "https://hyperion-testnet.metisdevops.link",
    "explorer": "https://hyperion-testnet-explorer.metisdevops.link",
    "currency": "tMETIS"
  }
]
```

#### GET `/networks/{network}/features`

Get features for a specific network.

**Response:**
```json
{
  "network": "hyperion_testnet",
  "features": {
    "pef": true,
    "metisvm": true,
    ...
  },
  "fallbacks": {}
}
```

#### GET `/networks/{network}/compatibility`

Get compatibility report for a network.

**Response:**
```json
{
  "network": "hyperion_testnet",
  "supports_pef": true,
  "supports_metisvm": true,
  "supports_eigenda": false,
  "supports_batch_deployment": true,
  "supports_floating_point": true,
  "supports_ai_inference": false,
  "fallback_strategies": {},
  "recommendations": [
    "Use PEF for batch deployments (10-50x faster)",
    "MetisVM optimization available"
  ]
}
```

### Metrics Endpoints

#### GET `/metrics`

Get application metrics (if enabled).

**Response:**
```json
{
  "workflows_total": 100,
  "workflows_completed": 95,
  "workflows_failed": 5,
  "contracts_generated": 95,
  "deployments_successful": 90,
  "average_generation_time_ms": 5000,
  "average_deployment_time_ms": 30000
}
```

## WebSocket API

### Connect to Workflow Updates

```
ws://localhost:8000/ws/workflow/{workflow_id}
```

**Message Format:**
```json
{
  "type": "progress",
  "workflow_id": "abc123...",
  "status": "generating",
  "progress_percentage": 50,
  "stage": "compilation"
}
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "status_code": 400,
  "error_type": "ValidationError"
}
```

**Common Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `500` - Internal Server Error

## Rate Limiting

If rate limiting is enabled, headers include:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1637232000
```

## Interactive API Documentation

- **Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/v1/openapi.json`

## Code Examples

### Python

```python
import httpx

# Create workflow
response = httpx.post(
    "http://localhost:8000/api/v1/workflows/generate",
    json={
        "nlp_input": "Create ERC20 token",
        "network": "hyperion_testnet",
        "contract_type": "ERC20"
    }
)
workflow = response.json()
workflow_id = workflow["workflow_id"]

# Monitor progress
status = httpx.get(
    f"http://localhost:8000/api/v1/workflows/{workflow_id}"
).json()
print(f"Status: {status['status']}, Progress: {status['progress_percentage']}%")
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

// Create workflow
const response = await axios.post(
  'http://localhost:8000/api/v1/workflows/generate',
  {
    nlp_input: 'Create ERC20 token',
    network: 'hyperion_testnet',
    contract_type: 'ERC20'
  }
);

const workflowId = response.data.workflow_id;

// Monitor progress
const status = await axios.get(
  `http://localhost:8000/api/v1/workflows/${workflowId}`
);
console.log(`Status: ${status.data.status}`);
```

### cURL

```bash
# Create workflow
curl -X POST http://localhost:8000/api/v1/workflows/generate \
  -H "Content-Type: application/json" \
  -d '{
    "nlp_input": "Create ERC20 token",
    "network": "hyperion_testnet",
    "contract_type": "ERC20"
  }'

# Get workflow status
curl http://localhost:8000/api/v1/workflows/{workflow_id}
```

## Additional Resources

- [Quick Start Guide](./QUICK_START.md) - Getting started
- [Configuration Guide](./CONFIGURATION.md) - Configuration options
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment

---

**Questions?** Open an issue on [GitHub](https://github.com/JustineDevs/HyperAgent/issues)

