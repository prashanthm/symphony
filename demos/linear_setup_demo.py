#!/usr/bin/env python3
"""
Linear Setup Demo - Step by Step Example

Demonstrates how to use the Symphony Linear integration with template-driven project creation.
"""

import asyncio
import json
import os
import yaml
from pathlib import Path
from typing import Dict, Any

# Mock the Linear integration for demo purposes (since we don't have real tokens)
class DemoLinearIntegration:
    """Demo version of Linear integration for walkthrough purposes"""
    
    def __init__(self, api_token: str = "demo_token"):
        self.api_token = api_token
        print(f"🔗 Initialized Linear integration with token: {api_token[:12]}...")
    
    async def initialize_workspace(
        self,
        organization_name: str,
        template_path: str = None,
        industry: str = None,
        size: str = None,
        customer_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Demo workspace initialization"""
        
        print(f"\n🚀 Initializing Linear workspace for: {organization_name}")
        print(f"   Industry: {industry}")
        print(f"   Size: {size}")
        print(f"   Template: {template_path or 'Generated from config'}")
        
        # Simulate finding Linear team
        demo_team = {"id": "team_demo_123", "name": "Operations", "key": "OPS"}
        print(f"✓ Found Linear team: {demo_team['name']} ({demo_team['key']})")
        
        # Generate industry/size-specific projects
        projects = self._generate_demo_projects(organization_name, industry, size)
        
        # Simulate creating projects
        created_projects = {}
        for i, project in enumerate(projects, 1):
            project_id = f"proj_demo_{i}"
            created_projects[project["name"]] = {
                "id": project_id,
                "name": project["name"],
                "description": project["description"],
                "url": f"https://linear.app/{project_id}"
            }
            print(f"✓ Created project: {project['name']}")
            await asyncio.sleep(0.1)  # Simulate API delay
        
        # Mock workflow states
        workflow_states = [
            {"id": "state_1", "name": "Backlog", "type": "backlog"},
            {"id": "state_2", "name": "Todo", "type": "unstarted"},
            {"id": "state_3", "name": "In Progress", "type": "started"},
            {"id": "state_4", "name": "Done", "type": "completed"}
        ]
        print(f"✓ Configured {len(workflow_states)} workflow states")
        
        workspace_config = {
            "organization_name": organization_name,
            "team": demo_team,
            "projects": created_projects,
            "workflow_states": workflow_states,
            "initialized_at": "2025-09-01T12:00:00Z",
            "template_used": template_path or "generated",
            "industry": industry,
            "size": size
        }
        
        print(f"\n🎉 Workspace '{organization_name}' created successfully!")
        return workspace_config
    
    def _generate_demo_projects(self, org_name: str, industry: str, size: str) -> list:
        """Generate demo projects based on industry and size"""
        
        base_projects = []
        
        # Industry-specific projects
        if industry == "healthcare":
            base_projects.extend([
                {
                    "name": f"{org_name} - Healthcare Compliance",
                    "description": "HIPAA compliance, regulatory requirements, and patient data protection"
                },
                {
                    "name": f"{org_name} - Clinical Operations",
                    "description": "Patient flow optimization, clinical workflows, and quality metrics"
                },
                {
                    "name": f"{org_name} - Digital Health Innovation",
                    "description": "Telemedicine, patient portals, and clinical decision support systems"
                }
            ])
        elif industry == "technology":
            base_projects.extend([
                {
                    "name": f"{org_name} - Product Development",
                    "description": "Feature development, technical roadmap, and innovation initiatives"
                },
                {
                    "name": f"{org_name} - Platform Engineering",
                    "description": "Infrastructure, DevOps, and platform reliability"
                },
                {
                    "name": f"{org_name} - Customer Success",
                    "description": "User onboarding, support automation, and customer feedback"
                }
            ])
        else:
            # Generic projects
            base_projects.extend([
                {
                    "name": f"{org_name} - Strategic Initiatives",
                    "description": "High-level strategic planning and business development"
                },
                {
                    "name": f"{org_name} - Operational Excellence",
                    "description": "Process optimization and operational improvements"
                }
            ])
        
        # Size-specific additional projects
        if size in ["enterprise", "global"]:
            base_projects.extend([
                {
                    "name": f"{org_name} - Enterprise Architecture",
                    "description": "System architecture, integration planning, and scalability"
                },
                {
                    "name": f"{org_name} - Compliance & Security",
                    "description": "Security frameworks, compliance monitoring, and risk management"
                }
            ])
        
        return base_projects


async def demo_step_by_step_setup():
    """Complete step-by-step demo"""
    
    print("=" * 60)
    print("🎼 SYMPHONY LINEAR INTEGRATION - STEP BY STEP DEMO")
    print("=" * 60)
    
    # Step 1: Load customer configuration
    print("\n📋 STEP 1: Loading Customer Configuration")
    print("-" * 40)
    
    customer_config_path = Path("organizations/customers/acme-corp/config/customer-config.yaml")
    if customer_config_path.exists():
        with open(customer_config_path, 'r') as f:
            customer_config = yaml.safe_load(f)
        
        customer_profile = customer_config.get('customer_profile', {})
        organization_name = customer_profile.get('organization_name', 'Demo Corp')
        industry = customer_profile.get('industry', 'technology')
        
        agent_config = customer_config.get('agent_configuration', {})
        selected_package = agent_config.get('selected_package', 'startup')
        
        print(f"✓ Loaded config for: {organization_name}")
        print(f"✓ Industry: {industry}")
        print(f"✓ Package: {selected_package}")
    else:
        # Fallback demo data
        print("ℹ️  Using demo configuration (ACME Corp config not found)")
        organization_name = "ACME Corp"
        industry = "healthcare"
        selected_package = "enterprise"
        customer_config = {
            "customer_profile": {
                "organization_name": organization_name,
                "industry": industry
            },
            "agent_configuration": {
                "selected_package": selected_package
            }
        }
    
    # Step 2: Initialize Linear integration
    print("\n🔗 STEP 2: Initialize Linear Integration")
    print("-" * 40)
    
    linear_token = os.getenv("LINEAR_API_TOKEN", "demo_token_12345")
    integration = DemoLinearIntegration(api_token=linear_token)
    
    # Step 3: Process template and create workspace
    print(f"\n🛠️  STEP 3: Create Template-Driven Workspace")
    print("-" * 40)
    
    workspace_config = await integration.initialize_workspace(
        organization_name=organization_name,
        industry=industry,
        size=selected_package,
        customer_config=customer_config
    )
    
    # Step 4: Display results
    print(f"\n📊 STEP 4: Deployment Results")
    print("-" * 40)
    
    print(f"Workspace Name: {workspace_config['organization_name']}")
    print(f"Team: {workspace_config['team']['name']} ({workspace_config['team']['key']})")
    print(f"Projects Created: {len(workspace_config['projects'])}")
    
    print(f"\n📋 Created Projects:")
    for project_name, project_info in workspace_config['projects'].items():
        print(f"  • {project_name}")
        print(f"    URL: {project_info['url']}")
    
    print(f"\n⚙️  Workflow States: {len(workspace_config['workflow_states'])}")
    for state in workspace_config['workflow_states']:
        print(f"  • {state['name']} ({state['type']})")
    
    # Step 5: Save configuration
    print(f"\n💾 STEP 5: Save Workspace Configuration")
    print("-" * 40)
    
    output_dir = Path("workspace-configs")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"{organization_name.lower().replace(' ', '_')}_linear_workspace.json"
    with open(output_file, 'w') as f:
        json.dump(workspace_config, f, indent=2)
    
    print(f"✓ Configuration saved to: {output_file}")
    
    print(f"\n✨ SETUP COMPLETE!")
    print("=" * 60)
    
    return workspace_config


def demo_cli_commands():
    """Show equivalent CLI commands"""
    
    print("\n🖥️  EQUIVALENT CLI COMMANDS")
    print("=" * 60)
    
    print("# Preview configuration:")
    print("python3 -m symphony_cli.commands.linear_hierarchy preview \\")
    print("  organizations/customers/acme-corp/config/customer-config.yaml")
    
    print("\n# Validate configuration:")
    print("python3 -m symphony_cli.commands.linear_hierarchy validate \\")
    print("  organizations/customers/acme-corp/config/customer-config.yaml")
    
    print("\n# Deploy workspace (with real Linear token):")
    print("export LINEAR_API_TOKEN='your_real_token_here'")
    print("python3 -m symphony_cli.commands.linear_hierarchy deploy \\")
    print("  --config organizations/customers/acme-corp/config/customer-config.yaml \\")
    print("  --linear-token $LINEAR_API_TOKEN")
    
    print("\n# Interactive configuration wizard:")
    print("python3 -m symphony_cli.commands.linear_hierarchy configure --interactive")
    
    print("\n# Generate defaults for new customer:")
    print("python3 -m symphony_cli.commands.linear_hierarchy generate \\")
    print("  --customer 'TechCorp' \\")
    print("  --industry technology \\")
    print("  --size enterprise \\")
    print("  --preview")


def demo_template_system():
    """Show template system capabilities"""
    
    print("\n📝 TEMPLATE SYSTEM CAPABILITIES")
    print("=" * 60)
    
    print("Template Variable Substitution:")
    template_example = {
        "projects": [
            {
                "name": "${customer_name} - ${industry} Compliance",
                "description": "Regulatory compliance for ${customer_name} in ${industry} sector"
            },
            {
                "name": "${customer_name} - Digital Transformation",
                "description": "Digital initiatives for ${size}-scale organization"
            }
        ]
    }
    
    variables = {
        "customer_name": "ACME Corp",
        "industry": "healthcare",
        "size": "enterprise",
        "current_year": 2025
    }
    
    print(f"\nTemplate: {json.dumps(template_example, indent=2)}")
    print(f"\nVariables: {json.dumps(variables, indent=2)}")
    
    # Show substitution result
    print(f"\nAfter substitution:")
    result_projects = []
    for project in template_example["projects"]:
        name = project["name"]
        description = project["description"]
        
        for var, value in variables.items():
            name = name.replace(f"${{{var}}}", str(value))
            description = description.replace(f"${{{var}}}", str(value))
        
        result_projects.append({"name": name, "description": description})
    
    for project in result_projects:
        print(f"  • {project['name']}")
        print(f"    {project['description']}")


async def main():
    """Run the complete demo"""
    
    # Main demo
    workspace_config = await demo_step_by_step_setup()
    
    # Show CLI equivalents
    demo_cli_commands()
    
    # Show template capabilities
    demo_template_system()
    
    return workspace_config


if __name__ == "__main__":
    asyncio.run(main())