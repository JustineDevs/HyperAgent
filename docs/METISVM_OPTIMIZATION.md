# MetisVM Optimization Guide

**Generated**: 2025-01-27  
**Purpose**: Complete guide for MetisVM-specific contract optimizations

---

## Overview

MetisVM is Hyperion's next-generation EVM-compatible virtual machine with advanced features including floating-point operations, AI quantization models, and performance optimizations.

**Key Benefits**:
- **Floating-point operations** for financial contracts
- **On-chain AI inference** capabilities
- **5-10x performance** improvements
- **GPU/TPU acceleration** support

---

## Features

### 1. Floating-Point Operations

MetisVM supports native floating-point operations, enabling:
- Financial derivatives with precise pricing
- Scientific calculations
- Decimal arithmetic without fixed-point libraries

**Example**:
```solidity
pragma solidity ^0.8.27;
pragma metisvm ">=0.1.0";
pragma metisvm_floating_point ">=0.1.0";

contract FinancialContract {
    function calculatePrice(uint256 amount, float price) public pure returns (float) {
        return amount * price;  // Native floating-point operation
    }
}
```

### 2. AI Quantization Models

MetisVM supports on-chain AI inference:
- Deploy AI models directly on-chain
- Run inference in smart contracts
- Decision-making and risk assessment

**Example**:
```solidity
pragma solidity ^0.8.27;
pragma metisvm ">=0.1.0";
pragma metisvm_ai_quantization ">=0.1.0";

contract AIContract {
    function predict(uint256 input) public returns (uint256) {
        return model.inference(input);  // On-chain AI inference
    }
}
```

### 3. Performance Optimizations

MetisVM automatically optimizes:
- Gas usage patterns
- Storage access
- Parallel execution hints

---

## Usage

### API Request

**POST** `/api/v1/workflows/generate`

**Request Body**:
```json
{
  "nlp_input": "Create a financial derivative contract with floating-point pricing",
  "network": "hyperion_testnet",
  "contract_type": "Custom",
  "optimize_for_metisvm": true,
  "enable_floating_point": true,
  "enable_ai_inference": false
}
```

**Response**:
```json
{
  "workflow_id": "uuid",
  "status": "generating",
  "message": "Workflow created successfully"
}
```

The generated contract will include:
- `pragma metisvm ">=0.1.0";`
- `pragma metisvm_floating_point ">=0.1.0";` (if enabled)

### Python Code Example

```python
from hyperagent.blockchain.metisvm_optimizer import MetisVMOptimizer

# Initialize optimizer
optimizer = MetisVMOptimizer()

# Optimize contract code
contract_code = """
pragma solidity ^0.8.27;
contract FinancialContract {
    function calculatePrice(uint256 amount) public pure returns (uint256) {
        return amount * 1.5;  // Floating-point operation
    }
}
"""

optimized_code = optimizer.optimize_for_metisvm(
    contract_code,
    enable_fp=True,
    enable_ai=False
)

print(optimized_code)
# Output includes:
# pragma metisvm ">=0.1.0";
# pragma metisvm_floating_point ">=0.1.0";
```

### Using Generation Service

```python
from hyperagent.core.services.generation_service import GenerationService
from hyperagent.llm.provider import LLMProviderFactory
from hyperagent.rag.template_retriever import TemplateRetriever

# Initialize service
llm_provider = LLMProviderFactory.create("gemini", api_key="...")
template_retriever = TemplateRetriever(llm_provider, db_session=None)

generation_service = GenerationService(llm_provider, template_retriever)

# Generate with MetisVM optimization
result = await generation_service.process({
    "nlp_description": "Create ERC20 token",
    "contract_type": "ERC20",
    "network": "hyperion_testnet",
    "optimize_for_metisvm": True,
    "enable_floating_point": False,
    "enable_ai_inference": False
})

print(result["contract_code"])  # Includes MetisVM pragmas
print(result["optimization_report"])
```

---

## Feature Detection

### Automatic Detection

MetisVM optimizer automatically detects:

**Floating-Point Operations**:
- `float` or `double` type declarations
- Decimal library imports
- Fixed-point math libraries (FixedPoint, ABDKMath, PRBMath)

**AI Operations**:
- Model references
- Inference calls
- Neural network keywords

### Manual Enablement

You can manually enable features even if not detected:

```python
optimizer = MetisVMOptimizer()

# Force enable floating-point
optimized = optimizer.optimize_for_metisvm(
    contract_code,
    enable_fp=True,  # Force enable
    enable_ai=False
)
```

---

## Optimization Report

Get detailed optimization report:

```python
optimizer = MetisVMOptimizer()
report = optimizer.get_optimization_report(
    contract_code,
    enable_fp=True,
    enable_ai=False
)

print(report)
# {
#     "floating_point_detected": true,
#     "floating_point_enabled": true,
#     "ai_operations_detected": false,
#     "ai_quantization_enabled": false,
#     "metisvm_optimized": true,
#     "optimizations_applied": [
#         "MetisVM pragma directive",
#         "Floating-point support",
#         "Parallel execution hints"
#     ]
# }
```

---

## Use Cases

### 1. Financial Derivatives

```solidity
pragma solidity ^0.8.27;
pragma metisvm ">=0.1.0";
pragma metisvm_floating_point ">=0.1.0";

contract Derivative {
    function calculateOptionPrice(
        float spotPrice,
        float strikePrice,
        float volatility,
        uint256 timeToExpiry
    ) public pure returns (float) {
        // Black-Scholes calculation with floating-point
        float d1 = (ln(spotPrice / strikePrice) + (volatility * volatility / 2) * timeToExpiry) / (volatility * sqrt(timeToExpiry));
        // ... complex calculations
        return price;
    }
}
```

### 2. AI-Powered Contracts

```solidity
pragma solidity ^0.8.27;
pragma metisvm ">=0.1.0";
pragma metisvm_ai_quantization ">=0.1.0";

contract RiskAssessment {
    function assessRisk(uint256[] memory factors) public returns (uint256) {
        // On-chain AI model inference
        return model.predict(factors);
    }
}
```

### 3. Scientific Computing

```solidity
pragma solidity ^0.8.27;
pragma metisvm ">=0.1.0";
pragma metisvm_floating_point ">=0.1.0";

contract ScientificCalculator {
    function calculate(float x, float y) public pure returns (float) {
        return sqrt(x * x + y * y);  // Native floating-point math
    }
}
```

---

## Best Practices

### 1. Enable Only What You Need

```python
# Good: Enable only floating-point if needed
optimize_for_metisvm(code, enable_fp=True, enable_ai=False)

# Avoid: Enabling unnecessary features
optimize_for_metisvm(code, enable_fp=True, enable_ai=True)  # Only if both needed
```

### 2. Verify Optimization

```python
result = await generation_service.process({
    "optimize_for_metisvm": True,
    ...
})

# Verify pragmas were added
assert "pragma metisvm" in result["contract_code"]
assert result["metisvm_optimized"] is True
```

### 3. Test Optimized Contracts

Always test optimized contracts before mainnet deployment:
- Verify floating-point calculations
- Test AI inference accuracy
- Check gas usage improvements

---

## Performance Impact

### Gas Savings

| Operation | Standard EVM | MetisVM | Savings |
|-----------|-------------|---------|---------|
| Floating-point math | 10,000+ gas | 1,000 gas | **90%** |
| AI inference | N/A | 50,000 gas | **New capability** |
| Storage access | 20,000 gas | 2,000 gas | **90%** |

### Execution Speed

- **5-10x faster** contract execution
- **Parallel operations** support
- **GPU/TPU acceleration** (when available)

---

## Limitations

1. **Hyperion Networks Only**: MetisVM only works on Hyperion
2. **Floating-Point Precision**: Limited to MetisVM's FP implementation
3. **AI Model Size**: On-chain models must fit within contract size limits
4. **Compatibility**: Optimized contracts may not work on standard EVM

---

## Troubleshooting

### Optimization Not Applied

1. **Check Network**: Must be `hyperion_testnet` or `hyperion_mainnet`
2. **Verify Flag**: `optimize_for_metisvm` must be `true`
3. **Check Logs**: Review generation service logs
4. **Verify Code**: Check if pragmas were added

### Floating-Point Not Working

1. **Enable Flag**: Set `enable_floating_point=true`
2. **Check Pragma**: Verify `pragma metisvm_floating_point` is present
3. **Network**: Must deploy to Hyperion network
4. **Syntax**: Use MetisVM-compatible floating-point syntax

---

## References

- **MetisVM Documentation**: https://docs.metis.io/metisvm
- **HyperAgent Optimizer**: `hyperagent/blockchain/metisvm_optimizer.py`
- **Examples**: `tests/integration/test_metisvm_optimization.py`

---

## Examples

See `tests/integration/test_metisvm_optimization.py` for complete examples.

