#!/usr/bin/env python3
"""
Linear Hierarchy CLI Commands

CLI commands for configurable Linear workspace management with maximum customer flexibility.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

import click
import yaml
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

try:
    from symphony_integrations.linear.client import LinearAPIClient, SymphonyLinearIntegration
    from symphony_integrations.linear.defaults_generator import SymphonyLinearDefaults
    from symphony_integrations.linear.template_engine import (
        ConfigurationWizard,
        TemplateEngine,
    )
    from symphony_integrations.linear.template_models import (
        IndustryType,
        OrganizationConfig,
        OrganizationSize,
    )
    from symphony_integrations.linear.template_validator import (
        TemplateValidator,
        WorkspacePreviewGenerator,
    )
    from symphony_core.config.customer_manager import get_customer_manager
except ImportError as e:
    click.echo(f"Error importing Linear integration modules: {e}")
    click.echo("Please ensure Symphony integrations are properly installed.")
    exit(1)

console = Console()


@click.group()
def hierarchy():
    """Linear workspace hierarchy management with maximum configurability"""
    pass


@hierarchy.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Customer configuration file path",
)
@click.option(
    "--interactive", "-i", is_flag=True, help="Run interactive configuration wizard"
)
@click.option(
    "--output", "-o", type=click.Path(), help="Output path for generated configuration"
)
@click.option(
    "--preview",
    "-p",
    is_flag=True,
    help="Preview configuration without creating workspace",
)
def configure(
    config: Optional[str], interactive: bool, output: Optional[str], preview: bool
):
    """Configure Linear workspace with customer-specific settings"""

    console.print(
        Panel.fit(
            "[bold blue]🎼 Symphony Linear Workspace Configuration[/bold blue]\n"
            "[dim]Maximum customer flexibility with intelligent defaults[/dim]",
            border_style="blue",
        )
    )

    template_engine = TemplateEngine()

    try:
        if interactive:
            # Run interactive wizard
            wizard = ConfigurationWizard(template_engine)
            console.print(
                "\n[bold green]Starting Interactive Configuration Wizard[/bold green]"
            )

            customer_config = wizard.run_interactive_wizard()

            if output:
                with open(output, "w") as f:
                    yaml.dump(customer_config, f, default_flow_style=False, indent=2)
                console.print(f"[green]✓[/green] Configuration saved to: {output}")

        elif config:
            # Process customer configuration file
            console.print(f"[blue]Processing configuration:[/blue] {config}")

            workspace_template = template_engine.process_customer_config(config)

            if preview:
                _display_workspace_preview(workspace_template)
            else:
                console.print("[green]✓[/green] Configuration processed successfully")

                if output:
                    template_engine.save_template(workspace_template, output)
                    console.print(f"[green]✓[/green] Template saved to: {output}")

        else:
            console.print(
                "[red]Error:[/red] Either --config or --interactive must be specified"
            )
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error configuring workspace:[/red] {str(e)}")
        raise click.Abort()


@hierarchy.command()
@click.option("--customer", "-c", required=True, help="Customer name")
@click.option(
    "--industry",
    "-i",
    type=click.Choice([ind.value for ind in IndustryType]),
    help="Customer industry",
)
@click.option(
    "--size",
    "-s",
    type=click.Choice([size.value for size in OrganizationSize]),
    help="Organization size",
)
@click.option("--regions", "-r", help="Comma-separated list of regions")
@click.option("--output", "-o", type=click.Path(), help="Output configuration file")
@click.option("--preview", "-p", is_flag=True, help="Preview only, don't save")
def generate(
    customer: str,
    industry: Optional[str],
    size: Optional[str],
    regions: Optional[str],
    output: Optional[str],
    preview: bool,
):
    """Generate intelligent defaults for customer organization"""

    console.print(
        Panel.fit(
            f"[bold green]🤖 Generating Intelligent Defaults[/bold green]\n"
            f"[dim]Customer: {customer}[/dim]",
            border_style="green",
        )
    )

    try:
        # Build organization config
        organization = OrganizationConfig(
            customer_name=customer,
            industry=IndustryType(industry) if industry else IndustryType.TECHNOLOGY,
            size=OrganizationSize(size) if size else OrganizationSize.STARTUP,
            regions=regions.split(",") if regions else [],
        )

        # Generate defaults
        defaults_generator = SymphonyLinearDefaults()
        workspace_template = defaults_generator.generate_defaults(organization)

        console.print(f"[green]✓[/green] Generated defaults for {customer}")

        if preview:
            _display_workspace_preview(workspace_template)

        if output:
            template_engine = TemplateEngine()
            template_engine.save_template(workspace_template, output)
            console.print(f"[green]✓[/green] Configuration saved to: {output}")

        # Display summary
        _display_generation_summary(workspace_template)

    except Exception as e:
        console.print(f"[red]Error generating defaults:[/red] {str(e)}")
        raise click.Abort()


@hierarchy.command()
@click.argument("config_file", type=click.Path(exists=True))
def validate(config_file: str):
    """Validate workspace configuration for correctness"""

    console.print(
        Panel.fit(
            "[bold yellow]🔍 Validating Workspace Configuration[/bold yellow]",
            border_style="yellow",
        )
    )

    try:
        # Load and validate template
        template_engine = TemplateEngine()
        workspace_template = template_engine.process_customer_config(config_file)

        validator = TemplateValidator()
        result = validator.validate_template(workspace_template)

        # Display validation results
        if result.is_valid:
            console.print("[bold green]✅ Configuration is valid![/bold green]")
        else:
            console.print("[bold red]❌ Configuration has errors:[/bold red]")
            for error in result.errors:
                console.print(f"  [red]•[/red] {error}")

        if result.warnings:
            console.print("\n[bold yellow]⚠️  Warnings:[/bold yellow]")
            for warning in result.warnings:
                console.print(f"  [yellow]•[/yellow] {warning}")

        if result.suggestions:
            console.print("\n[bold blue]💡 Suggestions:[/bold blue]")
            for suggestion in result.suggestions:
                console.print(f"  [blue]•[/blue] {suggestion}")

    except Exception as e:
        console.print(f"[red]Error validating configuration:[/red] {str(e)}")
        raise click.Abort()


@hierarchy.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--detailed", "-d", is_flag=True, help="Show detailed preview")
def preview(config_file: str, detailed: bool):
    """Preview what will be created from configuration"""

    console.print(
        Panel.fit("[bold cyan]👀 Workspace Preview[/bold cyan]", border_style="cyan")
    )

    try:
        # Load and process template - use appropriate method based on file type
        template_engine = TemplateEngine()
        
        # Check if this is a customer config or template file
        with open(config_file, 'r') as f:
            file_content = yaml.safe_load(f)
        
        if 'customer_profile' in file_content:
            # This is a customer configuration file
            workspace_template = template_engine.process_customer_config(config_file)
        else:
            # This is a template file
            workspace_template = template_engine.load_template(config_file)

        # Generate preview
        _display_workspace_preview(workspace_template, detailed=detailed)

    except Exception as e:
        console.print(f"[red]Error generating preview:[/red] {str(e)}")
        raise click.Abort()


@hierarchy.command()
@click.argument("config_file", type=click.Path(exists=True), required=False)
@click.option(
    "--linear-token",
    envvar="LINEAR_API_TOKEN",
    required=True,
    help="Linear API token (or set LINEAR_API_TOKEN env var)",
)
@click.option("--dry-run", is_flag=True, help="Validate but don't create workspace")
@click.option("--force", is_flag=True, help="Skip confirmation prompts")
@click.option("--customer-id", help="Customer ID to deploy (alternative to config file)")
@click.option("--interactive", is_flag=True, help="Select customer interactively")
def deploy(config_file: str, linear_token: str, dry_run: bool, force: bool, customer_id: str, interactive: bool):
    """Deploy workspace configuration to Linear"""

    console.print(
        Panel.fit(
            "[bold green]🚀 Deploying Linear Workspace[/bold green]",
            border_style="green",
        )
    )

    try:
        # Resolve customer configuration
        config_file_path = _resolve_customer_config(config_file, customer_id, interactive)
        
        if not config_file_path:
            console.print("[red]❌ No customer configuration specified[/red]")
            console.print("Use one of: config file path, --customer-id, or --interactive")
            raise click.Abort()
        
        # Display customer information
        customer_info = _get_customer_info(config_file_path)
        if customer_info:
            console.print(f"\n[bold cyan]📋 Customer Information[/bold cyan]")
            console.print(f"Organization: [green]{customer_info.get('organization_name', 'Unknown')}[/green]")
            console.print(f"Industry: [yellow]{customer_info.get('industry', 'Unknown')}[/yellow]")
            console.print(f"Package: [blue]{customer_info.get('package_type', 'Unknown')}[/blue]")
        
        # Load and validate configuration - use appropriate method based on file type
        template_engine = TemplateEngine()
        
        # Check if this is a customer config or template file
        with open(config_file_path, 'r') as f:
            file_content = yaml.safe_load(f)
        
        if 'customer_profile' in file_content:
            # This is a customer configuration file
            workspace_template = template_engine.process_customer_config(config_file_path)
        else:
            # This is a template file  
            workspace_template = template_engine.load_template(config_file_path)

        validator = TemplateValidator()
        result = validator.validate_template(workspace_template)

        if not result.is_valid:
            console.print(
                "[red]❌ Configuration has errors. Please fix before deploying:[/red]"
            )
            for error in result.errors:
                console.print(f"  [red]•[/red] {error}")
            raise click.Abort()

        # Show preview
        _display_workspace_preview(workspace_template)

        # Confirmation
        if not force and not dry_run:
            if not Confirm.ask("\n[bold]Proceed with workspace creation?[/bold]"):
                console.print("Deployment cancelled.")
                return

        if dry_run:
            console.print("[yellow]🔍 DRY RUN - No changes will be made[/yellow]")
            console.print(
                "[green]✓[/green] Configuration is valid and ready for deployment"
            )
            return

        # Deploy to Linear
        console.print("[blue]Creating Linear workspace...[/blue]")

        # Create Linear integration and deploy workspace with template
        asyncio.run(_deploy_workspace_with_template(
            workspace_template, config_file_path, linear_token
        ))

        console.print("[bold green]🎉 Workspace deployed successfully![/bold green]")

    except Exception as e:
        console.print(f"[red]Error deploying workspace:[/red] {str(e)}")
        raise click.Abort()


@hierarchy.command()
def dogfood():
    """Generate Symphony's own workspace configuration (eating our own dogfood)"""

    console.print(
        Panel.fit(
            "[bold magenta]🍖 Symphony Dogfooding Configuration[/bold magenta]\n"
            "[dim]Symphony uses Symphony to manage Symphony[/dim]",
            border_style="magenta",
        )
    )

    try:
        # Generate Symphony's own template
        defaults_generator = SymphonyLinearDefaults()
        symphony_template = defaults_generator.generate_dogfooding_template()

        console.print(
            "[green]✓[/green] Generated Symphony internal workspace configuration"
        )

        # Display the meta-configuration
        _display_dogfooding_preview(symphony_template)

        # Ask if they want to save it
        if Confirm.ask("\n[bold]Save Symphony dogfooding configuration?[/bold]"):
            output_path = "configs/symphony-dogfood-workspace.yaml"
            template_engine = TemplateEngine()
            template_engine.save_template(symphony_template, output_path)
            console.print(f"[green]✓[/green] Saved to: {output_path}")

    except Exception as e:
        console.print(f"[red]Error generating dogfood configuration:[/red] {str(e)}")
        raise click.Abort()


@hierarchy.command()
@click.option("--industry", type=click.Choice([ind.value for ind in IndustryType]))
@click.option("--size", type=click.Choice([size.value for size in OrganizationSize]))
def list_templates():
    """List available workspace templates"""

    console.print(
        Panel.fit(
            "[bold blue]📋 Available Workspace Templates[/bold blue]",
            border_style="blue",
        )
    )

    # Display template categories
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Category", style="cyan")
    table.add_column("Template", style="white")
    table.add_column("Description", style="dim")

    # Industry templates
    table.add_row(
        "Industry", "financial-services", "Banking and financial institutions"
    )
    table.add_row("", "healthcare", "Healthcare and medical organizations")
    table.add_row("", "technology", "Software and technology companies")
    table.add_row("", "manufacturing", "Manufacturing and industrial")
    table.add_row("", "consulting", "Professional services and consulting")

    # Size templates
    table.add_row("Size", "startup", "5-20 people, simple structure")
    table.add_row("", "smb", "20-100 people, departmental teams")
    table.add_row("", "enterprise", "100-500 people, matrix organization")
    table.add_row("", "global", "500+ people, multi-region")

    # Special templates
    table.add_row("Special", "symphony-dogfood", "Symphony internal workspace")

    console.print(table)


def _display_workspace_preview(template, detailed: bool = False):
    """Display workspace preview in a formatted table"""

    preview_generator = WorkspacePreviewGenerator()
    preview = preview_generator.generate_preview(template)

    # Main preview table
    table = Table(show_header=True, header_style="bold cyan", title="Workspace Preview")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Workspace Name", preview.workspace_name)
    table.add_row("Team Count", str(preview.team_count))
    table.add_row("Project Count", str(preview.project_count))
    table.add_row("Initiative Count", str(preview.initiative_count))
    table.add_row("Setup Time", preview.estimated_setup_time)
    table.add_row("Complexity", f"{preview.complexity_score}/10")
    table.add_row("Linear Features", ", ".join(preview.linear_features_used))

    if preview.symphony_agents_deployed:
        table.add_row("Symphony Agents", str(len(preview.symphony_agents_deployed)))

    console.print(table)

    if detailed:
        # Detailed structure
        if preview.structure_summary.get("teams"):
            _display_team_structure(preview.structure_summary["teams"])

        if preview.structure_summary.get("initiatives"):
            _display_initiative_structure(preview.structure_summary["initiatives"])


def _display_team_structure(teams):
    """Display team structure in detail"""

    console.print("\n[bold]Team Structure:[/bold]")

    table = Table(show_header=True, header_style="bold green")
    table.add_column("Team", style="green")
    table.add_column("Key", style="cyan")
    table.add_column("Sub-teams", style="yellow")
    table.add_column("Workflows", style="blue")
    table.add_column("Custom Fields", style="magenta")

    for team in teams:
        table.add_row(
            team["name"],
            team["key"],
            str(team["sub_teams"]),
            str(team["workflows"]),
            str(team["custom_fields"]),
        )

    console.print(table)


def _display_initiative_structure(initiatives):
    """Display initiative structure in detail"""

    console.print("\n[bold]Initiative Structure:[/bold]")

    table = Table(show_header=True, header_style="bold purple")
    table.add_column("Initiative", style="purple")
    table.add_column("Level", style="cyan")
    table.add_column("Sub-initiatives", style="yellow")

    for init in initiatives:
        table.add_row(init["name"], f"L{init['level']}", str(init["sub_initiatives"]))

    console.print(table)


def _display_generation_summary(template):
    """Display summary of generated defaults"""

    console.print(f"\n[bold]Generated Configuration Summary:[/bold]")
    console.print(f"  • Teams: {len(template.teams)}")
    console.print(f"  • Initiatives: {len(template.initiatives)}")
    console.print(f"  • Projects: {len(template.projects)}")

    if template.symphony_integration:
        total_agents = sum(
            len(agents)
            for agents in template.symphony_integration.agent_assignments.values()
        )
        console.print(f"  • Symphony Agents: {total_agents}")


def _display_dogfooding_preview(template):
    """Display Symphony dogfooding configuration preview"""

    console.print("\n[bold magenta]🎼 Symphony Meta-Configuration[/bold magenta]")
    console.print("[dim]How Symphony manages Symphony development[/dim]\n")

    # Special dogfooding features
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Feature", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Description", style="dim")

    table.add_row("Self-Managing", "✅ Enabled", "Symphony manages its own workspace")
    table.add_row(
        "Recursive Improvement", "✅ Enabled", "System improves its own templates"
    )
    table.add_row("Auto-Optimization", "✅ Enabled", "Automatic workspace optimization")

    console.print(table)

    # Regular preview
    _display_workspace_preview(template, detailed=True)


def _simulate_deployment(template):
    """Simulate workspace deployment to Linear"""

    import time

    steps = [
        "Creating workspace",
        "Setting up teams",
        "Configuring workflows",
        "Creating initiatives",
        "Setting up projects",
        "Assigning Symphony agents",
        "Finalizing configuration",
    ]

    for step in steps:
        console.print(f"[blue]•[/blue] {step}...")
        time.sleep(0.5)  # Simulate work

    console.print("[green]✓[/green] All components created successfully")


async def _deploy_workspace_with_template(
    workspace_template, config_file: str, linear_token: str
):
    """Deploy workspace using the Linear client with template support"""
    
    # Load customer configuration to extract template and organization info
    with open(config_file, 'r') as f:
        customer_config = yaml.safe_load(f)
    
    # Extract organization details
    customer_profile = customer_config.get('customer_profile', {})
    organization_name = customer_profile.get('organization_name', 'Unknown Customer')
    industry = customer_profile.get('industry')
    
    # Determine organization size from agent configuration
    agent_config = customer_config.get('agent_configuration', {})
    selected_package = agent_config.get('selected_package', 'startup')
    
    # Map package to organization size
    size_mapping = {
        'startup': 'startup',
        'smb': 'smb', 
        'enterprise': 'enterprise',
        'global': 'global'
    }
    size = size_mapping.get(selected_package, 'startup')
    
    console.print(f"[blue]Deploying for:[/blue] {organization_name}")
    console.print(f"[blue]Industry:[/blue] {industry}")
    console.print(f"[blue]Package:[/blue] {selected_package} ({size})")
    
    # Create Linear integration
    linear_integration = SymphonyLinearIntegration(api_token=linear_token)
    
    try:
        # Initialize workspace with template support
        # Determine if this is a template file or customer config
        # Re-read the file to check its type for Linear client call
        with open(config_file, 'r') as f:
            file_content_for_linear = yaml.safe_load(f)
            
        if 'customer_profile' in file_content_for_linear:
            # This is a customer configuration file
            workspace_config = await linear_integration.initialize_workspace(
                organization_name=organization_name,
                template_path=None,
                industry=industry,
                size=size,
                customer_config=file_content_for_linear
            )
        else:
            # This is a template file - pass the template path
            workspace_config = await linear_integration.initialize_workspace(
                organization_name=organization_name,
                template_path=config_file,  # Pass the template file path
                industry=industry,
                size=size,
                customer_config=None
            )
        
        console.print(f"[green]✓[/green] Created workspace: {workspace_config['organization_name']}")
        
        # Display created projects
        projects = workspace_config.get('projects', {})
        if projects:
            console.print(f"[green]✓[/green] Created {len(projects)} projects:")
            for project_name in projects.keys():
                console.print(f"  [cyan]•[/cyan] {project_name}")
        
        # Display team information
        team = workspace_config.get('team', {})
        if team:
            console.print(f"[green]✓[/green] Using team: {team.get('name')} ({team.get('key')})")
        
        # Display workflow states
        workflow_states = workspace_config.get('workflow_states', [])
        console.print(f"[green]✓[/green] Configured {len(workflow_states)} workflow states")
        
        return workspace_config
        
    except Exception as e:
        console.print(f"[red]❌ Deployment failed:[/red] {str(e)}")
        raise


def _resolve_customer_config(config_file: Optional[str], customer_id: Optional[str], interactive: bool) -> Optional[str]:
    """Resolve customer configuration file path from various input methods"""
    
    if interactive:
        return _interactive_customer_selection()
    elif customer_id:
        return _resolve_customer_by_id(customer_id)
    elif config_file:
        return config_file
    else:
        return None


def _interactive_customer_selection() -> Optional[str]:
    """Show interactive customer selection menu"""
    try:
        manager = get_customer_manager()
        customers = manager.list_customers()
        
        if not customers:
            console.print("[yellow]⚠️  No customers found in the system[/yellow]")
            return None
        
        console.print("\n[bold cyan]📋 Available Customers[/bold cyan]")
        table = Table()
        table.add_column("#", style="cyan")
        table.add_column("Customer ID", style="green")
        table.add_column("Organization", style="yellow")
        table.add_column("Industry", style="blue")
        table.add_column("Package", style="magenta")
        
        for i, customer in enumerate(customers, 1):
            table.add_row(
                str(i),
                customer.get('customer_id', 'Unknown'),
                customer.get('organization_name', 'Unknown'),
                customer.get('industry', 'Unknown'),
                customer.get('package_type', 'Unknown')
            )
        
        console.print(table)
        
        choice = Prompt.ask(
            "\nSelect customer number",
            choices=[str(i) for i in range(1, len(customers) + 1)]
        )
        
        selected_customer = customers[int(choice) - 1]
        customer_id = selected_customer.get('customer_id')
        
        return _resolve_customer_by_id(customer_id)
        
    except Exception as e:
        console.print(f"[red]Error loading customers:[/red] {str(e)}")
        return None


def _resolve_customer_by_id(customer_id: str) -> Optional[str]:
    """Resolve customer configuration file by customer ID"""
    from pathlib import Path
    
    config_path = Path(f"organizations/customers/{customer_id}/config/customer-config.yaml")
    
    if config_path.exists():
        return str(config_path)
    else:
        console.print(f"[red]❌ Customer configuration not found:[/red] {config_path}")
        console.print(f"[dim]Expected path: {config_path.absolute()}[/dim]")
        return None


def _get_customer_info(config_file_path: str) -> Optional[Dict[str, str]]:
    """Extract customer information from config file"""
    try:
        import yaml
        with open(config_file_path, 'r') as f:
            config = yaml.safe_load(f)
        
        customer_profile = config.get('customer_profile', {})
        agent_config = config.get('agent_configuration', {})
        
        return {
            'organization_name': customer_profile.get('organization_name'),
            'industry': customer_profile.get('industry'),
            'package_type': agent_config.get('selected_package'),
            'customer_id': customer_profile.get('customer_id')
        }
    except Exception:
        return None


if __name__ == "__main__":
    hierarchy()
