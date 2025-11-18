"""Unit tests for CompilationService"""
import pytest
import sys
from unittest.mock import patch, MagicMock
from hyperagent.core.services.compilation_service import CompilationService

pytestmark = [pytest.mark.unit]


@pytest.fixture
def compilation_service():
    """CompilationService fixture"""
    return CompilationService()


@pytest.fixture
def sample_solidity_code():
    """Sample Solidity contract code"""
    return """
pragma solidity ^0.8.27;

contract TestContract {
    uint256 public value;
    
    function setValue(uint256 _value) public {
        value = _value;
    }
    
    function getValue() public view returns (uint256) {
        return value;
    }
}
"""


def get_mock_compile_result():
    """Helper to get mock compilation result"""
    return {
        '<stdin>:TestContract': {
            'abi': [
                {
                    'type': 'function',
                    'name': 'setValue',
                    'inputs': [{'name': '_value', 'type': 'uint256'}],
                    'outputs': []
                },
                {
                    'type': 'function',
                    'name': 'getValue',
                    'inputs': [],
                    'outputs': [{'name': '', 'type': 'uint256'}]
                }
            ],
            'evm': {
                'bytecode': {
                    'object': '0x608060405234801561001057600080fd5b50610150806100206000396000f3fe6080604052348015600f57600080fd5b506004361060325760003560e01c80632e64cec11460375780636057361d146051575b600080fd5b603d6069565b6040516048919060c2565b60405180910390f35b6067600480360381019060639190608f565b6072565b005b60008054905090565b8060008190555050565b600080fd5b6000819050919050565b6089816078565b8114609357600080fd5b50565b60006020828403121560a057600080fd5b600060ac84828501608f565b91505092915050565b6000819050919050565b60c68160b5565b82525050565b600060208201905060df600083018460bf565b9291505056fea2646970667358221220d6c4e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e64736f6c63430008070033'
                },
                'deployedBytecode': {
                    'object': '0x6080604052348015600f57600080fd5b506004361060325760003560e01c80632e64cec11460375780636057361d146051575b600080fd5b603d6069565b6040516048919060c2565b60405180910390f35b6067600480360381019060639190608f565b6072565b005b60008054905090565b8060008190555050565b600080fd5b6000819050919050565b6089816078565b8114609357600080fd5b50565b60006020828403121560a057600080fd5b600060ac84828501608f565b91505092915050565b6000819050919050565b60c68160b5565b82525050565b600060208201905060df600083018460bf565b9291505056fea2646970667358221220d6c4e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e64736f6c63430008070033'
                }
            }
        }
    }


@pytest.mark.asyncio
async def test_compilation_success(compilation_service, sample_solidity_code):
    """Test successful compilation with valid Solidity code"""
    input_data = {"contract_code": sample_solidity_code}
    
    # Create mock module for py_solc_x
    mock_py_solc_x = MagicMock()
    mock_py_solc_x.compile_source = MagicMock(return_value=get_mock_compile_result())
    sys.modules['py_solc_x'] = mock_py_solc_x
    
    try:
        result = await compilation_service.process(input_data)
        
        assert result["status"] == "success"
        assert "compiled_contract" in result
        assert result["compiled_contract"]["bytecode"] is not None
        assert result["compiled_contract"]["abi"] is not None
        assert result["contract_name"] == "TestContract"
        assert result["contract_code"] == sample_solidity_code
        assert result["solidity_version"] == "0.8.27"
        assert result["source_code_hash"] is not None
        assert result["source_code_hash"].startswith("0x")
    finally:
        # Clean up
        if 'py_solc_x' in sys.modules:
            del sys.modules['py_solc_x']


@pytest.mark.asyncio
async def test_compilation_pragma_detection(compilation_service):
    """Test Solidity version detection from pragma"""
    code_with_pragma = "pragma solidity ^0.8.20; contract Test {}"
    
    mock_py_solc_x = MagicMock()
    mock_py_solc_x.compile_source = MagicMock(return_value=get_mock_compile_result())
    sys.modules['py_solc_x'] = mock_py_solc_x
    
    try:
        result = await compilation_service.process({"contract_code": code_with_pragma})
        assert result["solidity_version"] == "0.8.20"
    finally:
        if 'py_solc_x' in sys.modules:
            del sys.modules['py_solc_x']


@pytest.mark.asyncio
async def test_compilation_default_version(compilation_service):
    """Test default Solidity version when pragma not found"""
    code_no_pragma = "contract Test {}"
    
    mock_py_solc_x = MagicMock()
    mock_py_solc_x.compile_source = MagicMock(return_value=get_mock_compile_result())
    sys.modules['py_solc_x'] = mock_py_solc_x
    
    try:
        result = await compilation_service.process({"contract_code": code_no_pragma})
        assert result["solidity_version"] == "0.8.27"  # Default version
    finally:
        if 'py_solc_x' in sys.modules:
            del sys.modules['py_solc_x']


@pytest.mark.asyncio
async def test_compilation_missing_contract_code(compilation_service):
    """Test error handling for missing contract_code"""
    with pytest.raises(ValueError, match="contract_code is required"):
        await compilation_service.process({})


@pytest.mark.asyncio
async def test_compilation_invalid_solidity(compilation_service):
    """Test error handling for invalid Solidity syntax"""
    invalid_code = "contract Test { invalid syntax }"
    
    mock_py_solc_x = MagicMock()
    mock_py_solc_x.compile_source = MagicMock(side_effect=Exception("Compilation failed: syntax error"))
    sys.modules['py_solc_x'] = mock_py_solc_x
    
    try:
        with pytest.raises(ValueError, match="Compilation failed"):
            await compilation_service.process({"contract_code": invalid_code})
    finally:
        if 'py_solc_x' in sys.modules:
            del sys.modules['py_solc_x']


@pytest.mark.asyncio
async def test_compilation_empty_result(compilation_service):
    """Test error handling for empty compilation result"""
    mock_py_solc_x = MagicMock()
    mock_py_solc_x.compile_source = MagicMock(return_value={})
    sys.modules['py_solc_x'] = mock_py_solc_x
    
    try:
        with pytest.raises(ValueError, match="Compilation returned empty result"):
            await compilation_service.process({"contract_code": "contract Test {}"})
    finally:
        if 'py_solc_x' in sys.modules:
            del sys.modules['py_solc_x']


@pytest.mark.asyncio
async def test_compilation_missing_bytecode(compilation_service):
    """Test error handling when bytecode is missing"""
    mock_py_solc_x = MagicMock()
    mock_py_solc_x.compile_source = MagicMock(return_value={
        '<stdin>:TestContract': {
            'abi': [],
            'evm': {
                'bytecode': {
                    'object': ''  # Empty bytecode
                }
            }
        }
    })
    sys.modules['py_solc_x'] = mock_py_solc_x
    
    try:
        with pytest.raises(ValueError, match="no bytecode found"):
            await compilation_service.process({"contract_code": "contract Test {}"})
    finally:
        if 'py_solc_x' in sys.modules:
            del sys.modules['py_solc_x']


@pytest.mark.asyncio
async def test_compilation_py_solc_x_not_installed(compilation_service):
    """Test error handling when py-solc-x is not installed"""
    with patch('builtins.__import__', side_effect=ImportError("No module named 'py_solc_x'")):
        with pytest.raises(ValueError, match="py-solc-x not installed"):
            await compilation_service.process({"contract_code": "contract Test {}"})


@pytest.mark.asyncio
async def test_validate_contract_code_exists(compilation_service):
    """Test validate method with valid input"""
    assert await compilation_service.validate({"contract_code": "contract Test {}"}) is True


@pytest.mark.asyncio
async def test_validate_contract_code_missing(compilation_service):
    """Test validate method with missing contract_code"""
    assert await compilation_service.validate({}) is False


@pytest.mark.asyncio
async def test_validate_contract_code_empty(compilation_service):
    """Test validate method with empty contract_code"""
    assert await compilation_service.validate({"contract_code": ""}) is False
    assert await compilation_service.validate({"contract_code": "   "}) is False


@pytest.mark.asyncio
async def test_contract_name_extraction(compilation_service):
    """Test contract name extraction from compilation result key"""
    mock_py_solc_x = MagicMock()
    mock_py_solc_x.compile_source = MagicMock(return_value=get_mock_compile_result())
    sys.modules['py_solc_x'] = mock_py_solc_x
    
    try:
        result = await compilation_service.process({"contract_code": "contract MyContract {}"})
        assert result["contract_name"] == "TestContract"  # From mock
    finally:
        if 'py_solc_x' in sys.modules:
            del sys.modules['py_solc_x']


@pytest.mark.asyncio
async def test_source_code_hash_calculation(compilation_service, sample_solidity_code):
    """Test source code hash calculation"""
    mock_py_solc_x = MagicMock()
    mock_py_solc_x.compile_source = MagicMock(return_value=get_mock_compile_result())
    sys.modules['py_solc_x'] = mock_py_solc_x
    
    try:
        result = await compilation_service.process({"contract_code": sample_solidity_code})
        assert result["source_code_hash"] is not None
        assert result["source_code_hash"].startswith("0x")
        assert len(result["source_code_hash"]) == 66  # 0x + 64 hex chars
    finally:
        if 'py_solc_x' in sys.modules:
            del sys.modules['py_solc_x']


@pytest.mark.asyncio
async def test_deployed_bytecode_extraction(compilation_service, sample_solidity_code):
    """Test deployed bytecode extraction"""
    mock_py_solc_x = MagicMock()
    mock_py_solc_x.compile_source = MagicMock(return_value=get_mock_compile_result())
    sys.modules['py_solc_x'] = mock_py_solc_x
    
    try:
        result = await compilation_service.process({"contract_code": sample_solidity_code})
        assert "deployed_bytecode" in result["compiled_contract"]
        assert result["compiled_contract"]["deployed_bytecode"] is not None
    finally:
        if 'py_solc_x' in sys.modules:
            del sys.modules['py_solc_x']


@pytest.mark.asyncio
async def test_on_error_logging(compilation_service):
    """Test error logging in on_error method"""
    error = ValueError("Test error")
    
    with patch('hyperagent.core.services.compilation_service.logger') as mock_logger:
        await compilation_service.on_error(error)
        mock_logger.error.assert_called_once()

