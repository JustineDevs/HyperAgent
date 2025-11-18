"""Pydantic models for API requests/responses"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class WorkflowCreateRequest(BaseModel):
    """Request model for creating workflow"""
    nlp_input: str = Field(..., description="Natural language description of contract")
    network: str = Field(..., description="Target blockchain network")
    contract_type: Optional[str] = Field("Custom", description="Contract type")
    name: Optional[str] = Field(None, description="Workflow name")


class WorkflowResponse(BaseModel):
    """Workflow response model"""
    workflow_id: str
    status: str
    message: str
    created_at: Optional[datetime] = None


class WorkflowStatusResponse(BaseModel):
    """Workflow status response"""
    workflow_id: str
    status: str
    progress_percentage: int
    network: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class ContractGenerationRequest(BaseModel):
    """Contract generation request"""
    nlp_description: str
    contract_type: Optional[str] = "Custom"
    network: str


class ContractGenerationResponse(BaseModel):
    """Contract generation response"""
    contract_code: str
    contract_type: str
    abi: Dict[str, Any]
    constructor_args: List[Dict[str, Any]]


class AuditRequest(BaseModel):
    """Security audit request"""
    contract_code: str
    audit_level: Optional[str] = "standard"


class AuditResponse(BaseModel):
    """Security audit response"""
    vulnerabilities: List[Dict[str, Any]]
    overall_risk_score: float
    audit_status: str
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int


class DeploymentRequest(BaseModel):
    """Deployment request"""
    compiled_contract: Dict[str, Any]
    network: str
    private_key: str
    constructor_args: Optional[List[Any]] = []


class DeploymentResponse(BaseModel):
    """Deployment response"""
    contract_address: str
    transaction_hash: str
    block_number: int
    gas_used: int
    eigenda_commitment: Optional[str] = None


class BatchDeploymentContract(BaseModel):
    """Single contract in batch deployment"""
    compiled_contract: Dict[str, Any]
    network: str
    contract_name: Optional[str] = None
    source_code: Optional[str] = None


class BatchDeploymentRequest(BaseModel):
    """Batch deployment request"""
    contracts: List[BatchDeploymentContract]
    use_pef: Optional[bool] = True
    max_parallel: Optional[int] = 10
    private_key: Optional[str] = None


class BatchDeploymentResult(BaseModel):
    """Single contract deployment result in batch"""
    contract_name: str
    status: str
    contract_address: Optional[str] = None
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    gas_used: Optional[int] = None
    error: Optional[str] = None


class BatchDeploymentResponse(BaseModel):
    """Batch deployment response"""
    success: bool
    deployments: List[BatchDeploymentResult]
    total_time: float
    parallel_count: int
    success_count: int
    failed_count: int
    batches_deployed: int

