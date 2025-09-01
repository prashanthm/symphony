"""
SDLC Workflow Coordinator
Orchestrates role-based agents for SDLC workflows with strategic human decision gates
"""

from typing import Dict, List, Any, Optional, Tuple
import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum

from symphony_core.agents.base_agent import HandoffContext, HandoffStatus
from symphony_core.agents.agent_manager import AgentManager


class WorkflowType(Enum):
    IDEAS_INTAKE = "ideas_intake"
    PR_QUALITY_GATE = "pr_quality_gate" 
    REPO_SCAFFOLD = "repo_scaffold"
    CHANGE_REQUEST = "change_request"
    DISCOVERY_SPEC = "discovery_spec"
    DEFECT_HOTFIX = "defect_hotfix"
    DEPLOY_CANARY = "deploy_canary"
    POST_RELEASE_MONITOR = "post_release_monitor"
    RELEASE_AND_NOTES = "release_and_notes"


class HumanDecisionLevel(Enum):
    STRATEGIC = "strategic"  # Business impact, major changes
    TACTICAL = "tactical"    # Process changes, conflicts
    OPERATIONAL = "operational"  # Quality exceptions, urgent fixes


class SDLCWorkflowCoordinator:
    """
    Coordinates role-based agents for SDLC workflows
    
    Implements enterprise team simulation with:
    - Agent-to-agent collaboration and handoffs
    - Strategic human decision gates
    - Context preservation across workflow stages
    - Real-time coordination and monitoring
    """
    
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
        
        # Core agent team
        self.agent_team = {
            "business_coordinator": "business-coordinator-victoria",
            "engineering_lead": "engineering-lead-coordinator", 
            "product_manager": "product-manager-lead",
            "devops_engineer": "devops-engineer-infrastructure",
            "qa_engineer": "qa-engineer-quality"
        }
        
        # Workflow orchestration patterns
        self.workflow_patterns = {
            WorkflowType.IDEAS_INTAKE: self._define_ideas_intake_pattern(),
            WorkflowType.PR_QUALITY_GATE: self._define_pr_quality_gate_pattern(),
            WorkflowType.REPO_SCAFFOLD: self._define_repo_scaffold_pattern()
        }
        
        # Human decision gate configuration
        self.human_decision_gates = {
            HumanDecisionLevel.STRATEGIC: {
                "response_time": timedelta(hours=4),
                "escalation_path": ["CPO", "CTO", "CEO"],
                "approval_threshold": "executive_approval_required"
            },
            HumanDecisionLevel.TACTICAL: {
                "response_time": timedelta(hours=2),
                "escalation_path": ["Engineering Director", "VP Engineering"],
                "approval_threshold": "management_approval_required"
            },
            HumanDecisionLevel.OPERATIONAL: {
                "response_time": timedelta(minutes=30),
                "escalation_path": ["Lead Engineer", "Engineering Manager"],
                "approval_threshold": "lead_approval_required"
            }
        }
        
        # Active workflow tracking
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_metrics: Dict[str, Dict[str, float]] = {}
        
    async def execute_workflow(self, workflow_type: WorkflowType, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a complete SDLC workflow with agent coordination"""
        workflow_id = f"{workflow_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get workflow pattern
        pattern = self.workflow_patterns.get(workflow_type)
        if not pattern:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        # Initialize workflow tracking
        workflow_context = {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type.value,
            "start_time": datetime.now(),
            "status": "in_progress",
            "current_stage": 0,
            "total_stages": len(pattern["stages"]),
            "data": workflow_data,
            "agent_handoffs": [],
            "human_decisions": [],
            "context_preservation": {}
        }
        
        self.active_workflows[workflow_id] = workflow_context
        
        try:
            # Execute workflow stages with agent coordination
            result = await self._execute_workflow_stages(workflow_id, pattern, workflow_data)
            
            # Mark workflow complete
            workflow_context["status"] = "completed"
            workflow_context["end_time"] = datetime.now()
            workflow_context["duration"] = (workflow_context["end_time"] - workflow_context["start_time"]).total_seconds()
            
            # Update metrics
            await self._update_workflow_metrics(workflow_id, workflow_context)
            
            return {
                "workflow_completed": True,
                "workflow_id": workflow_id,
                "result": result,
                "metrics": self._calculate_workflow_metrics(workflow_context),
                "agent_coordination_summary": self._generate_coordination_summary(workflow_context)
            }
            
        except Exception as e:
            # Handle workflow failure
            workflow_context["status"] = "failed"
            workflow_context["error"] = str(e)
            workflow_context["end_time"] = datetime.now()
            
            return {
                "workflow_completed": False,
                "workflow_id": workflow_id,
                "error": str(e),
                "partial_results": workflow_context.get("partial_results", {}),
                "failure_analysis": await self._analyze_workflow_failure(workflow_context)
            }
            
    async def _execute_workflow_stages(self, workflow_id: str, pattern: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow stages with agent coordination"""
        workflow_context = self.active_workflows[workflow_id]
        stages = pattern["stages"]
        stage_results = {}
        current_context = data.copy()
        
        for stage_index, stage in enumerate(stages):
            workflow_context["current_stage"] = stage_index + 1
            
            # Execute stage with appropriate agent
            stage_result = await self._execute_workflow_stage(
                workflow_id, stage, current_context, stage_index
            )
            
            stage_results[stage["name"]] = stage_result
            
            # Check for human decision gates
            if stage.get("human_decision_gate"):
                human_decision = await self._handle_human_decision_gate(
                    workflow_id, stage, stage_result, current_context
                )
                
                if not human_decision["approved"]:
                    # Workflow paused or terminated by human decision
                    workflow_context["status"] = "paused_for_human_decision"
                    return {"paused": True, "human_decision_required": human_decision}
            
            # Update context for next stage
            current_context.update(stage_result.get("context_updates", {}))
            
            # Preserve context across stages
            workflow_context["context_preservation"][f"stage_{stage_index}"] = {
                "stage_name": stage["name"],
                "agent": stage["agent"],
                "input_context": current_context.copy(),
                "output_context": stage_result.get("context_updates", {}),
                "timestamp": datetime.now().isoformat()
            }
            
        return {
            "workflow_completed": True,
            "stage_results": stage_results,
            "final_context": current_context,
            "workflow_metrics": self._calculate_stage_metrics(stage_results)
        }
        
    async def _execute_workflow_stage(self, workflow_id: str, stage: Dict[str, Any], context: Dict[str, Any], stage_index: int) -> Dict[str, Any]:
        """Execute a single workflow stage with appropriate agent"""
        stage_name = stage["name"]
        agent_role = stage["agent"]
        task_type = stage["task_type"]
        
        # Get agent for this stage
        agent_id = self.agent_team.get(agent_role)
        if not agent_id:
            raise ValueError(f"No agent configured for role: {agent_role}")
        
        agent = await self.agent_manager.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        # Prepare task data for agent
        task_data = {
            "type": task_type,
            "workflow_id": workflow_id,
            "stage_name": stage_name,
            "stage_index": stage_index,
            **context,
            **stage.get("parameters", {})
        }
        
        # Execute agent task
        start_time = datetime.now()
        
        try:
            stage_result = await agent.execute_task(task_data)
            
            # Record successful agent handoff
            handoff_record = {
                "stage": stage_name,
                "agent": agent_role,
                "agent_id": agent_id,
                "start_time": start_time,
                "end_time": datetime.now(),
                "duration": (datetime.now() - start_time).total_seconds(),
                "success": True,
                "result_summary": stage_result.get("summary", "Stage completed successfully")
            }
            
            self.active_workflows[workflow_id]["agent_handoffs"].append(handoff_record)
            
            return {
                "success": True,
                "agent": agent_role,
                "stage_result": stage_result,
                "context_updates": stage_result.get("context", {}),
                "next_actions": stage_result.get("next_actions", []),
                "handoff_record": handoff_record
            }
            
        except Exception as e:
            # Record failed agent handoff
            handoff_record = {
                "stage": stage_name,
                "agent": agent_role,
                "agent_id": agent_id,
                "start_time": start_time,
                "end_time": datetime.now(),
                "duration": (datetime.now() - start_time).total_seconds(),
                "success": False,
                "error": str(e),
                "requires_intervention": True
            }
            
            self.active_workflows[workflow_id]["agent_handoffs"].append(handoff_record)
            raise e
            
    async def _handle_human_decision_gate(self, workflow_id: str, stage: Dict[str, Any], stage_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle human decision gate"""
        decision_gate = stage["human_decision_gate"]
        decision_level = HumanDecisionLevel(decision_gate["level"])
        gate_config = self.human_decision_gates[decision_level]
        
        # Prepare decision context for human
        decision_context = {
            "workflow_id": workflow_id,
            "stage_name": stage["name"],
            "decision_level": decision_level.value,
            "stage_result": stage_result,
            "business_context": context.get("business_context", {}),
            "technical_context": context.get("technical_context", {}),
            "decision_criteria": decision_gate["criteria"],
            "response_required_by": (datetime.now() + gate_config["response_time"]).isoformat(),
            "escalation_path": gate_config["escalation_path"]
        }
        
        # Create human decision request
        human_decision = {
            "decision_id": f"decision_{workflow_id}_{stage['name']}_{datetime.now().strftime('%H%M%S')}",
            "timestamp": datetime.now(),
            "decision_level": decision_level.value,
            "context": decision_context,
            "status": "pending_human_response",
            "approved": None,  # To be filled by human
            "notes": "",
            "response_deadline": datetime.now() + gate_config["response_time"]
        }
        
        # Record human decision requirement
        self.active_workflows[workflow_id]["human_decisions"].append(human_decision)
        
        # For demo purposes, simulate strategic business decisions
        # In real implementation, this would integrate with human approval systems
        if decision_level == HumanDecisionLevel.STRATEGIC:
            # Simulate strategic approval based on business impact
            business_impact = context.get("business_impact", "medium")
            if business_impact == "high" or stage_result.get("requires_executive_approval", False):
                # Require actual human approval
                return {
                    "requires_human_approval": True,
                    "decision_context": decision_context,
                    "approved": False,  # Pending human response
                    "simulation": False
                }
            else:
                # Auto-approve low impact decisions
                human_decision["approved"] = True
                human_decision["notes"] = "Auto-approved: Low business impact"
                human_decision["status"] = "approved"
                return {"approved": True, "decision": human_decision, "simulation": True}
        else:
            # Simulate tactical/operational approvals
            human_decision["approved"] = True
            human_decision["notes"] = f"Auto-approved: {decision_level.value} level decision"
            human_decision["status"] = "approved"
            return {"approved": True, "decision": human_decision, "simulation": True}
            
    def _define_ideas_intake_pattern(self) -> Dict[str, Any]:
        """Define ideas intake workflow pattern"""
        return {
            "name": "Ideas Intake Workflow",
            "description": "Process idea submissions through evaluation, scoring, and epic creation",
            "stages": [
                {
                    "name": "idea_analysis",
                    "agent": "product_manager",
                    "task_type": "analyze_idea",
                    "description": "Analyze and score the submitted idea",
                    "parameters": {"scoring_framework": "strategic_value"}
                },
                {
                    "name": "business_validation", 
                    "agent": "business_coordinator",
                    "task_type": "business_impact_assessment",
                    "description": "Validate business alignment and strategic value",
                    "human_decision_gate": {
                        "level": "strategic",
                        "criteria": ["strategic_alignment", "business_value", "resource_investment"],
                        "trigger": "business_impact_high"
                    }
                },
                {
                    "name": "technical_feasibility",
                    "agent": "engineering_lead",
                    "task_type": "technical_review",
                    "description": "Assess technical feasibility and complexity"
                },
                {
                    "name": "epic_creation",
                    "agent": "product_manager", 
                    "task_type": "create_specification",
                    "description": "Create epic and initial specification"
                }
            ]
        }
        
    def _define_pr_quality_gate_pattern(self) -> Dict[str, Any]:
        """Define PR quality gate workflow pattern"""
        return {
            "name": "PR Quality Gate Workflow",
            "description": "Validate PR through comprehensive quality checks and approvals",
            "stages": [
                {
                    "name": "automated_testing",
                    "agent": "qa_engineer",
                    "task_type": "run_test_suite",
                    "description": "Execute comprehensive test suite",
                    "parameters": {"test_types": ["unit", "integration", "security"]}
                },
                {
                    "name": "quality_gate_validation",
                    "agent": "qa_engineer",
                    "task_type": "validate_quality_gates",
                    "description": "Validate all quality gates and standards"
                },
                {
                    "name": "security_scanning",
                    "agent": "qa_engineer", 
                    "task_type": "security_scan",
                    "description": "Perform security scans and vulnerability assessment"
                },
                {
                    "name": "engineering_review",
                    "agent": "engineering_lead",
                    "task_type": "technical_review",
                    "description": "Technical review and approval",
                    "human_decision_gate": {
                        "level": "tactical",
                        "criteria": ["code_quality", "architecture_compliance", "security_clearance"],
                        "trigger": "quality_gate_failure"
                    }
                },
                {
                    "name": "deployment_preparation",
                    "agent": "devops_engineer",
                    "task_type": "deployment_preparation", 
                    "description": "Prepare for deployment pipeline"
                }
            ]
        }
        
    def _define_repo_scaffold_pattern(self) -> Dict[str, Any]:
        """Define repository scaffolding workflow pattern"""
        return {
            "name": "Repository Scaffold Workflow", 
            "description": "Set up complete repository infrastructure for new projects",
            "stages": [
                {
                    "name": "project_planning",
                    "agent": "product_manager",
                    "task_type": "validate_requirements",
                    "description": "Validate project requirements and scope"
                },
                {
                    "name": "architecture_design",
                    "agent": "engineering_lead", 
                    "task_type": "validate_architecture",
                    "description": "Design technical architecture and standards"
                },
                {
                    "name": "infrastructure_setup",
                    "agent": "devops_engineer",
                    "task_type": "setup_repository",
                    "description": "Set up repository with complete DevOps infrastructure"
                },
                {
                    "name": "quality_framework",
                    "agent": "qa_engineer",
                    "task_type": "create_test_plan",
                    "description": "Set up testing framework and quality gates"
                },
                {
                    "name": "business_alignment",
                    "agent": "business_coordinator",
                    "task_type": "strategic_validation",
                    "description": "Validate business alignment and readiness",
                    "human_decision_gate": {
                        "level": "strategic",
                        "criteria": ["business_readiness", "resource_allocation", "timeline_approval"],
                        "trigger": "project_authorization"
                    }
                }
            ]
        }
        
    def _calculate_workflow_metrics(self, workflow_context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate workflow performance metrics"""
        handoffs = workflow_context.get("agent_handoffs", [])
        human_decisions = workflow_context.get("human_decisions", [])
        
        metrics = {
            "total_duration": workflow_context.get("duration", 0),
            "agent_handoffs": len(handoffs),
            "successful_handoffs": len([h for h in handoffs if h["success"]]),
            "failed_handoffs": len([h for h in handoffs if not h["success"]]),
            "handoff_success_rate": len([h for h in handoffs if h["success"]]) / len(handoffs) if handoffs else 0,
            "human_decisions": len(human_decisions),
            "human_approvals": len([d for d in human_decisions if d.get("approved", False)]),
            "average_stage_duration": sum(h["duration"] for h in handoffs) / len(handoffs) if handoffs else 0,
            "context_preservation_stages": len(workflow_context.get("context_preservation", {}))
        }
        
        return metrics
        
    def _generate_coordination_summary(self, workflow_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate agent coordination summary"""
        handoffs = workflow_context.get("agent_handoffs", [])
        
        agent_participation = {}
        for handoff in handoffs:
            agent = handoff["agent"]
            if agent not in agent_participation:
                agent_participation[agent] = {
                    "stages": 0,
                    "total_time": 0,
                    "success_rate": 0,
                    "avg_duration": 0
                }
            
            agent_participation[agent]["stages"] += 1
            agent_participation[agent]["total_time"] += handoff["duration"]
            
        # Calculate agent performance metrics
        for agent, stats in agent_participation.items():
            agent_handoffs = [h for h in handoffs if h["agent"] == agent]
            stats["success_rate"] = len([h for h in agent_handoffs if h["success"]]) / len(agent_handoffs)
            stats["avg_duration"] = stats["total_time"] / stats["stages"]
        
        return {
            "total_agents_involved": len(agent_participation),
            "agent_participation": agent_participation,
            "coordination_pattern": workflow_context["workflow_type"],
            "context_handoffs": len(workflow_context.get("context_preservation", {})),
            "human_integration_points": len(workflow_context.get("human_decisions", []))
        }