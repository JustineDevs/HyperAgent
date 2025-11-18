# HyperAgent Collaborator Guide

**Document Type**: How-To Guide (Goal-Oriented)  
**Category**: Contributor Documentation  
**Audience**: Contributors, Collaborators  
**Location**: `GUIDE/COLLABORATOR_GUIDE.md`

This guide helps contributors understand how to contribute code, documentation, and improvements to HyperAgent. Follow this guide to ensure your contributions align with project standards and are accepted.

## Table of Contents

- [Getting Started as a Contributor](#getting-started-as-a-contributor)
- [Setting Up Development Environment](#setting-up-development-environment)
- [Making Code Changes](#making-code-changes)
- [Writing Tests](#writing-tests)
- [Submitting Changes](#submitting-changes)
- [Code Review Process](#code-review-process)
- [Documentation Contributions](#documentation-contributions)

---

## Getting Started as a Contributor

**Goal**: Understand the contribution process and get started.

### Prerequisites

- GitHub account
- Git installed
- Python 3.10+ installed
- Basic understanding of Python, async/await, and blockchain concepts

### Steps

1. **Fork the repository**:
   - Visit https://github.com/JustineDevs/HyperAgent
   - Click "Fork" button
   - Clone your fork locally:
     ```bash
     git clone https://github.com/YOUR_USERNAME/HyperAgent.git
     cd HyperAgent
     ```

2. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/JustineDevs/HyperAgent.git
   ```

3. **Read the Code of Conduct**:
   - See [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)
   - Ensure you understand and agree to follow it

4. **Read Contributing Guidelines**:
   - See [CONTRIBUTING.md](../CONTRIBUTING.md)
   - Review development workflow and standards

### Expected Result

- Repository forked and cloned
- Upstream remote configured
- Understanding of contribution process

---

## Setting Up Development Environment

**Goal**: Set up a complete development environment for contributing.

### Prerequisites

- Forked repository cloned locally
- Python 3.10+ installed
- PostgreSQL 15+ (or Supabase account)
- Redis 7+ (or Docker)

### Steps

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. **Set up pre-commit hooks**:
   ```bash
   pre-commit install
   ```

4. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**:
   ```bash
   # Create database and enable pgvector
   createdb hyperagent_dev
   psql hyperagent_dev -c "CREATE EXTENSION vector;"
   
   # Run migrations
   alembic upgrade head
   ```

6. **Run tests to verify setup**:
   ```bash
   pytest tests/unit/ -v
   ```

### Expected Result

- Development environment fully configured
- All tests passing
- Ready to make code changes

---

## Making Code Changes

**Goal**: Implement changes following project standards.

### Prerequisites

- Development environment set up
- Understanding of the codebase structure
- Clear understanding of what you want to change

### Steps

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # Or for bug fixes:
   git checkout -b fix/your-bug-fix-name
   ```

2. **Follow the development workflow**:
   - See [Developer Guide](./DEVELOPER_GUIDE.md) for architecture details
   - See [Development Workflow](../.cursor/rules/dev-workflow.mdc) for detailed process

3. **Write code following standards**:
   - Use Black for formatting: `black hyperagent/`
   - Use isort for imports: `isort hyperagent/`
   - Follow PEP 8 style guide
   - Add type hints to all functions
   - Write docstrings for public APIs

4. **Test your changes**:
   ```bash
   # Run unit tests
   pytest tests/unit/ -v
   
   # Run integration tests
   pytest tests/integration/ -v
   
   # Run with coverage
   pytest --cov=hyperagent --cov-report=html
   ```

5. **Update documentation**:
   - Update relevant documentation files
   - Add docstrings to new functions/classes
   - Update API documentation if endpoints changed

### Code Style Guidelines

**Formatting**:
```bash
# Auto-format code
black hyperagent/
isort hyperagent/

# Check formatting
black --check hyperagent/
isort --check hyperagent/
```

**Type Hints**:
```python
from typing import Dict, Any, Optional

async def process(
    input_data: Dict[str, Any],
    network: Optional[str] = None
) -> Dict[str, Any]:
    """Process input and return result."""
    pass
```

**Docstrings**:
```python
def generate_contract(
    nlp_input: str,
    network: str
) -> Dict[str, Any]:
    """
    Generate a smart contract from natural language input.
    
    Args:
        nlp_input: Natural language description of contract
        network: Target blockchain network
        
    Returns:
        Dictionary containing generated contract code and metadata
        
    Raises:
        ValueError: If input is invalid or network not supported
    """
    pass
```

### Expected Result

- Code changes implemented
- Code follows project standards
- Tests written and passing
- Documentation updated

---

## Writing Tests

**Goal**: Write comprehensive tests for your changes.

### Prerequisites

- Understanding of pytest and async testing
- Knowledge of what functionality needs testing

### Steps

1. **Write unit tests** (in `tests/unit/`):
   ```python
   import pytest
   from unittest.mock import AsyncMock, MagicMock
   from hyperagent.agents.generation import GenerationAgent
   
   @pytest.mark.asyncio
   async def test_generation_agent_process():
       # Setup
       mock_llm = AsyncMock()
       mock_llm.generate.return_value = "pragma solidity ^0.8.0; contract Test {}"
       agent = GenerationAgent(mock_llm)
       
       # Execute
       result = await agent.process({
           "nlp_description": "Create simple contract",
           "network": "hyperion_testnet"
       })
       
       # Verify
       assert result["status"] == "success"
       assert "contract_code" in result
   ```

2. **Write integration tests** (in `tests/integration/`):
   ```python
   @pytest.mark.asyncio
   async def test_workflow_end_to_end():
       # Test complete workflow pipeline
       coordinator = WorkflowCoordinator(...)
       result = await coordinator.execute_workflow(...)
       assert result["status"] == "success"
   ```

3. **Run tests**:
   ```bash
   # All tests
   pytest
   
   # Specific test file
   pytest tests/unit/test_generation_agent.py -v
   
   # With coverage
   pytest --cov=hyperagent --cov-report=html
   ```

### Test Requirements

- **Unit tests**: Test individual functions/classes in isolation
- **Integration tests**: Test component interactions
- **Coverage**: Aim for 80%+ coverage for new code
- **Mocking**: Mock external dependencies (LLM, blockchain, database)

### Expected Result

- Tests written and passing
- Good test coverage
- Tests are maintainable and well-documented

---

## Submitting Changes

**Goal**: Submit your changes for review via pull request.

### Prerequisites

- Code changes complete
- Tests written and passing
- Documentation updated
- Code follows project standards

### Steps

1. **Commit your changes**:
   ```bash
   # Stage changes
   git add .
   
   # Commit with conventional commit message
   git commit -m "feat: Add new feature for X"
   # Or:
   git commit -m "fix: Resolve bug in Y"
   # Or:
   git commit -m "docs: Update user guide"
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create pull request**:
   - Go to https://github.com/JustineDevs/HyperAgent
   - Click "New Pull Request"
   - Select your branch
   - Fill out PR template:
     - Description of changes
     - Related issues
     - Testing performed
     - Screenshots (if UI changes)

4. **Wait for review**:
   - Maintainers will review your PR
   - Address any feedback
   - Update PR as needed

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

**Examples**:
```
feat(agent-generation): Add constructor argument extraction
fix(deployment): Resolve gas estimation timeout issue
docs(user-guide): Add constructor arguments section
test(integration): Add end-to-end workflow tests
```

### Expected Result

- Pull request created
- CI/CD checks passing
- Ready for review

---

## Code Review Process

**Goal**: Understand and participate in the code review process.

### Prerequisites

- Pull request submitted
- CI/CD checks passing

### Steps

1. **Address review feedback**:
   - Read comments carefully
   - Ask questions if unclear
   - Make requested changes
   - Push updates to your branch

2. **Respond to comments**:
   - Acknowledge feedback
   - Explain your reasoning if needed
   - Mark conversations as resolved when done

3. **Request re-review**:
   - After addressing feedback, request another review
   - Maintainers will approve when ready

### Review Criteria

Your code will be reviewed for:
- **Correctness**: Does it work as intended?
- **Code Quality**: Follows project standards?
- **Test Coverage**: Adequate tests?
- **Documentation**: Updated appropriately?
- **Performance**: No performance regressions?
- **Security**: No security issues?

### Expected Result

- Code reviewed and approved
- Changes merged to main branch
- Contribution acknowledged

---

## Documentation Contributions

**Goal**: Contribute to project documentation.

### Prerequisites

- Understanding of Diátaxis framework (see [Documentation Rules](../.cursor/rules/Documentation.mdc))
- Markdown knowledge

### Steps

1. **Identify documentation need**:
   - Missing documentation
   - Outdated information
   - Unclear explanations

2. **Choose appropriate category**:
   - **Tutorial**: Step-by-step learning (e.g., Getting Started)
   - **How-To**: Goal-oriented tasks (e.g., Deploy Contract)
   - **Explanation**: Understanding concepts (e.g., Architecture)
   - **Reference**: Technical specifications (e.g., API Reference)

3. **Write documentation**:
   - Follow [Documentation Standards](../.cursor/rules/Documentation.mdc)
   - Use clear, concise language
   - Include code examples
   - Add links to related docs

4. **Submit as part of PR**:
   - Include documentation changes in your PR
   - Or create separate PR for docs-only changes

### Documentation Standards

- **Clear**: Plain language, define technical terms
- **Concise**: Only necessary information
- **Structured**: Use headings, lists, code blocks
- **Examples**: Include working code examples
- **Links**: Link to related documentation

### Expected Result

- Documentation updated
- Clear and helpful for users
- Follows project standards

---

## Related Documentation

- **[Contributing Guidelines](../CONTRIBUTING.md)** - General contribution guidelines
- **[Code of Conduct](../CODE_OF_CONDUCT.md)** - Community standards
- **[Developer Guide](./DEVELOPER_GUIDE.md)** - Technical development guide
- **[Development Workflow](../.cursor/rules/dev-workflow.mdc)** - Detailed development process
- **[Documentation Standards](../.cursor/rules/Documentation.mdc)** - Documentation guidelines

---

## Need Help?

- Review [Contributing Guidelines](../CONTRIBUTING.md)
- Check existing issues and PRs
- Ask questions in GitHub Discussions
- Contact maintainers: conduct@hyperionkit.xyz

---

## Recognition

Contributors are recognized in:
- [CONTRIBUTORS.md](../CONTRIBUTORS.md) (if exists)
- Release notes
- Project acknowledgments

Thank you for contributing to HyperAgent!

