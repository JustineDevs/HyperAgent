"""Integration tests for MetisVM optimization"""
import pytest
from hyperagent.blockchain.metisvm_optimizer import MetisVMOptimizer
from hyperagent.core.services.generation_service import GenerationService
from hyperagent.llm.provider import LLMProviderFactory
from hyperagent.rag.template_retriever import TemplateRetriever
from unittest.mock import AsyncMock, MagicMock

pytestmark = [pytest.mark.integration]


@pytest.fixture
def optimizer():
    """MetisVMOptimizer fixture"""
    return MetisVMOptimizer()


@pytest.fixture
def mock_generation_service():
    """Mock GenerationService with MetisVM optimization"""
    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(return_value="pragma solidity ^0.8.27; contract Test {}")
    
    mock_retriever = AsyncMock()
    mock_retriever.retrieve_and_generate = AsyncMock(return_value="pragma solidity ^0.8.27; contract Test {}")
    
    service = GenerationService(mock_llm, mock_retriever)
    return service


@pytest.mark.asyncio
async def test_metisvm_optimized_generation(mock_generation_service):
    """Test contract generation with MetisVM optimization"""
    input_data = {
        "nlp_description": "Create a simple ERC20 token",
        "contract_type": "ERC20",
        "network": "hyperion_testnet",
        "optimize_for_metisvm": True,
        "enable_floating_point": False,
        "enable_ai_inference": False
    }
    
    result = await mock_generation_service.process(input_data)
    
    assert result["status"] == "success"
    assert result["metisvm_optimized"] is True
    assert "pragma metisvm" in result["contract_code"].lower()
    assert result["optimization_report"] is not None


@pytest.mark.asyncio
async def test_metisvm_with_floating_point(optimizer):
    """Test MetisVM optimization with floating-point enabled"""
    code = """
    pragma solidity ^0.8.27;
    contract FinancialContract {
        function calculatePrice(uint256 amount) public pure returns (uint256) {
            return amount * 1.5;  // Floating-point operation
        }
    }
    """
    
    optimized = optimizer.optimize_for_metisvm(code, enable_fp=True)
    
    assert "pragma metisvm" in optimized.lower()
    assert "pragma metisvm_floating_point" in optimized.lower()


@pytest.mark.asyncio
async def test_metisvm_with_ai_inference(optimizer):
    """Test MetisVM optimization with AI inference enabled"""
    code = """
    pragma solidity ^0.8.27;
    contract AIContract {
        function predict() public {
            model.inference();
        }
    }
    """
    
    optimized = optimizer.optimize_for_metisvm(code, enable_ai=True)
    
    assert "pragma metisvm" in optimized.lower()
    assert "pragma metisvm_ai_quantization" in optimized.lower()


@pytest.mark.asyncio
async def test_metisvm_optimization_report(optimizer):
    """Test optimization report generation"""
    code = "pragma solidity ^0.8.27; contract Test {}"
    
    report = optimizer.get_optimization_report(
        code,
        enable_fp=True,
        enable_ai=False
    )
    
    assert report["metisvm_optimized"] is True
    assert report["floating_point_enabled"] is True
    assert report["ai_quantization_enabled"] is False
    assert "MetisVM pragma directive" in report["optimizations_applied"]


def test_metisvm_detection_floating_point(optimizer):
    """Test floating-point detection in contract code"""
    code_with_fp = """
    pragma solidity ^0.8.27;
    import "./Decimal.sol";
    contract Test {
        Decimal.Decimal public price;
    }
    """
    
    assert optimizer.detect_floating_point(code_with_fp) is True


def test_metisvm_detection_ai_operations(optimizer):
    """Test AI operations detection in contract code"""
    code_with_ai = """
    pragma solidity ^0.8.27;
    contract Test {
        function predict() public {
            model.inference();
        }
    }
    """
    
    assert optimizer.detect_ai_operations(code_with_ai) is True

