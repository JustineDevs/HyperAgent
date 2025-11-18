# Quick Start Guide

**Document Type**: Tutorial (Learning-Oriented)  
**Category**: Getting Started  
**Audience**: New Users  
**Location**: `docs/QUICK_START.md`

This guide will help you get HyperAgent up and running in minutes.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** installed
- **PostgreSQL 15+** or access to Supabase
- **Redis 7+** or access to Redis Cloud
- **Git** installed
- **Google Gemini API Key** ([Get one here](https://aistudio.google.com/app/apikey))

## Installation Methods

### Option 1: Docker (Recommended)

The fastest way to get started is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/JustineDevs/HyperAgent.git
cd HyperAgent

# Copy environment file
cp env.example .env

# Edit .env with your API keys
# Required: GEMINI_API_KEY
# Optional: OPENAI_API_KEY, DATABASE_URL, REDIS_URL

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f hyperagent
```

The API will be available at `http://localhost:8000`

### Option 2: Local Installation

```bash
# Clone the repository
git clone https://github.com/JustineDevs/HyperAgent.git
cd HyperAgent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp env.example .env

# Edit .env with your configuration
# Required: GEMINI_API_KEY, DATABASE_URL, REDIS_URL

# Initialize database
alembic upgrade head

# Start the API server
uvicorn hyperagent.api.main:app --reload
```

## Verify Installation

### Check API Health

```bash
# Via CLI
hyperagent system health

# Via curl
curl http://localhost:8000/api/v1/health/

# Expected response:
# {"status": "healthy", "app_name": "HyperAgent", "version": "1.0.0", ...}
```

### Check Detailed Health

```bash
curl http://localhost:8000/api/v1/health/detailed
```

This will check database and Redis connectivity.

## Your First Contract

### Using CLI

```bash
# Create a simple ERC20 token
hyperagent workflow create \
  -d "Create an ERC20 token named MyToken with symbol MTK and initial supply 1000000" \
  --network hyperion_testnet \
  --type ERC20 \
  --watch
```

The `--watch` flag will monitor the workflow progress in real-time.

### Using API

```bash
curl -X POST http://localhost:8000/api/v1/workflows/generate \
  -H "Content-Type: application/json" \
  -d '{
    "nlp_input": "Create an ERC20 token named MyToken with symbol MTK and initial supply 1000000",
    "network": "hyperion_testnet",
    "contract_type": "ERC20"
  }'
```

Response:
```json
{
  "workflow_id": "abc123-def456-...",
  "status": "generating",
  "progress_percentage": 10
}
```

### Monitor Progress

```bash
# Get workflow status
curl http://localhost:8000/api/v1/workflows/{workflow_id}

# Or use CLI
hyperagent workflow status --workflow-id {workflow_id} --watch
```

## Next Steps

1. **View Generated Contract**: Use the contract ID from the workflow response
2. **Deploy to Blockchain**: The workflow will automatically deploy if configured
3. **View on Explorer**: Check the transaction hash on the network explorer

## Common Issues

### Database Connection Failed

- Ensure PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Verify database credentials

### Redis Connection Failed

- Ensure Redis is running
- Check `REDIS_URL` in `.env`
- Verify Redis is accessible

### LLM API Errors

- Verify `GEMINI_API_KEY` is set correctly
- Check API key has sufficient quota
- Review API response in logs

For more troubleshooting, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

## Additional Resources

- [Configuration Guide](./CONFIGURATION.md) - Detailed configuration options
- [API Reference](./API_REFERENCE.md) - Complete API documentation
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment instructions
- [Networks Guide](./NETWORKS.md) - Supported networks and features

---

**Ready to build?** Start creating your first smart contract! 🚀

