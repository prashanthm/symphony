#!/usr/bin/env python3
"""
Onboarding Workflow Manager

Manages the complete customer onboarding workflow with state persistence,
progress tracking, and resumability.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import uuid
from dataclasses import dataclass, asdict
import yaml

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Individual step status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Individual step in the onboarding workflow"""
    step_id: str
    name: str
    description: str
    required: bool = True
    estimated_duration: int = 60  # seconds
    dependencies: List[str] = None
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    result_data: Dict[str, Any] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.result_data is None:
            self.result_data = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WorkflowState:
    """Complete workflow state for persistence"""
    workflow_id: str
    customer_name: str
    package_type: str
    industry: str
    status: WorkflowStatus
    current_step: Optional[str] = None
    created_at: str = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    steps: List[WorkflowStep] = None
    configuration: Dict[str, Any] = None
    integrations: Dict[str, Any] = None
    error_history: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.steps is None:
            self.steps = []
        if self.configuration is None:
            self.configuration = {}
        if self.integrations is None:
            self.integrations = {}
        if self.error_history is None:
            self.error_history = []
        if self.metadata is None:
            self.metadata = {}


class WorkflowManager:
    """Manages onboarding workflow execution and state"""
    
    def __init__(self, symphony_root: Optional[str] = None):
        self.symphony_root = Path(symphony_root or Path.cwd())
        self.workflows_dir = self.symphony_root / "workspace" / "onboarding"
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        
        # Step registry for different workflow types
        self.step_registry: Dict[str, List[WorkflowStep]] = {}
        self.step_handlers: Dict[str, Callable] = {}
        
        # Initialize default workflow templates
        self._initialize_workflow_templates()
        
        logger.info("Workflow Manager initialized")
    
    def create_workflow(
        self, 
        customer_name: str, 
        package_type: str = "startup", 
        industry: str = "general",
        template_file: Optional[str] = None
    ) -> str:
        """Create a new onboarding workflow"""
        
        workflow_id = f"onboard-{customer_name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
        
        # Get workflow template for package type
        steps = self._get_workflow_template(package_type, industry, template_file)
        
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            customer_name=customer_name,
            package_type=package_type,
            industry=industry,
            status=WorkflowStatus.NOT_STARTED,
            steps=steps,
            metadata={
                'package_type': package_type,
                'industry': industry,
                'estimated_duration': sum(step.estimated_duration for step in steps),
                'total_steps': len(steps),
                'required_steps': len([s for s in steps if s.required])
            }
        )
        
        self._save_workflow_state(workflow_state)
        
        logger.info(f"Created workflow {workflow_id} for customer {customer_name}")
        return workflow_id
    
    async def start_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Start or resume a workflow"""
        
        workflow_state = self._load_workflow_state(workflow_id)
        if not workflow_state:
            raise Exception(f"Workflow {workflow_id} not found")
        
        # Update status and start time
        workflow_state.status = WorkflowStatus.IN_PROGRESS
        if not workflow_state.started_at:
            workflow_state.started_at = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Starting workflow {workflow_id}")
        
        try:
            # Execute workflow steps
            result = await self._execute_workflow(workflow_state)
            
            if result['success']:
                workflow_state.status = WorkflowStatus.COMPLETED
                workflow_state.completed_at = datetime.now(timezone.utc).isoformat()
                logger.info(f"Workflow {workflow_id} completed successfully")
            else:
                workflow_state.status = WorkflowStatus.FAILED
                self._add_error_to_history(workflow_state, result.get('error', 'Unknown error'))
                logger.error(f"Workflow {workflow_id} failed: {result.get('error')}")
            
            self._save_workflow_state(workflow_state)
            return result
            
        except Exception as e:
            workflow_state.status = WorkflowStatus.FAILED
            self._add_error_to_history(workflow_state, str(e))
            self._save_workflow_state(workflow_state)
            logger.error(f"Workflow {workflow_id} execution failed: {e}")
            raise
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a running workflow"""
        
        workflow_state = self._load_workflow_state(workflow_id)
        if not workflow_state:
            return False
        
        if workflow_state.status == WorkflowStatus.IN_PROGRESS:
            workflow_state.status = WorkflowStatus.PAUSED
            self._save_workflow_state(workflow_state)
            logger.info(f"Workflow {workflow_id} paused")
            return True
        
        return False
    
    async def resume_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Resume a paused workflow"""
        
        workflow_state = self._load_workflow_state(workflow_id)
        if not workflow_state:
            raise Exception(f"Workflow {workflow_id} not found")
        
        if workflow_state.status != WorkflowStatus.PAUSED:
            raise Exception(f"Workflow {workflow_id} is not paused (status: {workflow_state.status})")
        
        workflow_state.status = WorkflowStatus.IN_PROGRESS
        return await self.start_workflow(workflow_id)
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current workflow status and progress"""
        
        workflow_state = self._load_workflow_state(workflow_id)
        if not workflow_state:
            return {'error': f'Workflow {workflow_id} not found'}
        
        completed_steps = len([s for s in workflow_state.steps if s.status == StepStatus.COMPLETED])
        total_steps = len(workflow_state.steps)
        progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        current_step = None
        if workflow_state.current_step:
            current_step = next((s for s in workflow_state.steps if s.step_id == workflow_state.current_step), None)
        
        return {
            'workflow_id': workflow_state.workflow_id,
            'customer_name': workflow_state.customer_name,
            'package_type': workflow_state.package_type,
            'status': workflow_state.status.value,
            'progress': {
                'completed_steps': completed_steps,
                'total_steps': total_steps,
                'percentage': round(progress_percentage, 1),
                'current_step': self._step_to_dict(current_step) if current_step else None
            },
            'timing': {
                'created_at': workflow_state.created_at,
                'started_at': workflow_state.started_at,
                'completed_at': workflow_state.completed_at
            },
            'configuration': workflow_state.configuration,
            'integrations': workflow_state.integrations,
            'metadata': workflow_state.metadata
        }
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows"""
        
        workflows = []
        
        for workflow_file in self.workflows_dir.glob("*.json"):
            try:
                workflow_state = self._load_workflow_state(workflow_file.stem)
                if workflow_state:
                    status = self.get_workflow_status(workflow_state.workflow_id)
                    workflows.append({
                        'workflow_id': status['workflow_id'],
                        'customer_name': status['customer_name'],
                        'package_type': status['package_type'],
                        'status': status['status'],
                        'progress_percentage': status['progress']['percentage'],
                        'created_at': status['timing']['created_at']
                    })
            except Exception as e:
                logger.warning(f"Could not load workflow {workflow_file.stem}: {e}")
        
        return sorted(workflows, key=lambda x: x['created_at'], reverse=True)
    
    def register_step_handler(self, step_id: str, handler: Callable):
        """Register a handler function for a specific step"""
        self.step_handlers[step_id] = handler
        logger.debug(f"Registered handler for step {step_id}")
    
    # Internal methods
    
    async def _execute_workflow(self, workflow_state: WorkflowState) -> Dict[str, Any]:
        """Execute the workflow steps"""
        
        try:
            for step in workflow_state.steps:
                # Skip completed steps
                if step.status == StepStatus.COMPLETED:
                    continue
                
                # Check dependencies
                if not self._check_dependencies(step, workflow_state.steps):
                    if step.required:
                        return {
                            'success': False,
                            'error': f'Step {step.name} has unmet dependencies: {step.dependencies}'
                        }
                    else:
                        step.status = StepStatus.SKIPPED
                        continue
                
                # Execute step
                workflow_state.current_step = step.step_id
                step.status = StepStatus.RUNNING
                step.started_at = datetime.now(timezone.utc).isoformat()
                
                self._save_workflow_state(workflow_state)
                
                logger.info(f"Executing step {step.name} in workflow {workflow_state.workflow_id}")
                
                try:
                    # Execute step handler
                    if step.step_id in self.step_handlers:
                        result = await self.step_handlers[step.step_id](workflow_state, step)
                        step.result_data = result
                    else:
                        # Default step execution
                        result = await self._execute_default_step(workflow_state, step)
                        step.result_data = result
                    
                    step.status = StepStatus.COMPLETED
                    step.completed_at = datetime.now(timezone.utc).isoformat()
                    
                except Exception as step_error:
                    step.status = StepStatus.FAILED
                    step.error_message = str(step_error)
                    step.retry_count += 1
                    
                    logger.error(f"Step {step.name} failed: {step_error}")
                    
                    # Retry if allowed
                    if step.retry_count <= step.max_retries:
                        logger.info(f"Retrying step {step.name} (attempt {step.retry_count}/{step.max_retries})")
                        step.status = StepStatus.PENDING
                        continue
                    
                    # If required step fails and can't retry, fail workflow
                    if step.required:
                        return {
                            'success': False,
                            'error': f'Required step {step.name} failed: {step_error}'
                        }
            
            workflow_state.current_step = None
            self._save_workflow_state(workflow_state)
            
            return {
                'success': True,
                'workflow_id': workflow_state.workflow_id,
                'completed_steps': len([s for s in workflow_state.steps if s.status == StepStatus.COMPLETED]),
                'total_steps': len(workflow_state.steps)
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _execute_default_step(self, workflow_state: WorkflowState, step: WorkflowStep) -> Dict[str, Any]:
        """Default step execution - can be overridden by step handlers"""
        
        # Simulate step execution
        await asyncio.sleep(1)
        
        return {
            'message': f'Step {step.name} executed with default handler',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _check_dependencies(self, step: WorkflowStep, all_steps: List[WorkflowStep]) -> bool:
        """Check if step dependencies are satisfied"""
        
        if not step.dependencies:
            return True
        
        step_status_map = {s.step_id: s.status for s in all_steps}
        
        for dependency in step.dependencies:
            if dependency not in step_status_map:
                logger.warning(f"Dependency {dependency} not found in workflow")
                return False
            
            if step_status_map[dependency] != StepStatus.COMPLETED:
                return False
        
        return True
    
    def _save_workflow_state(self, workflow_state: WorkflowState):
        """Save workflow state to disk"""
        
        workflow_file = self.workflows_dir / f"{workflow_state.workflow_id}.json"
        
        # Convert to dict and handle dataclass serialization
        state_dict = asdict(workflow_state)
        
        # Convert enums to their values for JSON serialization
        if hasattr(state_dict['status'], 'value'):
            state_dict['status'] = state_dict['status'].value
        elif isinstance(state_dict['status'], Enum):
            state_dict['status'] = state_dict['status'].value
        
        for step_dict in state_dict['steps']:
            if hasattr(step_dict['status'], 'value'):
                step_dict['status'] = step_dict['status'].value
            elif isinstance(step_dict['status'], Enum):
                step_dict['status'] = step_dict['status'].value
        
        with open(workflow_file, 'w') as f:
            json.dump(state_dict, f, indent=2)
        
        logger.debug(f"Saved workflow state for {workflow_state.workflow_id}")
    
    def _step_to_dict(self, step: WorkflowStep) -> Dict[str, Any]:
        """Convert workflow step to JSON-serializable dict"""
        step_dict = asdict(step)
        
        # Convert enum to value
        if hasattr(step_dict['status'], 'value'):
            step_dict['status'] = step_dict['status'].value
        elif isinstance(step_dict['status'], Enum):
            step_dict['status'] = step_dict['status'].value
        
        return step_dict
    
    def _load_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """Load workflow state from disk"""
        
        workflow_file = self.workflows_dir / f"{workflow_id}.json"
        
        if not workflow_file.exists():
            return None
        
        try:
            with open(workflow_file, 'r') as f:
                state_dict = json.load(f)
            
            # Reconstruct dataclasses
            steps = []
            for step_data in state_dict['steps']:
                step_data['status'] = StepStatus(step_data['status'])
                steps.append(WorkflowStep(**step_data))
            
            state_dict['steps'] = steps
            state_dict['status'] = WorkflowStatus(state_dict['status'])
            
            return WorkflowState(**state_dict)
            
        except Exception as e:
            logger.error(f"Failed to load workflow state {workflow_id}: {e}")
            return None
    
    def _add_error_to_history(self, workflow_state: WorkflowState, error_message: str):
        """Add error to workflow error history"""
        
        workflow_state.error_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': error_message,
            'current_step': workflow_state.current_step
        })
    
    def _initialize_workflow_templates(self):
        """Initialize default workflow templates for different package types"""
        
        # Common steps for all packages
        base_steps = [
            WorkflowStep(
                step_id="validate_environment",
                name="Environment Validation",
                description="Validate Symphony environment and dependencies",
                estimated_duration=30
            ),
            WorkflowStep(
                step_id="create_customer",
                name="Customer Creation",
                description="Create customer configuration and directory structure",
                estimated_duration=60,
                dependencies=["validate_environment"]
            ),
            WorkflowStep(
                step_id="setup_integrations",
                name="Integration Setup",
                description="Configure and validate integrations (Linear, GitHub, etc.)",
                estimated_duration=300,
                dependencies=["create_customer"]
            ),
            WorkflowStep(
                step_id="deploy_agents",
                name="Agent Deployment",
                description="Deploy and configure Symphony agents",
                estimated_duration=180,
                dependencies=["create_customer", "setup_integrations"]
            ),
            WorkflowStep(
                step_id="validate_deployment",
                name="Deployment Validation",
                description="Validate complete deployment and integration health",
                estimated_duration=120,
                dependencies=["deploy_agents"]
            ),
            WorkflowStep(
                step_id="go_live",
                name="Go Live",
                description="Finalize setup and activate customer environment",
                estimated_duration=60,
                dependencies=["validate_deployment"]
            )
        ]
        
        # Package-specific templates
        self.step_registry = {
            'startup': base_steps.copy(),
            'smb': base_steps.copy(),
            'enterprise': base_steps.copy(),
            'global': base_steps.copy()
        }
        
        # Add enterprise-specific steps
        self.step_registry['enterprise'].insert(3, WorkflowStep(
            step_id="setup_compliance",
            name="Compliance Setup",
            description="Configure enterprise compliance and security requirements",
            estimated_duration=240,
            dependencies=["setup_integrations"]
        ))
        
        # Add global-specific steps
        self.step_registry['global'].extend([
            WorkflowStep(
                step_id="setup_multi_region",
                name="Multi-Region Setup",
                description="Configure multi-region deployment and coordination",
                estimated_duration=360,
                dependencies=["setup_compliance"]
            ),
            WorkflowStep(
                step_id="setup_cultural_adaptation",
                name="Cultural Adaptation",
                description="Configure cultural and regional customizations",
                estimated_duration=180,
                dependencies=["setup_multi_region"]
            )
        ])
    
    def _get_workflow_template(self, package_type: str, industry: str, template_file: Optional[str] = None) -> List[WorkflowStep]:
        """Get workflow template for specific package and industry"""
        
        # If external template file is provided, load it
        if template_file:
            try:
                return self._load_external_template(template_file, package_type, industry)
            except Exception as e:
                logger.error(f"Failed to load external template {template_file}: {e}")
                logger.info("Falling back to built-in templates")
        
        if package_type not in self.step_registry:
            package_type = 'startup'  # Default fallback
        
        # Deep copy template steps
        template_steps = []
        for step in self.step_registry[package_type]:
            new_step = WorkflowStep(
                step_id=step.step_id,
                name=step.name,
                description=step.description,
                required=step.required,
                estimated_duration=step.estimated_duration,
                dependencies=step.dependencies.copy(),
                max_retries=step.max_retries
            )
            template_steps.append(new_step)
        
        # Industry-specific customizations can be added here
        if industry == 'healthcare':
            # Add HIPAA compliance step for healthcare
            template_steps.insert(-2, WorkflowStep(
                step_id="setup_hipaa_compliance",
                name="HIPAA Compliance Setup",
                description="Configure HIPAA compliance requirements",
                estimated_duration=180,
                dependencies=["setup_integrations"]
            ))
        
        return template_steps
    
    def _load_external_template(self, template_file: str, package_type: str, industry: str) -> List[WorkflowStep]:
        """Load workflow template from external file"""
        
        template_path = Path(template_file)
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_file}")
        
        logger.info(f"Loading external template: {template_file}")
        
        # Load template file
        try:
            with open(template_path, 'r') as f:
                template_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in template file: {e}")
        
        # Extract workflow template or use linear template for workspace creation
        if 'workflow_template' in template_data:
            return self._parse_workflow_template(template_data['workflow_template'], package_type, industry)
        elif 'workspace' in template_data:
            # This is a Linear workspace template - create a workflow step for workspace creation
            return self._create_linear_workspace_workflow(template_data, package_type, industry)
        else:
            # Generic template - try to parse as workflow
            return self._parse_generic_template(template_data, package_type, industry)
    
    def _parse_workflow_template(self, template_data: Dict[str, Any], package_type: str, industry: str) -> List[WorkflowStep]:
        """Parse explicit workflow template format"""
        
        steps = []
        step_configs = template_data.get('steps', [])
        
        for step_config in step_configs:
            step = WorkflowStep(
                step_id=step_config['id'],
                name=step_config['name'],
                description=step_config.get('description', ''),
                required=step_config.get('required', True),
                estimated_duration=step_config.get('estimated_duration', 300),
                dependencies=step_config.get('dependencies', []),
                status=StepStatus.PENDING,
                metadata=step_config.get('metadata', {})
            )
            steps.append(step)
        
        return steps
    
    def _create_linear_workspace_workflow(self, template_data: Dict[str, Any], package_type: str, industry: str) -> List[WorkflowStep]:
        """Create workflow steps for Linear workspace template"""
        
        # Start with standard workflow steps but enhance Linear integration step
        base_steps = self._get_base_workflow_steps(package_type, industry)
        
        # Find the setup_integrations step and enhance it with Linear template data
        enhanced_steps = []
        for step in base_steps:
            if step.step_id == "setup_integrations":
                # Enhance integration step with Linear template metadata
                enhanced_step = WorkflowStep(
                    step_id=step.step_id,
                    name=step.name,
                    description=f"{step.description} (Using Linear enterprise template)",
                    required=step.required,
                    estimated_duration=step.estimated_duration + 300,  # Additional time for template processing
                    dependencies=step.dependencies,
                    status=StepStatus.PENDING,
                    metadata={
                        **step.metadata,
                        'linear_template': template_data,
                        'template_type': 'linear_workspace',
                        'workspace_config': template_data.get('workspace', {}),
                        'team_structure': template_data.get('teams', []),
                        'project_templates': template_data.get('projects', {}),
                        'symphony_integration': template_data.get('symphony_integration', {})
                    }
                )
                enhanced_steps.append(enhanced_step)
            else:
                enhanced_steps.append(step)
        
        return enhanced_steps
    
    def _get_base_workflow_steps(self, package_type: str, industry: str) -> List[WorkflowStep]:
        """Get base workflow steps without external template processing"""
        
        if package_type not in self.step_registry:
            package_type = 'startup'  # Default fallback
        
        # Deep copy template steps
        template_steps = []
        for step in self.step_registry[package_type]:
            new_step = WorkflowStep(
                step_id=step.step_id,
                name=step.name,
                description=step.description,
                required=step.required,
                estimated_duration=step.estimated_duration,
                dependencies=step.dependencies[:] if step.dependencies else [],
                status=StepStatus.PENDING,
                metadata=step.metadata.copy() if step.metadata else {}
            )
            template_steps.append(new_step)
        
        # Apply industry-specific customizations
        if industry == "healthcare":
            template_steps.append(WorkflowStep(
                step_id="hipaa_compliance",
                name="HIPAA Compliance Setup",
                description="Configure HIPAA compliance requirements",
                required=True,
                estimated_duration=600,
                dependencies=["setup_integrations"]
            ))
        elif industry == "financial":
            template_steps.append(WorkflowStep(
                step_id="finra_compliance",
                name="FINRA Compliance Setup", 
                description="Configure financial services compliance",
                required=True,
                estimated_duration=900,
                dependencies=["setup_integrations"]
            ))
        
        return template_steps
    
    def _parse_generic_template(self, template_data: Dict[str, Any], package_type: str, industry: str) -> List[WorkflowStep]:
        """Parse generic template format"""
        
        # If no specific workflow is defined, create enhanced standard workflow
        base_steps = self._get_base_workflow_steps(package_type, industry)
        
        # Add template metadata to all steps
        enhanced_steps = []
        for step in base_steps:
            enhanced_step = WorkflowStep(
                step_id=step.step_id,
                name=step.name,
                description=step.description,
                required=step.required,
                estimated_duration=step.estimated_duration,
                dependencies=step.dependencies,
                status=StepStatus.PENDING,
                metadata={
                    **step.metadata,
                    'external_template': template_data,
                    'template_type': 'generic'
                }
            )
            enhanced_steps.append(enhanced_step)
        
        return enhanced_steps


# Factory function
def create_workflow_manager(symphony_root: Optional[str] = None) -> WorkflowManager:
    """Create and return a workflow manager instance"""
    return WorkflowManager(symphony_root)