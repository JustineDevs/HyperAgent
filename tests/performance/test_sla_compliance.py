"""Performance tests for SLA compliance"""
import pytest

pytestmark = [pytest.mark.performance, pytest.mark.slow]
import asyncio
import time
from unittest.mock import AsyncMock
from hyperagent.agents.generation import GenerationAgent
from hyperagent.agents.audit import AuditAgent
from hyperagent.core.services.generation_service import GenerationService


@pytest.mark.asyncio
@pytest.mark.slow
async def test_generation_agent_sla_p95():
    """Test Generation Agent p95 latency < 60s"""
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "contract Test {}"
    
    mock_template = AsyncMock()
    mock_template.retrieve_and_generate.return_value = "contract Test {}"
    
    mock_event_bus = AsyncMock()
    
    agent = GenerationAgent(mock_llm, mock_template, mock_event_bus)
    
    latencies = []
    iterations = 20
    
    for _ in range(iterations):
        start_time = time.time()
        
        await agent.process({
            "nlp_description": "Create ERC20 token",
            "contract_type": "ERC20",
            "workflow_id": "test-123"
        })
        
        latency = time.time() - start_time
        latencies.append(latency)
    
    # Calculate p95
    latencies.sort()
    p95_index = int(0.95 * len(latencies))
    p95_latency = latencies[p95_index]
    
    # SLA: p95 < 60s
    assert p95_latency < 60, f"p95 latency {p95_latency}s exceeds SLA of 60s"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_generation_agent_sla_p99():
    """Test Generation Agent p99 latency < 90s"""
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "contract Test {}"
    
    mock_template = AsyncMock()
    mock_template.retrieve_and_generate.return_value = "contract Test {}"
    
    mock_event_bus = AsyncMock()
    
    agent = GenerationAgent(mock_llm, mock_template, mock_event_bus)
    
    latencies = []
    iterations = 50
    
    for _ in range(iterations):
        start_time = time.time()
        
        await agent.process({
            "nlp_description": "Create ERC20 token",
            "contract_type": "ERC20",
            "workflow_id": "test-123"
        })
        
        latency = time.time() - start_time
        latencies.append(latency)
    
    # Calculate p99
    latencies.sort()
    p99_index = int(0.99 * len(latencies))
    p99_latency = latencies[p99_index]
    
    # SLA: p99 < 90s
    assert p99_latency < 90, f"p99 latency {p99_latency}s exceeds SLA of 90s"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_audit_agent_sla_p95():
    """Test Audit Agent p95 latency < 100s"""
    mock_auditor = AsyncMock()
    mock_auditor.run_slither.return_value = {
        "status": "success",
        "vulnerabilities": [],
        "summary": {"total": 0}
    }
    
    mock_event_bus = AsyncMock()
    
    agent = AuditAgent(mock_auditor, mock_event_bus)
    
    latencies = []
    iterations = 20
    
    for _ in range(iterations):
        start_time = time.time()
        
        await agent.process({
            "contract_code": "contract Test {}",
            "workflow_id": "test-123"
        })
        
        latency = time.time() - start_time
        latencies.append(latency)
    
    # Calculate p95
    latencies.sort()
    p95_index = int(0.95 * len(latencies))
    p95_latency = latencies[p95_index]
    
    # SLA: p95 < 100s
    assert p95_latency < 100, f"p95 latency {p95_latency}s exceeds SLA of 100s"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_concurrent_workflow_execution():
    """Test concurrent workflow execution"""
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "contract Test {}"
    
    mock_template = AsyncMock()
    mock_template.retrieve_and_generate.return_value = "contract Test {}"
    
    mock_event_bus = AsyncMock()
    
    agent = GenerationAgent(mock_llm, mock_template, mock_event_bus)
    
    # Execute 10 workflows concurrently
    tasks = []
    for i in range(10):
        task = agent.process({
            "nlp_description": f"Create token {i}",
            "contract_type": "ERC20",
            "workflow_id": f"test-{i}"
        })
        tasks.append(task)
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    
    # All should succeed
    assert all(r["status"] == "success" for r in results)
    
    # Concurrent execution should be faster than sequential
    # (This is a basic check - actual performance depends on I/O)
    assert total_time < 10.0  # Should complete in reasonable time

