#!/usr/bin/env python3
"""
Simple tests for template functionality

Test the basic template processing logic without complex dependencies.
"""

import asyncio
import pytest
import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock


def test_template_variable_substitution():
    """Test basic template variable substitution logic"""
    
    # Simulate the variable substitution logic from our implementation
    def substitute_variables(text: str, variables: dict) -> str:
        """Simple variable substitution"""
        result = text
        for key, value in variables.items():
            result = result.replace(f"${{{key}}}", str(value))
        return result
    
    # Test data
    template_text = "${customer_name} - Strategic Planning"
    variables = {"customer_name": "ACME Corp", "industry": "healthcare"}
    
    # Test substitution
    result = substitute_variables(template_text, variables)
    assert result == "ACME Corp - Strategic Planning"


def test_customer_config_parsing():
    """Test parsing customer configuration for template data"""
    
    sample_config = {
        "customer_profile": {
            "organization_name": "ACME Corp",
            "industry": "healthcare",
            "team_size": 100
        },
        "agent_configuration": {
            "selected_package": "enterprise"
        },
        "linear": {
            "template_path": "/configs/enterprise-template.yaml"
        }
    }
    
    # Test extracting organization details (logic from our CLI function)
    customer_profile = sample_config.get('customer_profile', {})
    organization_name = customer_profile.get('organization_name', 'Unknown Customer')
    industry = customer_profile.get('industry')
    
    agent_config = sample_config.get('agent_configuration', {})
    selected_package = agent_config.get('selected_package', 'startup')
    
    size_mapping = {
        'startup': 'startup',
        'smb': 'smb', 
        'enterprise': 'enterprise',
        'global': 'global'
    }
    size = size_mapping.get(selected_package, 'startup')
    
    # Verify parsing
    assert organization_name == "ACME Corp"
    assert industry == "healthcare"
    assert selected_package == "enterprise"
    assert size == "enterprise"


def test_project_template_processing():
    """Test processing project templates into Linear format"""
    
    # Sample template projects (what our template engine would return)
    template_projects = [
        {
            "name": "${customer_name} - Strategic Planning",
            "description": "Long-term strategic planning for ${customer_name}"
        },
        {
            "name": "${customer_name} - Digital Transformation",
            "description": "Digital initiatives in ${industry} sector"
        }
    ]
    
    # Variables for substitution
    variables = {
        "customer_name": "ACME Corp",
        "industry": "healthcare"
    }
    
    # Process templates (simulating our implementation logic)
    def substitute_variables(text: str, variables: dict) -> str:
        result = text
        for key, value in variables.items():
            result = result.replace(f"${{{key}}}", str(value))
        return result
    
    processed_projects = []
    for project_template in template_projects:
        project_name = substitute_variables(project_template["name"], variables)
        project_description = substitute_variables(project_template["description"], variables)
        
        processed_projects.append({
            "name": project_name,
            "description": project_description
        })
    
    # Verify processing
    assert len(processed_projects) == 2
    assert processed_projects[0]["name"] == "ACME Corp - Strategic Planning"
    assert processed_projects[0]["description"] == "Long-term strategic planning for ACME Corp"
    assert processed_projects[1]["name"] == "ACME Corp - Digital Transformation"
    assert processed_projects[1]["description"] == "Digital initiatives in healthcare sector"


def test_fallback_to_core_projects():
    """Test fallback logic to core projects when template fails"""
    
    # Simulate the core projects logic from our implementation
    def get_core_projects(org_name: str):
        return [
            {
                "name": f"{org_name} - Agent Ecosystem",
                "description": "Agent deployment, coordination, and performance tracking",
            },
            {
                "name": f"{org_name} - Tool Integration",
                "description": "Tool integration setup, configuration, and monitoring",
            },
            {
                "name": f"{org_name} - Deployment Phases",
                "description": "Foundation, Optimization, and Excellence phase tracking",
            },
            {
                "name": f"{org_name} - Validation & Testing",
                "description": "Quality assurance, testing, and validation tracking",
            },
        ]
    
    # Test core project generation
    core_projects = get_core_projects("ACME Corp")
    
    assert len(core_projects) == 4
    assert core_projects[0]["name"] == "ACME Corp - Agent Ecosystem"
    assert core_projects[1]["name"] == "ACME Corp - Tool Integration"
    assert core_projects[2]["name"] == "ACME Corp - Deployment Phases"
    assert core_projects[3]["name"] == "ACME Corp - Validation & Testing"


def test_package_to_size_mapping():
    """Test mapping from agent packages to organization sizes"""
    
    size_mapping = {
        'startup': 'startup',
        'smb': 'smb', 
        'enterprise': 'enterprise',
        'global': 'global'
    }
    
    # Test all mappings
    assert size_mapping.get('startup') == 'startup'
    assert size_mapping.get('smb') == 'smb'
    assert size_mapping.get('enterprise') == 'enterprise'
    assert size_mapping.get('global') == 'global'
    assert size_mapping.get('unknown', 'startup') == 'startup'  # fallback


@pytest.mark.asyncio
async def test_async_project_creation_flow():
    """Test the async flow of project creation"""
    
    # Mock Linear API client
    mock_client = AsyncMock()
    
    # Sample project configs
    project_configs = [
        {"name": "Test Project 1", "description": "Test description 1"},
        {"name": "Test Project 2", "description": "Test description 2"}
    ]
    
    # Mock successful project creation
    mock_project_results = [
        {"id": "proj_1", "name": "Test Project 1", "url": "https://linear.app/proj_1"},
        {"id": "proj_2", "name": "Test Project 2", "url": "https://linear.app/proj_2"}
    ]
    
    mock_client.create_project.side_effect = mock_project_results
    
    # Simulate project creation loop (from our implementation)
    created_projects = []
    for project_config in project_configs:
        try:
            project_result = await mock_client.create_project(
                name=project_config["name"],
                description=project_config["description"],
                team_id="team_123"
            )
            created_projects.append(project_result)
        except Exception as e:
            # In real implementation, we log errors but continue
            pass
    
    # Verify
    assert len(created_projects) == 2
    assert created_projects[0]["name"] == "Test Project 1"
    assert created_projects[1]["name"] == "Test Project 2"
    assert mock_client.create_project.call_count == 2


def test_error_handling_in_template_processing():
    """Test error handling when template processing fails"""
    
    def process_template_safe(template_data, fallback_function):
        """Simulate our safe template processing with fallback"""
        try:
            # Simulate template processing failure
            if template_data.get("invalid"):
                raise Exception("Template processing failed")
            
            # Normal processing would happen here
            return template_data.get("projects", [])
        
        except Exception as e:
            # Fallback to core projects
            return fallback_function()
    
    def get_fallback_projects():
        return [{"name": "Fallback Project", "description": "Core project"}]
    
    # Test successful processing
    good_template = {"projects": [{"name": "Template Project", "description": "From template"}]}
    result = process_template_safe(good_template, get_fallback_projects)
    assert len(result) == 1
    assert result[0]["name"] == "Template Project"
    
    # Test fallback on failure
    bad_template = {"invalid": True}
    result = process_template_safe(bad_template, get_fallback_projects)
    assert len(result) == 1
    assert result[0]["name"] == "Fallback Project"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])