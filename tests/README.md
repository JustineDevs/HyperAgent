# HyperAgent Testing Infrastructure

**Document Type**: Reference (Technical Specification)  
**Category**: Testing Documentation  
**Audience**: Developers, Contributors  
**Location**: `tests/README.md`

Comprehensive testing infrastructure for HyperAgent with unit, integration, performance, and load tests.

## Test Structure

```
tests/
├── unit/              # Unit tests for individual components
│   ├── test_agents_*.py          # Agent unit tests
│   ├── test_services.py          # Service unit tests
│   ├── test_a2a_protocol.py      # A2A protocol tests
│   ├── test_blockchain.py        # Blockchain integration tests
│   ├── test_compilation_service.py
│   ├── test_deployment_validation.py
│   ├── test_eigenda_enhanced.py
│   ├── test_event_bus.py
│   ├── test_hyperion_pef.py
│   ├── test_metisvm_optimizer.py
│   ├── test_metrics.py
│   ├── test_network_features.py
│   ├── test_service_registry.py
│   ├── test_template_retriever_async.py
│   ├── test_test_framework_detection.py
│   ├── test_user_creation.py
│   │
│   └── Manual Test Scripts (standalone, not pytest):
│       └── test_cli_watch_mode.py                # Manual CLI watch mode testing
│
├── integration/       # Integration tests
│   ├── test_api.py                    # API endpoint tests
│   ├── test_database.py               # Database integration tests
│   ├── test_eigenda_batch.py          # EigenDA batch operations
│   ├── test_end_to_end_workflow.py    # Complete workflow E2E tests
│   ├── test_full_workflow.py          # Feature-specific workflow tests
│   ├── test_ipfs_template_import.py   # IPFS template import
│   ├── test_metisvm_optimization.py   # MetisVM optimization integration
│   ├── test_network_fallbacks.py      # Network feature fallbacks
│   ├── test_pef_batch_deployment.py   # PEF batch deployment
│   ├── test_redis.py                  # Redis integration tests
│   ├── test_workflow_with_compilation.py
│   │
│   └── Manual Test Scripts (standalone, not pytest):
│       ├── test_api_endpoints_manual.py          # Manual API endpoint testing
│       ├── test_batch_deployment_manual.py       # Manual batch deployment testing
│       ├── test_metisvm_optimization_manual.py    # Manual MetisVM optimization testing
│       ├── test_production_workflow_manual.py     # Manual production workflow testing
│       ├── test_real_world_complete_manual.py     # Manual complete E2E testing
│       ├── test_real_world_deployment_manual.py   # Manual deployment testing
│       └── test_workflow_creation_manual.py       # Manual workflow creation testing
│
├── performance/       # Performance and SLA tests
│   ├── test_pef_performance.py       # PEF performance benchmarks
│   ├── test_sla_compliance.py         # SLA compliance tests
│   │
│   └── Manual Test Scripts (standalone, not pytest):
│       └── test_performance_manual.py             # Manual performance testing
│
└── load/              # Load testing
    └── load_test.py                   # Load testing scripts
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run by Category

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Performance tests only
pytest tests/performance/ -v

# Skip slow tests
pytest -m "not slow"
```

### Run with Coverage

```bash
pytest --cov=hyperagent --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/unit/test_agents_generation.py -v
```

### Run Specific Test Function

```bash
pytest tests/integration/test_end_to_end_workflow.py::test_complete_workflow_simple_contract -v
```

### Run Manual Test Scripts

Manual test scripts are standalone Python scripts (not pytest) that can be run directly:

```bash
# Integration manual tests
python tests/integration/test_api_endpoints_manual.py
python tests/integration/test_batch_deployment_manual.py
python tests/integration/test_metisvm_optimization_manual.py
python tests/integration/test_production_workflow_manual.py
python tests/integration/test_real_world_complete_manual.py
python tests/integration/test_real_world_deployment_manual.py
python tests/integration/test_workflow_creation_manual.py

# Performance manual tests
python tests/performance/test_performance_manual.py

# Unit manual tests
python tests/unit/test_cli_watch_mode.py
```

**Note**: Manual test scripts require the API server to be running and may require real API keys and funded wallets for deployment tests.

## Test Markers

Test files use pytest markers to categorize tests:

- `@pytest.mark.unit` - Unit tests (isolated component tests)
- `@pytest.mark.integration` - Integration tests (component interaction)
- `@pytest.mark.performance` - Performance/SLA tests
- `@pytest.mark.slow` - Slow-running tests (>5 seconds)
- `@pytest.mark.requires_db` - Tests requiring database connection
- `@pytest.mark.requires_redis` - Tests requiring Redis connection
- `@pytest.mark.requires_api` - Tests requiring external APIs (LLM, blockchain)

### Using Markers

```bash
# Run only unit tests
pytest -m unit

# Run integration tests excluding slow ones
pytest -m "integration and not slow"

# Run tests that require database
pytest -m requires_db
```

## Coverage Requirements

- **Target**: >80% overall code coverage
- **Critical Components**: >90% coverage (agents, services, orchestrator)
- **Coverage Reports**: HTML, XML, and terminal output
- **CI/CD**: Coverage reports generated automatically on pull requests

### View Coverage Report

```bash
# Generate HTML report
pytest --cov=hyperagent --cov-report=html

# Open report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

## Test Fixtures

### Common Fixtures (conftest.py)

- `redis_client` - Redis client for testing
- `event_bus` - Event bus instance with mocked Redis
- `test_settings` - Test configuration overrides
- `db_session` - Database session for integration tests
- `mock_web3` - Mock Web3 instance for blockchain tests
- `mock_llm_provider` - Mock LLM provider for generation tests
- `service_registry` - Service registry with mocked services

### Using Fixtures

```python
@pytest.mark.asyncio
async def test_my_feature(event_bus, service_registry):
    """Test using fixtures"""
    # event_bus and service_registry are automatically provided
    pass
```

## Test Categories

### Unit Tests (`tests/unit/`)

**Purpose**: Test individual components in isolation

**Characteristics**:
- Fast execution (<1 second per test)
- Mock all external dependencies
- Test single function/class behavior
- No database or network calls

**Examples**:
- `test_agents_generation.py` - Generation agent logic
- `test_services.py` - Service implementations
- `test_compilation_service.py` - Compilation service

### Integration Tests (`tests/integration/`)

**Purpose**: Test component interactions and workflows

**Characteristics**:
- Test multiple components together
- May use real database/Redis (with test data)
- Mock external APIs (LLM, blockchain RPC)
- Test data flow through pipeline

**Examples**:
- `test_end_to_end_workflow.py` - Complete workflow pipeline
- `test_api.py` - API endpoint integration
- `test_pef_batch_deployment.py` - Batch deployment integration

### Performance Tests (`tests/performance/`)

**Purpose**: Verify SLA compliance and performance benchmarks

**Characteristics**:
- Measure execution time
- Test under load
- Verify SLA requirements (p95, p99 latencies)
- May be marked as `@pytest.mark.slow`

**Examples**:
- `test_sla_compliance.py` - Agent SLA verification
- `test_pef_performance.py` - PEF batch deployment performance

### Load Tests (`tests/load/`)

**Purpose**: Stress testing and capacity planning

**Characteristics**:
- High concurrency scenarios
- Resource usage monitoring
- Throughput measurement
- Not run in regular CI/CD

## Performance Testing

### SLA Compliance Tests

Agent performance requirements:

- **Generation Agent**: p95 < 60s, p99 < 90s
- **Audit Agent**: p95 < 100s, p99 < 150s
- **Testing Agent**: p95 < 100s, p99 < 150s
- **Deployment Agent**: p95 < 120s, p99 < 180s

### Running Performance Tests

```bash
# Run all performance tests
pytest tests/performance/ -v

# Run specific SLA test
pytest tests/performance/test_sla_compliance.py::test_generation_agent_sla_p95 -v

# Run with timing information
pytest tests/performance/ --durations=10
```

## Integration Test Requirements

### Database Tests

- **Test Database**: `hyperagent_test`
- **User**: `test` / Password: `test` (or from `.env`)
- **Setup**: Database created and migrations run before tests
- **Cleanup**: Tests should clean up after themselves

### Redis Tests

- **Connection**: `localhost:6379`
- **Database**: `0` (test database)
- **Setup**: Redis must be running or tests will be skipped

### External API Tests

- **LLM APIs**: Mocked by default (use real APIs only in manual tests)
- **Blockchain RPC**: Mocked by default
- **IPFS/Pinata**: Mocked by default

## Continuous Integration

Tests are automatically run in CI/CD pipeline:

- **Unit tests**: Run on every commit
- **Integration tests**: Run on pull requests
- **Performance tests**: Run on release candidates
- **Coverage reports**: Generated and uploaded to codecov
- **Test results**: Reported in pull request comments

## Writing New Tests

### Unit Test Template

```python
"""Unit tests for ComponentName"""
import pytest
from unittest.mock import AsyncMock, MagicMock

pytestmark = [pytest.mark.unit]

@pytest.fixture
def mock_dependency():
    """Mock external dependency"""
    return AsyncMock()

@pytest.mark.asyncio
async def test_component_functionality(mock_dependency):
    """Test component behavior"""
    # Arrange
    component = MyComponent(mock_dependency)
    
    # Act
    result = await component.process(input_data)
    
    # Assert
    assert result["status"] == "success"
    mock_dependency.method.assert_called_once()
```

### Integration Test Template

```python
"""Integration tests for ComponentName"""
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.requires_db]

@pytest.mark.asyncio
async def test_component_integration(db_session, event_bus):
    """Test component with database"""
    # Test with real database connection
    component = MyComponent(db_session, event_bus)
    result = await component.process(input_data)
    
    # Verify database state
    assert result["status"] == "success"
```

### Performance Test Template

```python
"""Performance tests for ComponentName"""
import pytest
import time

pytestmark = [pytest.mark.performance, pytest.mark.slow]

@pytest.mark.asyncio
async def test_component_performance():
    """Test component meets SLA requirements"""
    start_time = time.time()
    
    result = await component.process(input_data)
    
    elapsed = time.time() - start_time
    
    # Verify SLA compliance (p95 < 60s)
    assert elapsed < 60.0
    assert result["status"] == "success"
```

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Mocking**: Mock external dependencies (APIs, databases, network calls)
3. **Fixtures**: Use fixtures for common setup/teardown
4. **Naming**: Use descriptive test names: `test_<component>_<behavior>_<expected_result>`
5. **Coverage**: Aim for >80% overall coverage, >90% for critical components
6. **Performance**: Mark slow tests with `@pytest.mark.slow`
7. **Cleanup**: Clean up test data and resources after tests
8. **Documentation**: Add docstrings explaining what each test verifies

## Test File Organization

### Naming Conventions

- **Unit tests**: `test_<component>.py` (e.g., `test_agents_generation.py`)
- **Integration tests**: `test_<feature>_integration.py` or `test_<workflow>.py`
- **Performance tests**: `test_<component>_performance.py` or `test_sla_compliance.py`

### File Structure

Each test file should:
- Have a module docstring explaining what it tests
- Use appropriate pytest markers
- Group related tests together
- Use fixtures for common setup

## Troubleshooting

### Tests Failing Locally

1. **Check dependencies**: Ensure all requirements are installed
2. **Check environment**: Verify `.env` is configured correctly
3. **Check services**: Ensure PostgreSQL and Redis are running
4. **Check mocks**: Verify mocks are set up correctly

### Tests Passing Locally but Failing in CI

1. **Check environment differences**: CI may have different Python/OS versions
2. **Check timing**: CI may be slower, causing timeout issues
3. **Check dependencies**: CI may have different dependency versions
4. **Check database**: CI uses test database, verify migrations are run

### Slow Tests

1. **Identify slow tests**: Use `pytest --durations=10`
2. **Optimize**: Reduce I/O, use better mocks, parallelize where possible
3. **Mark as slow**: Use `@pytest.mark.slow` for tests >5 seconds

## Related Documentation

- **[Developer Guide](../GUIDE/DEVELOPER_GUIDE.md)** - Development setup and practices
- **[Testing Setup Guide](../docs/TESTING_SETUP_GUIDE.md)** - Detailed testing configuration
- **[Contributing Guidelines](../CONTRIBUTING.md)** - Contribution process

---

## Quick Reference

### Common Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific category
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=hyperagent --cov-report=html

# Run and show slowest tests
pytest --durations=10

# Run only fast tests
pytest -m "not slow"
```

### Test File Locations

- **Unit tests**: `tests/unit/test_*.py` (pytest-based)
- **Integration tests**: `tests/integration/test_*.py` (pytest-based)
- **Performance tests**: `tests/performance/test_*.py` (pytest-based)
- **Load tests**: `tests/load/load_test.py`
- **Manual test scripts**: `tests/*/test_*_manual.py` (standalone scripts, not pytest)

### Manual Test Scripts

Manual test scripts are standalone Python scripts that test the system against a running API server. They are useful for:

- **Real-world testing**: Testing with actual API endpoints and database
- **End-to-end verification**: Complete workflow testing with real deployments
- **Performance benchmarking**: Measuring actual system performance
- **Debugging**: Troubleshooting issues in production-like environments

**Differences from pytest tests**:
- Run directly with `python` (not `pytest`)
- Require API server to be running
- May require real API keys and funded wallets
- Provide detailed console output with progress bars
- Exit with status codes (0 = success, 1 = failure)

**When to use manual tests**:
- Before deploying to production
- To verify system works with real infrastructure
- To benchmark performance under real conditions
- To test deployment workflows end-to-end
