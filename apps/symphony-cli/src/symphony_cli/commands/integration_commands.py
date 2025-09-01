#!/usr/bin/env python3
"""
Integration Orchestration CLI Commands

CLI commands for managing Symphony's integration orchestration framework.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

try:
    from symphony_core.orchestration.integration_coordinator import (
        OrchestrationType,
        create_data_sync_rule,
        create_error_handling_rule,
        create_integration_orchestrator,
    )
    from symphony_integrations.adapters.github_adapter import (
        create_github_adapter,
        get_default_github_config,
    )
    from symphony_integrations.adapters.linear_adapter import (
        create_linear_adapter,
        get_default_linear_config,
    )
except ImportError as e:
    click.echo(f"Error importing Symphony modules: {e}")
    click.echo("Please ensure Symphony packages are properly installed.")

console = Console()


@click.group()
def integration():
    """Integration orchestration management"""
    pass


@integration.command()
@click.option(
    "--integration", "-i", multiple=True, help="Specific integrations to initialize"
)
@click.option("--config-file", help="Configuration file path")
def init(integration: tuple, config_file: Optional[str]):
    """Initialize integration orchestration framework"""
    console.print("[green]🔧 Initializing Integration Orchestration Framework[/green]")

    async def run_initialization():
        try:
            # Create orchestrator
            orchestrator = create_integration_orchestrator()

            # Load configuration
            config = await _load_configuration(config_file)

            # Initialize specified integrations or all available
            integrations_to_init = (
                list(integration) if integration else ["linear", "github"]
            )

            initialized_count = 0

            for integration_name in integrations_to_init:
                console.print(
                    f"[blue]Initializing {integration_name} integration...[/blue]"
                )

                try:
                    if integration_name == "linear":
                        linear_config = config.get(
                            "linear", get_default_linear_config()
                        )
                        adapter = create_linear_adapter(linear_config)
                        success = await orchestrator.register_integration(adapter)

                    elif integration_name == "github":
                        github_config = config.get(
                            "github", get_default_github_config()
                        )
                        adapter = create_github_adapter(github_config)
                        success = await orchestrator.register_integration(adapter)

                    else:
                        console.print(
                            f"[yellow]⚠ Unknown integration: {integration_name}[/yellow]"
                        )
                        continue

                    if success:
                        console.print(
                            f"[green]✅ {integration_name} initialized successfully[/green]"
                        )
                        initialized_count += 1
                    else:
                        console.print(
                            f"[red]❌ {integration_name} initialization failed[/red]"
                        )

                except Exception as e:
                    console.print(
                        f"[red]❌ Error initializing {integration_name}: {e}[/red]"
                    )

            # Setup default orchestration rules
            if initialized_count > 1:
                console.print("[blue]Setting up default orchestration rules...[/blue]")

                # Data sync rule
                sync_rule = await create_data_sync_rule(integrations_to_init)
                await orchestrator.add_orchestration_rule(sync_rule)

                # Error handling rule
                error_rule = await create_error_handling_rule(integrations_to_init)
                await orchestrator.add_orchestration_rule(error_rule)

                console.print(
                    "[green]✅ Default orchestration rules configured[/green]"
                )

            console.print(
                f"\n[bold green]🎯 Integration orchestration initialized![/bold green]"
            )
            console.print(f"✅ Integrations active: {initialized_count}")
            console.print(f"✅ Orchestration rules: 2")

        except Exception as e:
            console.print(f"[red]❌ Initialization failed: {e}[/red]")

    asyncio.run(run_initialization())


@integration.command()
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def status(format: str):
    """Show integration orchestration status"""
    console.print("[blue]📊 Integration Orchestration Status[/blue]")

    async def show_status():
        try:
            orchestrator = create_integration_orchestrator()
            status = await orchestrator.get_orchestration_status()

            if format == "json":
                console.print(json.dumps(status, indent=2))
                return

            # Show orchestrator metrics
            metrics = status["orchestrator_metrics"]
            metrics_table = Table(title="Orchestrator Metrics")
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="green")

            metrics_table.add_row("Total Events", str(metrics["total_events"]))
            metrics_table.add_row(
                "Successful Orchestrations", str(metrics["successful_orchestrations"])
            )
            metrics_table.add_row(
                "Failed Orchestrations", str(metrics["failed_orchestrations"])
            )
            metrics_table.add_row(
                "Active Integrations", str(metrics["active_integrations"])
            )

            console.print(metrics_table)

            # Show integration status
            integration_status = status["integration_status"]
            if integration_status:
                integrations_table = Table(title="Integration Status")
                integrations_table.add_column("Integration", style="cyan")
                integrations_table.add_column("Status", style="green")
                integrations_table.add_column("Success Rate", style="yellow")
                integrations_table.add_column("Avg Response", style="blue")
                integrations_table.add_column("Errors", style="red")

                for name, info in integration_status.items():
                    integrations_table.add_row(
                        name.title(),
                        info["status"],
                        f"{info['success_rate']:.1f}%",
                        f"{info['response_time_avg']:.2f}s",
                        str(info["error_count"]),
                    )

                console.print(integrations_table)

            # Show summary
            console.print(f"\n[bold]Summary:[/bold]")
            console.print(f"  Orchestration Rules: {status['orchestration_rules']}")
            console.print(f"  Active Workflows: {status['active_workflows']}")
            console.print(f"  Event Queue Size: {status['event_queue_size']}")

        except Exception as e:
            console.print(f"[red]❌ Error getting status: {e}[/red]")

    asyncio.run(show_status())


@integration.command()
@click.option("--integration", "-i", required=True, help="Integration name")
@click.option("--data-type", "-t", help="Data type to sync (default: all)")
@click.option("--options", help="Sync options as JSON string")
def sync(integration: str, data_type: Optional[str], options: Optional[str]):
    """Trigger data synchronization for specific integration"""
    console.print(f"[green]🔄 Starting sync for {integration} integration[/green]")

    async def run_sync():
        try:
            orchestrator = create_integration_orchestrator()

            # Parse options
            sync_options = {}
            if options:
                try:
                    sync_options = json.loads(options)
                except json.JSONDecodeError:
                    console.print("[red]❌ Invalid JSON in options parameter[/red]")
                    return

            # Get integration adapter
            if integration not in orchestrator.integrations:
                console.print(
                    f"[red]❌ Integration '{integration}' not found or not initialized[/red]"
                )
                return

            adapter = orchestrator.integrations[integration]

            # Perform sync
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Syncing {integration}...", total=None)

                result = await adapter.sync_data(data_type or "all", sync_options)

                progress.update(task, completed=True)

            if result["success"]:
                console.print(f"[green]✅ Sync completed successfully[/green]")
                console.print(f"⏱ Duration: {result.get('sync_duration', 0):.2f}s")

                # Show sync results summary
                sync_results = result.get("results", {})
                if sync_results:
                    results_table = Table(title="Sync Results")
                    results_table.add_column("Data Type", style="cyan")
                    results_table.add_column("Status", style="green")
                    results_table.add_column("Count", style="yellow")

                    for sync_data_type, data_result in sync_results.items():
                        status = (
                            "✅ Success"
                            if data_result.get("success", False)
                            else "❌ Failed"
                        )
                        count = data_result.get(f"{sync_data_type}_count", "N/A")
                        results_table.add_row(
                            sync_data_type.title(), status, str(count)
                        )

                    console.print(results_table)
            else:
                console.print(
                    f"[red]❌ Sync failed: {result.get('error', 'Unknown error')}[/red]"
                )

        except Exception as e:
            console.print(f"[red]❌ Sync error: {e}[/red]")

    asyncio.run(run_sync())


@integration.command()
@click.option(
    "--data-type", "-t", default="all", help="Data type to sync across all integrations"
)
def sync_all(data_type: str):
    """Synchronize data across all active integrations"""
    console.print(f"[green]🔄 Starting sync across all integrations[/green]")

    async def run_sync_all():
        try:
            orchestrator = create_integration_orchestrator()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Syncing all integrations...", total=None)

                result = await orchestrator.sync_all_integrations(data_type)

                progress.update(task, completed=True)

            # Show results
            results_table = Table(title=f"All Integrations Sync Results - {data_type}")
            results_table.add_column("Integration", style="cyan")
            results_table.add_column("Status", style="green")
            results_table.add_column("Details", style="yellow")

            sync_results = result.get("results", {})
            for integration_name, integration_result in sync_results.items():
                status = (
                    "✅ Success"
                    if integration_result.get("success", False)
                    else "❌ Failed"
                )
                details = (
                    integration_result.get("error", "Completed")
                    if not integration_result.get("success", False)
                    else "Completed"
                )
                results_table.add_row(integration_name.title(), status, details)

            console.print(results_table)
            console.print(
                f"\n[bold]Integrations synced: {result['integrations_synced']}[/bold]"
            )

        except Exception as e:
            console.print(f"[red]❌ Sync all error: {e}[/red]")

    asyncio.run(run_sync_all())


@integration.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("--context", help="Workflow context as JSON string")
def workflow(workflow_file: str, context: Optional[str]):
    """Execute integration workflow from file"""
    console.print(f"[green]⚡ Executing workflow: {workflow_file}[/green]")

    async def run_workflow():
        try:
            orchestrator = create_integration_orchestrator()

            # Load workflow definition
            with open(workflow_file, "r") as f:
                workflow_def = json.load(f)

            # Parse context
            workflow_context = {}
            if context:
                try:
                    workflow_context = json.loads(context)
                except json.JSONDecodeError:
                    console.print("[red]❌ Invalid JSON in context parameter[/red]")
                    return

            # Execute workflow
            workflow_name = workflow_def.get("name", "Unnamed Workflow")
            steps = workflow_def.get("steps", [])

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Executing workflow: {workflow_name}", total=len(steps)
                )

                result = await orchestrator.execute_workflow(
                    workflow_name, steps, workflow_context
                )

                progress.update(task, completed=len(steps))

            if result["success"]:
                console.print(f"[green]✅ Workflow completed successfully[/green]")
                console.print(f"📋 Workflow ID: {result['workflow_id']}")
                console.print(f"📊 Steps completed: {result['steps_completed']}")
            else:
                console.print(
                    f"[red]❌ Workflow failed: {result.get('error', 'Unknown error')}[/red]"
                )

        except Exception as e:
            console.print(f"[red]❌ Workflow execution error: {e}[/red]")

    asyncio.run(run_workflow())


@integration.command()
@click.argument("trigger_event")
@click.option("--context", help="Trigger context as JSON string")
def trigger(trigger_event: str, context: Optional[str]):
    """Trigger orchestration based on event"""
    console.print(
        f"[purple]🎯 Triggering orchestration for event: {trigger_event}[/purple]"
    )

    async def run_trigger():
        try:
            orchestrator = create_integration_orchestrator()

            # Parse context
            trigger_context = {}
            if context:
                try:
                    trigger_context = json.loads(context)
                except json.JSONDecodeError:
                    console.print("[red]❌ Invalid JSON in context parameter[/red]")
                    return

            # Trigger orchestration
            result = await orchestrator.trigger_orchestration(
                trigger_event, trigger_context
            )

            # Show results
            console.print(f"[green]✅ Orchestration triggered[/green]")
            console.print(f"📊 Rules executed: {result['rules_executed']}")

            if result["results"]:
                results_table = Table(title="Orchestration Results")
                results_table.add_column("Rule", style="cyan")
                results_table.add_column("Status", style="green")
                results_table.add_column("Details", style="yellow")

                for rule_result in result["results"]:
                    status = (
                        "✅ Success"
                        if rule_result.get("success", False)
                        else "❌ Failed"
                    )
                    details = (
                        rule_result.get("error", "Completed")
                        if not rule_result.get("success", False)
                        else "Completed"
                    )
                    results_table.add_row(rule_result["rule_name"], status, details)

                console.print(results_table)

        except Exception as e:
            console.print(f"[red]❌ Trigger error: {e}[/red]")

    asyncio.run(run_trigger())


@integration.command()
@click.option("--output", "-o", help="Output file path")
def export_config(output: Optional[str]):
    """Export integration configuration template"""
    console.print("[blue]📄 Exporting integration configuration template[/blue]")

    config_template = {
        "version": "1.0",
        "orchestration": {
            "auto_sync_enabled": True,
            "error_retry_count": 3,
            "event_processing_interval": 5,
        },
        "integrations": {
            "linear": get_default_linear_config(),
            "github": get_default_github_config(),
        },
        "orchestration_rules": [
            {
                "rule_id": "default_sync",
                "name": "Default Data Synchronization",
                "trigger_conditions": ["data_change", "scheduled_sync"],
                "target_integrations": ["linear", "github"],
                "orchestration_type": "parallel",
                "actions": [
                    {"type": "sync_data", "params": {"sync_type": "incremental"}}
                ],
                "enabled": True,
            }
        ],
    }

    output_path = output or "integration-config-template.json"

    try:
        with open(output_path, "w") as f:
            json.dump(config_template, f, indent=2)

        console.print(
            f"[green]✅ Configuration template exported to: {output_path}[/green]"
        )
        console.print("\n[yellow]Next steps:[/yellow]")
        console.print(
            "1. Edit the configuration file with your API tokens and settings"
        )
        console.print(
            "2. Initialize integrations: symphony integration init --config-file integration-config.json"
        )

    except Exception as e:
        console.print(f"[red]❌ Export failed: {e}[/red]")


# Helper functions
async def _load_configuration(config_file: Optional[str]) -> Dict[str, Any]:
    """Load configuration from file or return defaults"""
    if config_file and Path(config_file).exists():
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[yellow]⚠ Failed to load config file: {e}[/yellow]")

    # Return minimal default configuration
    return {
        "linear": get_default_linear_config(),
        "github": get_default_github_config(),
    }
