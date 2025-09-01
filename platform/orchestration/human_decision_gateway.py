"""
Human Decision Gateway
Manages strategic human decision points in Symphony's autonomous workflows
"""

from typing import Dict, List, Any, Optional, Callable
import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from symphony_core.agents.base_agent import HandoffContext


class DecisionPriority(Enum):
    CRITICAL = "critical"  # Immediate response required
    HIGH = "high"         # Response within 1 hour
    MEDIUM = "medium"     # Response within 4 hours  
    LOW = "low"           # Response within 24 hours


class DecisionCategory(Enum):
    STRATEGIC = "strategic"           # Business strategy and direction
    FINANCIAL = "financial"          # Budget and investment decisions
    ARCHITECTURAL = "architectural"   # Major technical architecture changes
    OPERATIONAL = "operational"      # Process and operational changes
    SECURITY = "security"            # Security and compliance decisions
    CUSTOMER = "customer"            # Customer impact decisions


@dataclass
class HumanDecisionRequest:
    """Represents a decision requiring human approval"""
    decision_id: str
    category: DecisionCategory
    priority: DecisionPriority
    title: str
    description: str
    context: Dict[str, Any]
    options: List[Dict[str, Any]]
    recommendation: Optional[str]
    impact_assessment: Dict[str, Any]
    stakeholders: List[str]
    created_at: datetime
    deadline: datetime
    workflow_id: str
    stage_name: str
    agent_requester: str


@dataclass
class HumanDecisionResponse:
    """Human decision response"""
    decision_id: str
    approved: bool
    selected_option: Optional[str]
    notes: str
    conditions: List[str]
    approver: str
    approved_at: datetime
    escalated: bool = False


class HumanDecisionGateway:
    """
    Manages human decision points in autonomous workflows
    
    Provides:
    - Strategic decision routing to appropriate humans
    - Context-rich decision presentation
    - Deadline tracking and escalation
    - Decision audit trail and compliance
    """
    
    def __init__(self):
        # Decision routing configuration
        self.decision_routing = {
            DecisionCategory.STRATEGIC: {
                "primary_approvers": ["Business-Coordinator", "CPO", "CEO"],
                "escalation_path": ["CPO", "CEO", "Board"],
                "auto_approve_threshold": None,  # Always requires human approval
                "delegation_rules": self._strategic_delegation_rules()
            },
            DecisionCategory.FINANCIAL: {
                "primary_approvers": ["CFO", "Business-Coordinator", "CEO"],
                "escalation_path": ["CFO", "CEO", "Board"],
                "auto_approve_threshold": {"amount": 10000, "risk": "low"},
                "delegation_rules": self._financial_delegation_rules()
            },
            DecisionCategory.ARCHITECTURAL: {
                "primary_approvers": ["Engineering-Lead", "CTO", "Solution-Architect"],
                "escalation_path": ["CTO", "CEO"],
                "auto_approve_threshold": {"complexity": "low", "impact": "minimal"},
                "delegation_rules": self._technical_delegation_rules()
            },
            DecisionCategory.OPERATIONAL: {
                "primary_approvers": ["Engineering-Lead", "VP-Engineering", "CTO"],
                "escalation_path": ["VP-Engineering", "CTO"],
                "auto_approve_threshold": {"impact": "team_only", "risk": "low"},
                "delegation_rules": self._operational_delegation_rules()
            },
            DecisionCategory.SECURITY: {
                "primary_approvers": ["Security-Lead", "CISO", "CTO"],
                "escalation_path": ["CISO", "CTO", "CEO"],
                "auto_approve_threshold": None,  # Security always requires human review
                "delegation_rules": self._security_delegation_rules()
            },
            DecisionCategory.CUSTOMER: {
                "primary_approvers": ["Product-Manager", "CPO", "CEO"],
                "escalation_path": ["CPO", "CEO"],
                "auto_approve_threshold": {"customer_impact": "minimal", "revenue_impact": "none"},
                "delegation_rules": self._customer_delegation_rules()
            }
        }
        
        # Active decision tracking
        self.pending_decisions: Dict[str, HumanDecisionRequest] = {}
        self.decision_history: List[HumanDecisionResponse] = []
        self.escalation_queue: List[str] = []
        
        # Decision templates for common scenarios
        self.decision_templates = self._initialize_decision_templates()
        
    async def request_human_decision(self, 
                                   decision_request: HumanDecisionRequest) -> Dict[str, Any]:
        """Request human decision with appropriate routing"""
        
        # Validate decision request
        validation_result = await self._validate_decision_request(decision_request)
        if not validation_result["valid"]:
            return {"success": False, "error": validation_result["error"]}
        
        # Check for auto-approval eligibility
        auto_approval = await self._check_auto_approval_eligibility(decision_request)
        if auto_approval["eligible"]:
            return await self._process_auto_approval(decision_request, auto_approval)
        
        # Route decision to appropriate approvers
        routing_result = await self._route_decision_request(decision_request)
        
        # Store pending decision
        self.pending_decisions[decision_request.decision_id] = decision_request
        
        # Set up monitoring and escalation
        await self._setup_decision_monitoring(decision_request)
        
        return {
            "success": True,
            "decision_id": decision_request.decision_id,
            "routing": routing_result,
            "estimated_response_time": self._estimate_response_time(decision_request),
            "escalation_schedule": self._create_escalation_schedule(decision_request),
            "decision_context_url": self._generate_decision_context_url(decision_request)
        }
        
    async def process_human_response(self, 
                                   decision_response: HumanDecisionResponse) -> Dict[str, Any]:
        """Process human decision response"""
        
        decision_request = self.pending_decisions.get(decision_response.decision_id)
        if not decision_request:
            return {"success": False, "error": "Decision not found or already processed"}
        
        # Validate response against request context
        validation_result = await self._validate_decision_response(decision_request, decision_response)
        if not validation_result["valid"]:
            return {"success": False, "error": validation_result["error"]}
        
        # Process approval/rejection
        if decision_response.approved:
            result = await self._process_approval(decision_request, decision_response)
        else:
            result = await self._process_rejection(decision_request, decision_response)
        
        # Record decision in history
        self.decision_history.append(decision_response)
        
        # Remove from pending decisions
        del self.pending_decisions[decision_response.decision_id]
        
        # Update workflow with decision result
        await self._update_workflow_with_decision(decision_request, decision_response)
        
        return {
            "success": True,
            "decision_processed": True,
            "decision_result": result,
            "workflow_continuation": self._determine_workflow_continuation(decision_request, decision_response)
        }
        
    async def create_strategic_decision_request(self,
                                              workflow_context: Dict[str, Any],
                                              decision_context: Dict[str, Any]) -> HumanDecisionRequest:
        """Create strategic decision request with rich context"""
        
        # Generate decision ID
        decision_id = f"strategic_{workflow_context['workflow_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Assess business impact
        impact_assessment = await self._assess_strategic_impact(decision_context)
        
        # Generate decision options
        options = await self._generate_decision_options(decision_context, DecisionCategory.STRATEGIC)
        
        # Determine priority based on impact and urgency
        priority = self._determine_decision_priority(impact_assessment, decision_context.get("urgency", "medium"))
        
        # Calculate deadline
        deadline = self._calculate_decision_deadline(priority, decision_context.get("timeline_pressure", "normal"))
        
        return HumanDecisionRequest(
            decision_id=decision_id,
            category=DecisionCategory.STRATEGIC,
            priority=priority,
            title=decision_context.get("title", "Strategic Decision Required"),
            description=decision_context.get("description", ""),
            context=self._enrich_decision_context(workflow_context, decision_context),
            options=options,
            recommendation=await self._generate_strategic_recommendation(decision_context, options),
            impact_assessment=impact_assessment,
            stakeholders=self._identify_strategic_stakeholders(decision_context),
            created_at=datetime.now(),
            deadline=deadline,
            workflow_id=workflow_context["workflow_id"],
            stage_name=workflow_context.get("stage_name", "unknown"),
            agent_requester=workflow_context.get("agent", "system")
        )
        
    async def create_technical_decision_request(self,
                                              workflow_context: Dict[str, Any],
                                              technical_context: Dict[str, Any]) -> HumanDecisionRequest:
        """Create technical architecture decision request"""
        
        decision_id = f"technical_{workflow_context['workflow_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Assess technical impact
        impact_assessment = await self._assess_technical_impact(technical_context)
        
        # Generate technical options with pros/cons
        options = await self._generate_technical_options(technical_context)
        
        priority = self._determine_decision_priority(impact_assessment, technical_context.get("urgency", "medium"))
        deadline = self._calculate_decision_deadline(priority, technical_context.get("timeline_pressure", "normal"))
        
        return HumanDecisionRequest(
            decision_id=decision_id,
            category=DecisionCategory.ARCHITECTURAL,
            priority=priority,
            title=technical_context.get("title", "Technical Architecture Decision Required"),
            description=technical_context.get("description", ""),
            context=self._enrich_technical_context(workflow_context, technical_context),
            options=options,
            recommendation=await self._generate_technical_recommendation(technical_context, options),
            impact_assessment=impact_assessment,
            stakeholders=self._identify_technical_stakeholders(technical_context),
            created_at=datetime.now(),
            deadline=deadline,
            workflow_id=workflow_context["workflow_id"],
            stage_name=workflow_context.get("stage_name", "unknown"),
            agent_requester=workflow_context.get("agent", "system")
        )
        
    async def _assess_strategic_impact(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess strategic business impact of decision"""
        return {
            "revenue_impact": {
                "potential_gain": decision_context.get("revenue_opportunity", 0),
                "potential_loss": decision_context.get("revenue_risk", 0),
                "confidence": decision_context.get("revenue_confidence", "medium")
            },
            "customer_impact": {
                "affected_customers": decision_context.get("customer_count", 0),
                "satisfaction_risk": decision_context.get("satisfaction_risk", "low"),
                "experience_improvement": decision_context.get("experience_gain", "minimal")
            },
            "competitive_impact": {
                "competitive_advantage": decision_context.get("competitive_advantage", "none"),
                "market_positioning": decision_context.get("market_impact", "neutral"),
                "differentiation_value": decision_context.get("differentiation", "low")
            },
            "operational_impact": {
                "efficiency_gain": decision_context.get("efficiency_improvement", 0),
                "cost_impact": decision_context.get("cost_change", 0),
                "resource_requirements": decision_context.get("resource_needs", "standard")
            },
            "risk_assessment": {
                "implementation_risk": decision_context.get("implementation_risk", "medium"),
                "timeline_risk": decision_context.get("timeline_risk", "low"),
                "technical_risk": decision_context.get("technical_risk", "low")
            }
        }
        
    async def _generate_decision_options(self, context: Dict[str, Any], category: DecisionCategory) -> List[Dict[str, Any]]:
        """Generate decision options with analysis"""
        if category == DecisionCategory.STRATEGIC:
            return [
                {
                    "option_id": "approve",
                    "title": "Approve and Proceed",
                    "description": "Approve the proposed change and continue with implementation",
                    "pros": ["Maintains momentum", "Delivers planned value", "Meets commitments"],
                    "cons": ["May involve risks", "Resource commitment required"],
                    "risk_level": "medium",
                    "resource_impact": context.get("resource_requirements", "standard")
                },
                {
                    "option_id": "modify",
                    "title": "Approve with Modifications",
                    "description": "Approve with strategic modifications to reduce risk or increase value",
                    "pros": ["Risk mitigation", "Optimized value delivery", "Stakeholder alignment"],
                    "cons": ["Additional planning required", "Timeline impact"],
                    "risk_level": "low",
                    "resource_impact": "moderate"
                },
                {
                    "option_id": "defer",
                    "title": "Defer Decision",
                    "description": "Postpone decision pending additional information or changed circumstances",
                    "pros": ["More information available", "Better timing", "Risk avoidance"],
                    "cons": ["Lost momentum", "Delayed value", "Resource inefficiency"],
                    "risk_level": "low",
                    "resource_impact": "minimal"
                },
                {
                    "option_id": "reject",
                    "title": "Reject Proposal",
                    "description": "Reject the proposed change and maintain current approach",
                    "pros": ["No implementation risk", "Resource preservation", "Status quo maintained"],
                    "cons": ["Lost opportunity", "No value delivery", "Potential competitive disadvantage"],
                    "risk_level": "low",
                    "resource_impact": "none"
                }
            ]
        else:
            # Default options for other categories
            return [
                {
                    "option_id": "approve",
                    "title": "Approve",
                    "description": "Approve the proposed action",
                    "risk_level": "medium"
                },
                {
                    "option_id": "reject", 
                    "title": "Reject",
                    "description": "Reject the proposed action",
                    "risk_level": "low"
                }
            ]
            
    def _strategic_delegation_rules(self) -> Dict[str, Any]:
        """Strategic decision delegation rules"""
        return {
            "revenue_impact": {
                "high": "CEO",
                "medium": "CPO",
                "low": "Business-Coordinator"
            },
            "customer_impact": {
                "high": "CPO",
                "medium": "Product-Manager",
                "low": "Business-Coordinator"
            },
            "competitive_impact": {
                "high": "CEO",
                "medium": "CPO",
                "low": "Business-Coordinator"
            }
        }
        
    def _financial_delegation_rules(self) -> Dict[str, Any]:
        """Financial decision delegation rules"""
        return {
            "budget_thresholds": {
                "< 5000": "Engineering-Lead",
                "< 25000": "VP-Engineering", 
                "< 100000": "CFO",
                "> 100000": "CEO"
            },
            "recurring_costs": {
                "< 1000/month": "Engineering-Lead",
                "< 5000/month": "VP-Engineering",
                "> 5000/month": "CFO"
            }
        }
        
    def _technical_delegation_rules(self) -> Dict[str, Any]:
        """Technical decision delegation rules"""
        return {
            "architecture_impact": {
                "breaking_change": "CTO",
                "significant": "Engineering-Lead",
                "minor": "Solution-Architect"
            },
            "security_implications": {
                "high": "CISO",
                "medium": "Security-Lead",
                "low": "Engineering-Lead"
            }
        }
        
    def _determine_decision_priority(self, impact_assessment: Dict[str, Any], urgency: str) -> DecisionPriority:
        """Determine decision priority based on impact and urgency"""
        # Calculate impact score
        impact_factors = []
        
        if "revenue_impact" in impact_assessment:
            revenue_impact = impact_assessment["revenue_impact"]
            if revenue_impact.get("potential_loss", 0) > 50000:
                impact_factors.append("high")
            elif revenue_impact.get("potential_gain", 0) > 100000:
                impact_factors.append("high")
                
        if "customer_impact" in impact_assessment:
            customer_impact = impact_assessment["customer_impact"]
            if customer_impact.get("affected_customers", 0) > 1000:
                impact_factors.append("high")
            elif customer_impact.get("satisfaction_risk", "low") == "high":
                impact_factors.append("high")
        
        # Combine impact and urgency
        high_impact = "high" in impact_factors
        
        if urgency == "critical" or (high_impact and urgency == "high"):
            return DecisionPriority.CRITICAL
        elif urgency == "high" or high_impact:
            return DecisionPriority.HIGH
        elif urgency == "medium":
            return DecisionPriority.MEDIUM
        else:
            return DecisionPriority.LOW
            
    def _calculate_decision_deadline(self, priority: DecisionPriority, timeline_pressure: str) -> datetime:
        """Calculate decision deadline based on priority and timeline pressure"""
        base_times = {
            DecisionPriority.CRITICAL: timedelta(minutes=30),
            DecisionPriority.HIGH: timedelta(hours=2),
            DecisionPriority.MEDIUM: timedelta(hours=8),
            DecisionPriority.LOW: timedelta(days=1)
        }
        
        base_time = base_times[priority]
        
        # Adjust for timeline pressure
        if timeline_pressure == "critical":
            base_time = base_time / 2
        elif timeline_pressure == "high":
            base_time = base_time * 0.75
        elif timeline_pressure == "low":
            base_time = base_time * 2
            
        return datetime.now() + base_time
        
    def _initialize_decision_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize common decision templates"""
        return {
            "scope_change": {
                "category": DecisionCategory.STRATEGIC,
                "title": "Project Scope Change Request",
                "stakeholders": ["Product-Manager", "Engineering-Lead", "Business-Coordinator"],
                "required_context": ["impact_analysis", "resource_implications", "timeline_effects"]
            },
            "security_exception": {
                "category": DecisionCategory.SECURITY,
                "title": "Security Policy Exception Request", 
                "stakeholders": ["Security-Lead", "CISO", "Engineering-Lead"],
                "required_context": ["risk_assessment", "mitigation_plan", "business_justification"]
            },
            "architecture_change": {
                "category": DecisionCategory.ARCHITECTURAL,
                "title": "Architecture Change Proposal",
                "stakeholders": ["Solution-Architect", "Engineering-Lead", "CTO"],
                "required_context": ["technical_analysis", "migration_plan", "risk_assessment"]
            }
        }