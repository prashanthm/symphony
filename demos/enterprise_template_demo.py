#!/usr/bin/env python3
"""
Enterprise Template Demo

Demonstrates the complete enterprise Linear template with variable substitution.
"""

import yaml
from pathlib import Path

def demonstrate_enterprise_template():
    """Show enterprise template capabilities"""
    
    print("=" * 70)
    print("🏢 ENTERPRISE LINEAR TEMPLATE - COMPREHENSIVE DEMO")
    print("=" * 70)
    
    # Load the complete enterprise template
    template_path = Path("configs/linear-templates/enterprise/enterprise-complete.yaml")
    
    if not template_path.exists():
        print(f"❌ Template not found at: {template_path}")
        return
    
    with open(template_path, 'r') as f:
        template = yaml.safe_load(f)
    
    print("\n📋 ENTERPRISE TEMPLATE OVERVIEW")
    print("-" * 40)
    print(f"Template Type: {template.get('template_type', 'N/A')}")
    print(f"Version: {template.get('template_version', 'N/A')}")
    print(f"Target Size: {template.get('target_organization_size', 'N/A')}")
    print(f"Setup Time: {template.get('estimated_setup_time', 'N/A')}")
    print(f"Complexity: {template.get('complexity_level', 'N/A')}")
    print(f"Recommended Agents: {template.get('recommended_agents', 'N/A')}")
    
    # Show team structure
    teams = template.get('teams', [])
    print(f"\n🏗️  ENTERPRISE TEAM STRUCTURE ({len(teams)} teams)")
    print("-" * 40)
    for team in teams:
        workflows = team.get('workflows', [])
        custom_fields = team.get('custom_fields', [])
        print(f"• {team['name']} ({team['key']})")
        print(f"  Description: {team['description']}")
        print(f"  Workflows: {len(workflows)} states")
        print(f"  Custom Fields: {len(custom_fields)} fields")
    
    # Show project structure
    projects = template.get('projects', [])
    print(f"\n📊 ENTERPRISE PROJECT STRUCTURE ({len(projects)} projects)")
    print("-" * 40)
    for project in projects:
        milestones = project.get('milestones', [])
        print(f"• {project['name']}")
        print(f"  Timeline: {project.get('timeline', 'N/A')}")
        print(f"  Milestones: {len(milestones)} phases")
        print(f"  Teams: {', '.join(project.get('assignable_teams', []))}")
    
    # Show initiatives
    initiatives = template.get('initiatives', [])
    print(f"\n🎯 STRATEGIC INITIATIVES ({len(initiatives)} initiatives)")
    print("-" * 40)
    for initiative in initiatives:
        sub_initiatives = initiative.get('sub_initiatives', [])
        print(f"• {initiative['name']}")
        print(f"  Level: {initiative['level']}")
        print(f"  Sub-initiatives: {len(sub_initiatives)}")
        print(f"  Timeline: {initiative.get('timeline', 'N/A')}")
    
    # Show Symphony integration
    symphony = template.get('symphony_integration', {})
    agent_assignments = symphony.get('agent_assignments', {})
    print(f"\n🤖 SYMPHONY AGENT INTEGRATION")
    print("-" * 40)
    total_agents = 0
    for team_name, agents in agent_assignments.items():
        print(f"• {team_name}: {len(agents)} agents")
        total_agents += len(agents)
    print(f"Total Agents: {total_agents}")
    
    # Show enterprise features
    enterprise_features = symphony.get('enterprise_features', {})
    print(f"\n✨ ENTERPRISE FEATURES")
    print("-" * 40)
    for feature, enabled in enterprise_features.items():
        status = "✅" if enabled else "❌"
        print(f"{status} {feature.replace('_', ' ').title()}")
    
    # Show performance targets
    performance = symphony.get('performance_targets', {})
    print(f"\n📈 PERFORMANCE TARGETS")
    print("-" * 40)
    for metric, target in performance.items():
        print(f"• {metric.replace('_', ' ').title()}: {target}")
    
    return template

def demonstrate_variable_substitution():
    """Show how template variables work"""
    
    print("\n" + "=" * 70)
    print("🔄 TEMPLATE VARIABLE SUBSTITUTION DEMO")
    print("=" * 70)
    
    # Example customer scenarios
    scenarios = [
        {
            "name": "Healthcare Enterprise",
            "variables": {
                "customer_name": "MedTech Solutions",
                "industry": "healthcare",
                "region": "us-east-1",
                "timezone": "EST",
                "locale": "en-US",
                "current_year": "2025",
                "next_year": "2026"
            }
        },
        {
            "name": "Financial Services",
            "variables": {
                "customer_name": "Global Bank Corp",
                "industry": "financial_services",
                "region": "us-west-2",
                "timezone": "PST",
                "locale": "en-US",
                "current_year": "2025",
                "next_year": "2026"
            }
        },
        {
            "name": "Manufacturing Giant",
            "variables": {
                "customer_name": "Industrial Manufacturing Co",
                "industry": "manufacturing",
                "region": "eu-west-1",
                "timezone": "CET",
                "locale": "en-GB",
                "current_year": "2025",
                "next_year": "2026"
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 SCENARIO: {scenario['name']}")
        print("-" * 40)
        
        variables = scenario['variables']
        
        # Show what the workspace name would become
        workspace_template = "${customer_name} Enterprise Operations"
        workspace_name = substitute_template_vars(workspace_template, variables)
        print(f"Workspace: {workspace_name}")
        
        # Show what project names would become
        project_templates = [
            "${customer_name} - Strategic Planning",
            "${customer_name} - Enterprise Architecture",
            "${customer_name} - Digital Transformation",
            "${customer_name} - Compliance & Governance"
        ]
        
        print("Projects:")
        for template in project_templates:
            project_name = substitute_template_vars(template, variables)
            print(f"  • {project_name}")
        
        # Show initiative names
        initiative_template = "${customer_name} Enterprise Transformation ${current_year}"
        initiative_name = substitute_template_vars(initiative_template, variables)
        print(f"Initiative: {initiative_name}")

def substitute_template_vars(template_str, variables):
    """Simple template variable substitution"""
    result = template_str
    for var, value in variables.items():
        result = result.replace(f"${{{var}}}", str(value))
    return result

def show_cli_usage_examples():
    """Show how to use the enterprise templates via CLI"""
    
    print("\n" + "=" * 70)
    print("🖥️  CLI USAGE EXAMPLES")
    print("=" * 70)
    
    print("\n1. Preview Simple Enterprise Template:")
    print("python3 -m symphony_cli.commands.linear_hierarchy preview \\")
    print("  '/path/to/configs/linear-templates/enterprise/enterprise-simple.yaml'")
    
    print("\n2. Generate Enterprise Config for Healthcare Company:")
    print("python3 -m symphony_cli.commands.linear_hierarchy generate \\")
    print("  --customer 'MedTech Solutions' \\")
    print("  --industry healthcare \\")
    print("  --size enterprise \\")
    print("  --output medtech-config.yaml")
    
    print("\n3. Deploy Enterprise Workspace:")
    print("export LINEAR_API_TOKEN='your_token_here'")
    print("python3 -m symphony_cli.commands.linear_hierarchy deploy \\")
    print("  --config medtech-config.yaml \\")
    print("  --linear-token $LINEAR_API_TOKEN")
    
    print("\n4. Interactive Enterprise Setup:")
    print("python3 -m symphony_cli.commands.linear_hierarchy configure --interactive")

def show_enterprise_vs_startup_comparison():
    """Compare enterprise template with startup template"""
    
    print("\n" + "=" * 70)
    print("⚖️  ENTERPRISE vs STARTUP COMPARISON")
    print("=" * 70)
    
    comparison = [
        ("Teams", "4 departments (Leadership, Ops, Tech, Compliance)", "1-2 teams"),
        ("Projects", "5 comprehensive projects", "2-3 basic projects"),  
        ("Workflows", "4-5 states per team", "3-4 states per team"),
        ("Custom Fields", "3-4 fields per team", "1-2 fields per team"),
        ("Initiatives", "2 strategic initiatives", "1 basic initiative"),
        ("Agents", "20 specialized agents", "5-8 basic agents"),
        ("Setup Time", "45-90 minutes", "15-30 minutes"),
        ("Complexity", "High", "Low"),
        ("Compliance", "Full compliance tracking", "Basic compliance"),
        ("Architecture", "Enterprise architecture focus", "Simple structure")
    ]
    
    print(f"{'Feature':<20} {'Enterprise':<40} {'Startup':<30}")
    print("-" * 90)
    for feature, enterprise, startup in comparison:
        print(f"{feature:<20} {enterprise:<40} {startup:<30}")

if __name__ == "__main__":
    # Run all demonstrations
    template = demonstrate_enterprise_template()
    demonstrate_variable_substitution()
    show_cli_usage_examples()
    show_enterprise_vs_startup_comparison()
    
    print("\n" + "=" * 70)
    print("✅ ENTERPRISE TEMPLATE DEMO COMPLETE")
    print("=" * 70)
    print("\nThe enterprise template provides:")
    print("• 4 specialized teams with comprehensive workflows")
    print("• 5 enterprise-scale projects with detailed milestones")
    print("• 20+ Symphony agents for full automation")
    print("• Complete compliance and governance framework")
    print("• Variable substitution for customer customization")
    print("• Enterprise-grade features and performance targets")
    print("\nReady for production deployment to Linear workspaces!")