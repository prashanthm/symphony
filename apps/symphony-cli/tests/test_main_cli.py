#!/usr/bin/env python3
"""
Comprehensive tests for Symphony CLI main interface

Test-driven development for the Symphony CLI tool covering:
- Main CLI interface and version handling
- Setup commands (env, wizard)
- Linear commands (init, status)
- GitHub commands (create, test)
- Agent commands (deploy, status, handoff, execute, monitor)
- Config commands (generate, validate) 
- Monitor commands (dashboard)
- Status command
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import yaml
from click.testing import CliRunner

# Import the main CLI module
try:
    from symphony_cli.main import cli, show_header
    CLI_AVAILABLE = True
except ImportError:
    CLI_AVAILABLE = False


@pytest.fixture
def cli_runner():
    """Fixture providing Click CLI test runner"""
    return CliRunner()


@pytest.fixture
def temp_env_file():
    """Fixture providing temporary .env file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("# Test environment file\n")
        f.write("LINEAR_API_TOKEN=test_token\n")
        f.write("GITHUB_TOKEN=test_github_token\n")
        return f.name


@pytest.fixture  
def sample_config_file():
    """Fixture providing sample configuration file"""
    config_data = {
        'organization': {
            'name': 'Test Corp',
            'type': 'enterprise',
            'industry': 'technology'
        },
        'agents': {
            'package': 'enterprise',
            'count': 65
        },
        'integrations': {
            'linear': {'enabled': True},
            'github': {'enabled': True}
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        return f.name


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI not available")
class TestMainCLIInterface:
    """Test the main CLI interface"""
    
    def test_cli_without_command_shows_header(self, cli_runner):
        """Test CLI without command shows welcome header"""
        result = cli_runner.invoke(cli, [])
        
        assert result.exit_code == 0
        assert "🎼" in result.output
        assert "Symphony Universal CLI" in result.output
        assert "Run 'symphony --help' for available commands" in result.output
        
    def test_cli_help_command(self, cli_runner):
        """Test CLI help command shows available commands"""
        result = cli_runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Universal command line interface" in result.output
        # Verify main command groups are listed
        assert "setup" in result.output
        assert "linear" in result.output  
        assert "github" in result.output
        assert "agent" in result.output
        assert "config" in result.output
        assert "monitor" in result.output
        
    def test_cli_version_flag(self, cli_runner):
        """Test CLI --version flag returns version"""
        result = cli_runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert "Symphony CLI v2.0.0" in result.output
        
    def test_show_header_function(self, cli_runner):
        """Test show_header function displays correct information"""
        with patch('symphony_cli.main.console') as mock_console:
            show_header()
            
            # Should call console.print with Panel
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert hasattr(call_args, 'renderable')  # Panel object


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI not available")
class TestSetupCommands:
    """Test setup command group"""
    
    def test_setup_help(self, cli_runner):
        """Test setup command group help"""
        result = cli_runner.invoke(cli, ['setup', '--help'])
        
        assert result.exit_code == 0
        assert "Configuration-driven autonomous enterprise setup" in result.output
        assert "env" in result.output
        assert "wizard" in result.output
        
    @patch('symphony_cli.main.Path')
    @patch('symphony_cli.main.validate_setup')
    def test_setup_env_creates_env_file(self, mock_validate, mock_path, cli_runner):
        """Test setup env command creates .env file from example"""
        # Mock filesystem operations
        mock_current = Mock()
        mock_symphony_root = Mock()
        mock_env_file = Mock()
        mock_env_example = Mock()
        
        mock_path.return_value.parent = mock_current
        mock_current.parent = mock_current  # Prevent infinite loop
        mock_current.__truediv__ = Mock(return_value=mock_symphony_root)
        
        # Mock file existence checks
        mock_env_file.exists.return_value = False
        mock_env_example.exists.return_value = True
        mock_symphony_root.__truediv__.side_effect = [
            mock_env_file,  # .env
            mock_env_example  # .env.example
        ]
        
        with patch('symphony_cli.main.shutil') as mock_shutil:
            result = cli_runner.invoke(cli, ['setup', 'env'])
            
            assert result.exit_code == 0
            assert "Created .env file from .env.example" in result.output
            assert "Please edit .env and add your API tokens" in result.output
            mock_shutil.copy.assert_called_once()
            mock_validate.assert_called_once()
            
    def test_setup_env_file_already_exists(self, cli_runner):
        """Test setup env command when .env file already exists"""
        with patch('symphony_cli.main.Path') as mock_path:
            with patch('symphony_cli.main.validate_setup') as mock_validate:
                # Mock filesystem to show existing .env
                mock_current = Mock()
                mock_current.parent = mock_current
                mock_symphony_root = Mock()
                mock_env_file = Mock()
                mock_env_file.exists.return_value = True
                
                mock_path.return_value.parent = mock_current
                mock_current.__truediv__ = Mock(return_value=mock_symphony_root)
                mock_symphony_root.__truediv__.return_value = mock_env_file
                
                result = cli_runner.invoke(cli, ['setup', 'env'])
                
                assert result.exit_code == 0
                assert ".env file already exists" in result.output
                mock_validate.assert_called_once()
        
    def test_setup_wizard_command(self, cli_runner):
        """Test setup wizard command"""
        result = cli_runner.invoke(cli, ['setup', 'wizard'])
        
        assert result.exit_code == 0
        assert "Launching Maestro Setup Wizard" in result.output
        assert "Phase 1:" in result.output
        assert "Phase 2:" in result.output
        assert "Phase 3:" in result.output
        assert "Phase 4:" in result.output
        assert "autonomous enterprise transformation" in result.output


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI not available")
class TestLinearCommands:
    """Test Linear command group"""
    
    def test_linear_help(self, cli_runner):
        """Test linear command group help"""
        result = cli_runner.invoke(cli, ['linear', '--help'])
        
        assert result.exit_code == 0
        assert "Linear API integration" in result.output
        assert "init" in result.output
        assert "status" in result.output
        
    @patch('symphony_cli.main.asyncio.run')
    @patch('symphony_cli.main.SymphonyLinearIntegration')
    def test_linear_init_success(self, mock_integration_class, mock_asyncio_run, cli_runner):
        """Test linear init command success"""
        # Mock the integration and its async method
        mock_integration = Mock()
        mock_workspace = {
            'organization_name': 'Test Corp',
            'projects': ['proj1', 'proj2']
        }
        
        async def mock_initialize():
            return mock_workspace
            
        mock_integration.initialize_workspace = AsyncMock(return_value=mock_workspace)
        mock_integration_class.return_value = mock_integration
        
        # Mock asyncio.run to execute our async function
        def run_async(coro):
            return asyncio.get_event_loop().run_until_complete(coro())
            
        mock_asyncio_run.side_effect = run_async
        
        result = cli_runner.invoke(cli, ['linear', 'init', 'Test Corp'])
        
        assert result.exit_code == 0
        assert "Initializing Linear workspace for Test Corp" in result.output
        
    @patch('symphony_cli.main.asyncio.run')
    @patch('symphony_cli.main.SymphonyLinearIntegration')
    def test_linear_init_failure(self, mock_integration_class, mock_asyncio_run, cli_runner):
        """Test linear init command failure handling"""
        mock_integration = Mock()
        mock_integration.initialize_workspace = AsyncMock(side_effect=Exception("API Error"))
        mock_integration_class.return_value = mock_integration
        
        def run_async(coro):
            try:
                return asyncio.get_event_loop().run_until_complete(coro())
            except Exception:
                pass  # Expected to be handled in CLI
                
        mock_asyncio_run.side_effect = run_async
        
        result = cli_runner.invoke(cli, ['linear', 'init', 'Test Corp'])
        
        assert result.exit_code == 0  # CLI should handle the error gracefully
        assert "Initializing Linear workspace for Test Corp" in result.output
        
    def test_linear_status_command(self, cli_runner):
        """Test linear status command"""
        result = cli_runner.invoke(cli, ['linear', 'status'])
        
        assert result.exit_code == 0
        assert "Linear Workspace Status" in result.output
        assert "Status checking functionality will be implemented" in result.output


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI not available")
class TestGitHubCommands:
    """Test GitHub command group"""
    
    def test_github_help(self, cli_runner):
        """Test github command group help"""
        result = cli_runner.invoke(cli, ['github', '--help'])
        
        assert result.exit_code == 0
        assert "GitHub API integration" in result.output
        assert "create" in result.output
        assert "test" in result.output
        
    def test_github_create_command(self, cli_runner):
        """Test github create command"""
        result = cli_runner.invoke(cli, ['github', 'create', 'test-org'])
        
        assert result.exit_code == 0
        assert "Creating GitHub repository for test-org" in result.output
        assert "GitHub repository creation functionality will be implemented" in result.output
        
    def test_github_create_with_options(self, cli_runner):
        """Test github create command with options"""
        result = cli_runner.invoke(cli, [
            'github', 'create', 'test-org',
            '--config', 'config.yaml',
            '--org', 'symphony-org'
        ])
        
        assert result.exit_code == 0
        assert "Creating GitHub repository for test-org" in result.output
        
    def test_github_test_command(self, cli_runner):
        """Test github test command"""
        result = cli_runner.invoke(cli, ['github', 'test'])
        
        assert result.exit_code == 0
        assert "Testing GitHub API connection" in result.output
        assert "GitHub API test functionality will be implemented" in result.output


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI not available")
class TestAgentCommands:
    """Test agent command group"""
    
    def test_agent_help(self, cli_runner):
        """Test agent command group help"""
        result = cli_runner.invoke(cli, ['agent', '--help'])
        
        assert result.exit_code == 0
        assert "Agent management and coordination" in result.output
        assert "deploy" in result.output
        assert "status" in result.output
        assert "handoff" in result.output
        assert "execute" in result.output
        assert "monitor" in result.output
        
    def test_agent_deploy_no_package(self, cli_runner):
        """Test agent deploy command without package"""
        result = cli_runner.invoke(cli, ['agent', 'deploy'])
        
        assert result.exit_code == 0
        assert "Please specify a package type" in result.output
        
    def test_agent_deploy_package_choices(self, cli_runner):
        """Test agent deploy command shows correct package choices"""
        result = cli_runner.invoke(cli, ['agent', 'deploy', '--help'])
        
        assert result.exit_code == 0
        assert "startup" in result.output
        assert "smb" in result.output  
        assert "enterprise" in result.output
        assert "global" in result.output
        
    @patch('symphony_cli.main.asyncio.run')
    @patch('symphony_cli.main.create_agent_manager')
    def test_agent_deploy_with_package(self, mock_manager_func, mock_asyncio_run, cli_runner):
        """Test agent deploy command with package"""
        mock_manager = Mock()
        mock_result = {'success': True, 'agents_deployed': 65}
        
        async def mock_deploy():
            return mock_result
            
        mock_manager.deploy_customer_agents = AsyncMock(return_value=mock_result)
        mock_manager_func.return_value = mock_manager
        
        def run_async(coro):
            return asyncio.get_event_loop().run_until_complete(coro())
            
        mock_asyncio_run.side_effect = run_async
        
        result = cli_runner.invoke(cli, [
            'agent', 'deploy', 
            '--package', 'enterprise',
            '--customer-id', 'test-corp'
        ])
        
        assert result.exit_code == 0
        assert "Deploying enterprise agent package" in result.output
        
    @patch('symphony_cli.main.asyncio.run')
    @patch('symphony_cli.main.create_agent_manager')
    def test_agent_status_general(self, mock_manager_func, mock_asyncio_run, cli_runner):
        """Test agent status command general overview"""
        mock_manager = Mock()
        mock_manager_func.return_value = mock_manager
        
        def run_async(coro):
            return asyncio.get_event_loop().run_until_complete(coro())
            
        mock_asyncio_run.side_effect = run_async
        
        result = cli_runner.invoke(cli, ['agent', 'status'])
        
        assert result.exit_code == 0
        assert "Agent Ecosystem Status" in result.output
        
    @patch('symphony_cli.main.asyncio.run')
    @patch('symphony_cli.main.create_agent_manager')
    def test_agent_handoff_command(self, mock_manager_func, mock_asyncio_run, cli_runner):
        """Test agent handoff command"""
        mock_manager = Mock()
        mock_result = {
            'success': True,
            'handoff_id': 'handoff-123',
            'completion_summary': 'Task completed successfully'
        }
        mock_manager.execute_handoff = AsyncMock(return_value=mock_result)
        mock_manager_func.return_value = mock_manager
        
        def run_async(coro):
            return asyncio.get_event_loop().run_until_complete(coro())
            
        mock_asyncio_run.side_effect = run_async
        
        result = cli_runner.invoke(cli, [
            'agent', 'handoff', 'agent1', 'agent2',
            '--context', '{"task": "complete"}',
            '--user-objective', 'Finish the project'
        ])
        
        assert result.exit_code == 0
        assert "Executing handoff: agent1 → agent2" in result.output
        
    def test_agent_handoff_invalid_json(self, cli_runner):
        """Test agent handoff command with invalid JSON context"""
        with patch('symphony_cli.main.asyncio.run'):
            with patch('symphony_cli.main.create_agent_manager'):
                result = cli_runner.invoke(cli, [
                    'agent', 'handoff', 'agent1', 'agent2',
                    '--context', 'invalid json'
                ])
                
                assert result.exit_code == 0
                # The command should handle JSON parsing error internally
        
    @patch('symphony_cli.main.asyncio.run')
    @patch('symphony_cli.main.create_agent_manager')
    def test_agent_execute_command(self, mock_manager_func, mock_asyncio_run, cli_runner):
        """Test agent execute command"""
        mock_manager = Mock()
        mock_result = {
            'success': True,
            'execution_time': 2.5,
            'result': 'Task completed successfully'
        }
        mock_manager.execute_agent_task = AsyncMock(return_value=mock_result)
        mock_manager_func.return_value = mock_manager
        
        def run_async(coro):
            return asyncio.get_event_loop().run_until_complete(coro())
            
        mock_asyncio_run.side_effect = run_async
        
        result = cli_runner.invoke(cli, [
            'agent', 'execute', 'test-agent', 'Complete the analysis',
            '--priority', 'high'
        ])
        
        assert result.exit_code == 0
        assert "Executing task with agent: test-agent" in result.output
        assert "Priority: high" in result.output
        
    @patch('symphony_cli.main.asyncio.run')
    @patch('symphony_cli.main.create_agent_manager')
    @patch('symphony_cli.main.asyncio.sleep')
    def test_agent_monitor_command(self, mock_sleep, mock_manager_func, mock_asyncio_run, cli_runner):
        """Test agent monitor command"""
        mock_manager = Mock()
        mock_metrics = {
            'system_health': 95.5,
            'agent_coordination': 98.2,
            'performance_score': 92.1
        }
        mock_manager.get_system_metrics = AsyncMock(return_value=mock_metrics)
        mock_manager_func.return_value = mock_manager
        
        # Mock time to prevent infinite loop
        with patch('time.time') as mock_time:
            mock_time.side_effect = [0, 5, 10, 65]  # Start, first check, second check, exit
            
            def run_async(coro):
                return asyncio.get_event_loop().run_until_complete(coro())
                
            mock_asyncio_run.side_effect = run_async
            
            result = cli_runner.invoke(cli, [
                'agent', 'monitor',
                '--interval', '5',
                '--duration', '60'
            ])
            
            assert result.exit_code == 0
            assert "Starting agent performance monitoring" in result.output


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI not available")
class TestConfigCommands:
    """Test config command group"""
    
    def test_config_help(self, cli_runner):
        """Test config command group help"""
        result = cli_runner.invoke(cli, ['config', '--help'])
        
        assert result.exit_code == 0
        assert "Configuration management and generation" in result.output
        assert "generate" in result.output
        assert "validate" in result.output
        
    def test_config_generate_command(self, cli_runner):
        """Test config generate command"""
        result = cli_runner.invoke(cli, ['config', 'generate', 'test-corp', 'enterprise'])
        
        assert result.exit_code == 0
        assert "Generating Configuration for test-corp" in result.output
        assert "Organization Type: enterprise" in result.output
        assert "Master configuration schema loaded" in result.output
        assert "Configuration saved to: configs/test-corp-config.yaml" in result.output
        
    def test_config_generate_default_type(self, cli_runner):
        """Test config generate command with default organization type"""
        result = cli_runner.invoke(cli, ['config', 'generate', 'startup-corp'])
        
        assert result.exit_code == 0
        assert "Organization Type: startup" in result.output
        
    def test_config_validate_command(self, cli_runner):
        """Test config validate command"""
        result = cli_runner.invoke(cli, ['config', 'validate', 'test-config.yaml'])
        
        assert result.exit_code == 0
        assert "Validating Configuration: test-config.yaml" in result.output
        assert "Schema validation: PASSED" in result.output
        assert "Configuration is valid and deployment-ready" in result.output
        
    def test_config_validate_default_file(self, cli_runner):
        """Test config validate command with default file"""
        result = cli_runner.invoke(cli, ['config', 'validate'])
        
        assert result.exit_code == 0
        assert "Validating Configuration: master-configuration.yaml" in result.output


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI not available")
class TestMonitorCommands:
    """Test monitor command group"""
    
    def test_monitor_help(self, cli_runner):
        """Test monitor command group help"""
        result = cli_runner.invoke(cli, ['monitor', '--help'])
        
        assert result.exit_code == 0
        assert "Real-time monitoring and analytics" in result.output
        assert "dashboard" in result.output
        
    def test_monitor_dashboard_command(self, cli_runner):
        """Test monitor dashboard command"""
        result = cli_runner.invoke(cli, ['monitor', 'dashboard'])
        
        assert result.exit_code == 0
        assert "Symphony Monitoring Dashboard" in result.output
        assert "System Health" in result.output
        assert "99.9% uptime" in result.output
        assert "Business Metrics:" in result.output
        assert "Revenue Growth: +35% YoY" in result.output
        assert "Customer Satisfaction: 4.9/5" in result.output


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI not available")
class TestStatusCommand:
    """Test status command"""
    
    def test_status_command(self, cli_runner):
        """Test status command shows implementation status"""
        result = cli_runner.invoke(cli, ['status'])
        
        assert result.exit_code == 0
        assert "Symphony Implementation Bridge Status" in result.output
        assert "Core Components" in result.output
        assert "Master Configuration System" in result.output
        assert "Linear Integration" in result.output
        assert "GitHub Integration" in result.output
        assert "CLI Interface" in result.output
        assert "Quick Implementation Commands:" in result.output
        assert "symphony onboard start mycorp" in result.output


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI not available") 
class TestCLIErrorHandling:
    """Test CLI error handling and edge cases"""
    
    def test_import_errors_handled_gracefully(self, cli_runner):
        """Test that import errors are handled gracefully"""
        # The CLI should import and work even with missing optional dependencies
        result = cli_runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        
    def test_missing_symphony_packages_warning(self, cli_runner):
        """Test warning messages for missing Symphony packages"""
        with patch('symphony_cli.main.create_agent_manager', side_effect=ImportError("Test import error")):
            result = cli_runner.invoke(cli, ['agent', 'deploy', '--package', 'startup'])
            
            assert result.exit_code == 0
            assert "Import error:" in result.output
            assert "ensure Symphony packages are properly installed" in result.output
            
    def test_async_function_error_handling(self, cli_runner):
        """Test error handling in async function execution"""
        with patch('symphony_cli.main.asyncio.run', side_effect=Exception("Async error")):
            result = cli_runner.invoke(cli, ['linear', 'init', 'test-corp'])
            
            # Should not crash the CLI
            assert result.exit_code == 0
            
    def test_invalid_command_arguments(self, cli_runner):
        """Test handling of invalid command arguments"""
        # Test invalid agent package choice
        result = cli_runner.invoke(cli, ['agent', 'deploy', '--package', 'invalid'])
        
        assert result.exit_code != 0  # Should fail with invalid choice
        
    def test_file_operation_errors(self, cli_runner):
        """Test handling of file operation errors in setup commands"""
        with patch('symphony_cli.main.Path.exists', side_effect=OSError("File system error")):
            result = cli_runner.invoke(cli, ['setup', 'env'])
            
            # Should handle file system errors gracefully
            assert result.exit_code == 0 or "error" in result.output.lower()


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI not available")
class TestCLIIntegration:
    """Test CLI integration with command groups"""
    
    def test_onboard_command_integration(self, cli_runner):
        """Test onboard command integration if available"""
        result = cli_runner.invoke(cli, ['onboard', '--help'])
        
        # Should either work or show helpful error message
        # The command may not be available depending on imports
        assert result.exit_code in [0, 2]  # 0 = success, 2 = command not found
        
    def test_auth_command_integration(self, cli_runner):
        """Test auth command integration if available"""
        result = cli_runner.invoke(cli, ['auth', '--help'])
        
        # Should either work or show helpful error message
        assert result.exit_code in [0, 2]  # 0 = success, 2 = command not found
        
    def test_integration_command_integration(self, cli_runner):
        """Test integration command integration if available"""
        result = cli_runner.invoke(cli, ['integration', '--help'])
        
        # Should either work or show helpful error message
        assert result.exit_code in [0, 2]  # 0 = success, 2 = command not found
        
    def test_hierarchy_command_integration(self, cli_runner):
        """Test hierarchy command integration if available"""
        result = cli_runner.invoke(cli, ['hierarchy', '--help'])
        
        # Should either work or show helpful error message
        assert result.exit_code in [0, 2]  # 0 = success, 2 = command not found


class TestCLITestInfrastructure:
    """Test the test infrastructure itself"""
    
    def test_cli_runner_fixture(self, cli_runner):
        """Test that CLI runner fixture works correctly"""
        assert cli_runner is not None
        assert hasattr(cli_runner, 'invoke')
        
    def test_temp_files_cleanup(self, sample_config_file, temp_env_file):
        """Test that temporary files are created and accessible"""
        assert Path(sample_config_file).exists()
        assert Path(temp_env_file).exists()
        
        # Verify file contents
        with open(sample_config_file) as f:
            config = yaml.safe_load(f)
            assert 'organization' in config
            assert config['organization']['name'] == 'Test Corp'
            
    def test_mock_setup(self):
        """Test that mock setup works correctly"""
        with patch('symphony_cli.main.console') as mock_console:
            mock_console.print.return_value = None
            mock_console.print("test")
            mock_console.print.assert_called_once_with("test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])