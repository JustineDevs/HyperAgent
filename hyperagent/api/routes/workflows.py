"""Workflow API routes"""
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid

from hyperagent.db.session import get_db
from hyperagent.models.workflow import Workflow, WorkflowStatus
from hyperagent.models.user import User
from hyperagent.core.orchestrator import WorkflowCoordinator
from hyperagent.events.event_bus import EventBus
from hyperagent.core.config import settings
import redis.asyncio as redis
import asyncio
from hyperagent.architecture.soa import ServiceRegistry
from hyperagent.core.services.generation_service import GenerationService
from hyperagent.core.services.compilation_service import CompilationService
from hyperagent.core.services.audit_service import AuditService
from hyperagent.core.services.testing_service import TestingService
from hyperagent.core.services.deployment_service import DeploymentService
from hyperagent.llm.provider import LLMProviderFactory
from hyperagent.rag.template_retriever import TemplateRetriever
from hyperagent.blockchain.networks import NetworkManager
from hyperagent.blockchain.alith_client import AlithClient
from hyperagent.blockchain.eigenda_client import EigenDAClient
from hyperagent.security.audit import SecurityAuditor
from hyperagent.agents.testing import TestingAgent

logger = logging.getLogger(__name__)


async def get_or_create_default_user(db: AsyncSession) -> uuid.UUID:
    """
    Get or create default user for workflows
    
    Concept: Ensure a default user exists for workflows
    Logic: Check for default user, create if not exists
    Note: username=None to avoid unique constraint violations
    """
    # Try to find default user by email
    result = await db.execute(
        select(User).where(User.email == "default@hyperagent.local")
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Create default user (username=None to avoid unique constraint)
        user = User(
            email="default@hyperagent.local",
            username=None,  # Nullable field - avoids unique constraint conflict
            is_active=True
        )
        db.add(user)
        await db.commit()  # Commit user first
        await db.refresh(user)
        logger.info(f"Created default user: {user.id}")
    else:
        logger.debug(f"Using existing default user: {user.id}")
    
    return user.id


async def execute_workflow_background(
    workflow_id: str,
    nlp_input: str,
    network: str,
    optimize_for_metisvm: bool,
    enable_floating_point: bool,
    enable_ai_inference: bool,
    skip_audit: bool,
    skip_deployment: bool
):
    """
    Execute workflow in background task
    
    Concept: Initialize all services and execute workflow pipeline
    Logic:
        1. Create new database session for background task
        2. Initialize LLM provider and services
        3. Register services in ServiceRegistry
        4. Create WorkflowCoordinator
        5. Execute workflow
        6. Update workflow status in database
        7. Persist contracts to database
    """
    from hyperagent.db.session import AsyncSessionLocal
    
    # Create new database session for background task
    async with AsyncSessionLocal() as db:
        try:
            # Update workflow status to generating
            workflow_result = await db.execute(
                select(Workflow).where(Workflow.id == uuid.UUID(workflow_id))
            )
            workflow = workflow_result.scalar_one_or_none()
            if workflow:
                workflow.status = WorkflowStatus.GENERATING.value
                workflow.progress_percentage = 10
                await db.commit()
            
            # Initialize services
            # Create LLM provider (Gemini default, OpenAI fallback)
            if settings.gemini_api_key:
                llm_provider = LLMProviderFactory.create(
                    "gemini",
                    api_key=settings.gemini_api_key,
                    model_name=settings.gemini_model,
                    thinking_budget=settings.gemini_thinking_budget
                )
                logger.info(f"Using Gemini model: {settings.gemini_model}" + 
                            (f" with thinking_budget={settings.gemini_thinking_budget}" 
                             if settings.gemini_thinking_budget else ""))
            elif settings.openai_api_key:
                llm_provider = LLMProviderFactory.create(
                    "openai",
                    api_key=settings.openai_api_key
                )
                logger.info(f"Using OpenAI model: {settings.openai_model}")
            else:
                raise ValueError("No LLM API key configured (GEMINI_API_KEY or OPENAI_API_KEY required)")
            
            template_retriever = TemplateRetriever(llm_provider, db)
            
            network_manager = NetworkManager()
            alith_client = AlithClient()
            eigenda_client = EigenDAClient(
                disperser_url=settings.eigenda_disperser_url,
                private_key=settings.private_key,
                use_authenticated=settings.eigenda_use_authenticated
            )
            
            # Initialize Redis and EventBus
            redis_client = redis.from_url(settings.redis_url, decode_responses=False)
            event_bus = EventBus(redis_client)
            
            # Register services
            service_registry = ServiceRegistry()
            service_registry.register("generation", GenerationService(llm_provider, template_retriever))
            service_registry.register("compilation", CompilationService())
            service_registry.register("audit", AuditService(SecurityAuditor()))
            service_registry.register("testing", TestingService(TestingAgent(event_bus, llm_provider)))
            service_registry.register("deployment", DeploymentService(
                network_manager, alith_client, eigenda_client
            ))
            
            # Create progress callback
            async def progress_callback(status: str, progress: int):
                """Update workflow progress after each stage"""
                await update_workflow_progress(workflow_id, status, progress, db)
            
            # Create coordinator with progress callback
            coordinator = WorkflowCoordinator(service_registry, event_bus, progress_callback)
            
            # Execute workflow
            result = await coordinator.execute_workflow(
                workflow_id=workflow_id,
                nlp_input=nlp_input,
                network=network,
                optimize_for_metisvm=optimize_for_metisvm,
                enable_floating_point=enable_floating_point,
                enable_ai_inference=enable_ai_inference
            )
            
            # Update workflow status and persist contracts
            await update_workflow_and_persist_contracts(
                workflow_id=workflow_id,
                result=result,
                db=db
            )
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            # Update workflow with error
            try:
                workflow_result = await db.execute(
                    select(Workflow).where(Workflow.id == uuid.UUID(workflow_id))
                )
                workflow = workflow_result.scalar_one_or_none()
                if workflow:
                    workflow.status = WorkflowStatus.FAILED.value
                    workflow.error_message = str(e)
                    await db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update workflow error status: {db_error}")
                await db.rollback()
        except Exception as outer_error:
            logger.error(f"Critical error in workflow execution: {outer_error}", exc_info=True)
            await db.rollback()


async def update_workflow_progress(
    workflow_id: str,
    stage: str,
    progress: int,
    db: AsyncSession
):
    """Update workflow progress percentage based on stage"""
    try:
        result = await db.execute(
            select(Workflow).where(Workflow.id == uuid.UUID(workflow_id))
        )
        workflow = result.scalar_one_or_none()
        
        if workflow:
            workflow.status = stage
            workflow.progress_percentage = progress
            await db.commit()
            logger.info(f"Updated workflow {workflow_id} progress to {progress}% (stage: {stage})")
    except Exception as e:
        logger.error(f"Failed to update workflow progress: {e}")
        await db.rollback()


async def update_workflow_and_persist_contracts(
    workflow_id: str,
    result: Dict[str, Any],
    db: AsyncSession
):
    """
    Update workflow status and persist contracts to database
    
    Concept: Save generated contracts and update workflow status
    Logic:
        1. Extract contract data from workflow result
        2. Create GeneratedContract record
        3. Update workflow status to completed
        4. Calculate progress percentage
    """
    from hyperagent.models.contract import GeneratedContract
    import hashlib
    
    try:
        workflow_result = await db.execute(
            select(Workflow).where(Workflow.id == uuid.UUID(workflow_id))
        )
        workflow = workflow_result.scalar_one_or_none()
        
        if not workflow:
            logger.warning(f"Workflow {workflow_id} not found for persistence")
            return
        
        # Extract workflow result data (even if failed, we may have contracts)
        workflow_result_data = result.get("result", {})
        
        # Extract contract data (save even if workflow failed, as long as compilation succeeded)
        contract_code = workflow_result_data.get("contract_code")
        compiled_contract = workflow_result_data.get("compiled_contract", {})
        contract_name = workflow_result_data.get("contract_name", "GeneratedContract")
        
        # Save contracts if compilation succeeded (even if workflow failed later)
        if contract_code and compiled_contract:
            # Calculate source code hash
            source_code_hash = "0x" + hashlib.sha256(contract_code.encode('utf-8')).hexdigest()
            
            # Create GeneratedContract record
            generated_contract = GeneratedContract(
                workflow_id=uuid.UUID(workflow_id),
                contract_name=contract_name,
                contract_type=workflow_result_data.get("contract_type", "Custom"),
                solidity_version=workflow_result_data.get("solidity_version", "0.8.27"),
                source_code=contract_code,
                source_code_hash=source_code_hash,
                bytecode=compiled_contract.get("bytecode"),
                abi=compiled_contract.get("abi"),
                deployed_bytecode=compiled_contract.get("deployed_bytecode"),
                line_count=len(contract_code.splitlines()),
                function_count=len(compiled_contract.get("abi", [])) if isinstance(compiled_contract.get("abi"), list) else 0
            )
            
            db.add(generated_contract)
            logger.info(f"Persisted contract {contract_name} for workflow {workflow_id}")
        
        # Update workflow status
        # Check if deployment was successful (even if workflow result status is not explicitly "success")
        deployment_successful = (
            workflow_result_data.get("contract_address") is not None or
            workflow_result_data.get("transaction_hash") is not None or
            workflow_result_data.get("deployment_result", {}).get("status") == "success" or
            result.get("status") == "success"
        )
        
        if deployment_successful or result.get("status") == "success":
            workflow.status = WorkflowStatus.COMPLETED.value
            workflow.progress_percentage = 100
            logger.info(f"Workflow {workflow_id} marked as completed (deployment successful)")
        else:
            workflow.status = WorkflowStatus.FAILED.value
            workflow.error_message = result.get("error", "Unknown error")
            # Set progress based on which stage failed
            if compiled_contract:
                workflow.progress_percentage = 80  # Compilation succeeded
            else:
                workflow.progress_percentage = 20  # Failed early
        
        # Store test results in workflow metadata if available
        test_results = workflow_result_data.get("test_results")
        if test_results:
            if workflow.metadata is None:
                workflow.metadata = {}
            workflow.metadata["test_results"] = test_results
            logger.info(f"Stored test results for workflow {workflow_id}")
        
        # Persist deployment if available
        # Check multiple possible keys for deployment results
        deployment_result = (
            workflow_result_data.get("deployment") or
            workflow_result_data.get("deployment_result") or
            (workflow_result_data.get("deployment_result") if "deployment_result" in workflow_result_data else None)
        )
        
        # Also check if deployment keys are at top level
        if not deployment_result and workflow_result_data.get("contract_address"):
            deployment_result = {
                "status": "success",
                "contract_address": workflow_result_data.get("contract_address"),
                "deployer_address": workflow_result_data.get("deployer_address"),
                "transaction_hash": workflow_result_data.get("transaction_hash"),
                "block_number": workflow_result_data.get("block_number"),
                "gas_used": workflow_result_data.get("gas_used"),
                "gas_price": workflow_result_data.get("gas_price"),
                "total_cost_wei": workflow_result_data.get("total_cost_wei"),
                "eigenda_commitment": workflow_result_data.get("eigenda_commitment"),
                "deployment_method": workflow_result_data.get("deployment_method", "manual")
            }
        
        if deployment_result and deployment_result.get("status") == "success":
            from hyperagent.models.deployment import Deployment
            
            # Find the contract for this workflow
            contract_result = await db.execute(
                select(GeneratedContract).where(
                    GeneratedContract.workflow_id == uuid.UUID(workflow_id)
                ).order_by(GeneratedContract.created_at.desc())
            )
            contract = contract_result.scalar_one_or_none()
            
            if contract:
                # Determine if testnet
                is_testnet = workflow.network.endswith("_testnet")
                
                # Create deployment record
                deployment = Deployment(
                    contract_id=contract.id,
                    deployment_network=workflow.network,
                    is_testnet=is_testnet,
                    contract_address=deployment_result.get("contract_address"),
                    deployer_address=deployment_result.get("deployer_address", ""),
                    transaction_hash=deployment_result.get("transaction_hash"),
                    gas_used=deployment_result.get("gas_used"),
                    gas_price=deployment_result.get("gas_price"),
                    total_cost_wei=deployment_result.get("total_cost_wei"),
                    deployment_status="confirmed" if deployment_result.get("block_number") else "pending",
                    block_number=deployment_result.get("block_number"),
                    confirmation_blocks=1,  # Default to 1 confirmation
                    eigenda_commitment=deployment_result.get("eigenda_commitment"),
                    eigenda_batch_header=deployment_result.get("eigenda_batch_header"),
                    metadata={
                        "deployment_method": deployment_result.get("deployment_method", "manual"),
                        "eigenda_metadata_stored": deployment_result.get("eigenda_metadata_stored", False)
                    }
                )
                
                db.add(deployment)
                logger.info(f"Persisted deployment for contract {contract.contract_name} in workflow {workflow_id}")
        
        # Note: Workflow status is already updated above (lines 250-261)
        
        await db.commit()
        logger.info(f"Updated workflow {workflow_id} status to {workflow.status}")
        
    except Exception as e:
        logger.error(f"Failed to persist contracts: {e}", exc_info=True)
        await db.rollback()


router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])


class WorkflowCreateRequest(BaseModel):
    """Request model for creating workflow"""
    nlp_input: str
    network: str
    contract_type: Optional[str] = "Custom"
    name: Optional[str] = None
    skip_audit: bool = False
    skip_deployment: bool = False
    optimize_for_metisvm: bool = False
    enable_floating_point: bool = False
    enable_ai_inference: bool = False


class WorkflowResponse(BaseModel):
    """Workflow response model"""
    workflow_id: str
    status: str
    message: str
    warnings: Optional[List[str]] = None
    features_used: Optional[Dict[str, Any]] = None


@router.post("/generate", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new workflow for contract generation
    
    Concept: Create workflow record and trigger execution
    Logic:
        1. Validate input
        2. Create workflow record in database
        3. Initialize WorkflowCoordinator
        4. Queue workflow execution
        5. Return workflow ID
    
    Args:
        request: Workflow creation request
        db: Database session
    
    Returns:
        Workflow response with ID and status
    """
    try:
        # Get or create default user (in same transaction)
        result = await db.execute(
            select(User).where(User.email == "default@hyperagent.local")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Try to get any existing user first
            result2 = await db.execute(select(User).limit(1))
            existing_user = result2.scalar_one_or_none()
            
            if existing_user:
                user_id = existing_user.id
                logger.info(f"Using existing user: {user_id}")
            else:
                # Create new default user (username=None to avoid unique constraint)
                try:
                    user = User(
                        email="default@hyperagent.local",
                        username=None,  # Nullable field - avoids unique constraint conflict
                        is_active=True
                    )
                    db.add(user)
                    await db.flush()  # Flush to get ID in same transaction
                    user_id = user.id
                    logger.info(f"Creating default user: {user_id}")
                except IntegrityError as e:
                    # Handle any remaining constraint violations
                    await db.rollback()
                    logger.warning(f"User creation constraint error: {e}, retrying with existing user")
                    # Retry: get any existing user
                    result3 = await db.execute(select(User).limit(1))
                    fallback_user = result3.scalar_one_or_none()
                    if fallback_user:
                        user_id = fallback_user.id
                        logger.info(f"Using fallback user: {user_id}")
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to create or retrieve user"
                        )
        else:
            user_id = user.id
            logger.info(f"Using existing default user: {user_id}")
        
        # Validate requested features against network capabilities
        from hyperagent.blockchain.network_features import (
            NetworkFeatureManager,
            NetworkFeature
        )
        
        warnings = []
        features_used = {}
        
        # Check PEF availability (for batch deployments - not in this endpoint but for future)
        # Note: PEF is checked in deployment_service.deploy_batch()
        
        # Check MetisVM availability
        if request.optimize_for_metisvm:
            if NetworkFeatureManager.supports_feature(request.network, NetworkFeature.METISVM):
                features_used["metisvm"] = True
            else:
                warnings.append(
                    f"MetisVM optimization not available for {request.network}, "
                    f"continuing without optimization"
                )
                features_used["metisvm"] = False
                # Auto-disable incompatible feature
                request.optimize_for_metisvm = False
        else:
            features_used["metisvm"] = False
        
        # Check floating-point availability
        if request.enable_floating_point:
            if NetworkFeatureManager.supports_feature(request.network, NetworkFeature.FLOATING_POINT):
                features_used["floating_point"] = True
            else:
                warnings.append(
                    f"Floating-point operations not available for {request.network}, "
                    f"continuing without floating-point support"
                )
                features_used["floating_point"] = False
                request.enable_floating_point = False
        else:
            features_used["floating_point"] = False
        
        # Check AI inference availability
        if request.enable_ai_inference:
            if NetworkFeatureManager.supports_feature(request.network, NetworkFeature.AI_INFERENCE):
                features_used["ai_inference"] = True
            else:
                warnings.append(
                    f"AI inference not available for {request.network}, "
                    f"continuing without AI inference support"
                )
                features_used["ai_inference"] = False
                request.enable_ai_inference = False
        else:
            features_used["ai_inference"] = False
        
        # Check EigenDA availability (for deployment - informational)
        features_used["eigenda"] = NetworkFeatureManager.supports_feature(
            request.network, 
            NetworkFeature.EIGENDA
        )
        
        # Log warnings
        for warning in warnings:
            logger.warning(warning)
        
        # Generate workflow ID
        workflow_id = uuid.uuid4()
        
        # Create workflow record
        workflow = Workflow(
            id=workflow_id,
            user_id=user_id,
            name=request.name or f"Contract Generation - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description=request.nlp_input[:200],  # First 200 chars
            nlp_input=request.nlp_input,
            network=request.network,
            is_testnet=True,  # Default to testnet
            status=WorkflowStatus.CREATED.value,
            progress_percentage=0
        )
        
        db.add(workflow)
        await db.commit()  # Commit both user and workflow together
        await db.refresh(workflow)
        
        logger.info(f"Created workflow {workflow_id} for network {request.network}")
        
        # Initialize event bus and coordinator
        redis_client = redis.from_url(settings.redis_url, decode_responses=False)
        event_bus = EventBus(redis_client)
        
        # Initialize coordinator (would need proper service injection)
        # For now, just publish workflow created event
        from hyperagent.events.event_types import Event, EventType
        await event_bus.publish(Event(
            id=str(uuid.uuid4()),
            type=EventType.WORKFLOW_CREATED,
            workflow_id=str(workflow_id),
            timestamp=datetime.now(),
            data={
                "nlp_input": request.nlp_input,
                "network": request.network,
                "contract_type": request.contract_type,
                "skip_audit": request.skip_audit,
                "skip_deployment": request.skip_deployment,
                "optimize_for_metisvm": request.optimize_for_metisvm,
                "enable_floating_point": request.enable_floating_point,
                "enable_ai_inference": request.enable_ai_inference
            },
            source_agent="api"
        ))
        
        # Execute workflow in background task (create new DB session)
        asyncio.create_task(
            execute_workflow_background(
                workflow_id=str(workflow_id),
                nlp_input=request.nlp_input,
                network=request.network,
                optimize_for_metisvm=request.optimize_for_metisvm,
                enable_floating_point=request.enable_floating_point,
                enable_ai_inference=request.enable_ai_inference,
                skip_audit=request.skip_audit,
                skip_deployment=request.skip_deployment
            )
        )
        
        response_data = {
            "workflow_id": str(workflow_id),
            "status": WorkflowStatus.CREATED.value,
            "message": "Workflow created successfully"
        }
        
        # Include warnings and features_used in response if there are warnings
        if warnings:
            response_data["warnings"] = warnings
            response_data["features_used"] = features_used
        
        return WorkflowResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get("/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get workflow status
    
    Concept: Retrieve workflow status and progress from database
    Logic:
        1. Query database for workflow
        2. Return status, progress, and metadata
    
    Args:
        workflow_id: Workflow identifier
        db: Database session
    
    Returns:
        Workflow status and progress information
    """
    try:
        # Query workflow
        result = await db.execute(
            select(Workflow).where(Workflow.id == uuid.UUID(workflow_id))
        )
        workflow = result.scalar_one_or_none()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Query contracts and deployments
        from hyperagent.models.contract import GeneratedContract
        from hyperagent.models.deployment import Deployment
        
        contracts_result = await db.execute(
            select(GeneratedContract).where(GeneratedContract.workflow_id == uuid.UUID(workflow_id))
        )
        contracts = contracts_result.scalars().all()
        
        # Get deployments through contracts
        deployments = []
        for contract in contracts:
            deployments_result = await db.execute(
                select(Deployment).where(Deployment.contract_id == contract.id)
            )
            contract_deployments = deployments_result.scalars().all()
            deployments.extend(contract_deployments)
        
        return {
            "workflow_id": str(workflow.id),
            "status": workflow.status,
            "progress_percentage": workflow.progress_percentage,
            "network": workflow.network,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "error_message": workflow.error_message,
            "retry_count": workflow.retry_count,
            "contracts": [
                {
                    "id": str(c.id),
                    "contract_name": c.contract_name,
                    "contract_type": c.contract_type,
                    "solidity_version": c.solidity_version,
                    "created_at": c.created_at.isoformat() if c.created_at else None
                }
                for c in contracts
            ],
            "deployments": [
                {
                    "id": str(d.id),
                    "contract_address": d.contract_address,
                    "transaction_hash": d.transaction_hash,
                    "block_number": d.block_number,
                    "gas_used": d.gas_used,
                    "deployed_at": d.deployed_at.isoformat() if d.deployed_at else None
                }
                for d in deployments
            ]
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow ID format"
        )
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workflow: {str(e)}"
        )


@router.get("/{workflow_id}/contracts")
async def get_workflow_contracts(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all contracts generated for a workflow
    
    Concept: Retrieve contract source code, bytecode, and ABI
    Logic:
        1. Query GeneratedContract table filtered by workflow_id
        2. Return contract details including source_code, bytecode, abi
    
    Args:
        workflow_id: Workflow identifier
        db: Database session
    
    Returns:
        List of contracts with full details
    """
    try:
        from hyperagent.models.contract import GeneratedContract
        
        # Query contracts
        result = await db.execute(
            select(GeneratedContract).where(GeneratedContract.workflow_id == uuid.UUID(workflow_id))
        )
        contracts = result.scalars().all()
        
        if not contracts:
            return {
                "workflow_id": workflow_id,
                "contracts": []
            }
        
        return {
            "workflow_id": workflow_id,
            "contracts": [
                {
                    "id": str(c.id),
                    "contract_name": c.contract_name,
                    "contract_type": c.contract_type,
                    "solidity_version": c.solidity_version,
                    "source_code": c.source_code,
                    "bytecode": c.bytecode,
                    "abi": c.abi,
                    "deployed_bytecode": c.deployed_bytecode,
                    "source_code_hash": c.source_code_hash,
                    "line_count": c.line_count,
                    "function_count": c.function_count,
                    "created_at": c.created_at.isoformat() if c.created_at else None
                }
                for c in contracts
            ]
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow ID format"
        )
    except Exception as e:
        logger.error(f"Failed to get workflow contracts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve contracts: {str(e)}"
        )


@router.get("/{workflow_id}/deployments")
async def get_workflow_deployments(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get deployment information for a workflow
    
    Concept: Retrieve on-chain deployment details
    Logic:
        1. Query contracts for workflow
        2. Query deployments for each contract
        3. Return deployment addresses, transaction hashes, gas costs
    
    Args:
        workflow_id: Workflow identifier
        db: Database session
    
    Returns:
        List of deployments with on-chain information
    """
    try:
        from hyperagent.models.contract import GeneratedContract
        from hyperagent.models.deployment import Deployment
        
        # Query contracts for workflow
        contracts_result = await db.execute(
            select(GeneratedContract).where(GeneratedContract.workflow_id == uuid.UUID(workflow_id))
        )
        contracts = contracts_result.scalars().all()
        
        if not contracts:
            return {
                "workflow_id": workflow_id,
                "deployments": []
            }
        
        # Get deployments for all contracts
        deployments = []
        for contract in contracts:
            deployments_result = await db.execute(
                select(Deployment).where(Deployment.contract_id == contract.id)
            )
            contract_deployments = deployments_result.scalars().all()
            deployments.extend(contract_deployments)
        
        return {
            "workflow_id": workflow_id,
            "deployments": [
                {
                    "id": str(d.id),
                    "contract_address": d.contract_address,
                    "deployer_address": d.deployer_address,
                    "transaction_hash": d.transaction_hash,
                    "block_number": d.block_number,
                    "gas_used": d.gas_used,
                    "gas_price": d.gas_price,
                    "total_cost_wei": d.total_cost_wei,
                    "deployment_status": d.deployment_status,
                    "confirmation_blocks": d.confirmation_blocks,
                    "deployed_at": d.deployed_at.isoformat() if d.deployed_at else None,
                    "confirmed_at": d.confirmed_at.isoformat() if d.confirmed_at else None,
                    "eigenda_commitment": d.eigenda_commitment,
                    "deployment_network": d.deployment_network,
                    "is_testnet": d.is_testnet
                }
                for d in deployments
            ]
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow ID format"
        )
    except Exception as e:
        logger.error(f"Failed to get workflow deployments: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve deployments: {str(e)}"
        )


@router.get("/{workflow_id}/test-results")
async def get_workflow_test_results(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get test results for a workflow
    
    Concept: Retrieve test execution results and coverage
    Logic:
        1. Query contracts for workflow
        2. Extract test results from contract metadata or workflow metadata
        3. Return test results with coverage information
    
    Args:
        workflow_id: Workflow identifier
        db: Database session
    
    Returns:
        Test results including test cases, coverage, and execution details
    """
    try:
        from hyperagent.models.contract import GeneratedContract
        
        # Query contracts for workflow
        contracts_result = await db.execute(
            select(GeneratedContract).where(GeneratedContract.workflow_id == uuid.UUID(workflow_id))
        )
        contracts = contracts_result.scalars().all()
        
        if not contracts:
            return {
                "workflow_id": workflow_id,
                "test_results": None,
                "message": "No contracts found for this workflow"
            }
        
        # Get test results from workflow metadata or contract metadata
        workflow_result = await db.execute(
            select(Workflow).where(Workflow.id == uuid.UUID(workflow_id))
        )
        workflow = workflow_result.scalar_one_or_none()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        # Test results are stored in workflow metadata
        metadata = workflow.metadata or {}
        test_results = metadata.get("test_results")
        
        if not test_results:
            return {
                "workflow_id": workflow_id,
                "test_results": None,
                "message": "Test results not available. Tests may not have been executed yet."
            }
        
        return {
            "workflow_id": workflow_id,
            "test_results": test_results,
            "test_framework": test_results.get("test_framework", "unknown"),
            "total_tests": test_results.get("total_tests", 0),
            "passed": test_results.get("passed", 0),
            "failed": test_results.get("failed", 0),
            "skipped": test_results.get("skipped", 0),
            "coverage": test_results.get("coverage"),
            "test_cases": test_results.get("test_cases", [])
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow ID format"
        )
    except Exception as e:
        logger.error(f"Failed to get test results: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve test results: {str(e)}"
        )


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a running workflow
    
    Concept: Mark workflow as cancelled and stop execution
    Logic:
        1. Find workflow in database
        2. Update status to CANCELLED
        3. Publish cancellation event
    """
    try:
        result = await db.execute(
            select(Workflow).where(Workflow.id == uuid.UUID(workflow_id))
        )
        workflow = result.scalar_one_or_none()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Update status
        workflow.status = WorkflowStatus.CANCELLED.value
        workflow.updated_at = datetime.now()
        
        await db.commit()
        
        # Publish cancellation event
        redis_client = redis.from_url(settings.redis_url, decode_responses=False)
        event_bus = EventBus(redis_client)
        from hyperagent.events.event_types import Event, EventType
        await event_bus.publish(Event(
            id=str(uuid.uuid4()),
            type=EventType.WORKFLOW_CANCELLED,
            workflow_id=workflow_id,
            timestamp=datetime.now(),
            data={"message": "Workflow cancelled by user"},
            source_agent="api"
        ))
        
        return {
            "workflow_id": workflow_id,
            "status": "cancelled",
            "message": "Workflow cancelled successfully"
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow ID format"
        )
    except Exception as e:
        logger.error(f"Failed to cancel workflow: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel workflow: {str(e)}"
        )

