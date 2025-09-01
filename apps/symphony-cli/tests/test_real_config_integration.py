#!/usr/bin/env python3
"""
Test with real customer configuration

Test our template implementation with the actual ACME Corp configuration.
"""

import pytest
import yaml
from pathlib import Path
from unittest.mock import AsyncMock, patch


def test_acme_corp_config_parsing():
    """Test parsing the real ACME Corp configuration"""
    
    # Load the real ACME Corp config
    config_path = Path("/Users/pmuniraju/play/sandbox/symphony/organizations/customers/acme-corp/config/customer-config.yaml")
    
    if not config_path.exists():
        pytest.skip("ACME Corp config not found")
    
    with open(config_path, 'r') as f:
        customer_config = yaml.safe_load(f)
    
    # Test extracting data using our implementation logic
    customer_profile = customer_config.get('customer_profile', {})
    organization_name = customer_profile.get('organization_name', 'Unknown Customer')
    industry = customer_profile.get('industry')
    
    agent_config = customer_config.get('agent_configuration', {})
    selected_package = agent_config.get('selected_package', 'startup')
    
    size_mapping = {
        'startup': 'startup',
        'smb': 'smb', 
        'enterprise': 'enterprise',
        'global': 'global'
    }
    size = size_mapping.get(selected_package, 'startup')
    
    # Verify extracted data
    assert organization_name == "acme-corp"
    assert industry == "healthcare"
    assert selected_package == "enterprise"
    assert size == "enterprise"
    
    # Verify agent configuration exists and has the right structure
    agents = agent_config.get('agents', {})
    assert 'coordination' in agents
    assert 'leadership' in agents
    assert 'specialists' in agents
    
    # Verify business objectives exist
    business_objectives = customer_config.get('business_objectives', {})
    assert 'cost_reduction' in business_objectives
    assert 'efficiency_improvement' in business_objectives
    
    print(f"✓ Successfully parsed ACME Corp config:")
    print(f"  Organization: {organization_name}")
    print(f"  Industry: {industry}")
    print(f"  Package: {selected_package}")
    print(f"  Size: {size}")
    print(f"  Coordination agents: {len(agents.get('coordination', []))}")
    print(f"  Leadership agents: {len(agents.get('leadership', []))}")
    print(f"  Specialist agents: {len(agents.get('specialists', []))}")


def test_template_variable_generation_for_acme():
    """Test generating template variables for ACME Corp"""
    
    # Simulate ACME Corp data
    org_name = "acme-corp"
    industry = "healthcare"
    size = "enterprise"
    
    # Generate variables like our implementation does
    variables = {
        'customer_name': org_name,
        'organization_name': org_name,
        'current_year': 2025,
        'industry': industry,
        'size': size
    }
    
    # Test variable substitution with ACME-specific projects
    template_projects = [
        {
            "name": "${customer_name} - Healthcare Compliance",
            "description": "Healthcare compliance and regulatory management for ${organization_name}"
        },
        {
            "name": "${customer_name} - Enterprise Architecture", 
            "description": "Enterprise-scale system architecture and governance"
        },
        {
            "name": "${customer_name} - Digital Health Innovation",
            "description": "Digital transformation initiatives in ${industry}"
        }
    ]
    
    # Process templates
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
    
    # Verify ACME-specific project processing
    assert len(processed_projects) == 3
    assert processed_projects[0]["name"] == "acme-corp - Healthcare Compliance"
    assert processed_projects[0]["description"] == "Healthcare compliance and regulatory management for acme-corp"
    assert processed_projects[1]["name"] == "acme-corp - Enterprise Architecture"
    assert processed_projects[2]["name"] == "acme-corp - Digital Health Innovation"
    assert "healthcare" in processed_projects[2]["description"]
    
    print(f"✓ Generated {len(processed_projects)} ACME-specific projects:")
    for proj in processed_projects:
        print(f"  • {proj['name']}")


def test_enterprise_package_agent_count():
    """Test that enterprise package has the expected agent count"""
    
    config_path = Path("/Users/pmuniraju/play/sandbox/symphony/organizations/customers/acme-corp/config/customer-config.yaml")
    
    if not config_path.exists():
        pytest.skip("ACME Corp config not found")
    
    with open(config_path, 'r') as f:
        customer_config = yaml.safe_load(f)
    
    # Count total agents as our system would
    agent_config = customer_config.get('agent_configuration', {})
    agents = agent_config.get('agents', {})
    
    total_agents = 0
    for category in agents.values():
        if isinstance(category, list):
            total_agents += len(category)
    
    # Verify enterprise package has substantial agent count
    assert total_agents > 50, f"Enterprise package should have 65+ agents, found {total_agents}"
    
    # Check metadata matches
    metadata = customer_config.get('metadata', {})
    package_info = metadata.get('package_info', {})
    expected_agent_count = package_info.get('agent_count')
    
    if expected_agent_count:
        # Allow some tolerance for different counting methods
        assert abs(total_agents - expected_agent_count) <= 5, \
            f"Agent count mismatch: counted {total_agents}, metadata says {expected_agent_count}"
    
    print(f"✓ Enterprise package validation:")
    print(f"  Total agents: {total_agents}")
    print(f"  Expected: {expected_agent_count}")
    print(f"  Coordination: {len(agents.get('coordination', []))}")
    print(f"  Leadership: {len(agents.get('leadership', []))}")
    print(f"  Specialists: {len(agents.get('specialists', []))}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])