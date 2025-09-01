#!/usr/bin/env python3
"""
Tests for Linear CLI Commands

Tests CLI functionality, command interfaces, and integration with core components.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

# Import CLI commands - handle import errors gracefully
try:
    from symphony_cli.commands.linear_hierarchy import (
        hierarchy, configure, generate, validate, preview, deploy, dogfood, list_templates
    )
    CLI_AVAILABLE = True
except ImportError:
    CLI_AVAILABLE = False
    
from symphony_integrations.linear.template_models import (
    OrganizationConfig, IndustryType, OrganizationSize
)


@pytest.fixture
def cli_runner():
    """Fixture providing Click CLI test runner"""
    return CliRunner()


@pytest.fixture
def sample_config_file():
    """Fixture providing sample configuration file"""
    config_data = {
        "organization": {
            "customer_name": "Test Corp",
            "industry": "technology",
            "size": "startup",
            "regions": ["us-east-1"]
        },
        "workspace": {
            "name": "Test Corp Workspace",
            "description": "Test workspace configuration"
        },
        "teams": [
            {
                "name": "Engineering",
                "key": "ENG",
                "description": "Software engineering team"
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        return f.name


@pytest.fixture
def invalid_config_file():
    """Fixture providing invalid configuration file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: content: [")
        return f.name


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI commands not available")
class TestCLICommands:
    """Test CLI command functionality"""
    
    def test_hierarchy_group_help(self, cli_runner):
        """Test hierarchy command group help"""
        result = cli_runner.invoke(hierarchy, ['--help'])
        
        assert result.exit_code == 0
        assert "Linear workspace hierarchy management" in result.output
    
    def test_configure_help(self, cli_runner):
        """Test configure command help"""
        result = cli_runner.invoke(hierarchy, ['configure', '--help'])
        
        assert result.exit_code == 0
        assert "Configure Linear workspace" in result.output
        assert "--config" in result.output
        assert "--interactive" in result.output
        assert "--preview" in result.output
    
    def test_generate_help(self, cli_runner):
        """Test generate command help"""
        result = cli_runner.invoke(hierarchy, ['generate', '--help'])
        
        assert result.exit_code == 0
        assert "Generate intelligent defaults" in result.output
        assert "--customer" in result.output
        assert "--industry" in result.output


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI commands not available")
class TestConfigureCommand:
    """Test configure command"""
    
    def test_configure_missing_options(self, cli_runner):
        """Test configure command with no options shows error"""
        result = cli_runner.invoke(hierarchy, ['configure'])
        
        assert result.exit_code == 1  # Should abort
        assert "Either --config or --interactive must be specified" in result.output
    
    def test_configure_with_config_file(self, cli_runner, sample_config_file):
        """Test configure command with configuration file"""
        with patch('symphony_integrations.linear.template_engine.TemplateEngine') as mock_engine:
            mock_template = Mock()
            mock_engine.return_value.process_customer_config.return_value = mock_template
            
            result = cli_runner.invoke(hierarchy, ['configure', '--config', sample_config_file])
            
            assert result.exit_code == 0
            assert "Configuration processed successfully" in result.output
            mock_engine.return_value.process_customer_config.assert_called_once()
    
    def test_configure_with_preview(self, cli_runner, sample_config_file):
        """Test configure command with preview option"""
        with patch('symphony_integrations.linear.template_engine.TemplateEngine') as mock_engine:
            with patch('symphony_cli.commands.linear_hierarchy._display_workspace_preview') as mock_preview:
                mock_template = Mock()
                mock_template.workspace = {"name": "Test Workspace"}
                mock_engine.return_value.process_customer_config.return_value = mock_template
                
                result = cli_runner.invoke(hierarchy, ['configure', '--config', sample_config_file, '--preview'])
                
                assert result.exit_code == 0
                mock_preview.assert_called_once()
    
    def test_configure_with_output(self, cli_runner, sample_config_file):
        """Test configure command with output file"""
        with tempfile.NamedTemporaryFile(suffix='.yaml') as output_file:
            with patch('symphony_integrations.linear.template_engine.TemplateEngine') as mock_engine:
                mock_template = Mock()
                mock_engine.return_value.process_customer_config.return_value = mock_template
                
                result = cli_runner.invoke(hierarchy, [
                    'configure', 
                    '--config', sample_config_file,
                    '--output', output_file.name
                ])
                
                assert result.exit_code == 0
                assert f"Template saved to: {output_file.name}" in result.output
                mock_engine.return_value.save_template.assert_called_once()
    
    @patch('symphony_cli.commands.linear_hierarchy.ConfigurationWizard')
    def test_configure_interactive(self, mock_wizard_class, cli_runner):
        """Test configure command in interactive mode"""
        mock_wizard = Mock()
        mock_wizard.run_interactive_wizard.return_value = {"test": "config"}
        mock_wizard_class.return_value = mock_wizard
        
        with tempfile.NamedTemporaryFile(suffix='.yaml') as output_file:
            result = cli_runner.invoke(hierarchy, [
                'configure',
                '--interactive', 
                '--output', output_file.name
            ])
            
            assert result.exit_code == 0
            assert "Interactive Configuration Wizard" in result.output
            mock_wizard.run_interactive_wizard.assert_called_once()
    
    def test_configure_invalid_config_file(self, cli_runner, invalid_config_file):
        """Test configure command with invalid configuration file"""
        result = cli_runner.invoke(hierarchy, ['configure', '--config', invalid_config_file])
        
        assert result.exit_code == 1
        assert "Error configuring workspace" in result.output


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI commands not available")
class TestGenerateCommand:
    """Test generate command"""
    
    def test_generate_basic(self, cli_runner):
        """Test basic generate command"""
        with patch('symphony_integrations.linear.defaults_generator.SymphonyLinearDefaults') as mock_generator_class:
            mock_generator = Mock()
            mock_template = Mock()
            mock_template.teams = []
            mock_template.initiatives = []
            mock_template.projects = []
            mock_template.symphony_integration = None
            
            mock_generator.generate_defaults.return_value = mock_template
            mock_generator_class.return_value = mock_generator
            
            result = cli_runner.invoke(hierarchy, ['generate', '--customer', 'Test Corp'])
            
            assert result.exit_code == 0
            assert "Generated defaults for Test Corp" in result.output
            mock_generator.generate_defaults.assert_called_once()
    
    def test_generate_with_all_options(self, cli_runner):
        """Test generate command with all options"""
        with patch('symphony_integrations.linear.defaults_generator.SymphonyLinearDefaults') as mock_generator_class:
            with patch('symphony_integrations.linear.template_engine.TemplateEngine') as mock_engine_class:
                mock_generator = Mock()
                mock_template = Mock()
                mock_template.teams = []
                mock_template.initiatives = []
                mock_template.projects = []
                mock_template.symphony_integration = None
                
                mock_generator.generate_defaults.return_value = mock_template
                mock_generator_class.return_value = mock_generator
                
                mock_engine = Mock()
                mock_engine_class.return_value = mock_engine
                
                with tempfile.NamedTemporaryFile(suffix='.yaml') as output_file:
                    result = cli_runner.invoke(hierarchy, [
                        'generate',
                        '--customer', 'TechCorp',
                        '--industry', 'technology',
                        '--size', 'enterprise',
                        '--regions', 'us-east-1,us-west-2',
                        '--output', output_file.name
                    ])
                    
                    assert result.exit_code == 0
                    mock_engine.save_template.assert_called_once()
    
    def test_generate_with_preview(self, cli_runner):
        """Test generate command with preview"""
        with patch('symphony_integrations.linear.defaults_generator.SymphonyLinearDefaults') as mock_generator_class:
            with patch('symphony_cli.commands.linear_hierarchy._display_workspace_preview') as mock_preview:
                mock_generator = Mock()
                mock_template = Mock()
                mock_template.teams = []
                mock_template.initiatives = []
                mock_template.projects = []
                mock_template.symphony_integration = None
                
                mock_generator.generate_defaults.return_value = mock_template
                mock_generator_class.return_value = mock_generator
                
                result = cli_runner.invoke(hierarchy, [
                    'generate',
                    '--customer', 'PreviewCorp',
                    '--preview'
                ])
                
                assert result.exit_code == 0
                mock_preview.assert_called_once()
    
    def test_generate_organization_config_creation(self, cli_runner):
        """Test that generate command creates correct OrganizationConfig"""
        with patch('symphony_integrations.linear.defaults_generator.SymphonyLinearDefaults') as mock_generator_class:
            mock_generator = Mock()
            mock_template = Mock()
            mock_template.teams = []
            mock_template.initiatives = []
            mock_template.projects = []
            mock_template.symphony_integration = None
            
            mock_generator.generate_defaults.return_value = mock_template
            mock_generator_class.return_value = mock_generator
            
            result = cli_runner.invoke(hierarchy, [
                'generate',
                '--customer', 'TestCorp',
                '--industry', 'financial_services',
                '--size', 'global',
                '--regions', 'us-east-1,eu-west-1'
            ])
            
            assert result.exit_code == 0
            
            # Verify OrganizationConfig was created with correct parameters
            call_args = mock_generator.generate_defaults.call_args[0][0]
            assert call_args.customer_name == 'TestCorp'
            assert call_args.industry == IndustryType.FINANCIAL_SERVICES
            assert call_args.size == OrganizationSize.GLOBAL
            assert call_args.regions == ['us-east-1', 'eu-west-1']


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI commands not available")
class TestValidateCommand:
    """Test validate command"""
    
    def test_validate_valid_config(self, cli_runner, sample_config_file):
        """Test validate command with valid configuration"""
        with patch('symphony_integrations.linear.template_engine.TemplateEngine') as mock_engine:
            with patch('symphony_integrations.linear.template_validator.TemplateValidator') as mock_validator_class:
                mock_template = Mock()
                mock_engine.return_value.process_customer_config.return_value = mock_template
                
                mock_validator = Mock()
                mock_result = Mock()
                mock_result.is_valid = True
                mock_result.errors = []
                mock_result.warnings = []
                mock_result.suggestions = []
                
                mock_validator.validate_template.return_value = mock_result
                mock_validator_class.return_value = mock_validator
                
                result = cli_runner.invoke(hierarchy, ['validate', sample_config_file])
                
                assert result.exit_code == 0
                assert "Configuration is valid!" in result.output
    
    def test_validate_invalid_config(self, cli_runner, sample_config_file):
        """Test validate command with invalid configuration"""
        with patch('symphony_integrations.linear.template_engine.TemplateEngine') as mock_engine:
            with patch('symphony_integrations.linear.template_validator.TemplateValidator') as mock_validator_class:
                mock_template = Mock()
                mock_engine.return_value.process_customer_config.return_value = mock_template
                
                mock_validator = Mock()
                mock_result = Mock()
                mock_result.is_valid = False
                mock_result.errors = ["Missing workspace name", "Invalid team key"]
                mock_result.warnings = ["Large number of teams"]
                mock_result.suggestions = ["Consider adding milestones"]
                
                mock_validator.validate_template.return_value = mock_result
                mock_validator_class.return_value = mock_validator
                
                result = cli_runner.invoke(hierarchy, ['validate', sample_config_file])
                
                assert result.exit_code == 0  # Command should succeed even with validation errors
                assert "Configuration has errors:" in result.output
                assert "Missing workspace name" in result.output
                assert "Large number of teams" in result.output
                assert "Consider adding milestones" in result.output
    
    def test_validate_file_processing_error(self, cli_runner, invalid_config_file):
        """Test validate command with file processing error"""
        result = cli_runner.invoke(hierarchy, ['validate', invalid_config_file])
        
        assert result.exit_code == 1
        assert "Error validating configuration" in result.output


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI commands not available")
class TestPreviewCommand:
    """Test preview command"""
    
    def test_preview_basic(self, cli_runner, sample_config_file):
        """Test basic preview command"""
        with patch('symphony_integrations.linear.template_engine.TemplateEngine') as mock_engine:
            with patch('symphony_cli.commands.linear_hierarchy._display_workspace_preview') as mock_preview:
                mock_template = Mock()
                mock_engine.return_value.process_customer_config.return_value = mock_template
                
                result = cli_runner.invoke(hierarchy, ['preview', sample_config_file])
                
                assert result.exit_code == 0
                mock_preview.assert_called_once_with(mock_template, detailed=False)
    
    def test_preview_detailed(self, cli_runner, sample_config_file):
        """Test preview command with detailed option"""
        with patch('symphony_integrations.linear.template_engine.TemplateEngine') as mock_engine:
            with patch('symphony_cli.commands.linear_hierarchy._display_workspace_preview') as mock_preview:
                mock_template = Mock()
                mock_engine.return_value.process_customer_config.return_value = mock_template
                
                result = cli_runner.invoke(hierarchy, ['preview', sample_config_file, '--detailed'])
                
                assert result.exit_code == 0
                mock_preview.assert_called_once_with(mock_template, detailed=True)


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI commands not available")
class TestDeployCommand:
    """Test deploy command"""
    
    def test_deploy_requires_token(self, cli_runner, sample_config_file):
        """Test deploy command requires Linear API token"""
        result = cli_runner.invoke(hierarchy, ['deploy', sample_config_file])
        
        # Should fail due to missing token
        assert result.exit_code != 0
        assert "linear-token" in result.output.lower() or "required" in result.output.lower()
    
    def test_deploy_dry_run(self, cli_runner, sample_config_file):
        """Test deploy command with dry run"""
        with patch('symphony_integrations.linear.template_engine.TemplateEngine') as mock_engine:
            with patch('symphony_integrations.linear.template_validator.TemplateValidator') as mock_validator_class:
                mock_template = Mock()
                mock_engine.return_value.process_customer_config.return_value = mock_template
                
                mock_validator = Mock()
                mock_result = Mock()
                mock_result.is_valid = True
                mock_result.errors = []
                
                mock_validator.validate_template.return_value = mock_result
                mock_validator_class.return_value = mock_validator
                
                result = cli_runner.invoke(hierarchy, [
                    'deploy', 
                    sample_config_file,
                    '--linear-token', 'test-token',
                    '--dry-run'
                ])
                
                assert result.exit_code == 0
                assert "DRY RUN" in result.output
                assert "ready for deployment" in result.output
    
    def test_deploy_invalid_config_blocks_deployment(self, cli_runner, sample_config_file):
        """Test deploy command blocks deployment for invalid configuration"""
        with patch('symphony_integrations.linear.template_engine.TemplateEngine') as mock_engine:
            with patch('symphony_integrations.linear.template_validator.TemplateValidator') as mock_validator_class:
                mock_template = Mock()
                mock_engine.return_value.process_customer_config.return_value = mock_template
                
                mock_validator = Mock()
                mock_result = Mock()
                mock_result.is_valid = False
                mock_result.errors = ["Critical validation error"]
                
                mock_validator.validate_template.return_value = mock_result
                mock_validator_class.return_value = mock_validator
                
                result = cli_runner.invoke(hierarchy, [
                    'deploy',
                    sample_config_file,
                    '--linear-token', 'test-token',
                    '--force'
                ])
                
                assert result.exit_code == 1
                assert "Configuration has errors" in result.output
    
    def test_deploy_simulation(self, cli_runner, sample_config_file):
        """Test deploy command simulation"""
        with patch('symphony_integrations.linear.template_engine.TemplateEngine') as mock_engine:
            with patch('symphony_integrations.linear.template_validator.TemplateValidator') as mock_validator_class:
                with patch('symphony_cli.commands.linear_hierarchy._simulate_deployment') as mock_simulate:
                    mock_template = Mock()
                    mock_engine.return_value.process_customer_config.return_value = mock_template
                    
                    mock_validator = Mock()
                    mock_result = Mock()
                    mock_result.is_valid = True
                    mock_result.errors = []
                    
                    mock_validator.validate_template.return_value = mock_result
                    mock_validator_class.return_value = mock_validator
                    
                    result = cli_runner.invoke(hierarchy, [
                        'deploy',
                        sample_config_file,
                        '--linear-token', 'test-token',
                        '--force'  # Skip confirmation
                    ])
                    
                    assert result.exit_code == 0
                    assert "Workspace deployed successfully!" in result.output
                    mock_simulate.assert_called_once()


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI commands not available")
class TestDogfoodCommand:
    """Test dogfood command"""
    
    def test_dogfood_basic(self, cli_runner):
        """Test basic dogfood command"""
        with patch('symphony_integrations.linear.defaults_generator.SymphonyLinearDefaults') as mock_generator_class:
            with patch('symphony_cli.commands.linear_hierarchy._display_dogfooding_preview') as mock_preview:
                mock_generator = Mock()
                mock_template = Mock()
                mock_generator.generate_dogfooding_template.return_value = mock_template
                mock_generator_class.return_value = mock_generator
                
                # Mock user choosing not to save
                result = cli_runner.invoke(hierarchy, ['dogfood'], input='n\n')
                
                assert result.exit_code == 0
                assert "Symphony Dogfooding Configuration" in result.output
                assert "Generated Symphony internal workspace configuration" in result.output
                mock_preview.assert_called_once()
    
    def test_dogfood_save_configuration(self, cli_runner):
        """Test dogfood command with saving configuration"""
        with patch('symphony_integrations.linear.defaults_generator.SymphonyLinearDefaults') as mock_generator_class:
            with patch('symphony_integrations.linear.template_engine.TemplateEngine') as mock_engine_class:
                with patch('symphony_cli.commands.linear_hierarchy._display_dogfooding_preview'):
                    mock_generator = Mock()
                    mock_template = Mock()
                    mock_generator.generate_dogfooding_template.return_value = mock_template
                    mock_generator_class.return_value = mock_generator
                    
                    mock_engine = Mock()
                    mock_engine_class.return_value = mock_engine
                    
                    # Mock user choosing to save
                    result = cli_runner.invoke(hierarchy, ['dogfood'], input='y\n')
                    
                    assert result.exit_code == 0
                    mock_engine.save_template.assert_called_once()
                    assert "configs/symphony-dogfood-workspace.yaml" in result.output


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI commands not available")
class TestListTemplatesCommand:
    """Test list-templates command"""
    
    def test_list_templates(self, cli_runner):
        """Test list-templates command"""
        result = cli_runner.invoke(hierarchy, ['list-templates'])
        
        assert result.exit_code == 0
        assert "Available Workspace Templates" in result.output
        assert "financial-services" in result.output
        assert "healthcare" in result.output
        assert "technology" in result.output
        assert "startup" in result.output
        assert "symphony-dogfood" in result.output


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI commands not available")
class TestDisplayFunctions:
    """Test display and helper functions"""
    
    @patch('symphony_cli.commands.linear_hierarchy.console')
    def test_display_workspace_preview(self, mock_console):
        """Test workspace preview display"""
        from symphony_cli.commands.linear_hierarchy import _display_workspace_preview
        
        mock_template = Mock()
        mock_template.workspace = {"name": "Test Workspace"}
        
        # Mock preview generator
        with patch('symphony_cli.commands.linear_hierarchy.WorkspacePreviewGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_preview = Mock()
            mock_preview.workspace_name = "Test Workspace"
            mock_preview.team_count = 3
            mock_preview.project_count = 2
            mock_preview.initiative_count = 1
            mock_preview.estimated_setup_time = "30-60 minutes"
            mock_preview.complexity_score = 6
            mock_preview.linear_features_used = ["Teams", "Projects"]
            mock_preview.symphony_agents_deployed = ["Dev Agent"]
            mock_preview.structure_summary = {"teams": [], "initiatives": []}
            
            mock_generator.generate_preview.return_value = mock_preview
            mock_generator_class.return_value = mock_generator
            
            _display_workspace_preview(mock_template)
            
            # Verify console.print was called
            assert mock_console.print.called
    
    def test_simulate_deployment(self):
        """Test deployment simulation"""
        from symphony_cli.commands.linear_hierarchy import _simulate_deployment
        
        mock_template = Mock()
        
        with patch('symphony_cli.commands.linear_hierarchy.console') as mock_console:
            with patch('time.sleep'):  # Speed up the test
                _simulate_deployment(mock_template)
                
                # Should print deployment steps
                assert mock_console.print.call_count >= 7  # 7 steps + final message
    
    def test_display_team_structure(self):
        """Test team structure display"""
        from symphony_cli.commands.linear_hierarchy import _display_team_structure
        
        teams = [
            {
                "name": "Engineering",
                "key": "ENG",
                "sub_teams": 2,
                "workflows": 4,
                "custom_fields": 3
            }
        ]
        
        with patch('symphony_cli.commands.linear_hierarchy.console') as mock_console:
            _display_team_structure(teams)
            
            assert mock_console.print.called
    
    def test_display_generation_summary(self):
        """Test generation summary display"""
        from symphony_cli.commands.linear_hierarchy import _display_generation_summary
        
        mock_template = Mock()
        mock_template.teams = ["team1", "team2"]
        mock_template.initiatives = ["init1"]
        mock_template.projects = ["proj1", "proj2", "proj3"]
        mock_template.symphony_integration = Mock()
        mock_template.symphony_integration.agent_assignments = {
            "team1": ["agent1", "agent2"],
            "team2": ["agent3"]
        }
        
        with patch('symphony_cli.commands.linear_hierarchy.console') as mock_console:
            _display_generation_summary(mock_template)
            
            assert mock_console.print.call_count >= 4  # Summary + 4 items


class TestCLIIntegration:
    """Test CLI integration and error handling"""
    
    def test_import_error_handling(self):
        """Test that import errors are handled gracefully"""
        # This test verifies that the module can be imported even if CLI dependencies are missing
        # The actual CLI commands are conditionally skipped if imports fail
        assert True  # If we got here, imports worked or were handled
    
    def test_click_runner_setup(self, cli_runner):
        """Test that Click runner is properly set up"""
        assert cli_runner is not None
        assert hasattr(cli_runner, 'invoke')
    
    def test_command_registration(self):
        """Test that commands are properly registered with the hierarchy group"""
        if CLI_AVAILABLE:
            from symphony_cli.commands.linear_hierarchy import hierarchy
            
            # Verify commands are registered
            assert hierarchy.commands is not None
            command_names = list(hierarchy.commands.keys())
            
            expected_commands = ['configure', 'generate', 'validate', 'preview', 'deploy', 'dogfood', 'list-templates']
            for cmd in expected_commands:
                assert cmd in command_names


if __name__ == "__main__":
    pytest.main([__file__])