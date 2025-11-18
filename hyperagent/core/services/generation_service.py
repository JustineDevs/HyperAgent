"""Generation service implementation"""
from typing import Dict, Any
from hyperagent.core.agent_system import ServiceInterface
from hyperagent.llm.provider import LLMProvider
from hyperagent.rag.template_retriever import TemplateRetriever


class GenerationService(ServiceInterface):
    """LLM-based contract generation service"""
    
    def __init__(self, llm_provider: LLMProvider, template_retriever: TemplateRetriever):
        self.llm_provider = llm_provider
        self.template_retriever = template_retriever
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate smart contract from NLP description"""
        nlp_desc = input_data.get("nlp_description")
        contract_type = input_data.get("contract_type", "Custom")
        network = input_data.get("network", "")
        
        # Generate contract using RAG
        contract_code = await self.template_retriever.retrieve_and_generate(
            nlp_desc,
            contract_type
        )
        
        # Optimize for MetisVM if requested (with feature check and fallback)
        metisvm_optimized = False
        optimization_report = None
        optimize_requested = input_data.get("optimize_for_metisvm")
        
        if optimize_requested:
            from hyperagent.blockchain.network_features import (
                NetworkFeatureManager,
                NetworkFeature
            )
            
            if NetworkFeatureManager.supports_feature(network, NetworkFeature.METISVM):
                # Apply optimization
                from hyperagent.blockchain.metisvm_optimizer import MetisVMOptimizer
                optimizer = MetisVMOptimizer()
                contract_code = optimizer.optimize_for_metisvm(
                    contract_code,
                    enable_fp=input_data.get("enable_floating_point", False),
                    enable_ai=input_data.get("enable_ai_inference", False)
                )
                metisvm_optimized = True
                optimization_report = optimizer.get_optimization_report(
                    contract_code,
                    enable_fp=input_data.get("enable_floating_point", False),
                    enable_ai=input_data.get("enable_ai_inference", False)
                )
            else:
                # Log warning but continue without optimization
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"MetisVM optimization requested but not available for {network}. "
                    f"Continuing without optimization."
                )
                # Continue with standard contract code
        
        return {
            "status": "success",
            "contract_code": contract_code,
            "contract_type": contract_type,
            "metisvm_optimized": metisvm_optimized,
            "optimization_report": optimization_report
        }
    
    async def validate(self, data: Dict[str, Any]) -> bool:
        """Validate NLP input"""
        if not data.get("nlp_description"):
            return False
        return len(data["nlp_description"]) > 10
    
    async def on_error(self, error: Exception) -> None:
        """Handle service-specific errors"""
        # Log error
        print(f"Generation service error: {error}")

