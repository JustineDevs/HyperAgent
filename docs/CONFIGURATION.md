# Configuration Reference

**Document Type**: Reference (Technical Specification)  
**Category**: Configuration  
**Audience**: Developers, System Administrators  
**Location**: `docs/CONFIGURATION.md`

Complete reference for all HyperAgent configuration options.

## Configuration File

HyperAgent uses environment variables for configuration. Copy `env.example` to `.env` and customize:

```bash
cp env.example .env
```

## Environment Variables

### Application Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `NODE_ENV` | string | `development` | Environment mode (`development`, `production`) |
| `LOG_LEVEL` | string | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `APP_NAME` | string | `HyperAgent` | Application name |
| `APP_VERSION` | string | `1.0.0` | Application version |
| `DEBUG` | boolean | `false` | Enable debug mode |
| `LOG_FORMAT` | string | `json` | Log format (`json`, `text`) |
| `LOG_FILE` | string | `logs/hyperagent.log` | Log file path |

### Database Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | string | `postgresql://...` | PostgreSQL connection string |
| `SUPABASE_URL` | string | - | Supabase project URL (alternative) |
| `SUPABASE_ANON_KEY` | string | - | Supabase anonymous key |

**Example:**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/hyperagent_db
```

### Redis Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_URL` | string | `redis://localhost:6379/0` | Redis connection URL |
| `REDIS_PASSWORD` | string | - | Redis password (if required) |

**Example:**
```env
REDIS_URL=redis://:password@localhost:6379/0
REDIS_PASSWORD=your_redis_password
```

### LLM Provider Configuration

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `GEMINI_API_KEY` | string | **Yes** | Google Gemini API key |
| `GEMINI_MODEL` | string | `gemini-2.5-flash` | Gemini model name |
| `GEMINI_THINKING_BUDGET` | integer | - | Thinking budget (1-1000) for Gemini 2.5 |
| `OPENAI_API_KEY` | string | No | OpenAI API key (fallback) |
| `OPENAI_MODEL` | string | `gpt-4o` | OpenAI model name |

**LLM Timeout Settings:**
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LLM_TIMEOUT_SECONDS` | integer | `30` | General LLM API timeout |
| `LLM_CONSTRUCTOR_TIMEOUT_SECONDS` | integer | `20` | Constructor value generation timeout |
| `LLM_EMBED_TIMEOUT_SECONDS` | integer | `10` | Embedding generation timeout |

**Example:**
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
OPENAI_API_KEY=your_openai_api_key_here  # Optional
```

### Blockchain Network Configuration

#### Hyperion Network

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `HYPERION_TESTNET_RPC` | string | `https://hyperion-testnet.metisdevops.link` | Hyperion testnet RPC URL |
| `HYPERION_TESTNET_CHAIN_ID` | integer | `133717` | Hyperion testnet chain ID |
| `HYPERION_MAINNET_RPC` | string | `https://hyperion.metisdevops.link` | Hyperion mainnet RPC URL |
| `HYPERION_MAINNET_CHAIN_ID` | integer | `133718` | Hyperion mainnet chain ID |

#### Mantle Network

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MANTLE_TESTNET_RPC` | string | `https://rpc.sepolia.mantle.xyz` | Mantle testnet RPC URL |
| `MANTLE_TESTNET_CHAIN_ID` | integer | `5003` | Mantle testnet chain ID |
| `MANTLE_MAINNET_RPC` | string | `https://rpc.mantle.xyz` | Mantle mainnet RPC URL |
| `MANTLE_MAINNET_CHAIN_ID` | integer | `5000` | Mantle mainnet chain ID |

### Wallet Configuration

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `PRIVATE_KEY` | string | **Yes** | Private key (hex, without 0x prefix) |
| `PUBLIC_ADDRESS` | string | **Yes** | Public address (0x format) |

**Security Note:** Never commit private keys to version control!

**Example:**
```env
PRIVATE_KEY=your_private_key_hex_without_0x_prefix
PUBLIC_ADDRESS=0xYourPublicAddress
```

### EigenDA Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `EIGENDA_DISPERSER_URL` | string | `https://disperser.eigenda.xyz` | EigenDA disperser URL |
| `EIGENDA_USE_AUTHENTICATED` | boolean | `true` | Use authenticated endpoint |

### IPFS/Pinata Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PINATA_JWT` | string | - | Pinata JWT token |
| `PINATA_GATEWAY` | string | `https://gateway.pinata.cloud` | Pinata gateway URL |
| `ENABLE_IPFS_UPLOAD` | boolean | `true` | Enable IPFS uploads |
| `IPFS_VERIFY_INTEGRITY` | boolean | `true` | Verify IPFS integrity |

### API Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `API_HOST` | string | `0.0.0.0` | API host address |
| `API_PORT` | integer | `8000` | API port |
| `API_WORKERS` | integer | `4` | Number of worker processes |
| `CORS_ORIGINS` | string | `*` | CORS allowed origins (comma-separated) |

**Example:**
```env
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Security Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_AUTHENTICATION` | boolean | `false` | Enable JWT authentication |
| `ENABLE_RATE_LIMITING` | boolean | `false` | Enable rate limiting |
| `JWT_SECRET_KEY` | string | `change-me-in-production` | JWT secret key |
| `JWT_ALGORITHM` | string | `HS256` | JWT algorithm |
| `JWT_EXPIRE_MINUTES` | integer | `1440` | JWT expiration (minutes) |
| `API_KEYS` | string | - | API keys (comma-separated) |

**Production Security:**
```env
ENABLE_AUTHENTICATION=true
ENABLE_RATE_LIMITING=true
JWT_SECRET_KEY=<generate-strong-random-key>
```

### Feature Flags

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_WEBSOCKET` | boolean | `true` | Enable WebSocket support |
| `ENABLE_METRICS` | boolean | `true` | Enable metrics endpoint |
| `SKIP_AUDIT` | boolean | `false` | Skip security audit |
| `SKIP_TESTING` | boolean | `false` | Skip automated testing |
| `SKIP_DEPLOYMENT` | boolean | `false` | Skip deployment |

### Workflow Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_RETRIES` | integer | `3` | Maximum retry attempts |
| `RETRY_BACKOFF_BASE` | integer | `2` | Exponential backoff base |

### Template Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TEMPLATE_CACHE_TTL` | integer | `3600` | Template cache TTL (seconds) |
| `TEMPLATE_BATCH_SIZE` | integer | `10` | Template batch size |

### Testing Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_FOUNDRY` | boolean | `false` | Enable Foundry test framework |
| `TEST_FRAMEWORK_AUTO_DETECT` | boolean | `true` | Auto-detect test framework |

### Deployment Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_DEPLOYMENT_VALIDATION` | boolean | `true` | Validate before deployment |
| `MIN_WALLET_BALANCE_ETH` | float | `0.001` | Minimum wallet balance (ETH) |
| `USE_MANTLE_SDK` | boolean | `false` | Use Mantle SDK if available |

### Monitoring Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `METRICS_PORT` | integer | `9090` | Metrics endpoint port |

## Configuration Validation

HyperAgent validates configuration on startup. Invalid values will cause startup to fail with clear error messages.

## Environment-Specific Configuration

### Development

```env
NODE_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_AUTHENTICATION=false
ENABLE_RATE_LIMITING=false
```

### Production

```env
NODE_ENV=production
DEBUG=false
LOG_LEVEL=INFO
ENABLE_AUTHENTICATION=true
ENABLE_RATE_LIMITING=true
JWT_SECRET_KEY=<strong-random-key>
```

## Docker Configuration

When using Docker, environment variables can be set in:

1. `.env` file (for docker-compose)
2. `docker-compose.yml` environment section
3. Docker secrets (for sensitive data)

## Additional Resources

- [Quick Start Guide](./QUICK_START.md) - Getting started
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment
- [API Reference](./API_REFERENCE.md) - API documentation

---

**Questions?** Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) or open an issue on GitHub.

