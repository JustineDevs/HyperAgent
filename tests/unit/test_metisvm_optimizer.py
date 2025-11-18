"""Unit tests for MetisVM Optimizer"""
import pytest
from hyperagent.blockchain.metisvm_optimizer import MetisVMOptimizer


@pytest.fixture
def optimizer():
    """Create MetisVMOptimizer instance"""
    return MetisVMOptimizer()


def test_detect_floating_point_negative(optimizer):
    """Test floating-point detection with no FP operations"""
    code = "contract Test { uint256 value; }"
    assert optimizer.detect_floating_point(code) == False


def test_detect_floating_point_positive(optimizer):
    """Test floating-point detection with FP operations"""
    code = "contract Test { float value; }"
    assert optimizer.detect_floating_point(code) == True


def test_detect_ai_operations_negative(optimizer):
    """Test AI operations detection with no AI code"""
    code = "contract Test { uint256 value; }"
    assert optimizer.detect_ai_operations(code) == False


def test_detect_ai_operations_positive(optimizer):
    """Test AI operations detection with AI code"""
    code = "contract Test { function inference() {} }"
    assert optimizer.detect_ai_operations(code) == True


def test_optimize_for_metisvm_basic(optimizer):
    """Test basic MetisVM optimization"""
    code = "pragma solidity ^0.8.27;\ncontract Test {}"
    
    optimized = optimizer.optimize_for_metisvm(code)
    
    assert "pragma metisvm" in optimized
    assert "contract Test" in optimized


def test_optimize_for_metisvm_with_fp(optimizer):
    """Test MetisVM optimization with floating-point enabled"""
    code = "pragma solidity ^0.8.27;\ncontract Test {}"
    
    optimized = optimizer.optimize_for_metisvm(code, enable_fp=True)
    
    assert "pragma metisvm_floating_point" in optimized


def test_optimize_for_metisvm_with_ai(optimizer):
    """Test MetisVM optimization with AI enabled"""
    code = "pragma solidity ^0.8.27;\ncontract Test {}"
    
    optimized = optimizer.optimize_for_metisvm(code, enable_ai=True)
    
    assert "pragma metisvm_ai_quantization" in optimized


def test_optimize_for_metisvm_no_pragma(optimizer):
    """Test MetisVM optimization when no pragma exists"""
    code = "contract Test {}"
    
    optimized = optimizer.optimize_for_metisvm(code)
    
    assert "pragma solidity" in optimized
    assert "pragma metisvm" in optimized


def test_get_optimization_report(optimizer):
    """Test optimization report generation"""
    code = "contract Test {}"
    
    report = optimizer.get_optimization_report(code)
    
    assert "floating_point_detected" in report
    assert "ai_operations_detected" in report
    assert "metisvm_optimized" in report
    assert report["metisvm_optimized"] == True
