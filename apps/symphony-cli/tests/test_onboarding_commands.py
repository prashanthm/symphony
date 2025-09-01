#!/usr/bin/env python3
"""
Comprehensive tests for Symphony CLI onboarding commands

Test-driven development for the onboarding workflow covering:
- Start command (with and without external templates)
- Resume command (with proper error handling)
- Status command (workflow listing and details)
- Validate command (configuration validation)
- Validate-template command (external template validation)
- Workflow state management and persistence
- External template integration and processing
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import yaml
from click.testing import CliRunner

# Import onboarding commands
try:
    from symphony_cli.commands.onboarding_commands import onboard
    from symphony_core.onboarding.workflow_manager import WorkflowManager, WorkflowStatus
    ONBOARDING_AVAILABLE = True
except ImportError:
    ONBOARDING_AVAILABLE = False


@pytest.fixture
def cli_runner():
    """Fixture providing Click CLI test runner"""
    return CliRunner()


@pytest.fixture
def sample_external_template():
    """Fixture providing external template file"""
    template_data = {
        'organization': {
            'customer_name': 'External Corp',
            'industry': 'technology',
            'size': 'enterprise',
            'regions': ['us-east-1']
        },
        'workspace': {
            'name': 'External Corp Workspace',
            'description': 'External template workspace'
        },
        'teams': [
            {
                'name': 'Engineering',
                'key': 'ENG',
                'description': 'Engineering team',
                'workflows': [
                    {'name': 'Todo', 'type': 'unstarted'},
                    {'name': 'In Progress', 'type': 'started'},
                    {'name': 'Done', 'type': 'completed'}
                ]
            }
        ],
        'initiatives': [
            {
                'name': 'Platform Development',
                'description': 'Core platform development initiative',
                'level': 1
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(template_data, f)
        return f.name


@pytest.fixture
def invalid_template_file():
    """Fixture providing invalid template file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: content: [")
        return f.name


@pytest.fixture
def workflow_state_file():
    """Fixture providing workflow state file"""
    workflow_data = {
        'workflow_id': 'onboard-test-12345',
        'customer_name': 'Test Corp',
        'package': 'enterprise',
        'industry': 'technology',
        'status': 'in_progress',
        'current_step': 1,
        'steps': [
            {
                'name': 'create_customer',
                'status': 'completed',
                'description': 'Create customer configuration'
            },
            {
                'name': 'setup_integrations',
                'status': 'in_progress', 
                'description': 'Setup Linear and GitHub integrations'
            },
            {
                'name': 'deploy_agents',
                'status': 'pending',
                'description': 'Deploy agent ecosystem'
            }
        ],
        'template_metadata': {
            'source': 'external',
            'template_file': '/path/to/template.yaml'
        },
        'created_at': '2025-09-01T10:00:00Z',
        'updated_at': '2025-09-01T10:30:00Z'
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(workflow_data, f)
        return f.name


@pytest.mark.skipif(not ONBOARDING_AVAILABLE, reason="Onboarding commands not available")
class TestOnboardingCommandGroup:
    """Test onboarding command group"""
    
    def test_onboard_help(self, cli_runner):
        """Test onboard command group help"""
        result = cli_runner.invoke(onboard, ['--help'])
        
        assert result.exit_code == 0
        assert "Complete customer onboarding workflow" in result.output
        assert "start" in result.output
        assert "resume" in result.output
        assert "status" in result.output
        assert "validate" in result.output
        assert "validate-template" in result.output


@pytest.mark.skipif(not ONBOARDING_AVAILABLE, reason="Onboarding commands not available")
class TestStartCommand:
    """Test onboard start command"""
    
    def test_start_help(self, cli_runner):
        """Test start command help"""
        result = cli_runner.invoke(onboard, ['start', '--help'])
        
        assert result.exit_code == 0
        assert "Start comprehensive customer onboarding" in result.output
        assert "--package" in result.output
        assert "--industry" in result.output
        assert "--config-file" in result.output
        assert "--resume" in result.output
        
    def test_start_package_choices(self, cli_runner):
        """Test start command shows correct package choices"""
        result = cli_runner.invoke(onboard, ['start', '--help'])
        
        assert result.exit_code == 0
        assert "startup" in result.output
        assert "smb" in result.output
        assert "enterprise" in result.output
        assert "global" in result.output
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_start_basic_workflow(self, mock_workflow_manager_class, cli_runner):
        """Test start command with basic parameters"""
        mock_manager = Mock()
        mock_workflow = Mock()
        mock_workflow.workflow_id = 'onboard-testcorp-12345'
        mock_workflow.status = WorkflowStatus.IN_PROGRESS
        
        mock_manager.create_workflow.return_value = mock_workflow
        mock_manager.start_workflow.return_value = True
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, [
            'start', 'testcorp',
            '--package', 'enterprise',
            '--industry', 'technology'
        ])
        
        assert result.exit_code == 0
        assert "Starting onboarding for testcorp" in result.output
        assert "enterprise package" in result.output
        assert "technology industry" in result.output
        
        # Verify workflow manager was called correctly
        mock_manager.create_workflow.assert_called_once()
        call_kwargs = mock_manager.create_workflow.call_args[1]
        assert call_kwargs['customer_name'] == 'testcorp'
        assert call_kwargs['package'] == 'enterprise'
        assert call_kwargs['industry'] == 'technology'
        assert call_kwargs['template_file'] is None
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_start_with_external_template(self, mock_workflow_manager_class, cli_runner, sample_external_template):
        """Test start command with external template file"""
        mock_manager = Mock()
        mock_workflow = Mock()
        mock_workflow.workflow_id = 'onboard-external-12345'
        mock_workflow.status = WorkflowStatus.IN_PROGRESS
        
        mock_manager.create_workflow.return_value = mock_workflow
        mock_manager.start_workflow.return_value = True
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, [
            'start', 'external-corp',
            '--config-file', sample_external_template
        ])
        
        assert result.exit_code == 0
        assert "Starting onboarding for external-corp" in result.output
        assert "Using external template" in result.output
        assert sample_external_template in result.output
        
        # Verify external template was passed
        mock_manager.create_workflow.assert_called_once()
        call_kwargs = mock_manager.create_workflow.call_args[1]
        assert call_kwargs['customer_name'] == 'external-corp'
        assert call_kwargs['template_file'] == sample_external_template
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_start_interactive_package_selection(self, mock_workflow_manager_class, cli_runner):
        """Test start command with interactive package selection"""
        mock_manager = Mock()
        mock_workflow = Mock()
        mock_workflow.workflow_id = 'onboard-interactive-12345'
        mock_workflow.status = WorkflowStatus.IN_PROGRESS
        
        mock_manager.create_workflow.return_value = mock_workflow
        mock_manager.start_workflow.return_value = True
        mock_workflow_manager_class.return_value = mock_manager
        
        # Simulate user selecting package 2 (enterprise)
        result = cli_runner.invoke(onboard, ['start', 'interactive-corp'], input='2\n')
        
        assert result.exit_code == 0
        assert "Starting onboarding for interactive-corp" in result.output
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager') 
    def test_start_interactive_industry_selection(self, mock_workflow_manager_class, cli_runner):
        """Test start command with interactive industry selection"""
        mock_manager = Mock()
        mock_workflow = Mock()
        mock_workflow.workflow_id = 'onboard-industry-12345'
        mock_workflow.status = WorkflowStatus.IN_PROGRESS
        
        mock_manager.create_workflow.return_value = mock_workflow
        mock_manager.start_workflow.return_value = True
        mock_workflow_manager_class.return_value = mock_manager
        
        # Simulate user selections: package 1 (startup), industry 2 (healthcare)
        result = cli_runner.invoke(onboard, ['start', 'industry-corp'], input='1\n2\n')
        
        assert result.exit_code == 0
        assert "Starting onboarding for industry-corp" in result.output
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_start_workflow_creation_failure(self, mock_workflow_manager_class, cli_runner):
        """Test start command handles workflow creation failure"""
        mock_manager = Mock()
        mock_manager.create_workflow.side_effect = Exception("Workflow creation failed")
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, [
            'start', 'failcorp',
            '--package', 'enterprise'
        ])
        
        assert result.exit_code == 0  # CLI should handle error gracefully
        assert "Error starting workflow" in result.output or "failed" in result.output.lower()
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_start_invalid_template_file(self, mock_workflow_manager_class, cli_runner, invalid_template_file):
        """Test start command with invalid template file"""
        mock_manager = Mock()
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, [
            'start', 'invalid-corp',
            '--config-file', invalid_template_file
        ])
        
        assert result.exit_code == 0
        # Should show error about invalid template
        assert "Error" in result.output or "invalid" in result.output.lower()
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_start_resume_existing_workflow(self, mock_workflow_manager_class, cli_runner):
        """Test start command with resume option"""
        mock_manager = Mock()
        mock_existing_workflow = Mock()
        mock_existing_workflow.workflow_id = 'onboard-existing-12345'
        mock_existing_workflow.status = WorkflowStatus.PAUSED
        
        mock_manager.find_customer_workflow.return_value = mock_existing_workflow
        mock_manager.resume_workflow.return_value = True
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, [
            'start', 'existing-corp',
            '--resume'
        ])
        
        assert result.exit_code == 0
        assert "Found existing workflow" in result.output
        assert "Resuming workflow" in result.output


@pytest.mark.skipif(not ONBOARDING_AVAILABLE, reason="Onboarding commands not available")
class TestResumeCommand:
    """Test onboard resume command"""
    
    def test_resume_help(self, cli_runner):
        """Test resume command help"""
        result = cli_runner.invoke(onboard, ['resume', '--help'])
        
        assert result.exit_code == 0
        assert "Resume interrupted onboarding workflow" in result.output
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_resume_by_customer_name(self, mock_workflow_manager_class, cli_runner):
        """Test resume command by customer name"""
        mock_manager = Mock()
        mock_workflow = Mock()
        mock_workflow.workflow_id = 'onboard-testcorp-12345'
        mock_workflow.status = WorkflowStatus.PAUSED
        mock_workflow.customer_name = 'testcorp'
        
        mock_manager.find_customer_workflow.return_value = mock_workflow
        mock_manager.resume_workflow.return_value = True
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, ['resume', 'testcorp'])
        
        assert result.exit_code == 0
        assert "Resuming workflow for testcorp" in result.output
        
        mock_manager.find_customer_workflow.assert_called_once_with('testcorp')
        mock_manager.resume_workflow.assert_called_once_with(mock_workflow.workflow_id)
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_resume_by_workflow_id(self, mock_workflow_manager_class, cli_runner):
        """Test resume command by workflow ID"""
        mock_manager = Mock()
        mock_workflow = Mock()
        mock_workflow.workflow_id = 'onboard-specific-98765'
        mock_workflow.status = WorkflowStatus.PAUSED
        mock_workflow.customer_name = 'specific-corp'
        
        mock_manager.find_customer_workflow.return_value = None
        mock_manager._load_workflow_state.return_value = {
            'workflow_id': 'onboard-specific-98765',
            'customer_name': 'specific-corp',
            'status': 'paused'
        }
        mock_manager.resume_workflow.return_value = True
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, ['resume', 'onboard-specific-98765'])
        
        assert result.exit_code == 0
        assert "Resuming workflow for specific-corp" in result.output
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_resume_workflow_not_found(self, mock_workflow_manager_class, cli_runner):
        """Test resume command with workflow not found"""
        mock_manager = Mock()
        mock_manager.find_customer_workflow.return_value = None
        mock_manager._load_workflow_state.side_effect = FileNotFoundError()
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, ['resume', 'nonexistent'])
        
        assert result.exit_code == 0
        assert "Workflow nonexistent not found" in result.output
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_resume_workflow_not_paused(self, mock_workflow_manager_class, cli_runner):
        """Test resume command with workflow not in paused state"""
        mock_manager = Mock()
        mock_workflow = Mock()
        mock_workflow.workflow_id = 'onboard-running-12345'
        mock_workflow.status = WorkflowStatus.IN_PROGRESS
        
        mock_manager.find_customer_workflow.return_value = mock_workflow
        mock_manager.resume_workflow.side_effect = Exception("Workflow onboard-running-12345 is not paused (status: WorkflowStatus.IN_PROGRESS)")
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, ['resume', 'running-corp'])
        
        assert result.exit_code == 0
        assert "Error resuming workflow" in result.output
        assert "not paused" in result.output
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_resume_workflow_failed_status(self, mock_workflow_manager_class, cli_runner):
        """Test resume command with failed workflow"""
        mock_manager = Mock()
        mock_workflow = Mock()
        mock_workflow.workflow_id = 'onboard-failed-12345'
        mock_workflow.status = WorkflowStatus.FAILED
        
        mock_manager.find_customer_workflow.return_value = mock_workflow
        mock_manager.resume_workflow.side_effect = Exception("Workflow onboard-failed-12345 is not paused (status: WorkflowStatus.FAILED)")
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, ['resume', 'failed-corp'])
        
        assert result.exit_code == 0
        assert "Error resuming workflow" in result.output
        assert "FAILED" in result.output


@pytest.mark.skipif(not ONBOARDING_AVAILABLE, reason="Onboarding commands not available")
class TestStatusCommand:
    """Test onboard status command"""
    
    def test_status_help(self, cli_runner):
        """Test status command help"""
        result = cli_runner.invoke(onboard, ['status', '--help'])
        
        assert result.exit_code == 0
        assert "Show onboarding workflow status" in result.output
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_status_list_workflows(self, mock_workflow_manager_class, cli_runner):
        """Test status command lists all workflows"""
        mock_manager = Mock()
        mock_workflows = [
            {
                'workflow_id': 'onboard-corp1-12345',
                'customer_name': 'corp1',
                'package': 'enterprise',
                'status': 'in_progress',
                'progress': 75.0,
                'created_at': '2025-09-01T10:00:00Z'
            },
            {
                'workflow_id': 'onboard-corp2-67890',
                'customer_name': 'corp2', 
                'package': 'startup',
                'status': 'completed',
                'progress': 100.0,
                'created_at': '2025-09-01T09:00:00Z'
            }
        ]
        
        mock_manager.list_workflows.return_value = mock_workflows
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, ['status'])
        
        assert result.exit_code == 0
        assert "Onboarding Workflows" in result.output
        assert "corp1" in result.output
        assert "corp2" in result.output
        assert "enterprise" in result.output
        assert "startup" in result.output
        assert "in_progress" in result.output
        assert "completed" in result.output
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_status_no_workflows(self, mock_workflow_manager_class, cli_runner):
        """Test status command with no workflows"""
        mock_manager = Mock()
        mock_manager.list_workflows.return_value = []
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, ['status'])
        
        assert result.exit_code == 0
        assert "No onboarding workflows found" in result.output


@pytest.mark.skipif(not ONBOARDING_AVAILABLE, reason="Onboarding commands not available")
class TestValidateCommand:
    """Test onboard validate command"""
    
    def test_validate_help(self, cli_runner):
        """Test validate command help"""
        result = cli_runner.invoke(onboard, ['validate', '--help'])
        
        assert result.exit_code == 0
        assert "Validate onboarding workflow and configuration" in result.output
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_validate_workflow_by_customer(self, mock_workflow_manager_class, cli_runner):
        """Test validate command for specific customer workflow"""
        mock_manager = Mock()
        mock_workflow = Mock()
        mock_workflow.workflow_id = 'onboard-testcorp-12345'
        mock_workflow.customer_name = 'testcorp'
        
        mock_manager.find_customer_workflow.return_value = mock_workflow
        mock_manager.validate_workflow.return_value = {
            'valid': True,
            'errors': [],
            'warnings': ['Minor configuration issue'],
            'score': 95
        }
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, ['validate', 'testcorp'])
        
        assert result.exit_code == 0
        assert "Validating workflow for testcorp" in result.output
        assert "Validation Score: 95" in result.output or "valid" in result.output.lower()
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_validate_workflow_with_errors(self, mock_workflow_manager_class, cli_runner):
        """Test validate command with workflow errors"""
        mock_manager = Mock()
        mock_workflow = Mock()
        mock_workflow.workflow_id = 'onboard-errorprone-12345'
        
        mock_manager.find_customer_workflow.return_value = mock_workflow
        mock_manager.validate_workflow.return_value = {
            'valid': False,
            'errors': ['Missing required configuration', 'Invalid agent package'],
            'warnings': ['Performance may be impacted'],
            'score': 60
        }
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, ['validate', 'errorprone'])
        
        assert result.exit_code == 0
        assert "Validation found issues" in result.output or "errors" in result.output.lower()
        assert "Missing required configuration" in result.output
        assert "Invalid agent package" in result.output
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_validate_workflow_not_found(self, mock_workflow_manager_class, cli_runner):
        """Test validate command with workflow not found"""
        mock_manager = Mock()
        mock_manager.find_customer_workflow.return_value = None
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, ['validate', 'nonexistent'])
        
        assert result.exit_code == 0
        assert "Workflow not found for nonexistent" in result.output


@pytest.mark.skipif(not ONBOARDING_AVAILABLE, reason="Onboarding commands not available")
class TestValidateTemplateCommand:
    """Test onboard validate-template command"""
    
    def test_validate_template_help(self, cli_runner):
        """Test validate-template command help"""
        result = cli_runner.invoke(onboard, ['validate-template', '--help'])
        
        assert result.exit_code == 0
        assert "Validate external template file" in result.output
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_validate_template_valid_file(self, mock_workflow_manager_class, cli_runner, sample_external_template):
        """Test validate-template command with valid template"""
        mock_manager = Mock()
        mock_manager._load_external_template.return_value = {
            'organization': {'customer_name': 'Test'},
            'teams': [{'name': 'Engineering'}],
            'workspace': {'name': 'Test Workspace'}
        }
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, ['validate-template', sample_external_template])
        
        assert result.exit_code == 0
        assert "Validating external template" in result.output
        assert "✅" in result.output or "valid" in result.output.lower()
        
    def test_validate_template_invalid_file(self, cli_runner, invalid_template_file):
        """Test validate-template command with invalid template"""
        result = cli_runner.invoke(onboard, ['validate-template', invalid_template_file])
        
        assert result.exit_code == 0
        assert "Error validating template" in result.output or "invalid" in result.output.lower()
        
    def test_validate_template_nonexistent_file(self, cli_runner):
        """Test validate-template command with nonexistent file"""
        result = cli_runner.invoke(onboard, ['validate-template', '/nonexistent/template.yaml'])
        
        assert result.exit_code == 0
        assert "Error" in result.output or "not found" in result.output.lower()
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_validate_template_with_preview(self, mock_workflow_manager_class, cli_runner, sample_external_template):
        """Test validate-template command with preview option"""
        mock_manager = Mock()
        mock_template_data = {
            'organization': {'customer_name': 'Preview Corp'},
            'teams': [{'name': 'Engineering', 'key': 'ENG'}],
            'workspace': {'name': 'Preview Workspace'}
        }
        mock_manager._load_external_template.return_value = mock_template_data
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, ['validate-template', sample_external_template, '--preview'])
        
        assert result.exit_code == 0
        assert "Template Preview" in result.output or "preview" in result.output.lower()
        assert "Preview Corp" in result.output or "Engineering" in result.output


@pytest.mark.skipif(not ONBOARDING_AVAILABLE, reason="Onboarding commands not available")
class TestWorkflowStateManagement:
    """Test workflow state management functionality"""
    
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_workflow_persistence(self, mock_workflow_manager_class, cli_runner):
        """Test that workflow state is properly persisted"""
        mock_manager = Mock()
        mock_workflow = Mock()
        mock_workflow.workflow_id = 'onboard-persist-12345'
        mock_workflow.status = WorkflowStatus.IN_PROGRESS
        mock_workflow.get_progress.return_value = (2, 5)  # 2 of 5 steps completed
        
        mock_manager.create_workflow.return_value = mock_workflow
        mock_manager.start_workflow.return_value = True
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, [
            'start', 'persist-corp',
            '--package', 'enterprise'
        ])
        
        assert result.exit_code == 0
        
        # Verify workflow was created and started
        mock_manager.create_workflow.assert_called_once()
        mock_manager.start_workflow.assert_called_once_with('onboard-persist-12345')
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_workflow_progress_tracking(self, mock_workflow_manager_class, cli_runner):
        """Test workflow progress is tracked correctly"""
        mock_manager = Mock()
        mock_workflows = [
            {
                'workflow_id': 'onboard-progress-12345',
                'customer_name': 'progress-corp',
                'package': 'enterprise',
                'status': 'in_progress',
                'progress': 60.0,  # 3 of 5 steps completed
                'created_at': '2025-09-01T10:00:00Z'
            }
        ]
        
        mock_manager.list_workflows.return_value = mock_workflows
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, ['status'])
        
        assert result.exit_code == 0
        assert "60.0%" in result.output or "3/5" in result.output
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_external_template_metadata(self, mock_workflow_manager_class, cli_runner, sample_external_template):
        """Test external template metadata is preserved"""
        mock_manager = Mock()
        mock_workflow = Mock()
        mock_workflow.workflow_id = 'onboard-template-12345'
        mock_workflow.status = WorkflowStatus.IN_PROGRESS
        
        mock_manager.create_workflow.return_value = mock_workflow
        mock_manager.start_workflow.return_value = True
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, [
            'start', 'template-corp',
            '--config-file', sample_external_template
        ])
        
        assert result.exit_code == 0
        
        # Verify template file was passed to workflow creation
        call_kwargs = mock_manager.create_workflow.call_args[1]
        assert call_kwargs['template_file'] == sample_external_template


@pytest.mark.skipif(not ONBOARDING_AVAILABLE, reason="Onboarding commands not available")
class TestErrorHandling:
    """Test error handling in onboarding commands"""
    
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_workflow_manager_initialization_failure(self, mock_workflow_manager_class, cli_runner):
        """Test handling of workflow manager initialization failure"""
        mock_workflow_manager_class.side_effect = Exception("Manager initialization failed")
        
        result = cli_runner.invoke(onboard, ['start', 'failcorp'])
        
        assert result.exit_code == 0
        # Should handle initialization error gracefully
        assert "Error" in result.output or "failed" in result.output.lower()
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_file_permission_errors(self, mock_workflow_manager_class, cli_runner):
        """Test handling of file permission errors"""
        mock_manager = Mock()
        mock_manager.create_workflow.side_effect = PermissionError("Permission denied")
        mock_workflow_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(onboard, ['start', 'permissioncorp'])
        
        assert result.exit_code == 0
        # Should handle permission error gracefully
        
    @patch('symphony_cli.commands.onboarding_commands.WorkflowManager')
    def test_invalid_user_input(self, mock_workflow_manager_class, cli_runner):
        """Test handling of invalid user input"""
        mock_manager = Mock()
        mock_workflow_manager_class.return_value = mock_manager
        
        # Test invalid package selection (select option 99)
        result = cli_runner.invoke(onboard, ['start', 'invalidcorp'], input='99\n1\n')
        
        # Should handle invalid selection and re-prompt
        assert result.exit_code == 0
        
    def test_missing_template_file(self, cli_runner):
        """Test handling of missing template file"""
        result = cli_runner.invoke(onboard, [
            'start', 'missingcorp',
            '--config-file', '/nonexistent/template.yaml'
        ])
        
        assert result.exit_code == 0
        assert "Error" in result.output or "not found" in result.output.lower()


class TestOnboardingInfrastructure:
    """Test onboarding test infrastructure"""
    
    def test_fixtures_work_correctly(self, sample_external_template, invalid_template_file, workflow_state_file):
        """Test that test fixtures work correctly"""
        # Test external template fixture
        assert Path(sample_external_template).exists()
        with open(sample_external_template) as f:
            template_data = yaml.safe_load(f)
            assert 'organization' in template_data
            assert template_data['organization']['customer_name'] == 'External Corp'
            
        # Test invalid template fixture
        assert Path(invalid_template_file).exists()
        with open(invalid_template_file) as f:
            content = f.read()
            assert 'invalid: yaml: content: [' in content
            
        # Test workflow state fixture
        assert Path(workflow_state_file).exists()
        with open(workflow_state_file) as f:
            state_data = json.load(f)
            assert 'workflow_id' in state_data
            assert state_data['customer_name'] == 'Test Corp'
            
    def test_mock_workflow_status_enum(self):
        """Test WorkflowStatus enum mocking"""
        if ONBOARDING_AVAILABLE:
            assert hasattr(WorkflowStatus, 'IN_PROGRESS')
            assert hasattr(WorkflowStatus, 'PAUSED')
            assert hasattr(WorkflowStatus, 'COMPLETED')
            assert hasattr(WorkflowStatus, 'FAILED')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])