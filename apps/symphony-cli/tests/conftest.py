#!/usr/bin/env python3
"""
Shared test configuration and fixtures for Symphony CLI tests

Provides common fixtures and test utilities used across all CLI test modules.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture(scope="session")
def temp_workspace():
    """Session-scoped temporary workspace directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_dir = Path(temp_dir) / "workspace"
        workspace_dir.mkdir()
        yield workspace_dir


@pytest.fixture
def mock_symphony_root():
    """Mock Symphony root directory structure"""
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        
        # Create expected directory structure
        (root / "libs").mkdir()
        (root / "apps").mkdir()
        (root / "workspace").mkdir()
        (root / "workspace" / "onboarding").mkdir()
        
        # Create pyproject.toml to mark as Symphony root
        (root / "pyproject.toml").write_text("""
[tool.uv.workspace]
members = ["libs/*", "apps/*"]
""")
        
        # Create .env.example
        (root / ".env.example").write_text("""
# Symphony Environment Configuration
LINEAR_API_TOKEN=your_linear_token_here
GITHUB_TOKEN=your_github_token_here
HUBSPOT_API_KEY=your_hubspot_key_here
""")
        
        yield root


@pytest.fixture
def mock_workflow_state():
    """Mock workflow state data"""
    return {
        'workflow_id': 'onboard-test-12345',
        'customer_name': 'Test Corp',
        'package': 'enterprise',
        'industry': 'technology',
        'status': 'in_progress',
        'current_step': 2,
        'total_steps': 5,
        'steps': [
            {
                'name': 'create_customer',
                'status': 'completed',
                'description': 'Create customer configuration'
            },
            {
                'name': 'setup_integrations',
                'status': 'completed',
                'description': 'Setup Linear and GitHub integrations'
            },
            {
                'name': 'deploy_agents',
                'status': 'in_progress',
                'description': 'Deploy agent ecosystem'
            },
            {
                'name': 'configure_workflows',
                'status': 'pending',
                'description': 'Configure automated workflows'
            },
            {
                'name': 'final_validation',
                'status': 'pending',
                'description': 'Final validation and testing'
            }
        ],
        'created_at': '2025-09-01T10:00:00Z',
        'updated_at': '2025-09-01T11:30:00Z'
    }


@pytest.fixture
def mock_agent_status():
    """Mock agent status data"""
    return [
        {
            'name': 'Maestro Coordinator',
            'status': '✅ Active',
            'role': 'Supreme orchestration',
            'performance': 98.5
        },
        {
            'name': 'CTO Agent',
            'status': '✅ Active',
            'role': 'Technical leadership',
            'performance': 96.2
        },
        {
            'name': 'CFO Agent',
            'status': '⚠️ Warning',
            'role': 'Financial management',
            'performance': 88.1
        },
        {
            'name': 'Victoria Strategic Intel',
            'status': '❌ Error',
            'role': 'Strategic intelligence',
            'performance': 0.0
        }
    ]


@pytest.fixture
def mock_auth_status():
    """Mock authentication status data"""
    return {
        'linear': {
            'authenticated': True,
            'token_type': 'API Token',
            'expires_at': None,
            'last_verified': '2025-09-01T10:00:00Z',
            'user_info': {
                'name': 'Test User',
                'email': 'test@example.com'
            }
        },
        'github': {
            'authenticated': True,
            'token_type': 'Personal Access Token',
            'expires_at': '2025-12-01T00:00:00Z',
            'last_verified': '2025-09-01T09:30:00Z',
            'user_info': {
                'login': 'testuser',
                'name': 'Test User'
            }
        },
        'hubspot': {
            'authenticated': False,
            'token_type': None,
            'expires_at': None,
            'last_verified': None,
            'user_info': None
        }
    }


@pytest.fixture
def mock_system_metrics():
    """Mock system metrics data"""
    return {
        'system_health': 99.2,
        'agent_coordination': 98.8,
        'performance_score': 95.5,
        'memory_usage': 68.3,
        'cpu_utilization': 45.2,
        'active_workflows': 12,
        'completed_tasks': 1847,
        'error_rate': 0.12
    }


class MockCLIComponent:
    """Base class for mock CLI components"""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockWorkflowManager(MockCLIComponent):
    """Mock WorkflowManager for testing"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.workflows = []
        
    def create_workflow(self, customer_name, package=None, industry=None, template_file=None):
        workflow = Mock()
        workflow.workflow_id = f"onboard-{customer_name}-12345"
        workflow.customer_name = customer_name
        workflow.package = package or 'enterprise'
        workflow.industry = industry or 'technology'
        workflow.status = Mock()
        workflow.status.value = 'in_progress'
        return workflow
        
    def list_workflows(self):
        return self.workflows
        
    def find_customer_workflow(self, customer_name):
        for workflow in self.workflows:
            if workflow.get('customer_name') == customer_name:
                return Mock(**workflow)
        return None


class MockAuthenticationManager(MockCLIComponent):
    """Mock AuthenticationManager for testing"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stored_credentials = {}
        
    def store_credentials(self, service, credentials):
        self.stored_credentials[service] = credentials
        return True
        
    def verify_credentials(self, service):
        return service in self.stored_credentials
        
    def remove_credentials(self, service):
        if service in self.stored_credentials:
            del self.stored_credentials[service]
            return True
        return False
        
    def get_authentication_status(self):
        status = {}
        for service in ['linear', 'github', 'hubspot']:
            status[service] = {
                'authenticated': service in self.stored_credentials,
                'token_type': 'API Token' if service in self.stored_credentials else None
            }
        return status


@pytest.fixture
def mock_workflow_manager():
    """Mock WorkflowManager instance"""
    return MockWorkflowManager()


@pytest.fixture
def mock_auth_manager():
    """Mock AuthenticationManager instance"""
    return MockAuthenticationManager()


# Utility functions for tests
def create_temp_config_file(config_data, suffix='.yaml'):
    """Create temporary configuration file with given data"""
    import yaml
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
        yaml.dump(config_data, f)
        return f.name


def create_temp_json_file(json_data):
    """Create temporary JSON file with given data"""
    import json
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(json_data, f)
        return f.name


def assert_table_contains_data(output, expected_data):
    """Assert that CLI table output contains expected data"""
    for item in expected_data:
        if isinstance(item, str):
            assert item in output
        elif isinstance(item, dict):
            for key, value in item.items():
                assert str(value) in output


def assert_success_output(result, expected_messages=None):
    """Assert CLI command succeeded with expected messages"""
    assert result.exit_code == 0
    
    if expected_messages:
        for message in expected_messages:
            assert message in result.output


def assert_error_output(result, expected_error_messages=None):
    """Assert CLI command handled error with expected messages"""
    # CLI should handle errors gracefully (exit_code 0) but show error messages
    assert result.exit_code == 0
    
    if expected_error_messages:
        for error_msg in expected_error_messages:
            assert error_msg in result.output


# Pytest markers for conditional testing
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires external services)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "cli: mark test as CLI interface test"
    )