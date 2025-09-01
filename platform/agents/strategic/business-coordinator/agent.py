"""
Business Coordinator Agent - Strategic Command Level
Role: Strategic alignment, business context preservation, executive validation
"""

from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime

from symphony_core.agents.base_agent import BaseAgent, AgentCapability, create_agent_capability, AgentSchedule
from symphony_core.agents.base_agent import HandoffContext, HandoffStatus


class BusinessCoordinatorAgent(BaseAgent):
    """
    Business Coordinator Agent (Victoria-style)
    
    Strategic Command Level agent responsible for:
    - Strategic alignment and business context preservation
    - Executive validation and decision escalation
    - Business value assessment and ROI validation
    - Cross-workflow impact analysis
    """
    
    def __init__(self, customer_id: Optional[str] = None):
        # Define agent capabilities
        capabilities = [
            create_agent_capability(
                "strategic_alignment", 
                "Maintain strategic business alignment across all workflows",
                "critical",
                performance_target=99.5
            ),
            create_agent_capability(
                "business_value_assessment",
                "Assess business value and ROI of decisions and changes", 
                "critical",
                performance_target=98.0
            ),
            create_agent_capability(
                "executive_validation",
                "Validate decisions requiring executive approval",
                "critical", 
                performance_target=99.0
            ),
            create_agent_capability(
                "cross_workflow_impact",
                "Analyze impact of decisions across multiple workflows",
                "high",
                performance_target=97.0
            ),
            create_agent_capability(
                "context_preservation", 
                "Maintain business context across agent handoffs",
                "critical",
                performance_target=99.5
            ),
            create_agent_capability(
                "stakeholder_coordination",
                "Coordinate with business stakeholders and customers",
                "high",
                performance_target=96.0
            )
        ]
        
        # Create schedule for strategic coordination
        schedule = AgentSchedule(
            max_concurrent_tasks=5,
            business_hours_only=False,  # Strategic decisions may be needed 24/7
            preferred_hours=(8, 20),  # Business hours preference
            escalation_hours=2.0  # 2 hour response time for escalations
        )
        
        super().__init__(
            agent_id="business-coordinator-victoria",
            name="Victoria (Business Coordinator)",
            role="Strategic Business Coordinator", 
            category="strategic",
            capabilities=capabilities,
            schedule=schedule,
            customer_id=customer_id
        )
        
        # Strategic context tracking
        self.strategic_objectives: Dict[str, Any] = {}
        self.business_metrics: Dict[str, float] = {}
        self.stakeholder_map: Dict[str, List[str]] = {}
        self.executive_decisions: List[Dict[str, Any]] = []
        
    async def _initialize_agent(self) -> None:
        """Initialize business coordinator with strategic context"""
        await super()._initialize_agent()
        
        # Load business context and objectives
        self.strategic_objectives = {
            "revenue_growth": {"target": 30.0, "current": 0.0, "priority": "critical"},
            "customer_satisfaction": {"target": 95.0, "current": 0.0, "priority": "critical"}, 
            "operational_efficiency": {"target": 25.0, "current": 0.0, "priority": "high"},
            "market_expansion": {"target": 15.0, "current": 0.0, "priority": "medium"}
        }
        
        # Initialize stakeholder mapping
        self.stakeholder_map = {
            "executive": ["CEO", "CTO", "CPO", "COO"],
            "product": ["VP Product", "Product Managers"],
            "engineering": ["VP Engineering", "Engineering Directors"],
            "customers": ["Key Customer Contacts", "Customer Success"]
        }
        
        self.logger.info(f"Business Coordinator {self.name} initialized with strategic objectives")
        
    async def _execute_task_impl(self, task_data: Dict[str, Any]) -> Any:
        """Execute business coordination tasks"""
        task_type = task_data.get("type", "unknown")
        
        if task_type == "strategic_validation":
            return await self._validate_strategic_alignment(task_data)
        elif task_type == "business_impact_assessment":
            return await self._assess_business_impact(task_data)
        elif task_type == "executive_escalation":
            return await self._handle_executive_escalation(task_data)
        elif task_type == "cross_workflow_analysis":
            return await self._analyze_cross_workflow_impact(task_data)
        elif task_type == "stakeholder_coordination":
            return await self._coordinate_stakeholders(task_data)
        elif task_type == "context_validation":
            return await self._validate_business_context(task_data)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
            
    async def _process_handoff(self, handoff_context: HandoffContext) -> bool:
        """Process handoff with business context validation"""
        try:
            # Extract business context from handoff
            business_context = handoff_context.context_data.get("business_context", {})
            strategic_impact = handoff_context.context_data.get("strategic_impact", "low")
            
            # Validate strategic alignment
            alignment_valid = await self._validate_strategic_alignment({
                "context": business_context,
                "impact": strategic_impact
            })
            
            if not alignment_valid["is_aligned"]:
                # Escalate misalignment to human decision makers
                await self._escalate_to_human({
                    "type": "strategic_misalignment",
                    "handoff_id": handoff_context.handoff_id,
                    "context": handoff_context,
                    "misalignment_details": alignment_valid["details"]
                })
                return False
                
            # Preserve and enhance business context
            enhanced_context = await self._enhance_business_context(handoff_context)
            handoff_context.context_data.update(enhanced_context)
            
            # Log business decision
            await self._log_business_decision({
                "handoff_id": handoff_context.handoff_id,
                "decision": "approved_with_context",
                "business_impact": strategic_impact,
                "context_enhancement": enhanced_context
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing handoff {handoff_context.handoff_id}: {str(e)}")
            return False
            
    async def _validate_strategic_alignment(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate strategic alignment of decisions and changes"""
        context = task_data.get("context", {})
        impact = task_data.get("impact", "low")
        
        # Check alignment with strategic objectives
        alignment_score = 0.0
        alignment_details = []
        
        for objective_name, objective in self.strategic_objectives.items():
            if objective["priority"] == "critical" and impact in ["high", "critical"]:
                # Critical objectives must be considered for high-impact changes
                objective_alignment = context.get(f"{objective_name}_impact", 0.0)
                alignment_score += objective_alignment * 0.4
                alignment_details.append({
                    "objective": objective_name,
                    "alignment": objective_alignment,
                    "required": objective["target"]
                })
        
        is_aligned = alignment_score >= 0.7  # 70% alignment threshold
        
        return {
            "is_aligned": is_aligned,
            "alignment_score": alignment_score,
            "details": alignment_details,
            "recommendation": "approved" if is_aligned else "requires_executive_review"
        }
        
    async def _assess_business_impact(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess business impact of proposed changes"""
        change_type = task_data.get("change_type", "unknown")
        scope = task_data.get("scope", {})
        
        # Calculate impact scores across different dimensions
        impact_assessment = {
            "revenue_impact": self._calculate_revenue_impact(scope),
            "customer_impact": self._calculate_customer_impact(scope),
            "operational_impact": self._calculate_operational_impact(scope),
            "risk_assessment": self._calculate_risk_assessment(scope)
        }
        
        # Overall business impact score
        overall_impact = (
            impact_assessment["revenue_impact"] * 0.3 +
            impact_assessment["customer_impact"] * 0.3 +
            impact_assessment["operational_impact"] * 0.2 +
            (1.0 - impact_assessment["risk_assessment"]) * 0.2  # Lower risk = higher score
        )
        
        return {
            "overall_impact": overall_impact,
            "detailed_assessment": impact_assessment,
            "recommendation": self._generate_business_recommendation(overall_impact),
            "executive_approval_required": overall_impact > 0.7 or impact_assessment["risk_assessment"] > 0.6
        }
        
    async def _handle_executive_escalation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle escalation to executive decision makers"""
        escalation_type = task_data.get("type", "unknown")
        context = task_data.get("context", {})
        
        # Prepare executive summary
        executive_summary = {
            "escalation_type": escalation_type,
            "business_context": context.get("business_context", {}),
            "strategic_impact": context.get("strategic_impact", "medium"),
            "recommended_action": context.get("recommended_action", "review_required"),
            "timeline": context.get("timeline", "standard"),
            "stakeholders_affected": self._identify_affected_stakeholders(context)
        }
        
        # Create human handoff for executive decision
        human_handoff_context = {
            "requires_human_decision": True,
            "decision_level": "executive",
            "summary": executive_summary,
            "response_required_by": self._calculate_response_deadline(context),
            "escalation_reason": f"Business decision requires executive approval: {escalation_type}"
        }
        
        # Log escalation
        self.executive_decisions.append({
            "timestamp": datetime.now().isoformat(),
            "escalation_type": escalation_type, 
            "context": context,
            "status": "pending_human_decision"
        })
        
        return {
            "escalated": True,
            "human_handoff": human_handoff_context,
            "tracking_id": len(self.executive_decisions) - 1
        }
        
    async def _enhance_business_context(self, handoff_context: HandoffContext) -> Dict[str, Any]:
        """Enhance handoff context with business intelligence"""
        enhanced_context = {
            "strategic_alignment": await self._get_strategic_alignment_score(handoff_context),
            "business_priority": self._determine_business_priority(handoff_context),
            "stakeholder_impact": self._assess_stakeholder_impact(handoff_context),
            "success_metrics": self._define_success_metrics(handoff_context),
            "business_timestamp": datetime.now().isoformat()
        }
        
        return enhanced_context
        
    def _calculate_revenue_impact(self, scope: Dict[str, Any]) -> float:
        """Calculate potential revenue impact (0.0 to 1.0 scale)"""
        # Simplified revenue impact calculation
        customer_facing = scope.get("customer_facing", False)
        feature_type = scope.get("feature_type", "internal")
        customer_count = scope.get("affected_customers", 0)
        
        base_impact = 0.3 if customer_facing else 0.1
        if feature_type == "revenue_generating":
            base_impact += 0.4
        elif feature_type == "customer_retention":
            base_impact += 0.3
            
        customer_multiplier = min(customer_count / 1000.0, 1.0)  # Scale by customer count
        
        return min(base_impact + customer_multiplier, 1.0)
        
    def _calculate_customer_impact(self, scope: Dict[str, Any]) -> float:
        """Calculate customer impact score"""
        user_facing = scope.get("user_facing", False)
        breaking_changes = scope.get("breaking_changes", False)
        customer_requests = scope.get("customer_requests", 0)
        
        impact = 0.2 if user_facing else 0.1
        impact -= 0.3 if breaking_changes else 0.0
        impact += min(customer_requests / 10.0, 0.4)  # Up to 40% boost for customer requests
        
        return max(min(impact, 1.0), 0.0)
        
    def _calculate_operational_impact(self, scope: Dict[str, Any]) -> float:
        """Calculate operational efficiency impact"""
        automation_level = scope.get("automation_improvement", 0.0)
        process_optimization = scope.get("process_optimization", 0.0)  
        team_productivity = scope.get("team_productivity_impact", 0.0)
        
        return min((automation_level + process_optimization + team_productivity) / 3.0, 1.0)
        
    def _calculate_risk_assessment(self, scope: Dict[str, Any]) -> float:
        """Calculate risk level (higher score = higher risk)"""
        complexity = scope.get("complexity", "low")
        dependencies = scope.get("external_dependencies", 0)
        timeline_pressure = scope.get("timeline_pressure", "normal")
        
        risk_score = 0.2  # Base risk
        
        if complexity == "high":
            risk_score += 0.3
        elif complexity == "medium":
            risk_score += 0.15
            
        risk_score += min(dependencies * 0.1, 0.3)  # Max 30% risk from dependencies
        
        if timeline_pressure == "high":
            risk_score += 0.2
        elif timeline_pressure == "critical":
            risk_score += 0.3
            
        return min(risk_score, 1.0)
        
    def _generate_business_recommendation(self, overall_impact: float) -> str:
        """Generate business recommendation based on impact assessment"""
        if overall_impact >= 0.8:
            return "strongly_recommended"
        elif overall_impact >= 0.6:
            return "recommended"
        elif overall_impact >= 0.4:
            return "conditional_approval"
        else:
            return "requires_justification"