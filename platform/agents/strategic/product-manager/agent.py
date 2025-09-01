"""
Product Manager Agent - Strategic Command Level  
Role: Feature specifications, product requirements, customer impact management
"""

from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime, timedelta

from symphony_core.agents.base_agent import BaseAgent, AgentCapability, create_agent_capability, AgentSchedule
from symphony_core.agents.base_agent import HandoffContext, HandoffStatus


class ProductManagerAgent(BaseAgent):
    """
    Product Manager Agent - Strategic Command Level
    
    Responsible for:
    - Product feature specifications and requirements analysis
    - Customer needs assessment and impact evaluation  
    - Product roadmap alignment and prioritization
    - User story creation and acceptance criteria definition
    """
    
    def __init__(self, customer_id: Optional[str] = None):
        # Define product management capabilities
        capabilities = [
            create_agent_capability(
                "requirements_analysis",
                "Analyze and validate product requirements from multiple sources",
                "critical",
                performance_target=98.0
            ),
            create_agent_capability(
                "customer_needs_assessment", 
                "Assess customer needs and translate to product requirements",
                "critical",
                performance_target=96.5
            ),
            create_agent_capability(
                "feature_specification",
                "Create detailed feature specifications and acceptance criteria",
                "critical",
                performance_target=97.0
            ),
            create_agent_capability(
                "product_prioritization",
                "Prioritize features and manage product backlog",
                "high",
                performance_target=94.0
            ),
            create_agent_capability(
                "user_story_creation",
                "Create well-formed user stories following INVEST principles",
                "high", 
                performance_target=95.0
            ),
            create_agent_capability(
                "stakeholder_coordination",
                "Coordinate with stakeholders across product development lifecycle",
                "high",
                performance_target=93.0
            ),
            create_agent_capability(
                "product_analytics",
                "Analyze product performance and user behavior metrics",
                "medium",
                performance_target=90.0
            )
        ]
        
        # Product manager schedule - business and customer focused
        schedule = AgentSchedule(
            max_concurrent_tasks=6,
            business_hours_only=True,  # Customer-focused role
            preferred_hours=(8, 18),  # Business hours
            escalation_hours=2.0  # 2 hour response for product decisions
        )
        
        super().__init__(
            agent_id="product-manager-lead",
            name="Product Manager", 
            role="Product Strategy and Requirements Lead",
            category="strategic",
            capabilities=capabilities,
            schedule=schedule,
            customer_id=customer_id
        )
        
        # Product management state
        self.product_backlog: List[Dict[str, Any]] = []
        self.customer_feedback: Dict[str, List[Dict[str, Any]]] = {}
        self.feature_specifications: Dict[str, Dict[str, Any]] = {}
        self.user_personas: Dict[str, Dict[str, Any]] = {}
        self.market_analysis: Dict[str, Any] = {}
        self.product_metrics: Dict[str, float] = {}
        
    async def _initialize_agent(self) -> None:
        """Initialize product manager with product context"""
        await super()._initialize_agent()
        
        # Initialize user personas
        self.user_personas = {
            "enterprise_admin": {
                "name": "Enterprise Administrator",
                "goals": ["System reliability", "Security compliance", "Cost optimization"],
                "pain_points": ["Complex configuration", "Limited visibility", "Manual processes"],
                "technical_level": "high"
            },
            "business_user": {
                "name": "Business User",
                "goals": ["Easy workflow automation", "Quick results", "Minimal learning curve"],
                "pain_points": ["Technical complexity", "Slow support", "Limited customization"], 
                "technical_level": "medium"
            },
            "developer": {
                "name": "Developer",
                "goals": ["Developer experience", "API flexibility", "Integration ease"],
                "pain_points": ["Poor documentation", "Limited SDKs", "Breaking changes"],
                "technical_level": "expert"
            }
        }
        
        # Product success metrics
        self.product_metrics = {
            "user_adoption": 0.0,
            "feature_usage": 0.0, 
            "customer_satisfaction": 0.0,
            "time_to_value": 0.0,
            "retention_rate": 0.0
        }
        
        self.logger.info(f"Product Manager {self.name} initialized with user personas and metrics")
        
    async def _execute_task_impl(self, task_data: Dict[str, Any]) -> Any:
        """Execute product management tasks"""
        task_type = task_data.get("type", "unknown")
        
        if task_type == "analyze_idea":
            return await self._analyze_product_idea(task_data)
        elif task_type == "create_specification":
            return await self._create_feature_specification(task_data)  
        elif task_type == "prioritize_backlog":
            return await self._prioritize_product_backlog(task_data)
        elif task_type == "create_user_stories":
            return await self._create_user_stories(task_data)
        elif task_type == "assess_customer_impact":
            return await self._assess_customer_impact(task_data)
        elif task_type == "validate_requirements":
            return await self._validate_requirements(task_data)
        elif task_type == "analyze_feedback":
            return await self._analyze_customer_feedback(task_data)
        else:
            raise ValueError(f"Unknown product management task type: {task_type}")
            
    async def _process_handoff(self, handoff_context: HandoffContext) -> bool:
        """Process handoff with product context validation"""
        try:
            # Extract product context
            product_context = handoff_context.context_data.get("product_context", {})
            customer_impact = handoff_context.context_data.get("customer_impact", "low")
            
            # Validate product requirements alignment
            requirements_valid = await self._validate_product_alignment(product_context, customer_impact)
            
            if not requirements_valid["is_aligned"]:
                # Flag for product review
                handoff_context.context_data["requires_product_review"] = True
                handoff_context.context_data["product_concerns"] = requirements_valid["concerns"]
                
                self.logger.warning(f"Product alignment issues in handoff {handoff_context.handoff_id}")
            
            # Enhance with product intelligence
            product_intelligence = await self._add_product_intelligence(handoff_context)
            handoff_context.context_data.update(product_intelligence)
            
            # Track for product metrics
            await self._track_product_handoff(handoff_context)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing product handoff {handoff_context.handoff_id}: {str(e)}")
            return False
            
    async def _analyze_product_idea(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and score a product idea"""
        idea = task_data.get("idea", {})
        source = task_data.get("source", "internal")
        
        # Idea analysis framework
        analysis = {
            "market_opportunity": self._assess_market_opportunity(idea),
            "customer_value": self._assess_customer_value(idea),
            "technical_feasibility": self._assess_technical_feasibility(idea),
            "competitive_advantage": self._assess_competitive_advantage(idea),
            "resource_requirements": self._assess_resource_requirements(idea),
            "strategic_alignment": self._assess_strategic_alignment(idea)
        }
        
        # Calculate overall idea score
        weights = {
            "market_opportunity": 0.25,
            "customer_value": 0.25, 
            "technical_feasibility": 0.20,
            "competitive_advantage": 0.15,
            "resource_requirements": 0.10,  # Lower score = better (less resources needed)
            "strategic_alignment": 0.05
        }
        
        overall_score = sum(
            analysis[criterion] * weight 
            for criterion, weight in weights.items()
        )
        
        # Generate recommendation
        recommendation = self._generate_idea_recommendation(overall_score, analysis)
        
        return {
            "idea_id": idea.get("id", "unknown"),
            "overall_score": overall_score,
            "detailed_analysis": analysis,
            "recommendation": recommendation,
            "next_steps": self._define_next_steps(recommendation, analysis),
            "estimated_effort": self._estimate_development_effort(idea, analysis)
        }
        
    async def _create_feature_specification(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed feature specification"""
        feature_request = task_data.get("feature", {})
        context = task_data.get("context", {})
        
        # Create comprehensive specification
        specification = {
            "feature_id": feature_request.get("id", f"feat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            "title": feature_request.get("title", "Unknown Feature"),
            "description": feature_request.get("description", ""),
            "business_objectives": self._define_business_objectives(feature_request, context),
            "user_stories": await self._generate_user_stories(feature_request),
            "acceptance_criteria": self._define_acceptance_criteria(feature_request),
            "technical_requirements": self._define_technical_requirements(feature_request),
            "design_requirements": self._define_design_requirements(feature_request),
            "success_metrics": self._define_success_metrics(feature_request),
            "dependencies": self._identify_dependencies(feature_request),
            "risks_and_assumptions": self._identify_risks_and_assumptions(feature_request)
        }
        
        # Store specification
        self.feature_specifications[specification["feature_id"]] = specification
        
        return {
            "specification_created": True,
            "feature_id": specification["feature_id"],
            "specification": specification,
            "estimated_timeline": self._estimate_development_timeline(specification),
            "resource_allocation": self._recommend_resource_allocation(specification)
        }
        
    async def _create_user_stories(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create INVEST-compliant user stories"""
        epic_data = task_data.get("epic", {})
        requirements = task_data.get("requirements", [])
        
        user_stories = []
        
        for requirement in requirements:
            # Generate user stories for each requirement
            stories = await self._generate_stories_for_requirement(requirement, epic_data)
            user_stories.extend(stories)
        
        # Validate INVEST compliance
        validated_stories = []
        for story in user_stories:
            invest_validation = self._validate_invest_principles(story)
            story["invest_compliance"] = invest_validation
            
            if invest_validation["compliant"]:
                validated_stories.append(story)
            else:
                # Improve story to meet INVEST criteria
                improved_story = await self._improve_story_invest_compliance(story, invest_validation)
                validated_stories.append(improved_story)
        
        return {
            "user_stories_created": True,
            "total_stories": len(validated_stories),
            "stories": validated_stories,
            "epic_breakdown": self._analyze_epic_breakdown(validated_stories),
            "estimation_summary": self._create_estimation_summary(validated_stories)
        }
        
    def _assess_market_opportunity(self, idea: Dict[str, Any]) -> float:
        """Assess market opportunity for the idea (0.0 to 1.0)"""
        market_size = idea.get("market_size", "unknown")
        growth_trend = idea.get("growth_trend", "stable")
        competitive_landscape = idea.get("competitive_landscape", "crowded")
        
        score = 0.5  # Base score
        
        # Market size impact
        if market_size == "large":
            score += 0.3
        elif market_size == "medium":
            score += 0.2
        elif market_size == "small":
            score += 0.1
        
        # Growth trend impact
        if growth_trend == "high_growth":
            score += 0.2
        elif growth_trend == "growing":
            score += 0.1
        elif growth_trend == "declining":
            score -= 0.2
            
        # Competitive landscape
        if competitive_landscape == "blue_ocean":
            score += 0.2
        elif competitive_landscape == "emerging":
            score += 0.1
        elif competitive_landscape == "crowded":
            score -= 0.1
            
        return min(max(score, 0.0), 1.0)
        
    def _assess_customer_value(self, idea: Dict[str, Any]) -> float:
        """Assess customer value proposition (0.0 to 1.0)"""
        pain_point_severity = idea.get("pain_point_severity", "medium")
        solution_uniqueness = idea.get("solution_uniqueness", "moderate")
        user_impact = idea.get("user_impact", "medium")
        
        score = 0.3  # Base score
        
        # Pain point severity
        if pain_point_severity == "critical":
            score += 0.4
        elif pain_point_severity == "high":
            score += 0.3
        elif pain_point_severity == "medium":
            score += 0.2
            
        # Solution uniqueness
        if solution_uniqueness == "highly_unique":
            score += 0.2
        elif solution_uniqueness == "moderate":
            score += 0.1
            
        # User impact
        if user_impact == "high":
            score += 0.1
        elif user_impact == "medium":
            score += 0.05
            
        return min(score, 1.0)
        
    def _generate_idea_recommendation(self, overall_score: float, analysis: Dict[str, Any]) -> str:
        """Generate recommendation based on idea analysis"""
        if overall_score >= 0.8:
            return "strongly_recommend"
        elif overall_score >= 0.6:
            return "recommend_with_conditions"
        elif overall_score >= 0.4:
            return "requires_further_analysis"
        else:
            return "not_recommended"
            
    async def _generate_user_stories(self, feature_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate user stories for a feature"""
        stories = []
        
        # Identify user personas affected by this feature
        affected_personas = self._identify_affected_personas(feature_request)
        
        for persona_id in affected_personas:
            persona = self.user_personas.get(persona_id, {})
            
            # Generate stories for this persona
            persona_stories = self._generate_persona_stories(feature_request, persona, persona_id)
            stories.extend(persona_stories)
        
        return stories
        
    def _validate_invest_principles(self, story: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user story against INVEST principles"""
        validation = {
            "independent": self._check_independence(story),
            "negotiable": self._check_negotiable(story), 
            "valuable": self._check_valuable(story),
            "estimable": self._check_estimable(story),
            "small": self._check_small(story),
            "testable": self._check_testable(story)
        }
        
        compliance_score = sum(1 for check in validation.values() if check["valid"]) / len(validation)
        
        return {
            "compliant": compliance_score >= 0.8,  # 80% compliance threshold
            "score": compliance_score,
            "detailed_validation": validation,
            "improvement_areas": [
                principle for principle, result in validation.items() 
                if not result["valid"]
            ]
        }
        
    def _check_independence(self, story: Dict[str, Any]) -> Dict[str, bool]:
        """Check if story is independent"""
        dependencies = story.get("dependencies", [])
        return {
            "valid": len(dependencies) <= 1,  # At most 1 dependency
            "details": f"Story has {len(dependencies)} dependencies"
        }
        
    def _check_valuable(self, story: Dict[str, Any]) -> Dict[str, bool]:
        """Check if story provides user value"""
        has_user_benefit = bool(story.get("user_benefit", ""))
        has_business_value = bool(story.get("business_value", ""))
        
        return {
            "valid": has_user_benefit and has_business_value,
            "details": "Story must have clear user benefit and business value"
        }