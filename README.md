<div align="center">
  <img src="/docs/public/ascii-art-doh-HyperAgent.png" alt="HyperAgent ASCII Art" width="800">
</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Quick Start](#-quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Verification](#verification)
- [Usage](#-usage)
  - [Basic Workflow](#basic-workflow)
  - [Advanced Features](#advanced-features)
  - [Python API](#python-api)
- [Documentation](#-documentation)
- [Architecture](#-architecture)
- [Security](#-security)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [Support](#-support)
- [License](#-license)
- [Links](#-links)

---

## 🎯 Overview

**HyperAgent** is an enterprise-grade, AI-powered platform that automates the complete smart contract development lifecycle. By leveraging Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), and advanced blockchain integration, HyperAgent transforms natural language descriptions into production-ready, audited, and deployed smart contracts across multiple blockchain networks.

### Key Benefits

- ⚡ **10-50x Faster Development** - Reduce smart contract development time from days to minutes
- 🛡️ **Enterprise-Grade Security** - Automated security auditing with industry-standard tools (Slither, Mythril, Echidna)
- 🌐 **Multi-Chain Support** - Deploy to Hyperion, Mantle, and other EVM-compatible networks
- 🤖 **Intelligent Automation** - AI-powered constructor argument generation and contract optimization
- 📊 **Real-Time Monitoring** - Live progress tracking and workflow status updates
- 🚀 **Production-Ready** - End-to-end pipeline from NLP to on-chain deployment

---

## ✨ Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| 🔍 **AI-Powered Generation** | Convert natural language to Solidity contracts using Gemini/GPT-4 |
| 🛡️ **Automated Security Auditing** | Comprehensive analysis with Slither, Mythril, and Echidna |
| 🧪 **Automated Testing** | Compile contracts and generate unit tests automatically |
| 🚀 **On-Chain Deployment** | Deploy to Hyperion and Mantle networks via Alith SDK |
| 📚 **RAG-Enhanced Generation** | Template retrieval for improved code quality |
| ⚡ **Parallel Batch Deployment** | Deploy multiple contracts simultaneously (10-50x faster with PEF) |
| 🎯 **MetisVM Optimization** | Generate contracts optimized for MetisVM with floating-point support |
| 💾 **EigenDA Integration** | Cost-efficient data availability storage |
| 📊 **Real-Time Progress Tracking** | Monitor workflow progress with live updates |
| 🔧 **Constructor Argument Generation** | Automatically extract and generate constructor values |

### Supported Networks

- **Hyperion Testnet** - Full support with PEF batch deployment
- **Mantle Testnet** - Full support with EigenDA integration
- **Additional Networks** - EVM-compatible networks via Web3

---

## 🚀 Quick Start

### Prerequisites

#### Required Software

| Software | Version | Installation |
|----------|---------|--------------|
| **Python** | 3.10+ | [Windows](https://www.python.org/downloads/windows) • [macOS](https://www.python.org/downloads/mac-osx) • [Linux](https://www.python.org/downloads/source/) |
| **PostgreSQL** | 15+ | [Download](https://www.postgresql.org/download/) • [Supabase (Cloud)](https://supabase.com) |
| **Redis** | 7+ | [Download](https://redis.io/download) • [Redis Cloud](https://redis.com/try-free/) |
| **Git** | Latest | [Download](https://git-scm.com/downloads) |

#### Optional but Recommended

| Software | Purpose | Installation |
|----------|---------|--------------|
| **Node.js** | Contract testing (Hardhat/Foundry) | [Download](https://nodejs.org/en/download/) |
| **Docker** | Containerized development | [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| **GNU Make** | Build automation | [Download](http://gnuwin32.sourceforge.net/packages/make.htm) |
| **VS Code** | Recommended IDE | [Download](https://code.visualstudio.com/download) |

#### Required API Keys

- **Google Gemini API Key** (Required)
  - Get from: [Google AI Studio](https://aistudio.google.com/app/apikey)
- **OpenAI API Key** (Optional - fallback provider)
  - Get from: [OpenAI Platform](https://platform.openai.com/api-keys)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/JustineDevs/HyperAgent.git
cd HyperAgent
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows Git Bash)
source venv/Scripts/activate

# Activate (Windows Command Prompt)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment

```bash
# Copy example environment file
cp env.example .env

# Edit .env with your API keys and configuration
# Required: GEMINI_API_KEY
# Optional: OPENAI_API_KEY, DATABASE_URL, REDIS_URL
```

#### 5. Initialize Database

```bash
# Run database migrations
alembic upgrade head
```

#### 6. Start the API Server

```bash
# Development mode (with auto-reload)
uvicorn hyperagent.api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn hyperagent.api.main:app --host 0.0.0.0 --port 8000
```

### Verification

```bash
# Check system health via CLI
hyperagent system health

# Or via API
curl http://localhost:8000/api/v1/health/

# Expected response: {"status": "healthy", ...}
```

> 📖 **Need more help?** See the [Getting Started Guide](./GUIDE/GETTING_STARTED.md) for detailed setup instructions.

---

## 💻 Usage

### Basic Workflow

#### Generate and Deploy a Contract

```bash
# Create a workflow with constructor arguments
hyperagent workflow create \
  -d "Create an ERC20 token with name 'HYPERAGENT', symbol 'HYPE', and initial supply of 10000" \
  --network hyperion_testnet \
  --type ERC20 \
  --watch

# Monitor workflow progress
hyperagent workflow status --workflow-id <workflow-id> --watch

# View generated contract
hyperagent contract view <contract-id>
```

#### Interactive Mode

```bash
# Launch interactive CLI
hyperagent workflow create --interactive
```

### Advanced Features

#### MetisVM Optimization

```bash
# Generate contract optimized for MetisVM
hyperagent workflow create \
  --description "Create a financial derivative contract with floating-point pricing" \
  --network hyperion_testnet \
  --optimize-metisvm \
  --enable-fp
```

#### Batch Deployment with PEF

```bash
# Deploy multiple contracts in parallel (10-50x faster)
hyperagent deployment batch \
  --contracts-file examples/batch_deployment_example.json \
  --network hyperion_testnet \
  --use-pef \
  --max-parallel 10
```

#### Export and Share Contracts

```bash
# Export workflow to JSON
hyperagent workflow export --workflow-id <id> -o workflow.json

# Search contract templates
hyperagent template search -q "ERC20"
```

### Python API

```python
import httpx

# Create workflow
response = httpx.post(
    "http://localhost:8000/api/v1/workflows/generate",
    json={
        "nlp_input": "Create an ERC20 token with 1 million supply",
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

> 📚 **More Examples:** See [Usage Examples](./GUIDE/GETTING_STARTED.md#example-workflows) for additional use cases.

---

## 📚 Documentation

### Getting Started

- **[Getting Started Guide](./GUIDE/GETTING_STARTED.md)** - Complete setup and first contract generation
- **[Developer Guide](./GUIDE/DEVELOPER_GUIDE.md)** - Development environment and workflow
- **[User Guide](./GUIDE/USER_GUIDE.md)** - End-user task-oriented instructions
- **[API Documentation](./GUIDE/API.md)** - Complete API reference

### How-To Guides

- **[Deployment Guide](./GUIDE/DEPLOYMENT.md)** - Deploy contracts to blockchain
- **[Docker Setup](./GUIDE/DOCKER.md)** - Run HyperAgent with Docker
- **[Hyperion PEF Guide](./docs/HYPERION_PEF_GUIDE.md)** - Parallel batch deployment
- **[MetisVM Optimization](./docs/METISVM_OPTIMIZATION.md)** - MetisVM-specific features
- **[Troubleshooting](./docs/TROUBLESHOOTING.md)** - Common issues and solutions

### Technical Documentation

- **[Architecture Diagrams](./docs/ARCHITECTURE_DIAGRAMS.md)** - System architecture and patterns
- **[Complete Technical Specification](./docs/complete-tech-spec.md)** - Full technical details
- **[Network Compatibility](./docs/NETWORK_COMPATIBILITY.md)** - Supported networks and features
- **[Testing Setup Guide](./docs/TESTING_SETUP_GUIDE.md)** - Testing configuration and examples

### Contributing

- **[Contributing Guidelines](./CONTRIBUTING.md)** - How to contribute
- **[Collaborator Guide](./GUIDE/COLLABORATOR_GUIDE.md)** - Contributor workflow
- **[Code of Conduct](./CODE_OF_CONDUCT.md)** - Community standards

---

## 🏗️ Architecture

HyperAgent follows a **Service-Oriented Architecture (SOA)** with event-driven design principles:

### Architecture Principles

- **Agent-to-Agent (A2A) Protocol** - Decoupled agent communication via event bus
- **Event-Driven Architecture** - Redis Streams for event persistence and real-time updates
- **Service Orchestration** - Sequential and parallel service execution patterns
- **RAG System** - Template retrieval and similarity matching for enhanced generation

### Core Components

```
hyperagent/
├── api/          # FastAPI REST endpoints and WebSocket support
├── agents/       # Agent implementations (Generation, Audit, Testing, Deployment)
├── architecture/ # SOA, A2A patterns and orchestration
├── blockchain/   # Alith SDK, EigenDA, Web3 integration
├── core/         # Core services and configuration
├── events/       # Event bus and event types
├── llm/          # LLM providers (Gemini, OpenAI)
├── rag/          # RAG system for template retrieval
├── security/     # Security audit tools (Slither, Mythril, Echidna)
└── cli/          # Command-line interface
```

### Technology Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL 15+ with pgvector extension
- **Cache/Events**: Redis 7+ with Streams
- **Blockchain**: Web3.py, Alith SDK, EigenDA
- **LLM**: Google Gemini, OpenAI GPT-4
- **Security**: Slither, Mythril, Echidna

> 📖 **Detailed Architecture:** See [Architecture Diagrams](./docs/ARCHITECTURE_DIAGRAMS.md) for comprehensive system design.

---

## 🔒 Security

HyperAgent implements multiple layers of security:

### Security Features

- ✅ **Automated Security Auditing** - Multi-tool analysis (Slither, Mythril, Echidna)
- ✅ **Constructor Argument Validation** - Type-safe argument generation and validation
- ✅ **Network Feature Detection** - Graceful fallbacks for unsupported features
- ✅ **Secret Management** - Secure API key and private key handling
- ✅ **Input Validation** - Comprehensive input sanitization and validation

### Security Best Practices

- Use environment variables for sensitive data (API keys, private keys)
- Never commit `.env` files to version control
- Regularly update dependencies for security patches
- Review generated contracts before production deployment
- Follow [Security Guidelines](./SECURITY.md) for reporting vulnerabilities

> 🔐 **Security Issues:** Report security vulnerabilities via [SECURITY.md](./SECURITY.md)

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run with coverage
pytest --cov=hyperagent --cov-report=html

# Run specific test file
pytest tests/integration/test_end_to_end_workflow.py -v
```

### Test Structure

```
tests/
├── unit/          # Unit tests for individual components
├── integration/   # Integration tests for services
├── performance/   # Performance and SLA tests
└── load/          # Load testing scripts
```

> 📖 **Testing Guide:** See [Testing Setup Guide](./docs/TESTING_SETUP_GUIDE.md) for complete testing documentation.

---

## 🤝 Contributing

We welcome contributions from the community! HyperAgent is an open-source project and we appreciate your help.

### How to Contribute

1. **Fork** the repository
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** following our [Development Workflow](./.cursor/rules/dev-workflow.mdc)
4. **Write tests** for your changes
5. **Commit** your changes (`git commit -m 'feat: Add amazing feature'`)
6. **Push** to your branch (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

### Development Guidelines

- Follow the [Standard Development Workflow](./.cursor/rules/dev-workflow.mdc)
- Write tests before implementation (TDD approach)
- Follow code style guidelines (PEP 8, type hints, async/await)
- Update documentation for new features
- Ensure all tests pass before submitting PR

### Code of Conduct

Please note we have a [Code of Conduct](./CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

> 📖 **Contributing Guide:** See [CONTRIBUTING.md](./CONTRIBUTING.md) and [Collaborator Guide](./GUIDE/COLLABORATOR_GUIDE.md) for detailed contribution guidelines.

---

## 💬 Support

### Getting Help

- 📖 **Documentation** - Check our [documentation](#-documentation) section
- 🐛 **Bug Reports** - Open an issue on [GitHub Issues](https://github.com/JustineDevs/HyperAgent/issues)
- 💡 **Feature Requests** - Submit via [GitHub Issues](https://github.com/JustineDevs/HyperAgent/issues)
- ❓ **Questions** - Check [Troubleshooting Guide](./docs/TROUBLESHOOTING.md)

### Community

- 🌐 **Website**: [hyperionkit.xyz](https://hyperionkit.xyz/)
- 🔗 **Linktree**: [linktr.ee/Hyperionkit](https://linktr.ee/Hyperionkit)
- 📝 **Blog**: [Medium](https://medium.com/@hyperionkit)

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](./LICENSE) file for details.

Contributions to this project are accepted under the same license.

---

## 🔗 Links

### Official Resources

- **Website**: [https://hyperionkit.xyz/](https://hyperionkit.xyz/)
- **GitHub Repository**: [https://github.com/JustineDevs/HyperAgent](https://github.com/JustineDevs/HyperAgent)
- **Organization**: [https://github.com/HyperionKit/Hyperkit](https://github.com/HyperionKit/Hyperkit)
- **Linktree**: [https://linktr.ee/Hyperionkit](https://linktr.ee/Hyperionkit)
- **Medium Blog**: [https://medium.com/@hyperionkit](https://medium.com/@hyperionkit)

---

## 🙏 Acknowledgments

Special thanks to:

- All [contributors](https://github.com/JustineDevs/HyperAgent/graphs/contributors) who have helped improve this project
- The **Hyperion** and **Mantle** communities for network support
- **OpenZeppelin** for contract standards and best practices
- The open-source community for tools and libraries

---

<div align="center">

**Built with ❤️ by the HyperAgent team**

[⬆ Back to Top](#-table-of-contents)

</div>
