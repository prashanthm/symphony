"""
QA Engineer Agent - Execution Specialist Level  
Role: Testing, quality validation, security scanning, test automation
"""

from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime, timedelta

from symphony_core.agents.base_agent import BaseAgent, AgentCapability, create_agent_capability, AgentSchedule
from symphony_core.agents.base_agent import HandoffContext, HandoffStatus


class QAEngineerAgent(BaseAgent):
    """
    QA Engineer Agent - Execution Specialist Level
    
    Responsible for:
    - Comprehensive test strategy design and execution
    - Quality gate enforcement and validation
    - Security scanning and vulnerability assessment
    - Test automation framework development and maintenance
    """
    
    def __init__(self, customer_id: Optional[str] = None):
        # Define QA engineering capabilities
        capabilities = [
            create_agent_capability(
                "test_strategy_design",
                "Design comprehensive testing strategies for applications and systems",
                "critical",
                performance_target=97.0
            ),
            create_agent_capability(
                "automated_testing", 
                "Develop and maintain automated test suites and frameworks",
                "critical",
                performance_target=98.5
            ),
            create_agent_capability(
                "quality_gate_validation",
                "Validate and enforce quality gates across development workflows",
                "critical",
                performance_target=99.0
            ),
            create_agent_capability(
                "security_scanning",
                "Perform comprehensive security scans and vulnerability assessments",
                "critical",
                performance_target=96.5
            ),
            create_agent_capability(
                "performance_testing",
                "Execute performance and load testing scenarios",
                "high", 
                performance_target=94.0
            ),
            create_agent_capability(
                "test_data_management",
                "Manage test data creation, maintenance, and privacy compliance",
                "medium",
                performance_target=92.0
            ),
            create_agent_capability(
                "defect_analysis", 
                "Analyze defects, root causes, and quality trends",
                "high",
                performance_target=95.0
            )
        ]
        
        # QA schedule - aligned with development cycles
        schedule = AgentSchedule(
            max_concurrent_tasks=8,
            business_hours_only=False,  # Testing may run during off-hours
            preferred_hours=(8, 20),  # Development hours
            escalation_hours=1.0  # 1 hour response for quality issues
        )
        
        super().__init__(
            agent_id="qa-engineer-quality",
            name="QA Engineer", 
            role="Quality Assurance and Testing Specialist",
            category="specialists",
            capabilities=capabilities,
            schedule=schedule,
            customer_id=customer_id
        )
        
        # QA state management
        self.test_suites: Dict[str, Dict[str, Any]] = {}
        self.quality_metrics: Dict[str, Dict[str, float]] = {}
        self.security_scan_results: Dict[str, Dict[str, Any]] = {}
        self.defect_tracking: Dict[str, Dict[str, Any]] = {}
        self.testing_frameworks: Dict[str, Dict[str, Any]] = {}
        
    async def _initialize_agent(self) -> None:
        """Initialize QA engineer with testing frameworks and standards"""
        await super()._initialize_agent()
        
        # Initialize testing frameworks
        self.testing_frameworks = {
            "unit_testing": {
                "purpose": "Individual component testing",
                "tools": ["pytest", "jest", "junit"],
                "coverage_target": 85,
                "execution_time": "fast"
            },
            "integration_testing": {
                "purpose": "Component interaction testing",
                "tools": ["pytest", "testcontainers", "postman"],
                "coverage_target": 75,
                "execution_time": "medium"
            },
            "end_to_end_testing": {
                "purpose": "Full user workflow testing",
                "tools": ["playwright", "cypress", "selenium"],
                "coverage_target": 60,
                "execution_time": "slow"
            },
            "performance_testing": {
                "purpose": "System performance validation",
                "tools": ["k6", "locust", "jmeter"],
                "metrics": ["response_time", "throughput", "resource_utilization"],
                "execution_time": "variable"
            }
        }
        
        # Quality gate standards
        self.quality_gates = {
            "code_coverage": {
                "minimum_threshold": 80.0,
                "target_threshold": 90.0,
                "measurement": "line_coverage"
            },
            "security_scan": {
                "critical_vulnerabilities": 0,
                "high_vulnerabilities": 0,
                "medium_vulnerabilities": 5,
                "tools": ["codeql", "semgrep", "dependency_check"]
            },
            "performance_benchmarks": {
                "response_time_p95": 500,  # milliseconds
                "memory_usage_limit": "512MB",
                "cpu_utilization_limit": 70  # percentage
            },
            "code_quality": {
                "complexity_limit": 10,
                "duplication_limit": 3.0,  # percentage
                "maintainability_index": 80
            }
        }
        
        # Security scanning configuration
        self.security_scan_config = {
            "static_analysis": {
                "enabled": True,
                "tools": ["codeql", "semgrep", "bandit"],
                "severity_threshold": "medium"
            },
            "dependency_scanning": {
                "enabled": True,
                "tools": ["npm_audit", "safety", "snyk"],
                "exclude_dev_dependencies": True
            },
            "secrets_scanning": {
                "enabled": True,
                "tools": ["gitleaks", "truffleHog", "detect_secrets"],
                "custom_patterns": True
            },
            "container_scanning": {
                "enabled": True,
                "tools": ["trivy", "clair", "anchore"],
                "base_image_validation": True
            }
        }
        
        self.logger.info(f"QA Engineer {self.name} initialized with testing frameworks and quality gates")
        
    async def _execute_task_impl(self, task_data: Dict[str, Any]) -> Any:
        """Execute QA engineering tasks"""
        task_type = task_data.get("type", "unknown")
        
        if task_type == "run_test_suite":
            return await self._run_test_suite(task_data)
        elif task_type == "validate_quality_gates":
            return await self._validate_quality_gates(task_data)
        elif task_type == "security_scan":
            return await self._perform_security_scan(task_data)
        elif task_type == "performance_test":
            return await self._execute_performance_test(task_data)
        elif task_type == "analyze_defects":
            return await self._analyze_defects(task_data)
        elif task_type == "create_test_plan":
            return await self._create_test_plan(task_data)
        elif task_type == "generate_test_report":
            return await self._generate_test_report(task_data)
        else:
            raise ValueError(f"Unknown QA task type: {task_type}")
            
    async def _process_handoff(self, handoff_context: HandoffContext) -> bool:
        """Process handoff with quality validation"""
        try:
            # Extract quality requirements
            quality_requirements = handoff_context.context_data.get("quality_requirements", {})
            testing_scope = handoff_context.context_data.get("testing_scope", "standard")
            
            # Perform quality assessment
            quality_assessment = await self._assess_quality_requirements(quality_requirements, testing_scope)
            
            if quality_assessment["quality_risk"] == "high":
                # Flag for enhanced testing
                handoff_context.context_data["enhanced_testing_required"] = True
                handoff_context.context_data["quality_concerns"] = quality_assessment["concerns"]
                handoff_context.context_data["recommended_testing"] = quality_assessment["recommendations"]
                
                self.logger.warning(f"High quality risk detected in handoff {handoff_context.handoff_id}")
            
            # Add QA context and testing strategy
            qa_context = await self._add_qa_context(handoff_context)
            handoff_context.context_data.update(qa_context)
            
            # Track handoff for quality metrics
            await self._track_quality_handoff(handoff_context)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing QA handoff {handoff_context.handoff_id}: {str(e)}")
            return False
            
    async def _run_test_suite(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive test suite"""
        test_config = task_data.get("test_config", {})
        test_types = test_config.get("test_types", ["unit", "integration"])
        application = test_config.get("application", "default")
        
        # Execute test suites
        test_results = {}
        overall_success = True
        
        for test_type in test_types:
            if test_type in self.testing_frameworks:
                result = await self._execute_test_type(test_type, application, test_config)
                test_results[test_type] = result
                
                if not result["passed"]:
                    overall_success = False
        
        # Generate consolidated report
        consolidated_report = await self._generate_consolidated_test_report(test_results)
        
        # Update quality metrics
        await self._update_quality_metrics(application, test_results)
        
        return {
            "test_suite_completed": True,
            "overall_success": overall_success,
            "test_results": test_results,
            "consolidated_report": consolidated_report,
            "quality_metrics": self._calculate_quality_metrics(test_results),
            "recommendations": self._generate_test_recommendations(test_results)
        }
        
    async def _validate_quality_gates(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all quality gates for a release"""
        artifact_data = task_data.get("artifact", {})
        gate_config = task_data.get("gates", self.quality_gates)
        
        gate_results = {}
        overall_passed = True
        
        # Validate each quality gate
        for gate_name, gate_criteria in gate_config.items():
            gate_result = await self._validate_single_quality_gate(gate_name, gate_criteria, artifact_data)
            gate_results[gate_name] = gate_result
            
            if not gate_result["passed"]:
                overall_passed = False
        
        # Create quality gate report
        quality_report = {
            "overall_passed": overall_passed,
            "gate_results": gate_results,
            "quality_score": self._calculate_overall_quality_score(gate_results),
            "blockers": [
                gate for gate, result in gate_results.items() 
                if not result["passed"] and result.get("blocking", True)
            ],
            "warnings": [
                gate for gate, result in gate_results.items()
                if result.get("warning", False)
            ]
        }
        
        if not overall_passed:
            quality_report["remediation_plan"] = await self._create_quality_remediation_plan(gate_results)
        
        return quality_report
        
    async def _perform_security_scan(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive security scanning"""
        scan_config = task_data.get("scan_config", self.security_scan_config)
        target = task_data.get("target", {})
        scan_types = task_data.get("scan_types", ["static_analysis", "dependency_scanning", "secrets_scanning"])
        
        scan_results = {}
        overall_security_score = 1.0
        critical_issues = []
        
        # Execute security scans
        for scan_type in scan_types:
            if scan_type in scan_config:
                result = await self._execute_security_scan(scan_type, target, scan_config[scan_type])
                scan_results[scan_type] = result
                
                # Update overall security assessment
                overall_security_score = min(overall_security_score, result["security_score"])
                
                # Collect critical issues
                critical_issues.extend(result.get("critical_issues", []))
        
        # Security assessment
        security_assessment = {
            "overall_security_score": overall_security_score,
            "security_level": self._determine_security_level(overall_security_score),
            "critical_issues_count": len(critical_issues),
            "requires_remediation": overall_security_score < 0.8 or len(critical_issues) > 0,
            "scan_results": scan_results,
            "critical_issues": critical_issues
        }
        
        if security_assessment["requires_remediation"]:
            security_assessment["remediation_priority"] = self._prioritize_security_issues(critical_issues)
            security_assessment["estimated_fix_time"] = self._estimate_security_fix_time(critical_issues)
        
        # Store scan results for tracking
        scan_id = f"security_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.security_scan_results[scan_id] = security_assessment
        
        return {
            "scan_completed": True,
            "scan_id": scan_id,
            "security_assessment": security_assessment,
            "compliance_status": self._check_compliance_status(security_assessment),
            "next_scan_recommendation": self._recommend_next_scan(security_assessment)
        }
        
    async def _execute_security_scan(self, scan_type: str, target: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific type of security scan"""
        if scan_type == "static_analysis":
            return await self._run_static_analysis_scan(target, config)
        elif scan_type == "dependency_scanning":
            return await self._run_dependency_scan(target, config)
        elif scan_type == "secrets_scanning":
            return await self._run_secrets_scan(target, config)
        elif scan_type == "container_scanning":
            return await self._run_container_scan(target, config)
        else:
            return {
                "scan_type": scan_type,
                "success": False,
                "error": f"Unknown scan type: {scan_type}",
                "security_score": 0.0
            }
            
    async def _run_static_analysis_scan(self, target: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Run static code analysis security scan"""
        # Simulated static analysis results
        findings = [
            {
                "severity": "medium",
                "category": "injection",
                "description": "Potential SQL injection vulnerability",
                "file": "src/database.py",
                "line": 42,
                "cwe": "CWE-89"
            },
            {
                "severity": "low", 
                "category": "crypto",
                "description": "Weak cryptographic hash function",
                "file": "src/auth.py",
                "line": 15,
                "cwe": "CWE-327"
            }
        ]
        
        # Calculate security score based on findings
        severity_weights = {"critical": 1.0, "high": 0.8, "medium": 0.4, "low": 0.1}
        total_weight = sum(severity_weights[finding["severity"]] for finding in findings)
        security_score = max(0.0, 1.0 - (total_weight / 10.0))  # Normalize to 0-1
        
        return {
            "scan_type": "static_analysis",
            "success": True,
            "findings_count": len(findings),
            "findings": findings,
            "security_score": security_score,
            "critical_issues": [f for f in findings if f["severity"] in ["critical", "high"]],
            "tools_used": config.get("tools", [])
        }
        
    async def _execute_performance_test(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute performance testing scenarios"""
        test_config = task_data.get("performance_config", {})
        test_scenarios = test_config.get("scenarios", ["load_test", "stress_test"])
        target_application = test_config.get("application", "default")
        
        performance_results = {}
        overall_performance_score = 1.0
        
        # Execute performance test scenarios
        for scenario in test_scenarios:
            result = await self._run_performance_scenario(scenario, target_application, test_config)
            performance_results[scenario] = result
            overall_performance_score = min(overall_performance_score, result["performance_score"])
        
        # Performance assessment
        performance_assessment = {
            "overall_performance_score": overall_performance_score,
            "performance_level": self._determine_performance_level(overall_performance_score),
            "test_results": performance_results,
            "bottlenecks_identified": self._identify_performance_bottlenecks(performance_results),
            "recommendations": self._generate_performance_recommendations(performance_results)
        }
        
        return {
            "performance_test_completed": True,
            "performance_assessment": performance_assessment,
            "meets_sla": overall_performance_score >= 0.8,
            "optimization_required": overall_performance_score < 0.7
        }
        
    def _calculate_overall_quality_score(self, gate_results: Dict[str, Dict[str, Any]]) -> float:
        """Calculate overall quality score from gate results"""
        if not gate_results:
            return 0.0
            
        total_score = sum(
            result.get("score", 0.0) 
            for result in gate_results.values()
        )
        
        return total_score / len(gate_results)
        
    def _determine_security_level(self, security_score: float) -> str:
        """Determine security level based on score"""
        if security_score >= 0.95:
            return "excellent"
        elif security_score >= 0.8:
            return "good"
        elif security_score >= 0.6:
            return "acceptable"
        else:
            return "needs_improvement"
            
    async def _validate_single_quality_gate(self, gate_name: str, criteria: Dict[str, Any], artifact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single quality gate"""
        if gate_name == "code_coverage":
            return await self._validate_coverage_gate(criteria, artifact_data)
        elif gate_name == "security_scan":
            return await self._validate_security_gate(criteria, artifact_data)
        elif gate_name == "performance_benchmarks":
            return await self._validate_performance_gate(criteria, artifact_data)
        elif gate_name == "code_quality":
            return await self._validate_code_quality_gate(criteria, artifact_data)
        else:
            return {
                "passed": False,
                "score": 0.0,
                "error": f"Unknown quality gate: {gate_name}"
            }
            
    async def _validate_coverage_gate(self, criteria: Dict[str, Any], artifact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate code coverage quality gate"""
        current_coverage = artifact_data.get("test_coverage", 0.0)
        minimum_threshold = criteria.get("minimum_threshold", 80.0)
        target_threshold = criteria.get("target_threshold", 90.0)
        
        passed = current_coverage >= minimum_threshold
        score = min(current_coverage / target_threshold, 1.0)
        
        return {
            "passed": passed,
            "score": score,
            "current_coverage": current_coverage,
            "minimum_required": minimum_threshold,
            "target": target_threshold,
            "details": f"Coverage: {current_coverage:.1f}% (Required: {minimum_threshold:.1f}%)"
        }