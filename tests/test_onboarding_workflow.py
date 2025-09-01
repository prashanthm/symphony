#!/usr/bin/env python3
"""
Test Suite for Symphony Onboarding Workflow

Comprehensive tests for the customer onboarding workflow system
including workflow management, state persistence, and validation.
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

# Test imports - adjust based on actual package structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "libs" / "symphony-core" / "src"))

from symphony_core.onboarding.workflow_manager import (
    WorkflowManager, WorkflowStatus, StepStatus, WorkflowStep, WorkflowState,
    create_workflow_manager
)
from symphony_core.onboarding.validation import (
    ValidationEngine, ValidationStatus, ValidationLevel, ValidationResult,
    create_validation_engine
)
from symphony_core.auth.auth_manager import (
    AuthenticationManager, AuthToken, create_auth_manager
)


class TestWorkflowManager:
    """Test cases for WorkflowManager"""
    
    @pytest.fixture
    def temp_symphony_root(self):
        """Create temporary symphony root directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def workflow_manager(self, temp_symphony_root):
        """Create workflow manager with temporary directory"""
        return create_workflow_manager(temp_symphony_root)
    
    def test_create_workflow_manager(self, temp_symphony_root):
        """Test workflow manager creation"""
        manager = create_workflow_manager(temp_symphony_root)
        assert isinstance(manager, WorkflowManager)
        assert manager.symphony_root == Path(temp_symphony_root)
    
    def test_create_workflow(self, workflow_manager):
        """Test workflow creation"""
        workflow_id = workflow_manager.create_workflow(
            customer_name="test-customer",
            package_type="startup",
            industry="technology"
        )
        
        assert workflow_id is not None
        assert workflow_id.startswith("test-customer-")
        
        # Check workflow state file exists
        state_file = workflow_manager.workflows_dir / f"{workflow_id}.json"
        assert state_file.exists()
        
        # Load and verify workflow state
        with open(state_file, 'r') as f:
            workflow_data = json.load(f)
        
        assert workflow_data['workflow_id'] == workflow_id
        assert workflow_data['customer_name'] == "test-customer"
        assert workflow_data['package_type'] == "startup"
        assert workflow_data['industry'] == "technology"
        assert workflow_data['status'] == WorkflowStatus.PENDING.value
    
    def test_get_workflow_state(self, workflow_manager):
        """Test workflow state retrieval"""
        workflow_id = workflow_manager.create_workflow("test-customer")
        state = workflow_manager._load_workflow_state(workflow_id)
        
        assert state is not None
        assert isinstance(state, WorkflowState)
        assert state.workflow_id == workflow_id
        assert state.customer_name == "test-customer"
        assert state.status == WorkflowStatus.PENDING
    
    def test_list_workflows(self, workflow_manager):
        """Test workflow listing"""
        # Create multiple workflows
        workflow_id1 = workflow_manager.create_workflow("customer1", "startup")
        workflow_id2 = workflow_manager.create_workflow("customer2", "enterprise")
        
        workflows = workflow_manager.list_workflows()
        workflow_ids = [w['workflow_id'] for w in workflows]
        
        assert workflow_id1 in workflow_ids
        assert workflow_id2 in workflow_ids
        assert len(workflows) >= 2
    
    @pytest.mark.asyncio
    async def test_start_workflow(self, workflow_manager):
        """Test workflow execution start"""
        workflow_id = workflow_manager.create_workflow("test-customer")
        
        # Mock external dependencies
        with patch.object(workflow_manager, '_handle_environment_validation', new_callable=AsyncMock) as mock_env:
            mock_env.return_value = {"success": True, "message": "Environment validated"}
            
            result = await workflow_manager.start_workflow(workflow_id)
            
            assert result['success'] is True
            assert result['workflow_id'] == workflow_id
            
            # Verify workflow state updated
            state = workflow_manager._load_workflow_state(workflow_id)
            assert state.status == WorkflowStatus.IN_PROGRESS
    
    @pytest.mark.asyncio
    async def test_resume_workflow(self, workflow_manager):
        """Test workflow resume functionality"""
        workflow_id = workflow_manager.create_workflow("test-customer")
        
        # Start workflow first
        with patch.object(workflow_manager, '_handle_environment_validation', new_callable=AsyncMock) as mock_env:
            mock_env.return_value = {"success": True, "message": "Environment validated"}
            await workflow_manager.start_workflow(workflow_id)
        
        # Resume workflow
        with patch.object(workflow_manager, '_handle_customer_creation', new_callable=AsyncMock) as mock_customer:
            mock_customer.return_value = {"success": True, "message": "Customer created"}
            
            result = await workflow_manager.resume_workflow(workflow_id)
            
            assert result['success'] is True
            assert result['workflow_id'] == workflow_id
    
    def test_update_step_status(self, workflow_manager):
        """Test step status update"""
        workflow_id = workflow_manager.create_workflow("test-customer")
        
        workflow_manager.update_step_status(
            workflow_id, 
            "environment_validation", 
            StepStatus.IN_PROGRESS,
            "Validating environment..."
        )
        
        state = workflow_manager._load_workflow_state(workflow_id)
        env_step = next(s for s in state.steps if s.step_id == "environment_validation")
        
        assert env_step.status == StepStatus.IN_PROGRESS
        assert env_step.message == "Validating environment..."
        assert env_step.updated_at is not None
    
    def test_package_specific_workflow(self, workflow_manager):
        """Test package-specific workflow creation"""
        # Test enterprise package
        enterprise_id = workflow_manager.create_workflow("enterprise-corp", "enterprise")
        enterprise_state = workflow_manager.get_workflow_state(enterprise_id)
        
        # Enterprise should have all steps
        step_ids = [s.step_id for s in enterprise_state.steps]
        expected_steps = [
            "environment_validation", "customer_creation", "integration_setup",
            "agent_deployment", "go_live"
        ]
        
        for step_id in expected_steps:
            assert step_id in step_ids
        
        # Test startup package (should have same steps but different configuration)
        startup_id = workflow_manager.create_workflow("startup-corp", "startup")
        startup_state = workflow_manager.get_workflow_state(startup_id)
        
        assert len(startup_state.steps) == len(enterprise_state.steps)
    
    def test_external_template_loading(self, workflow_manager, temp_symphony_root):
        """Test loading external template files"""
        
        # Create a test template file
        template_path = Path(temp_symphony_root) / "test_template.yaml"
        template_content = """
workspace:
  name: "${customer_name} Test Workspace"
  organization:
    name: "${customer_name}"
teams:
  - name: "Engineering"
    key: "ENG"
    workflows:
      - name: "Development"
        type: "started"
projects:
  test_project:
    name: "Test Project"
    description: "Test project from template"
symphony_integration:
  agent_assignments:
    Engineering:
      - "CTO Agent"
      - "Tech Lead Agent"
"""
        
        with open(template_path, 'w') as f:
            f.write(template_content)
        
        # Test creating workflow with external template
        workflow_id = workflow_manager.create_workflow(
            "test-customer", 
            "enterprise", 
            "technology",
            template_file=str(template_path)
        )
        
        assert workflow_id is not None
        
        # Verify workflow state
        state = workflow_manager._load_workflow_state(workflow_id)
        assert state.customer_name == "test-customer"
        assert state.package_type == "enterprise"
        
        # Check for enhanced integration setup step
        integration_step = next(s for s in state.steps if s.step_id == "setup_integrations")
        assert integration_step is not None
        assert "Using Linear enterprise template" in integration_step.description
        assert hasattr(integration_step, 'metadata')
        assert integration_step.metadata is not None
        assert 'linear_template' in integration_step.metadata
        
        # Verify template data is preserved
        template_data = integration_step.metadata['linear_template']
        assert 'workspace' in template_data
        assert 'teams' in template_data
        assert template_data['workspace']['name'] == "${customer_name} Test Workspace"
    
    def test_template_file_not_found(self, workflow_manager):
        """Test handling of missing template files"""
        
        # Should fall back to built-in templates
        workflow_id = workflow_manager.create_workflow(
            "test-customer",
            "startup",
            "general", 
            template_file="/nonexistent/template.yaml"
        )
        
        assert workflow_id is not None
        
        # Should use built-in template
        state = workflow_manager._load_workflow_state(workflow_id)
        assert len(state.steps) > 0
    
    def test_workflow_template_format(self, workflow_manager, temp_symphony_root):
        """Test explicit workflow template format"""
        
        # Create workflow template file
        template_path = Path(temp_symphony_root) / "workflow_template.yaml"
        template_content = """
workflow_template:
  package_type: enterprise
  steps:
    - id: custom_validation
      name: "Custom Validation Step"
      description: "Custom validation from template"
      required: true
      estimated_duration: 600
      dependencies: []
    - id: custom_setup
      name: "Custom Setup Step"
      description: "Custom setup step"
      required: true
      estimated_duration: 300
      dependencies: ["custom_validation"]
"""
        
        with open(template_path, 'w') as f:
            f.write(template_content)
        
        workflow_id = workflow_manager.create_workflow(
            "template-test", 
            "enterprise",
            "general",
            template_file=str(template_path)
        )
        
        state = workflow_manager._load_workflow_state(workflow_id)
        
        # Should have exactly the steps from template
        assert len(state.steps) == 2
        
        step_ids = [s.step_id for s in state.steps]
        assert "custom_validation" in step_ids
        assert "custom_setup" in step_ids
        
        # Check step properties
        validation_step = next(s for s in state.steps if s.step_id == "custom_validation")
        assert validation_step.name == "Custom Validation Step"
        assert validation_step.estimated_duration == 600
        assert validation_step.required is True


class TestValidationEngine:
    """Test cases for ValidationEngine"""
    
    @pytest.fixture
    def temp_symphony_root(self):
        """Create temporary symphony root directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create required directory structure
            temp_path = Path(temp_dir)
            (temp_path / 'libs' / 'symphony-core').mkdir(parents=True)
            (temp_path / 'libs' / 'symphony-integrations').mkdir(parents=True)
            (temp_path / 'apps' / 'symphony-cli').mkdir(parents=True)
            (temp_path / '.symphony').mkdir(parents=True)
            
            yield temp_dir
    
    @pytest.fixture
    def validation_engine(self, temp_symphony_root):
        """Create validation engine with temporary directory"""
        return create_validation_engine(temp_symphony_root)
    
    def test_create_validation_engine(self, temp_symphony_root):
        """Test validation engine creation"""
        engine = create_validation_engine(temp_symphony_root)
        assert isinstance(engine, ValidationEngine)
        assert engine.symphony_root == Path(temp_symphony_root)
    
    def test_validation_suites_loaded(self, validation_engine):
        """Test that validation suites are properly loaded"""
        assert len(validation_engine.validation_suites) > 0
        
        # Check for required suites
        required_suites = [
            'environment_checks',
            'customer_setup_checks', 
            'integration_checks',
            'agent_deployment_checks',
            'deployment_validation'
        ]
        
        for suite_id in required_suites:
            assert suite_id in validation_engine.validation_suites
    
    @pytest.mark.asyncio
    async def test_python_version_check(self, validation_engine):
        """Test Python version validation"""
        result = await validation_engine._check_python_version({})
        
        # Should pass since we're running in a Python environment
        assert result['status'] == 'passed'
        assert 'Python' in result['message']
        assert 'current' in result['details']
        assert 'required' in result['details']
    
    @pytest.mark.asyncio
    async def test_symphony_structure_check(self, validation_engine):
        """Test Symphony directory structure validation"""
        result = await validation_engine._check_symphony_structure({})
        
        # Should pass since we created the structure in the fixture
        assert result['status'] == 'passed'
        assert 'structure is complete' in result['message']
        assert 'checked_directories' in result['details']
    
    @pytest.mark.asyncio
    async def test_customer_name_validation(self, validation_engine):
        """Test customer name format validation"""
        # Test valid name
        context = {'customer_name': 'valid-customer-name'}
        result = await validation_engine._validate_customer_name(context)
        assert result['status'] == 'passed'
        
        # Test invalid name (spaces)
        context = {'customer_name': 'invalid customer name'}
        result = await validation_engine._validate_customer_name(context)
        assert result['status'] == 'failed'
        
        # Test empty name
        context = {'customer_name': ''}
        result = await validation_engine._validate_customer_name(context)
        assert result['status'] == 'failed'
    
    @pytest.mark.asyncio
    async def test_package_type_validation(self, validation_engine):
        """Test package type validation"""
        # Test valid package
        context = {'package_type': 'startup'}
        result = await validation_engine._validate_package_type(context)
        assert result['status'] == 'passed'
        
        # Test invalid package
        context = {'package_type': 'invalid-package'}
        result = await validation_engine._validate_package_type(context)
        assert result['status'] == 'failed'
    
    @pytest.mark.asyncio
    async def test_run_validation_suite(self, validation_engine):
        """Test running a complete validation suite"""
        context = {
            'customer_name': 'test-customer',
            'package_type': 'startup'
        }
        
        result = await validation_engine.run_validation_suite('customer_setup_checks', context)
        
        assert 'suite_id' in result
        assert 'overall_status' in result
        assert 'summary' in result
        assert 'results' in result
        
        # Should have some checks
        assert result['summary']['total_checks'] > 0
    
    @pytest.mark.asyncio
    async def test_validate_onboarding_phase(self, validation_engine):
        """Test onboarding phase validation"""
        result = await validation_engine.validate_onboarding_phase(
            'customer_creation',
            'test-customer',
            'startup',
            {'industry': 'technology'}
        )
        
        assert result['overall_status'] in ['passed', 'failed', 'warning']
        assert 'summary' in result
        assert 'results' in result
    
    def test_register_custom_validator(self, validation_engine):
        """Test custom validator registration"""
        def custom_validator(context):
            return {'status': 'passed', 'message': 'Custom validation passed'}
        
        validation_engine.register_custom_validator('custom_test', custom_validator)
        assert 'custom_test' in validation_engine.custom_validators
    
    def test_save_validation_report(self, validation_engine):
        """Test validation report saving"""
        test_result = {
            'customer_name': 'test-customer',
            'overall_status': 'passed',
            'summary': {'total_checks': 1, 'passed': 1}
        }
        
        report_file = validation_engine.save_validation_report(test_result)
        
        assert report_file.exists()
        assert report_file.name.startswith('validation_report_test-customer_')
        
        # Verify content
        with open(report_file, 'r') as f:
            saved_result = json.load(f)
        
        assert saved_result['customer_name'] == 'test-customer'
        assert saved_result['overall_status'] == 'passed'


class TestAuthenticationManager:
    """Test cases for AuthenticationManager"""
    
    @pytest.fixture
    def temp_symphony_root(self):
        """Create temporary symphony root directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def auth_manager(self, temp_symphony_root):
        """Create authentication manager with temporary directory"""
        return create_auth_manager(temp_symphony_root)
    
    def test_create_auth_manager(self, temp_symphony_root):
        """Test authentication manager creation"""
        manager = create_auth_manager(temp_symphony_root)
        assert isinstance(manager, AuthenticationManager)
        assert manager.symphony_root == Path(temp_symphony_root)
    
    def test_supported_services(self, auth_manager):
        """Test supported services configuration"""
        services = auth_manager.supported_services
        
        required_services = ['linear', 'github', 'slack', 'hubspot']
        for service in required_services:
            assert service in services
            assert 'name' in services[service]
            assert 'token_type' in services[service]
            assert 'scopes' in services[service]
    
    def test_store_and_retrieve_token(self, auth_manager):
        """Test token storage and retrieval"""
        # Store a test token
        success = auth_manager.store_token(
            service='linear',
            access_token='test-linear-token-12345',
            scopes=['read', 'write']
        )
        
        assert success is True
        
        # Retrieve the token
        token = auth_manager.get_token('linear')
        
        assert token is not None
        assert isinstance(token, AuthToken)
        assert token.service == 'linear'
        assert token.access_token == 'test-linear-token-12345'
        assert 'read' in token.scopes
        assert 'write' in token.scopes
    
    def test_is_authenticated(self, auth_manager):
        """Test authentication status check"""
        # Should not be authenticated initially
        assert auth_manager.is_authenticated('linear') is False
        
        # Store token and check again
        auth_manager.store_token('linear', 'test-token')
        assert auth_manager.is_authenticated('linear') is True
    
    def test_revoke_token(self, auth_manager):
        """Test token revocation"""
        # Store token first
        auth_manager.store_token('github', 'test-github-token')
        assert auth_manager.is_authenticated('github') is True
        
        # Revoke token
        success = auth_manager.revoke_token('github')
        assert success is True
        assert auth_manager.is_authenticated('github') is False
    
    def test_list_authenticated_services(self, auth_manager):
        """Test listing authenticated services"""
        # Store tokens for multiple services
        auth_manager.store_token('linear', 'test-linear-token')
        auth_manager.store_token('github', 'test-github-token')
        
        services = auth_manager.list_authenticated_services()
        
        # Should have entries for all supported services
        service_names = [s['service'] for s in services]
        assert 'linear' in service_names
        assert 'github' in service_names
        assert 'slack' in service_names
        assert 'hubspot' in service_names
        
        # Check authentication status
        linear_service = next(s for s in services if s['service'] == 'linear')
        github_service = next(s for s in services if s['service'] == 'github')
        slack_service = next(s for s in services if s['service'] == 'slack')
        
        assert linear_service['authenticated'] is True
        assert github_service['authenticated'] is True
        assert slack_service['authenticated'] is False
    
    def test_get_service_info(self, auth_manager):
        """Test service information retrieval"""
        info = auth_manager.get_service_info('linear')
        
        assert info is not None
        assert info['name'] == 'Linear'
        assert info['token_type'] == 'personal_access_token'
        assert 'authenticated' in info
        
        # Test with authentication
        auth_manager.store_token('linear', 'test-token')
        info = auth_manager.get_service_info('linear')
        assert info['authenticated'] is True
        assert 'token_info' in info
    
    def test_export_config_template(self, auth_manager):
        """Test configuration template export"""
        template = auth_manager.export_config_template()
        
        assert 'environment_variables' in template
        assert 'authentication_guide' in template
        assert 'services' in template
        
        # Check environment variables
        env_vars = template['environment_variables']
        assert 'LINEAR_TOKEN' in env_vars
        assert 'GITHUB_TOKEN' in env_vars
        
        # Check authentication guide
        auth_guide = template['authentication_guide']
        assert 'linear' in auth_guide
        assert 'github' in auth_guide
        
        linear_guide = auth_guide['linear']
        assert 'name' in linear_guide
        assert 'token_type' in linear_guide
        assert 'required_scopes' in linear_guide


class TestIntegration:
    """Integration tests for the complete onboarding system"""
    
    @pytest.fixture
    def temp_symphony_root(self):
        """Create temporary symphony root with full structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create comprehensive directory structure
            temp_path = Path(temp_dir)
            (temp_path / 'libs' / 'symphony-core' / 'src').mkdir(parents=True)
            (temp_path / 'libs' / 'symphony-integrations' / 'src').mkdir(parents=True)
            (temp_path / 'libs' / 'symphony-templates' / 'src' / 'symphony_templates' / 'packages').mkdir(parents=True)
            (temp_path / 'apps' / 'symphony-cli' / 'src').mkdir(parents=True)
            (temp_path / '.symphony' / 'workflows').mkdir(parents=True)
            (temp_path / '.symphony' / 'auth').mkdir(parents=True)
            (temp_path / '.symphony' / 'validation').mkdir(parents=True)
            
            # Create template files
            template_dir = temp_path / 'libs' / 'symphony-templates' / 'src' / 'symphony_templates' / 'packages'
            for package in ['startup', 'smb', 'enterprise', 'global']:
                template_file = template_dir / f'{package}.yaml'
                template_file.write_text(f'# {package} template\npackage_type: {package}\n')
            
            yield temp_dir
    
    @pytest.fixture
    def managers(self, temp_symphony_root):
        """Create all managers for integration testing"""
        return {
            'workflow': create_workflow_manager(temp_symphony_root),
            'validation': create_validation_engine(temp_symphony_root),
            'auth': create_auth_manager(temp_symphony_root)
        }
    
    @pytest.mark.asyncio
    async def test_complete_onboarding_flow(self, managers):
        """Test complete onboarding workflow integration"""
        workflow_mgr = managers['workflow']
        validation_engine = managers['validation']
        auth_manager = managers['auth']
        
        # 1. Create workflow
        workflow_id = workflow_mgr.create_workflow(
            customer_name="integration-test-corp",
            package_type="startup",
            industry="technology"
        )
        
        assert workflow_id is not None
        
        # 2. Set up authentication (mock)
        auth_manager.store_token('linear', 'test-linear-token')
        auth_manager.store_token('github', 'test-github-token')
        
        # 3. Run validation for customer creation phase
        validation_result = await validation_engine.validate_onboarding_phase(
            'customer_creation',
            'integration-test-corp',
            'startup'
        )
        
        assert validation_result['overall_status'] in ['passed', 'warning']
        
        # 4. Start workflow with mocked handlers
        with patch.object(workflow_mgr, '_handle_environment_validation', new_callable=AsyncMock) as mock_env:
            mock_env.return_value = {"success": True, "message": "Environment validated"}
            
            start_result = await workflow_mgr.start_workflow(workflow_id)
            assert start_result['success'] is True
        
        # 5. Check final state
        final_state = workflow_mgr.get_workflow_state(workflow_id)
        assert final_state.status == WorkflowStatus.IN_PROGRESS
        
        # Find completed environment validation step
        env_step = next(s for s in final_state.steps if s.step_id == "environment_validation")
        assert env_step.status == StepStatus.COMPLETED
    
    def test_validation_and_auth_integration(self, managers):
        """Test validation engine with authentication manager"""
        validation_engine = managers['validation']
        auth_manager = managers['auth']
        
        # Store authentication
        auth_manager.store_token('linear', 'test-linear-token')
        
        # Validation should detect authentication
        assert auth_manager.is_authenticated('linear') is True
        
        # Service info should reflect authentication status
        service_info = auth_manager.get_service_info('linear')
        assert service_info['authenticated'] is True
    
    def test_workflow_persistence_and_recovery(self, managers):
        """Test workflow state persistence and recovery"""
        workflow_mgr = managers['workflow']
        
        # Create workflow
        workflow_id = workflow_mgr.create_workflow("persistence-test")
        
        # Update step status
        workflow_mgr.update_step_status(
            workflow_id,
            "environment_validation",
            StepStatus.IN_PROGRESS,
            "Testing persistence"
        )
        
        # Create new manager instance (simulating restart)
        new_workflow_mgr = create_workflow_manager(workflow_mgr.symphony_root)
        
        # Should be able to retrieve the workflow
        recovered_state = new_workflow_mgr.get_workflow_state(workflow_id)
        
        assert recovered_state is not None
        assert recovered_state.customer_name == "persistence-test"
        
        # Check step status was persisted
        env_step = next(s for s in recovered_state.steps if s.step_id == "environment_validation")
        assert env_step.status == StepStatus.IN_PROGRESS
        assert env_step.message == "Testing persistence"


# Test runner configuration
if __name__ == '__main__':
    # Run tests with pytest
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, '-m', 'pytest', __file__, '-v', '--tb=short'
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    sys.exit(result.returncode)