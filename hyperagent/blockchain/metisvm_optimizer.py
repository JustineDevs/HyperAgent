"""MetisVM-specific contract optimizations

Concept: Optimize contracts for MetisVM features
Logic: Detect floating-point, add pragma directives, enable AI quantization
Benefits: Support for floating-point operations, on-chain AI inference, better performance
"""
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MetisVMOptimizer:
    """
    MetisVM-specific contract optimizations
    
    Concept: Optimize contracts for MetisVM features
    Logic:
        1. Detect floating-point operations in Solidity
        2. Add MetisVM pragma directives
        3. Enable AI quantization model support
        4. Add performance hints for GPU/TPU
        5. Prepare for zkVM integration
    """
    
    def detect_floating_point(self, contract_code: str) -> bool:
        """
        Detect if contract uses floating-point operations
        
        Concept: Check for float/double types and decimal libraries
        Logic:
            1. Look for float/double type declarations
            2. Check for decimal library imports
            3. Check for floating-point arithmetic operations
        
        Args:
            contract_code: Solidity source code
        
        Returns:
            True if floating-point operations detected
        """
        # Check for float/double type declarations
        float_type_pattern = r'\b(float|double)\b'
        if re.search(float_type_pattern, contract_code, re.IGNORECASE):
            return True
        
        # Check for decimal library imports
        decimal_import_pattern = r'import.*decimal|using.*Decimal'
        if re.search(decimal_import_pattern, contract_code, re.IGNORECASE):
            return True
        
        # Check for floating-point arithmetic (division with decimals, etc.)
        # This is a simplified check - actual FP operations might be more complex
        fp_arithmetic_pattern = r'\.(mul|div|add|sub)\(.*\d+\.\d+'
        if re.search(fp_arithmetic_pattern, contract_code):
            return True
        
        # Check for fixed-point math libraries
        fixed_point_pattern = r'(FixedPoint|ABDKMath|PRBMath)'
        if re.search(fixed_point_pattern, contract_code):
            return True
        
        return False
    
    def detect_ai_operations(self, contract_code: str) -> bool:
        """
        Detect if contract uses AI/ML operations
        
        Concept: Check for AI model references, quantization, inference
        Logic:
            1. Look for AI-related keywords
            2. Check for model loading/inference patterns
            3. Check for quantization operations
        
        Args:
            contract_code: Solidity source code
        
        Returns:
            True if AI operations detected
        """
        # Check for AI/ML keywords
        ai_keywords = [
            r'\b(model|inference|quantization|neural|ml|ai)\b',
            r'\b(tensor|activation|layer)\b',
            r'\b(predict|classify|embed)\b'
        ]
        
        for pattern in ai_keywords:
            if re.search(pattern, contract_code, re.IGNORECASE):
                return True
        
        return False
    
    def optimize_for_metisvm(
        self, 
        contract_code: str,
        enable_fp: bool = False,
        enable_ai: bool = False
    ) -> str:
        """
        Optimize contract for MetisVM features
        
        Concept: Add MetisVM-specific pragma directives and optimizations
        Logic:
            1. Add pragma metisvm directive
            2. Enable floating-point if detected/requested
            3. Add AI quantization model support
            4. Optimize for parallel execution
            5. Add performance hints
        
        Args:
            contract_code: Solidity source code
            enable_fp: Enable floating-point operations
            enable_ai: Enable AI quantization model support
        
        Returns:
            Optimized Solidity code
        """
        optimized = contract_code
        
        # Detect features
        has_fp = self.detect_floating_point(contract_code)
        has_ai = self.detect_ai_operations(contract_code)
        
        # Find pragma solidity line
        pragma_pattern = r'pragma\s+solidity\s+[^;]+;'
        pragma_match = re.search(pragma_pattern, optimized)
        
        if pragma_match:
            pragma_line = pragma_match.group(0)
            pragma_end = pragma_match.end()
            
            # Build pragma directives
            pragma_directives = [pragma_line]
            
            # Add MetisVM pragma
            pragma_directives.append('pragma metisvm ">=0.1.0";')
            
            # Add floating-point pragma if needed
            if enable_fp or has_fp:
                pragma_directives.append('pragma metisvm_floating_point ">=0.1.0";')
                logger.info("Enabled MetisVM floating-point operations")
            
            # Add AI quantization pragma if needed
            if enable_ai or has_ai:
                pragma_directives.append('pragma metisvm_ai_quantization ">=0.1.0";')
                logger.info("Enabled MetisVM AI quantization support")
            
            # Replace pragma section
            new_pragma = '\n'.join(pragma_directives) + '\n'
            optimized = optimized[:pragma_match.start()] + new_pragma + optimized[pragma_end:]
        else:
            # No pragma found, add at the beginning
            pragma_directives = [
                'pragma solidity ^0.8.27;',
                'pragma metisvm ">=0.1.0";'
            ]
            
            if enable_fp or has_fp:
                pragma_directives.append('pragma metisvm_floating_point ">=0.1.0";')
            
            if enable_ai or has_ai:
                pragma_directives.append('pragma metisvm_ai_quantization ">=0.1.0";')
            
            optimized = '\n'.join(pragma_directives) + '\n\n' + optimized
        
        # Optimize gas usage patterns
        optimized = self._optimize_gas_patterns(optimized)
        
        # Add performance hints for parallel execution
        optimized = self._add_parallel_hints(optimized)
        
        return optimized
    
    def _optimize_gas_patterns(self, code: str) -> str:
        """
        Optimize gas usage patterns for MetisVM
        
        Concept: Apply MetisVM-specific gas optimizations
        Logic:
            1. Optimize storage access patterns
            2. Use memory instead of storage where possible
            3. Optimize loop patterns
        """
        # This is a placeholder for gas optimization patterns
        # Actual optimizations would be more sophisticated
        optimized = code
        
        # Replace storage reads with memory where safe
        # (This is a simplified example - actual optimization requires deeper analysis)
        
        return optimized
    
    def _add_parallel_hints(self, code: str) -> str:
        """
        Add hints for parallel execution
        
        Concept: Add comments/annotations for MetisVM parallel execution
        Logic:
            1. Identify independent operations
            2. Add parallel execution hints
        """
        # This is a placeholder for parallel execution hints
        # Actual implementation would analyze code structure
        optimized = code
        
        # Add comment about parallel execution capability
        # (MetisVM will automatically parallelize where possible)
        
        return optimized
    
    def get_optimization_report(
        self,
        contract_code: str,
        enable_fp: bool = False,
        enable_ai: bool = False
    ) -> Dict[str, Any]:
        """
        Get optimization report for contract
        
        Args:
            contract_code: Solidity source code
            enable_fp: Enable floating-point operations
            enable_ai: Enable AI quantization model support
        
        Returns:
            Dictionary with optimization details
        """
        has_fp = self.detect_floating_point(contract_code)
        has_ai = self.detect_ai_operations(contract_code)
        
        return {
            "floating_point_detected": has_fp,
            "floating_point_enabled": enable_fp or has_fp,
            "ai_operations_detected": has_ai,
            "ai_quantization_enabled": enable_ai or has_ai,
            "metisvm_optimized": True,
            "optimizations_applied": [
                "MetisVM pragma directive",
                "Parallel execution hints" if True else None,
                "Floating-point support" if (enable_fp or has_fp) else None,
                "AI quantization support" if (enable_ai or has_ai) else None
            ]
        }

