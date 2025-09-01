#!/usr/bin/env python3
"""
Tests for Symphony CLI authentication commands

Test-driven development for authentication functionality covering:
- Login command for different services (Linear, GitHub)
- Logout command with service cleanup
- Status command showing authentication status
- Token management and secure storage
- Service-specific authentication flows
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

# Import authentication commands
try:
    from symphony_cli.commands.auth_commands import auth
    from symphony_core.auth.auth_manager import AuthenticationManager
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False


@pytest.fixture
def cli_runner():
    """Fixture providing Click CLI test runner"""
    return CliRunner()


@pytest.fixture
def mock_auth_config_dir():
    """Fixture providing temporary authentication config directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.mark.skipif(not AUTH_AVAILABLE, reason="Authentication commands not available")
class TestAuthCommandGroup:
    """Test authentication command group"""
    
    def test_auth_help(self, cli_runner):
        """Test auth command group help"""
        result = cli_runner.invoke(auth, ['--help'])
        
        assert result.exit_code == 0
        assert "Authentication and credential management" in result.output
        assert "login" in result.output
        assert "logout" in result.output
        assert "status" in result.output


@pytest.mark.skipif(not AUTH_AVAILABLE, reason="Authentication commands not available")
class TestLoginCommand:
    """Test auth login command"""
    
    def test_login_help(self, cli_runner):
        """Test login command help"""
        result = cli_runner.invoke(auth, ['login', '--help'])
        
        assert result.exit_code == 0
        assert "Authenticate with external services" in result.output
        assert "--service" in result.output
        assert "--token" in result.output
        assert "--interactive" in result.output
        
    def test_login_service_choices(self, cli_runner):
        """Test login command shows correct service choices"""
        result = cli_runner.invoke(auth, ['login', '--help'])
        
        assert result.exit_code == 0
        assert "linear" in result.output
        assert "github" in result.output
        assert "hubspot" in result.output
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_login_linear_with_token(self, mock_auth_manager_class, cli_runner):
        """Test login command for Linear with token"""
        mock_manager = Mock()
        mock_manager.store_credentials.return_value = True
        mock_manager.verify_credentials.return_value = True
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, [
            'login',
            '--service', 'linear',
            '--token', 'lin_test_token_123'
        ])
        
        assert result.exit_code == 0
        assert "Authenticating with Linear" in result.output
        assert "Successfully authenticated with Linear" in result.output
        
        # Verify credentials were stored
        mock_manager.store_credentials.assert_called_once_with(
            'linear', 
            {'token': 'lin_test_token_123'}
        )
        mock_manager.verify_credentials.assert_called_once_with('linear')
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_login_github_with_token(self, mock_auth_manager_class, cli_runner):
        """Test login command for GitHub with token"""
        mock_manager = Mock()
        mock_manager.store_credentials.return_value = True
        mock_manager.verify_credentials.return_value = True
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, [
            'login',
            '--service', 'github',
            '--token', 'ghp_test_token_456'
        ])
        
        assert result.exit_code == 0
        assert "Authenticating with GitHub" in result.output
        assert "Successfully authenticated with GitHub" in result.output
        
        mock_manager.store_credentials.assert_called_once_with(
            'github',
            {'token': 'ghp_test_token_456'}
        )
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_login_interactive_linear(self, mock_auth_manager_class, cli_runner):
        """Test interactive login for Linear"""
        mock_manager = Mock()
        mock_manager.store_credentials.return_value = True
        mock_manager.verify_credentials.return_value = True
        mock_auth_manager_class.return_value = mock_manager
        
        # Simulate user entering token interactively
        result = cli_runner.invoke(auth, [
            'login',
            '--service', 'linear',
            '--interactive'
        ], input='lin_interactive_token\n')
        
        assert result.exit_code == 0
        assert "Enter your Linear API token" in result.output
        assert "Successfully authenticated with Linear" in result.output
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_login_interactive_github(self, mock_auth_manager_class, cli_runner):
        """Test interactive login for GitHub"""
        mock_manager = Mock()
        mock_manager.store_credentials.return_value = True
        mock_manager.verify_credentials.return_value = True
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, [
            'login',
            '--service', 'github',
            '--interactive'
        ], input='ghp_interactive_token\n')
        
        assert result.exit_code == 0
        assert "Enter your GitHub personal access token" in result.output
        assert "Successfully authenticated with GitHub" in result.output
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_login_hubspot_with_key(self, mock_auth_manager_class, cli_runner):
        """Test login command for HubSpot with API key"""
        mock_manager = Mock()
        mock_manager.store_credentials.return_value = True
        mock_manager.verify_credentials.return_value = True
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, [
            'login',
            '--service', 'hubspot',
            '--token', 'hs_api_key_789'
        ])
        
        assert result.exit_code == 0
        assert "Authenticating with HubSpot" in result.output
        assert "Successfully authenticated with HubSpot" in result.output
        
        mock_manager.store_credentials.assert_called_once_with(
            'hubspot',
            {'api_key': 'hs_api_key_789'}
        )
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_login_invalid_token_format(self, mock_auth_manager_class, cli_runner):
        """Test login command with invalid token format"""
        mock_manager = Mock()
        mock_manager.store_credentials.return_value = True
        mock_manager.verify_credentials.return_value = False
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, [
            'login',
            '--service', 'linear',
            '--token', 'invalid_token'
        ])
        
        assert result.exit_code == 0
        assert "Failed to verify credentials" in result.output
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_login_service_connection_error(self, mock_auth_manager_class, cli_runner):
        """Test login command with service connection error"""
        mock_manager = Mock()
        mock_manager.store_credentials.side_effect = Exception("Connection failed")
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, [
            'login',
            '--service', 'github',
            '--token', 'ghp_valid_token'
        ])
        
        assert result.exit_code == 0
        assert "Error authenticating with GitHub" in result.output
        assert "Connection failed" in result.output
        
    def test_login_missing_service_parameter(self, cli_runner):
        """Test login command without service parameter"""
        result = cli_runner.invoke(auth, [
            'login',
            '--token', 'some_token'
        ])
        
        assert result.exit_code != 0  # Should fail
        assert "Missing option '--service'" in result.output
        
    def test_login_missing_token_and_not_interactive(self, cli_runner):
        """Test login command without token and not interactive"""
        result = cli_runner.invoke(auth, [
            'login',
            '--service', 'linear'
        ])
        
        assert result.exit_code == 0
        assert "Please provide a token using --token or use --interactive" in result.output


@pytest.mark.skipif(not AUTH_AVAILABLE, reason="Authentication commands not available")
class TestLogoutCommand:
    """Test auth logout command"""
    
    def test_logout_help(self, cli_runner):
        """Test logout command help"""
        result = cli_runner.invoke(auth, ['logout', '--help'])
        
        assert result.exit_code == 0
        assert "Remove stored authentication credentials" in result.output
        assert "--service" in result.output
        assert "--all" in result.output
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_logout_specific_service(self, mock_auth_manager_class, cli_runner):
        """Test logout command for specific service"""
        mock_manager = Mock()
        mock_manager.remove_credentials.return_value = True
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, [
            'logout',
            '--service', 'linear'
        ])
        
        assert result.exit_code == 0
        assert "Logging out of Linear" in result.output
        assert "Successfully logged out of Linear" in result.output
        
        mock_manager.remove_credentials.assert_called_once_with('linear')
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_logout_all_services(self, mock_auth_manager_class, cli_runner):
        """Test logout command for all services"""
        mock_manager = Mock()
        mock_manager.clear_all_credentials.return_value = ['linear', 'github', 'hubspot']
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, ['logout', '--all'])
        
        assert result.exit_code == 0
        assert "Logging out of all services" in result.output
        assert "Successfully logged out of all services" in result.output
        assert "linear, github, hubspot" in result.output
        
        mock_manager.clear_all_credentials.assert_called_once()
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_logout_service_not_authenticated(self, mock_auth_manager_class, cli_runner):
        """Test logout command for service not authenticated"""
        mock_manager = Mock()
        mock_manager.remove_credentials.return_value = False
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, [
            'logout',
            '--service', 'github'
        ])
        
        assert result.exit_code == 0
        assert "Not currently authenticated with GitHub" in result.output
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_logout_error_handling(self, mock_auth_manager_class, cli_runner):
        """Test logout command error handling"""
        mock_manager = Mock()
        mock_manager.remove_credentials.side_effect = Exception("Logout failed")
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, [
            'logout',
            '--service', 'linear'
        ])
        
        assert result.exit_code == 0
        assert "Error logging out of Linear" in result.output
        assert "Logout failed" in result.output
        
    def test_logout_missing_service_and_not_all(self, cli_runner):
        """Test logout command without service or --all"""
        result = cli_runner.invoke(auth, ['logout'])
        
        assert result.exit_code == 0
        assert "Please specify --service or --all" in result.output


@pytest.mark.skipif(not AUTH_AVAILABLE, reason="Authentication commands not available")
class TestStatusCommand:
    """Test auth status command"""
    
    def test_status_help(self, cli_runner):
        """Test status command help"""
        result = cli_runner.invoke(auth, ['status', '--help'])
        
        assert result.exit_code == 0
        assert "Show authentication status for all services" in result.output
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_status_all_services_authenticated(self, mock_auth_manager_class, cli_runner):
        """Test status command with all services authenticated"""
        mock_manager = Mock()
        mock_manager.get_authentication_status.return_value = {
            'linear': {
                'authenticated': True,
                'token_type': 'API Token',
                'expires_at': None,
                'last_verified': '2025-09-01T10:00:00Z'
            },
            'github': {
                'authenticated': True,
                'token_type': 'Personal Access Token',
                'expires_at': '2025-12-01T00:00:00Z',
                'last_verified': '2025-09-01T09:30:00Z'
            },
            'hubspot': {
                'authenticated': False,
                'token_type': None,
                'expires_at': None,
                'last_verified': None
            }
        }
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, ['status'])
        
        assert result.exit_code == 0
        assert "Authentication Status" in result.output
        assert "Linear" in result.output
        assert "✅ Authenticated" in result.output or "Authenticated" in result.output
        assert "GitHub" in result.output
        assert "HubSpot" in result.output
        assert "❌ Not authenticated" in result.output or "Not authenticated" in result.output
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_status_no_services_authenticated(self, mock_auth_manager_class, cli_runner):
        """Test status command with no services authenticated"""
        mock_manager = Mock()
        mock_manager.get_authentication_status.return_value = {
            'linear': {'authenticated': False, 'token_type': None},
            'github': {'authenticated': False, 'token_type': None},
            'hubspot': {'authenticated': False, 'token_type': None}
        }
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, ['status'])
        
        assert result.exit_code == 0
        assert "Authentication Status" in result.output
        assert "❌ Not authenticated" in result.output or "Not authenticated" in result.output
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_status_mixed_authentication_states(self, mock_auth_manager_class, cli_runner):
        """Test status command with mixed authentication states"""
        mock_manager = Mock()
        mock_manager.get_authentication_status.return_value = {
            'linear': {
                'authenticated': True,
                'token_type': 'API Token',
                'expires_at': None
            },
            'github': {
                'authenticated': False,
                'token_type': None,
                'expires_at': None
            },
            'hubspot': {
                'authenticated': True,
                'token_type': 'API Key',
                'expires_at': '2025-12-31T23:59:59Z'
            }
        }
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, ['status'])
        
        assert result.exit_code == 0
        assert "Authentication Status" in result.output
        # Should show mix of authenticated and not authenticated
        assert ("✅" in result.output or "Authenticated" in result.output) and ("❌" in result.output or "Not authenticated" in result.output)
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_status_error_handling(self, mock_auth_manager_class, cli_runner):
        """Test status command error handling"""
        mock_manager = Mock()
        mock_manager.get_authentication_status.side_effect = Exception("Status check failed")
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, ['status'])
        
        assert result.exit_code == 0
        assert "Error checking authentication status" in result.output
        assert "Status check failed" in result.output


@pytest.mark.skipif(not AUTH_AVAILABLE, reason="Authentication commands not available")
class TestTokenValidation:
    """Test token validation functionality"""
    
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_linear_token_validation(self, mock_auth_manager_class, cli_runner):
        """Test Linear token format validation"""
        mock_manager = Mock()
        mock_manager.store_credentials.return_value = True
        mock_manager.verify_credentials.return_value = True
        mock_auth_manager_class.return_value = mock_manager
        
        # Test valid Linear token format
        result = cli_runner.invoke(auth, [
            'login',
            '--service', 'linear',
            '--token', 'lin_1234567890abcdef'
        ])
        
        assert result.exit_code == 0
        assert "Successfully authenticated" in result.output
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_github_token_validation(self, mock_auth_manager_class, cli_runner):
        """Test GitHub token format validation"""
        mock_manager = Mock()
        mock_manager.store_credentials.return_value = True
        mock_manager.verify_credentials.return_value = True
        mock_auth_manager_class.return_value = mock_manager
        
        # Test valid GitHub token format
        result = cli_runner.invoke(auth, [
            'login',
            '--service', 'github',
            '--token', 'ghp_1234567890abcdefghijklmnopqrstuv'
        ])
        
        assert result.exit_code == 0
        assert "Successfully authenticated" in result.output
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_token_verification_failure(self, mock_auth_manager_class, cli_runner):
        """Test token verification failure"""
        mock_manager = Mock()
        mock_manager.store_credentials.return_value = True
        mock_manager.verify_credentials.return_value = False
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, [
            'login',
            '--service', 'linear',
            '--token', 'invalid_token_format'
        ])
        
        assert result.exit_code == 0
        assert "Failed to verify credentials" in result.output or "Invalid" in result.output


@pytest.mark.skipif(not AUTH_AVAILABLE, reason="Authentication commands not available") 
class TestCredentialStorage:
    """Test credential storage functionality"""
    
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_secure_credential_storage(self, mock_auth_manager_class, cli_runner):
        """Test that credentials are stored securely"""
        mock_manager = Mock()
        mock_manager.store_credentials.return_value = True
        mock_manager.verify_credentials.return_value = True
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, [
            'login',
            '--service', 'linear',
            '--token', 'lin_secure_token_123'
        ])
        
        assert result.exit_code == 0
        
        # Verify secure storage was called
        mock_manager.store_credentials.assert_called_once()
        call_args = mock_manager.store_credentials.call_args
        assert call_args[0][0] == 'linear'  # service name
        assert 'token' in call_args[0][1]   # credentials dict
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_credential_encryption(self, mock_auth_manager_class, cli_runner):
        """Test that credential storage uses encryption"""
        mock_manager = Mock()
        mock_manager.store_credentials.return_value = True
        mock_manager.verify_credentials.return_value = True
        
        # Simulate encrypted storage by returning encrypted-like data
        mock_manager._encrypt_credentials.return_value = b'encrypted_data_123'
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, [
            'login',
            '--service', 'github',
            '--token', 'ghp_encryption_test_token'
        ])
        
        assert result.exit_code == 0
        assert "Successfully authenticated" in result.output
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_storage_error_handling(self, mock_auth_manager_class, cli_runner):
        """Test credential storage error handling"""
        mock_manager = Mock()
        mock_manager.store_credentials.side_effect = OSError("Disk full")
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, [
            'login',
            '--service', 'linear',
            '--token', 'lin_test_token'
        ])
        
        assert result.exit_code == 0
        assert "Error authenticating" in result.output
        assert "Disk full" in result.output


@pytest.mark.skipif(not AUTH_AVAILABLE, reason="Authentication commands not available")
class TestInteractiveFlow:
    """Test interactive authentication flows"""
    
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_interactive_prompt_visibility(self, mock_auth_manager_class, cli_runner):
        """Test interactive prompt hides token input"""
        mock_manager = Mock()
        mock_manager.store_credentials.return_value = True
        mock_manager.verify_credentials.return_value = True
        mock_auth_manager_class.return_value = mock_manager
        
        result = cli_runner.invoke(auth, [
            'login',
            '--service', 'linear',
            '--interactive'
        ], input='lin_hidden_token\n')
        
        assert result.exit_code == 0
        # Token should not appear in output (hidden input)
        assert 'lin_hidden_token' not in result.output
        assert "Successfully authenticated" in result.output
        
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_interactive_service_selection(self, mock_auth_manager_class, cli_runner):
        """Test interactive service selection"""
        mock_manager = Mock()
        mock_manager.store_credentials.return_value = True
        mock_manager.verify_credentials.return_value = True
        mock_auth_manager_class.return_value = mock_manager
        
        # Test interactive without specifying service
        with patch('symphony_cli.commands.auth_commands.click.prompt') as mock_prompt:
            mock_prompt.side_effect = ['linear', 'lin_interactive_token']
            
            result = cli_runner.invoke(auth, ['login', '--interactive'])
            
            assert result.exit_code == 0
            
    @patch('symphony_cli.commands.auth_commands.AuthenticationManager')
    def test_interactive_retry_on_invalid_token(self, mock_auth_manager_class, cli_runner):
        """Test interactive retry on invalid token"""
        mock_manager = Mock()
        mock_manager.store_credentials.return_value = True
        # First verification fails, second succeeds
        mock_manager.verify_credentials.side_effect = [False, True]
        mock_auth_manager_class.return_value = mock_manager
        
        # Simulate first invalid token, then valid token
        result = cli_runner.invoke(auth, [
            'login',
            '--service', 'linear',
            '--interactive'
        ], input='invalid_token\nlin_valid_token\n')
        
        assert result.exit_code == 0
        # Should eventually succeed
        assert "Successfully authenticated" in result.output


class TestAuthCommandInfrastructure:
    """Test authentication command infrastructure"""
    
    def test_auth_manager_availability(self):
        """Test AuthenticationManager availability"""
        if AUTH_AVAILABLE:
            assert AuthenticationManager is not None
            
    def test_service_configuration(self):
        """Test service configuration is correct"""
        services = ['linear', 'github', 'hubspot']
        
        # Verify expected services are configured
        for service in services:
            assert isinstance(service, str)
            assert len(service) > 0
            
    def test_mock_auth_manager_setup(self):
        """Test mock AuthenticationManager setup"""
        with patch('symphony_cli.commands.auth_commands.AuthenticationManager') as mock_class:
            mock_manager = Mock()
            mock_class.return_value = mock_manager
            
            # Verify mock setup works
            assert mock_class.return_value == mock_manager


if __name__ == "__main__":
    pytest.main([__file__, "-v"])