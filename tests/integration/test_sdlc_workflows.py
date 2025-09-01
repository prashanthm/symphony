"""
Integration tests for SDLC workflow coordination
Tests the role-based agent team coordination for key workflows
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

from platform.orchestration.sdlc_workflow_coordinator import SDLCWorkflowCoordinator, WorkflowType
from platform.orchestration.human_decision_gateway import HumanDecisionGateway, DecisionCategory, DecisionPriority
from symphony_core.agents.agent_manager import AgentManager


class TestSDLCWorkflowCoordination:
    """Test SDLC workflow coordination with role-based agents"""
    
    @pytest.fixture
    def mock_agent_manager(self):
        """Mock agent manager with test agents"""
        manager = Mock(spec=AgentManager)
        
        # Mock agent responses for each role
        mock_agents = {
            "business-coordinator-victoria": self._create_mock_business_coordinator(),
            "engineering-lead-coordinator": self._create_mock_engineering_lead(),
            "product-manager-lead": self._create_mock_product_manager(),
            "devops-engineer-infrastructure": self._create_mock_devops_engineer(),
            "qa-engineer-quality": self._create_mock_qa_engineer()
        }
        
        async def get_agent(agent_id):
            return mock_agents.get(agent_id)
            
        manager.get_agent = get_agent
        return manager
        
    @pytest.fixture
    def workflow_coordinator(self, mock_agent_manager):
        """SDLC workflow coordinator with mocked agents"""
        return SDLCWorkflowCoordinator(mock_agent_manager)
        
    @pytest.fixture 
    def human_decision_gateway(self):
        """Human decision gateway for testing"""
        return HumanDecisionGateway()
        
    @pytest.mark.asyncio
    async def test_ideas_intake_workflow_success(self, workflow_coordinator):
        """Test successful ideas intake workflow execution"""
        # Arrange
        workflow_data = {
            "idea": {
                "id": "idea_123",
                "title": "Automated Customer Onboarding",
                "description": "Streamline customer onboarding process with AI automation",
                "source": "customer_feedback",
                "market_size": "large",
                "growth_trend": "high_growth",
                "competitive_landscape": "emerging",
                "pain_point_severity": "high",
                "solution_uniqueness": "highly_unique",
                "user_impact": "high"
            },
            "business_context": {
                "strategic_alignment": "high",
                "revenue_opportunity": 150000,
                "customer_requests": 8,
                "market_urgency": "medium"
            }
        }
        
        # Act
        result = await workflow_coordinator.execute_workflow(
            WorkflowType.IDEAS_INTAKE, 
            workflow_data
        )
        
        # Assert
        assert result["workflow_completed"] is True
        assert "workflow_id" in result
        assert result["result"]["workflow_completed"] is True
        
        # Verify agent coordination
        metrics = result["metrics"]
        assert metrics["agent_handoffs"] == 4  # 4 stages in ideas intake
        assert metrics["handoff_success_rate"] == 1.0  # All handoffs successful
        assert metrics["human_decisions"] >= 1  # Business validation gate
        
        # Verify workflow stages completed
        stage_results = result["result"]["stage_results"]
        assert "idea_analysis" in stage_results
        assert "business_validation" in stage_results
        assert "technical_feasibility" in stage_results 
        assert "epic_creation" in stage_results
        
        # Verify context preservation
        coordination_summary = result["agent_coordination_summary"]
        assert coordination_summary["total_agents_involved"] == 3  # Product Manager, Business Coordinator, Engineering Lead
        assert coordination_summary["context_handoffs"] == 4
        
    @pytest.mark.asyncio
    async def test_pr_quality_gate_workflow_with_failures(self, workflow_coordinator):
        """Test PR quality gate workflow with quality failures requiring human intervention"""
        # Arrange - PR with quality issues
        workflow_data = {
            "pr": {
                "id": "pr_456",
                "title": "Add user authentication service", 
                "repository": "user-service",
                "branch": "feature/auth-service",
                "author": "developer_1",
                "files_changed": 12,
                "lines_added": 450,
                "lines_deleted": 23
            },
            "test_coverage": 75.5,  # Below 80% threshold
            "security_scan": {
                "critical_vulnerabilities": 0,
                "high_vulnerabilities": 1,  # Will trigger human review
                "medium_vulnerabilities": 3
            },
            "code_quality": {
                "complexity": 8,
                "duplication": 2.1,
                "maintainability_index": 82
            }
        }
        
        # Act
        result = await workflow_coordinator.execute_workflow(
            WorkflowType.PR_QUALITY_GATE,
            workflow_data
        )
        
        # Assert - Workflow should complete but with quality concerns
        assert result["workflow_completed"] is True
        
        # Verify quality gate enforcement
        stage_results = result["result"]["stage_results"]
        quality_validation = stage_results["quality_gate_validation"]
        assert quality_validation["stage_result"]["overall_passed"] is False
        
        # Verify human decision gate triggered
        metrics = result["metrics"]
        assert metrics["human_decisions"] >= 1  # Quality gate failure should trigger human review
        
        # Verify engineering review stage handled the quality issues
        engineering_review = stage_results["engineering_review"]
        assert engineering_review["success"] is True
        
    @pytest.mark.asyncio
    async def test_repo_scaffold_workflow_complete_setup(self, workflow_coordinator):
        """Test repository scaffolding workflow with complete infrastructure setup"""
        # Arrange
        workflow_data = {
            "project": {
                "name": "customer-analytics-service",
                "type": "microservice",
                "team": "data-platform",
                "business_priority": "high"
            },
            "requirements": {
                "programming_language": "python",
                "framework": "fastapi",
                "database": "postgresql",
                "deployment_target": "kubernetes",
                "compliance_requirements": ["SOC2", "GDPR"]
            },
            "business_context": {
                "customer_facing": True,
                "revenue_impact": "high",
                "timeline": "6_weeks",
                "stakeholders": ["data-team", "product-team", "security-team"]
            }
        }
        
        # Act
        result = await workflow_coordinator.execute_workflow(
            WorkflowType.REPO_SCAFFOLD,
            workflow_data
        )
        
        # Assert
        assert result["workflow_completed"] is True
        
        # Verify all infrastructure components set up
        stage_results = result["result"]["stage_results"]
        
        # Project planning
        project_planning = stage_results["project_planning"]
        assert project_planning["success"] is True
        
        # Architecture design
        architecture = stage_results["architecture_design"]
        assert architecture["success"] is True
        
        # Infrastructure setup
        infrastructure = stage_results["infrastructure_setup"]
        assert infrastructure["stage_result"]["repository_ready"] is True
        assert "cicd_pipeline" in infrastructure["stage_result"]["infrastructure_setup"]
        assert "environments" in infrastructure["stage_result"]["infrastructure_setup"]
        
        # Quality framework
        quality_framework = stage_results["quality_framework"]
        assert quality_framework["success"] is True
        
        # Business alignment with strategic approval
        business_alignment = stage_results["business_alignment"]
        assert business_alignment["success"] is True
        
        # Verify agent coordination across specialties
        coordination_summary = result["agent_coordination_summary"]
        assert coordination_summary["total_agents_involved"] == 5  # All 5 core agents involved
        
    @pytest.mark.asyncio
    async def test_human_decision_integration_strategic(self, human_decision_gateway):
        """Test strategic human decision integration"""
        # Arrange
        workflow_context = {
            "workflow_id": "test_workflow_789",
            "workflow_type": "ideas_intake",
            "stage_name": "business_validation"
        }
        
        decision_context = {
            "title": "High-Impact Feature Investment Decision",
            "description": "Approve significant investment in AI-powered customer analytics",
            "revenue_opportunity": 250000,
            "resource_needs": "significant",
            "customer_count": 1500,
            "urgency": "high",
            "timeline_pressure": "medium"
        }
        
        # Act
        decision_request = await human_decision_gateway.create_strategic_decision_request(
            workflow_context, decision_context
        )
        
        request_result = await human_decision_gateway.request_human_decision(decision_request)
        
        # Assert
        assert request_result["success"] is True
        assert decision_request.category == DecisionCategory.STRATEGIC
        assert decision_request.priority == DecisionPriority.HIGH
        assert len(decision_request.options) == 4  # approve, modify, defer, reject
        
        # Verify impact assessment
        impact = decision_request.impact_assessment
        assert impact["revenue_impact"]["potential_gain"] == 250000
        assert impact["customer_impact"]["affected_customers"] == 1500
        
        # Verify routing
        assert "estimated_response_time" in request_result
        assert "escalation_schedule" in request_result
        
    @pytest.mark.asyncio
    async def test_workflow_failure_recovery(self, workflow_coordinator):
        """Test workflow failure handling and recovery"""
        # Arrange - Simulate agent failure
        with patch.object(workflow_coordinator.agent_manager, 'get_agent') as mock_get_agent:
            # First agent succeeds, second fails
            mock_agents = [
                self._create_mock_product_manager(),
                None  # Simulate missing agent
            ]
            mock_get_agent.side_effect = mock_agents
            
            workflow_data = {
                "idea": {
                    "id": "test_idea_failure",
                    "title": "Test Idea",
                    "description": "Test failure handling"
                }
            }
            
            # Act
            result = await workflow_coordinator.execute_workflow(
                WorkflowType.IDEAS_INTAKE,
                workflow_data
            )
            
            # Assert
            assert result["workflow_completed"] is False
            assert "error" in result
            assert "failure_analysis" in result
            
            # Verify partial results captured
            assert "partial_results" in result
            
    def _create_mock_business_coordinator(self):
        """Create mock Business Coordinator agent"""
        agent = AsyncMock()
        agent.agent_id = "business-coordinator-victoria"
        
        async def execute_task(task_data):
            task_type = task_data.get("type", "unknown")
            
            if task_type == "business_impact_assessment":
                return {
                    "overall_impact": 0.85,
                    "detailed_assessment": {
                        "revenue_impact": 0.8,
                        "customer_impact": 0.9,
                        "operational_impact": 0.7,
                        "risk_assessment": 0.3
                    },
                    "recommendation": "strongly_recommend",
                    "executive_approval_required": True,
                    "context": {"business_priority": "high", "strategic_alignment": 0.9}
                }
            elif task_type == "strategic_validation":
                return {
                    "validation_successful": True,
                    "strategic_alignment_score": 0.9,
                    "business_readiness": True,
                    "context": {"strategic_priority": "high"}
                }
                
        agent.execute_task = execute_task
        return agent
        
    def _create_mock_engineering_lead(self):
        """Create mock Engineering Lead agent"""
        agent = AsyncMock()
        agent.agent_id = "engineering-lead-coordinator"
        
        async def execute_task(task_data):
            task_type = task_data.get("type", "unknown")
            
            if task_type == "technical_review":
                return {
                    "technical_feasibility": 0.85,
                    "complexity_assessment": "medium",
                    "resource_estimate": "4-6 weeks",
                    "technical_risks": ["integration_complexity", "performance_requirements"],
                    "recommendation": "approved_with_monitoring",
                    "context": {"technical_complexity": "medium", "architecture_impact": "moderate"}
                }
            elif task_type == "validate_architecture":
                return {
                    "architecture_valid": True,
                    "compliance_check": "passed",
                    "security_review": "approved",
                    "context": {"architecture_pattern": "microservices", "security_level": "high"}
                }
                
        agent.execute_task = execute_task
        return agent
        
    def _create_mock_product_manager(self):
        """Create mock Product Manager agent"""
        agent = AsyncMock()
        agent.agent_id = "product-manager-lead"
        
        async def execute_task(task_data):
            task_type = task_data.get("type", "unknown")
            
            if task_type == "analyze_idea":
                return {
                    "idea_id": task_data.get("idea", {}).get("id", "unknown"),
                    "overall_score": 0.82,
                    "detailed_analysis": {
                        "market_opportunity": 0.8,
                        "customer_value": 0.9,
                        "technical_feasibility": 0.75,
                        "competitive_advantage": 0.85,
                        "resource_requirements": 0.7,
                        "strategic_alignment": 0.9
                    },
                    "recommendation": "strongly_recommend",
                    "context": {"product_priority": "high", "customer_value": 0.9}
                }
            elif task_type == "create_specification":
                return {
                    "specification_created": True,
                    "feature_id": "feat_" + datetime.now().strftime('%Y%m%d_%H%M%S'),
                    "specification": {
                        "title": "Generated Feature Specification",
                        "user_stories": ["Story 1", "Story 2", "Story 3"],
                        "acceptance_criteria": ["Criteria 1", "Criteria 2"]
                    },
                    "context": {"specification_quality": "high"}
                }
            elif task_type == "validate_requirements":
                return {
                    "requirements_valid": True,
                    "completeness_score": 0.9,
                    "clarity_score": 0.85,
                    "context": {"requirements_quality": "high"}
                }
                
        agent.execute_task = execute_task
        return agent
        
    def _create_mock_devops_engineer(self):
        """Create mock DevOps Engineer agent"""
        agent = AsyncMock()
        agent.agent_id = "devops-engineer-infrastructure"
        
        async def execute_task(task_data):
            task_type = task_data.get("type", "unknown")
            
            if task_type == "setup_repository":
                return {
                    "repository_ready": True,
                    "infrastructure_setup": {
                        "repository": {"url": "https://github.com/test/repo", "branches": ["main", "develop"]},
                        "cicd_pipeline": {"status": "configured", "estimated_build_time": "8 minutes"},
                        "environments": {"dev": "ready", "staging": "ready", "prod": "ready"},
                        "monitoring": {"dashboards": "configured", "alerts": "enabled"}
                    },
                    "context": {"infrastructure_quality": "enterprise_grade"}
                }
                
        agent.execute_task = execute_task
        return agent
        
    def _create_mock_qa_engineer(self):
        """Create mock QA Engineer agent"""
        agent = AsyncMock()
        agent.agent_id = "qa-engineer-quality"
        
        async def execute_task(task_data):
            task_type = task_data.get("type", "unknown")
            
            if task_type == "run_test_suite":
                return {
                    "test_suite_completed": True,
                    "overall_success": True,
                    "test_results": {
                        "unit": {"passed": True, "coverage": 87.5},
                        "integration": {"passed": True, "coverage": 78.2},
                        "security": {"passed": True, "vulnerabilities": 0}
                    },
                    "context": {"test_quality": "high", "coverage_sufficient": True}
                }
            elif task_type == "validate_quality_gates":
                # Use test data to determine pass/fail
                test_coverage = task_data.get("test_coverage", 85.0)
                security_scan = task_data.get("security_scan", {})
                
                passed = (test_coverage >= 80.0 and 
                         security_scan.get("critical_vulnerabilities", 0) == 0 and
                         security_scan.get("high_vulnerabilities", 0) == 0)
                
                return {
                    "overall_passed": passed,
                    "gate_results": {
                        "code_coverage": {"passed": test_coverage >= 80.0, "score": min(test_coverage/90.0, 1.0)},
                        "security_scan": {"passed": security_scan.get("high_vulnerabilities", 0) == 0, "score": 0.8}
                    },
                    "quality_score": 0.85 if passed else 0.65,
                    "context": {"quality_gates_status": "passed" if passed else "failed"}
                }
            elif task_type == "create_test_plan":
                return {
                    "test_plan_created": True,
                    "test_strategy": "comprehensive",
                    "frameworks_configured": ["pytest", "playwright", "k6"],
                    "context": {"testing_framework": "enterprise_grade"}
                }
                
        agent.execute_task = execute_task
        return agent


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])