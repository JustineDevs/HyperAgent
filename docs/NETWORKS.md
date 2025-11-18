# Supported Networks

**Document Type**: Reference (Technical Specification)  
**Category**: Network Configuration  
**Audience**: Developers, Users  
**Location**: `docs/NETWORKS.md`

Complete guide to supported blockchain networks and their features.

## Supported Networks

### Hyperion Testnet

**Network Name:** `hyperion_testnet`

**Configuration:**
- **Chain ID:** `133717`
- **RPC URL:** `https://hyperion-testnet.metisdevops.link`
- **Explorer:** `https://hyperion-testnet-explorer.metisdevops.link`
- **Currency:** `tMETIS` (Test METIS)

**Features:**
- ✅ **PEF (Parallel Execution Framework)** - 10-50x faster batch deployments
- ✅ **MetisVM Optimization** - Optimized contract generation
- ✅ **Floating-Point Support** - Native floating-point operations
- ⚠️ **EigenDA** - Not available (use IPFS/Pinata)

**Environment Variables:**
```env
HYPERION_TESTNET_RPC=https://hyperion-testnet.metisdevops.link
HYPERION_TESTNET_CHAIN_ID=133717
```

**Usage:**
```bash
hyperagent workflow create \
  -d "Create ERC20 token" \
  --network hyperion_testnet
```

### Hyperion Mainnet

**Network Name:** `hyperion_mainnet`

**Configuration:**
- **Chain ID:** `133718`
- **RPC URL:** `https://hyperion.metisdevops.link`
- **Explorer:** `https://hyperion-explorer.metisdevops.link`
- **Currency:** `METIS`

**Features:**
- ✅ **PEF** - Available
- ✅ **MetisVM Optimization** - Available
- ✅ **Floating-Point Support** - Available
- ⚠️ **EigenDA** - Not available

**Environment Variables:**
```env
HYPERION_MAINNET_RPC=https://hyperion.metisdevops.link
HYPERION_MAINNET_CHAIN_ID=133718
```

### Mantle Testnet

**Network Name:** `mantle_testnet`

**Configuration:**
- **Chain ID:** `5003`
- **RPC URL:** `https://rpc.sepolia.mantle.xyz`
- **Explorer:** `https://explorer.testnet.mantle.xyz`
- **Currency:** `BIT` (Test BIT)

**Features:**
- ⚠️ **PEF** - Not available (sequential deployment)
- ⚠️ **MetisVM** - Not available
- ⚠️ **Floating-Point** - Not available
- ✅ **EigenDA Integration** - Available for data availability

**Environment Variables:**
```env
MANTLE_TESTNET_RPC=https://rpc.sepolia.mantle.xyz
MANTLE_TESTNET_CHAIN_ID=5003
```

**Usage:**
```bash
hyperagent workflow create \
  -d "Create ERC20 token" \
  --network mantle_testnet
```

### Mantle Mainnet

**Network Name:** `mantle_mainnet`

**Configuration:**
- **Chain ID:** `5000`
- **RPC URL:** `https://rpc.mantle.xyz`
- **Explorer:** `https://explorer.mantle.xyz`
- **Currency:** `BIT`

**Features:**
- ⚠️ **PEF** - Not available
- ⚠️ **MetisVM** - Not available
- ⚠️ **Floating-Point** - Not available
- ✅ **EigenDA Integration** - Available

**Environment Variables:**
```env
MANTLE_MAINNET_RPC=https://rpc.mantle.xyz
MANTLE_MAINNET_CHAIN_ID=5000
```

## Network Features Comparison

| Feature | Hyperion Testnet | Hyperion Mainnet | Mantle Testnet | Mantle Mainnet |
|---------|------------------|------------------|----------------|----------------|
| **PEF (Batch Deployment)** | ✅ | ✅ | ❌ | ❌ |
| **MetisVM Optimization** | ✅ | ✅ | ❌ | ❌ |
| **Floating-Point** | ✅ | ✅ | ❌ | ❌ |
| **EigenDA** | ❌ | ❌ | ✅ | ✅ |
| **AI Inference** | ⚠️ | ⚠️ | ❌ | ❌ |

## Feature Details

### PEF (Parallel Execution Framework)

**Available on:** Hyperion networks only

**Benefits:**
- 10-50x faster batch deployments
- Parallel contract deployment
- Reduced gas costs

**Usage:**
```bash
hyperagent deployment batch \
  --contracts-file contracts.json \
  --network hyperion_testnet \
  --use-pef \
  --max-parallel 10
```

### MetisVM Optimization

**Available on:** Hyperion networks only

**Benefits:**
- Optimized contract generation
- Better gas efficiency
- Enhanced performance

**Usage:**
```bash
hyperagent workflow create \
  -d "Create contract" \
  --network hyperion_testnet \
  --optimize-metisvm
```

### Floating-Point Support

**Available on:** Hyperion networks only

**Benefits:**
- Native floating-point operations
- Financial calculations
- Scientific computations

**Usage:**
```bash
hyperagent workflow create \
  -d "Create financial derivative" \
  --network hyperion_testnet \
  --enable-fp
```

### EigenDA Integration

**Available on:** Mantle networks only

**Benefits:**
- Cost-efficient data availability
- Contract metadata storage
- Decentralized storage

**Configuration:**
```env
EIGENDA_DISPERSER_URL=https://disperser.eigenda.xyz
EIGENDA_USE_AUTHENTICATED=true
```

## Network Selection Guide

### For Development/Testing

**Recommended:** Hyperion Testnet
- Fast batch deployments (PEF)
- Rich feature set
- Free testnet tokens

### For Production

**Hyperion Mainnet:**
- If you need PEF for batch deployments
- If you need MetisVM optimization
- If you need floating-point support

**Mantle Mainnet:**
- If you need EigenDA integration
- If you prefer Mantle ecosystem
- Standard EVM features

## API Endpoints

### List All Networks

```bash
GET /api/v1/networks
```

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
    "chain_id": 133717,
    "rpc_url": "https://hyperion-testnet.metisdevops.link",
    "explorer": "https://hyperion-testnet-explorer.metisdevops.link"
  }
]
```

### Get Network Features

```bash
GET /api/v1/networks/{network}/features
```

### Get Network Compatibility

```bash
GET /api/v1/networks/{network}/compatibility
```

**Response:**
```json
{
  "network": "hyperion_testnet",
  "supports_pef": true,
  "supports_metisvm": true,
  "supports_eigenda": false,
  "supports_batch_deployment": true,
  "recommendations": [
    "Use PEF for batch deployments (10-50x faster)"
  ]
}
```

## Fallback Strategies

HyperAgent automatically handles feature fallbacks:

- **PEF unavailable:** Falls back to sequential deployment
- **MetisVM unavailable:** Generates standard EVM contracts
- **Floating-point unavailable:** Uses fixed-point arithmetic
- **EigenDA unavailable:** Uses IPFS/Pinata for storage

## Network Configuration

### Custom RPC Endpoints

You can override default RPC URLs:

```env
HYPERION_TESTNET_RPC=https://your-custom-rpc.com
MANTLE_TESTNET_RPC=https://your-custom-rpc.com
```

### Adding New Networks

To add support for additional EVM-compatible networks:

1. Add network configuration to `hyperagent/blockchain/networks.py`
2. Update `hyperagent/blockchain/network_features.py`
3. Add environment variables for RPC URLs
4. Test network connectivity

## Getting Testnet Tokens

### Hyperion Testnet

- Visit: [Hyperion Testnet Faucet](https://hyperion-testnet-explorer.metisdevops.link)
- Request testnet tokens
- Verify balance on explorer

### Mantle Testnet

- Visit: [Mantle Testnet Faucet](https://faucet.testnet.mantle.xyz)
- Request testnet tokens
- Verify balance on explorer

## Additional Resources

- [Quick Start Guide](./QUICK_START.md) - Getting started
- [Configuration Guide](./CONFIGURATION.md) - Network configuration
- [API Reference](./API_REFERENCE.md) - Network API endpoints
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment

---

**Questions?** Open an issue on [GitHub](https://github.com/JustineDevs/HyperAgent/issues)

