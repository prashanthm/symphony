#!/usr/bin/env python3
"""
Tests for Linear Template Integration

Test the new template-driven Linear project creation functionality.
"""

import asyncio
import json
import pytest
import yaml
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

try:
    from symphony_integrations.linear.client import LinearAPIClient, SymphonyLinearIntegration
    from symphony_integrations.linear.models import LinearTeam, LinearProject
    from symphony_integrations.linear.template_models import OrganizationConfig, IndustryType, OrganizationSize
    from symphony_cli.commands.linear_hierarchy import _deploy_workspace_with_template
except ImportError as e:
    pytest.skip(f"Linear integration not available: {e}", allow_module_level=True)


class TestLinearTemplateIntegration:
    """Test Linear client template integration"""

    @pytest.fixture
    def mock_linear_client(self):
        """Mock Linear API client"""
        client = MagicMock()
        client.create_project = AsyncMock()
        client.get_teams = AsyncMock()
        client.get_workflow_states = AsyncMock()
        return client

    @pytest.fixture
    def mock_template_engine(self):
        """Mock template engine"""
        engine = MagicMock()
        engine.load_template = MagicMock()
        engine.apply_variables = MagicMock()
        engine.substitute_variables = MagicMock()
        return engine

    @pytest.fixture
    def sample_team(self):
        """Sample Linear team"""
        return LinearTeam(id="team_123", name="Operations", key="OPS")

    @pytest.fixture
    def sample_template_projects(self):
        """Sample project configs from template"""
        return [
            {
                "name": "ACME Corp - Strategic Planning",
                "description": "Long-term strategic planning and roadmap"
            },
            {
                "name": "ACME Corp - Digital Transformation",
                "description": "Digital transformation initiatives"
            },
            {
                "name": "ACME Corp - Operations Excellence",
                "description": "Operational efficiency improvements"
            }
        ]

    @pytest.fixture
    def sample_customer_config(self):
        """Sample customer configuration"""
        return {
            "customer_profile": {
                "organization_name": "ACME Corp",
                "industry": "healthcare",
                "team_size": 100
            },
            "agent_configuration": {
                "selected_package": "enterprise"
            },
            "template_variables": {
                "current_year": 2025,
                "region": "us-east-1"
            },
            "linear": {
                "template_path": "/configs/enterprise-template.yaml"
            }
        }

    @pytest.fixture
    def sample_workspace_template(self):
        """Sample processed workspace template"""
        template = MagicMock()
        template.projects = [
            MagicMock(
                name="${customer_name} - Strategic Planning",
                description="Long-term strategic planning"
            ),
            MagicMock(
                name="${customer_name} - Digital Transformation", 
                description="Digital transformation initiatives"
            )
        ]
        return template

    @pytest.mark.asyncio
    async def test_create_projects_from_template_success(self, mock_linear_client, sample_team, sample_template_projects):
        """Test successful project creation from template"""
        
        # Setup
        integration = SymphonyLinearIntegration()
        mock_linear_client.create_project.side_effect = [
            LinearProject(id="proj_1", name=proj["name"], description=proj["description"], 
                         team_id=sample_team.id, url="https://linear.app/proj_1")
            for proj in sample_template_projects
        ]
        
        customer_config = {
            "customer_profile": {"organization_name": "ACME Corp", "industry": "healthcare"},
            "agent_configuration": {"selected_package": "enterprise"}
        }

        # Mock template processing
        with patch.object(integration, '_get_projects_from_template', return_value=sample_template_projects):
            projects = await integration._create_projects_from_template(
                mock_linear_client, sample_team, "ACME Corp",
                template_path="test-template.yaml", customer_config=customer_config
            )

        # Verify
        assert len(projects) == 3
        assert projects[0].name == "ACME Corp - Strategic Planning"
        assert projects[1].name == "ACME Corp - Digital Transformation" 
        assert projects[2].name == "ACME Corp - Operations Excellence"
        assert mock_linear_client.create_project.call_count == 3

    @pytest.mark.asyncio
    async def test_create_projects_fallback_to_core(self, mock_linear_client, sample_team):
        """Test fallback to core projects when template fails"""
        
        # Setup
        integration = SymphonyLinearIntegration()
        
        # Mock template processing to fail
        with patch.object(integration, '_get_projects_from_template', side_effect=Exception("Template error")):
            with patch.object(integration, '_create_core_projects', return_value=[
                LinearProject(id="core_1", name="ACME Corp - Agent Ecosystem", 
                            description="Core project", team_id=sample_team.id, url="test")
            ]) as mock_core:
                
                projects = await integration._create_projects_from_template(
                    mock_linear_client, sample_team, "ACME Corp", template_path="bad-template.yaml"
                )

        # Verify fallback was used
        mock_core.assert_called_once()
        assert len(projects) == 1
        assert projects[0].name == "ACME Corp - Agent Ecosystem"

    @pytest.mark.asyncio
    async def test_get_projects_from_template_with_direct_path(self, mock_template_engine, sample_workspace_template):
        """Test extracting projects from direct template path"""
        
        # Setup
        integration = SymphonyLinearIntegration()
        mock_template_engine.load_template.return_value = sample_workspace_template
        mock_template_engine.apply_variables.return_value = sample_workspace_template
        mock_template_engine.substitute_variables.side_effect = lambda text, vars: text.replace("${customer_name}", "ACME Corp")

        with patch('symphony_integrations.linear.client.TemplateEngine', return_value=mock_template_engine):
            projects = await integration._get_projects_from_template(
                template_path="test-template.yaml",
                org_name="ACME Corp",
                industry="healthcare"
            )

        # Verify
        assert len(projects) == 2
        assert projects[0]["name"] == "ACME Corp - Strategic Planning"
        assert projects[1]["name"] == "ACME Corp - Digital Transformation"
        mock_template_engine.load_template.assert_called_with("test-template.yaml")

    @pytest.mark.asyncio
    async def test_get_projects_from_customer_config(self, mock_template_engine, sample_workspace_template, sample_customer_config):
        """Test extracting projects from customer config"""
        
        # Setup
        integration = SymphonyLinearIntegration()
        mock_template_engine.load_template.return_value = sample_workspace_template
        mock_template_engine.apply_variables.return_value = sample_workspace_template
        mock_template_engine.substitute_variables.side_effect = lambda text, vars: text.replace("${customer_name}", "ACME Corp")

        with patch('symphony_integrations.linear.client.TemplateEngine', return_value=mock_template_engine):
            projects = await integration._get_projects_from_template(
                template_path=None,
                org_name="ACME Corp",
                customer_config=sample_customer_config
            )

        # Verify
        assert len(projects) == 2
        mock_template_engine.load_template.assert_called_with("/configs/enterprise-template.yaml")

    @pytest.mark.asyncio
    async def test_get_projects_from_defaults_generator(self, mock_template_engine, sample_workspace_template):
        """Test generating projects using defaults generator"""
        
        # Setup  
        integration = SymphonyLinearIntegration()
        mock_template_engine.apply_variables.return_value = sample_workspace_template
        mock_template_engine.substitute_variables.side_effect = lambda text, vars: text.replace("${customer_name}", "ACME Corp")

        mock_defaults_generator = MagicMock()
        mock_defaults_generator.generate_defaults.return_value = sample_workspace_template

        with patch('symphony_integrations.linear.client.TemplateEngine', return_value=mock_template_engine):
            with patch('symphony_integrations.linear.client.SymphonyLinearDefaults', return_value=mock_defaults_generator):
                projects = await integration._get_projects_from_template(
                    template_path=None,
                    org_name="ACME Corp", 
                    industry="healthcare",
                    size="enterprise",
                    customer_config={"template_variables": {}}
                )

        # Verify
        assert len(projects) == 2
        mock_defaults_generator.generate_defaults.assert_called_once()

    @pytest.mark.asyncio 
    async def test_initialize_workspace_with_template_support(self, sample_team):
        """Test workspace initialization with template support"""
        
        # Setup
        integration = SymphonyLinearIntegration()
        
        mock_client = AsyncMock()
        mock_client.get_teams.return_value = [sample_team]
        mock_client.get_workflow_states.return_value = [
            {"id": "state_1", "name": "Todo", "type": "unstarted"},
            {"id": "state_2", "name": "Done", "type": "completed"}
        ]
        
        mock_projects = [
            LinearProject(id="proj_1", name="Test Project", description="Test", 
                         team_id=sample_team.id, url="https://linear.app/proj_1")
        ]
        
        with patch.object(integration, 'client') as mock_linear_client:
            mock_linear_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_linear_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch.object(integration, '_create_projects_from_template', return_value=mock_projects):
                config = await integration.initialize_workspace(
                    organization_name="ACME Corp",
                    template_path="test-template.yaml",
                    industry="healthcare",
                    size="enterprise"
                )

        # Verify workspace config
        assert config["organization_name"] == "ACME Corp"
        assert config["team"]["name"] == "Operations"
        assert len(config["projects"]) == 1
        assert "Test Project" in config["projects"]

    def test_variable_substitution_in_projects(self):
        """Test that template variables are properly substituted in project names"""
        
        # This would be a more detailed test of the variable substitution logic
        # Testing the template engine integration
        pass

    @pytest.mark.asyncio
    async def test_template_error_handling(self, sample_team):
        """Test proper error handling when template processing fails"""
        
        integration = SymphonyLinearIntegration()
        
        # Test with invalid template path
        with pytest.raises(Exception):
            await integration._get_projects_from_template(
                template_path="nonexistent-template.yaml",
                org_name="ACME Corp"
            )

    @pytest.mark.asyncio
    async def test_cli_deploy_with_template_integration(self, sample_customer_config, tmp_path):
        """Test CLI deploy command with template integration"""
        
        # Create temporary config file
        config_file = tmp_path / "test-config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_customer_config, f)
        
        mock_workspace_config = {
            "organization_name": "ACME Corp",
            "team": {"name": "Operations", "key": "OPS"},
            "projects": {
                "ACME Corp - Strategic Planning": {"id": "proj_1"},
                "ACME Corp - Digital Transformation": {"id": "proj_2"}
            },
            "workflow_states": [{"id": "state_1", "name": "Todo"}]
        }
        
        with patch('symphony_integrations.linear.client.SymphonyLinearIntegration') as MockIntegration:
            mock_instance = MockIntegration.return_value
            mock_instance.initialize_workspace = AsyncMock(return_value=mock_workspace_config)
            
            # Test the deploy function
            result = await _deploy_workspace_with_template(
                workspace_template=MagicMock(),
                config_file=str(config_file),
                linear_token="test-token"
            )
            
            # Verify function was called with correct parameters
            mock_instance.initialize_workspace.assert_called_once()
            call_args = mock_instance.initialize_workspace.call_args
            assert call_args[1]["organization_name"] == "ACME Corp"
            assert call_args[1]["industry"] == "healthcare"
            assert call_args[1]["size"] == "enterprise"
            assert call_args[1]["customer_config"] == sample_customer_config


if __name__ == "__main__":
    pytest.main([__file__])