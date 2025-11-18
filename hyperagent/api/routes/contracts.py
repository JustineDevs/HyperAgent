"""Contract API routes"""
from fastapi import APIRouter, HTTPException
from hyperagent.api.models import AuditRequest, AuditResponse, ContractGenerationRequest, ContractGenerationResponse
from hyperagent.security.audit import SecurityAuditor
from hyperagent.llm.provider import LLMProviderFactory
from hyperagent.rag.template_retriever import TemplateRetriever
from hyperagent.core.config import settings

router = APIRouter(prefix="/api/v1/contracts", tags=["contracts"])


@router.post("/audit", response_model=AuditResponse)
async def audit_contract(request: AuditRequest):
    """
    Run security audit on contract
    
    Logic:
    1. Initialize security auditor
    2. Run Slither analysis
    3. Aggregate vulnerabilities
    4. Calculate risk score
    """
    auditor = SecurityAuditor()
    
    # Run Slither
    slither_result = await auditor.run_slither(request.contract_code)
    
    vulnerabilities = slither_result.get("vulnerabilities", [])
    
    # Calculate risk score
    weights = {"critical": 25, "high": 10, "medium": 5, "low": 1}
    risk_score = 0
    critical_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0
    
    for vuln in vulnerabilities:
        severity = vuln.get("severity", "low")
        risk_score += weights.get(severity, 1)
        if severity == "critical":
            critical_count += 1
        elif severity == "high":
            high_count += 1
        elif severity == "medium":
            medium_count += 1
        else:
            low_count += 1
    
    risk_score = min(100, risk_score)
    
    return AuditResponse(
        vulnerabilities=vulnerabilities,
        overall_risk_score=risk_score,
        audit_status="passed" if risk_score < 30 else "failed",
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count
    )


@router.post("/generate", response_model=ContractGenerationResponse)
async def generate_contract(request: ContractGenerationRequest):
    """
    Generate contract from NLP description
    
    Logic:
    1. Initialize LLM provider
    2. Initialize template retriever
    3. Generate contract using RAG
    4. Return contract code
    """
    # Initialize LLM provider
    llm_provider = LLMProviderFactory.create(
        "gemini",
        api_key=settings.gemini_api_key
    )
    
    # TODO: Initialize database session for template retriever
    # For now, use placeholder
    template_retriever = TemplateRetriever(llm_provider, db_session=None)
    
    # Generate contract
    contract_code = await template_retriever.retrieve_and_generate(
        request.nlp_description,
        request.contract_type
    )
    
    # Extract ABI (simplified)
    abi = {}  # TODO: Use actual compiler
    
    return ContractGenerationResponse(
        contract_code=contract_code,
        contract_type=request.contract_type,
        abi=abi,
        constructor_args=[]
    )

