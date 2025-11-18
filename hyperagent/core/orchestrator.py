"""Workflow coordinator orchestrator"""
from typing import Dict, Any
from datetime import datetime
import uuid
from hyperagent.architecture.soa import ServiceRegistry, SequentialOrchestrator
from hyperagent.events.event_bus import EventBus
from hyperagent.events.event_types import Event, EventType
from hyperagent.core.agent_system import WorkflowStage


class WorkflowCoordinator:
    """
    Workflow Coordinator
    
    Concept: Orchestrates complete workflow pipeline
    Logic: Manages state transitions, coordinates agents, handles errors
    Pattern: Service Orchestration Pattern (SOP)
    """
    
    def __init__(self, service_registry: ServiceRegistry, event_bus: EventBus, progress_callback=None):
        self.registry = service_registry
        self.event_bus = event_bus
        self.orchestrator = SequentialOrchestrator(service_registry, event_bus, progress_callback)
        self.workflow_id = None
        self.state = {}
    
    async def execute_workflow(self, workflow_id: str, nlp_input: str, 
                              network: str, optimize_for_metisvm: bool = False,
                              enable_floating_point: bool = False,
                              enable_ai_inference: bool = False) -> Dict[str, Any]:
        """
        Execute complete workflow pipeline
        
        Pipeline Flow:
        1. Parse NLP input
        2. Generate contract (GenerationService)
        3. Compile contract (CompilationService)
        4. Audit contract (AuditService)
        5. Test contract (TestingService)
        6. Deploy contract (DeploymentService)
        """
        self.workflow_id = workflow_id
        self.state = {
            "workflow_id": workflow_id,
            "nlp_input": nlp_input,
            "network": network,
            "stages_completed": [],
            "optimize_for_metisvm": optimize_for_metisvm,
            "enable_floating_point": enable_floating_point,
            "enable_ai_inference": enable_ai_inference
        }
        
        # Publish workflow started
        await self.event_bus.publish(Event(
            id=str(uuid.uuid4()),
            type=EventType.WORKFLOW_STARTED,
            workflow_id=workflow_id,
            timestamp=datetime.now(),
            data=self.state,
            source_agent="coordinator"
        ))
        
        try:
            # Define pipeline stages
            pipeline = [
                {
                    "service": "generation",
                    "input_mapping": {
                        "nlp_description": "nlp_input",
                        "network": "network",
                        "optimize_for_metisvm": "optimize_for_metisvm",
                        "enable_floating_point": "enable_floating_point",
                        "enable_ai_inference": "enable_ai_inference"
                    }
                },
                {
                    "service": "compilation",
                    "input_mapping": {
                        "contract_code": "contract_code"
                    }
                },
                {
                    "service": "audit",
                    "input_mapping": {
                        "contract_code": "contract_code"
                    }
                },
                {
                    "service": "testing",
                    "input_mapping": {
                        "contract_code": "contract_code",
                        "contract_name": "contract_name",
                        "network": "network",
                        "compiled_contract": "compiled_contract",  # Pass compiled contract from CompilationService
                        "workflow_id": "workflow_id"
                    }
                },
                {
                    "service": "deployment",
                    "input_mapping": {
                        "compiled_contract": "compiled_contract",
                        "network": "network",
                        "source_code": "contract_code",
                        "constructor_args": "constructor_args"
                    }
                }
            ]
            
            workflow_context = {
                "pipeline": pipeline,
                "initial_data": {
                    "nlp_input": nlp_input,
                    "network": network,
                    "workflow_id": workflow_id,
                    "optimize_for_metisvm": optimize_for_metisvm,
                    "enable_floating_point": enable_floating_point,
                    "enable_ai_inference": enable_ai_inference
                }
            }
            
            # Execute pipeline
            result = await self.orchestrator.orchestrate(workflow_context)
            
            # Publish workflow completed
            await self.event_bus.publish(Event(
                id=str(uuid.uuid4()),
                type=EventType.WORKFLOW_COMPLETED,
                workflow_id=workflow_id,
                timestamp=datetime.now(),
                data=result,
                source_agent="coordinator"
            ))
            
            return {
                "status": "success",
                "workflow_id": self.workflow_id,
                "result": result
            }
        
        except Exception as e:
            await self.event_bus.publish(Event(
                id=str(uuid.uuid4()),
                type=EventType.WORKFLOW_FAILED,
                workflow_id=workflow_id,
                timestamp=datetime.now(),
                data={"error": str(e)},
                source_agent="coordinator"
            ))
            return {
                "status": "failed",
                "workflow_id": self.workflow_id,
                "error": str(e)
            }

