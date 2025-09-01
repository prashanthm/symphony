#!/usr/bin/env python3
"""
Agent Management CLI Commands

Comprehensive CLI commands for managing Symphony agents including deployment,
coordination, monitoring, and lifecycle management.
"""

import asyncio
import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from symphony_core.agents.agent_manager import (
        create_agent_manager,
        deploy_core_agents,
    )
    from symphony_core.config.customer_manager import get_customer_manager
except ImportError as e:
    click.echo(f"Error importing Symphony modules: {e}")
    click.echo("Please ensure Symphony packages are properly installed.")
    exit(1)

console = Console()


@click.group()
def agent():
    """Agent management and coordination commands"""
    pass


@agent.command()
@click.option("--customer-id", "-c", help="Customer ID for agent deployment")
@click.option(
    "--package",
    "-p",
    type=click.Choice(["startup", "smb", "enterprise", "global"]),
    default="startup",
    help="Agent package to deploy",
)
@click.option(
    "--core-only", is_flag=True, help="Deploy only core agents (Maestro and Victoria)"
)
def deploy(customer_id: Optional[str], package: str, core_only: bool):
    """Deploy agents for autonomous enterprise operations"""

    console.print(
        Panel.fit(
            "[bold blue]🚀 Symphony Agent Deployment[/bold blue]\n"
            f"[dim]Package: {package} | Customer: {customer_id or 'system'}[/dim]",
            border_style="blue",
        )
    )

    asyncio.run(_deploy_agents(customer_id, package, core_only))


@agent.command()
@click.option("--customer-id", "-c", help="Customer ID")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed agent information")
def status(customer_id: Optional[str], detailed: bool):
    """Show agent system status and health"""

    console.print(
        Panel.fit(
            "[bold green]📊 Symphony Agent Status[/bold green]", border_style="green"
        )
    )

    asyncio.run(_show_agent_status(customer_id, detailed))


@agent.command()
@click.argument("agent_id")
@click.option("--customer-id", "-c", help="Customer ID")
def start(agent_id: str, customer_id: Optional[str]):
    """Start a specific agent"""

    console.print(f"[blue]▶️ Starting agent:[/blue] {agent_id}")
    asyncio.run(_start_agent(agent_id, customer_id))


@agent.command()
@click.argument("agent_id")
@click.option("--customer-id", "-c", help="Customer ID")
def stop(agent_id: str, customer_id: Optional[str]):
    """Stop a specific agent"""

    console.print(f"[yellow]⏹️ Stopping agent:[/yellow] {agent_id}")
    asyncio.run(_stop_agent(agent_id, customer_id))


@agent.command()
@click.option("--customer-id", "-c", help="Customer ID")
@click.confirmation_option(prompt="Are you sure you want to stop all agents?")
def stop_all(customer_id: Optional[str]):
    """Stop all agents"""

    console.print("[red]🛑 Stopping all agents...[/red]")
    asyncio.run(_stop_all_agents(customer_id))


@agent.command()
def list_available():
    """List all available agent types"""

    console.print(
        Panel.fit(
            "[bold cyan]📋 Available Agent Types[/bold cyan]", border_style="cyan"
        )
    )

    asyncio.run(_list_available_agents())


@agent.command()
@click.argument("from_agent")
@click.argument("to_agent")
@click.option("--objective", "-o", required=True, help="Handoff objective")
@click.option("--context", "-ctx", help="Additional context data (JSON)")
@click.option("--customer-id", "-c", help="Customer ID")
def handoff(
    from_agent: str,
    to_agent: str,
    objective: str,
    context: Optional[str],
    customer_id: Optional[str],
):
    """Initiate handoff between agents"""

    console.print(f"[blue]🔄 Initiating handoff:[/blue] {from_agent} → {to_agent}")

    context_data = {
        "user_objective": objective,
        "completion_summary": f"Handoff initiated for: {objective}",
        "key_findings": [],
        "next_actions": [],
    }

    if context:
        try:
            additional_context = json.loads(context)
            context_data.update(additional_context)
        except json.JSONDecodeError:
            console.print("[red]Error:[/red] Invalid JSON in context parameter")
            return

    asyncio.run(_initiate_handoff(from_agent, to_agent, context_data, customer_id))


@agent.command()
@click.argument("task_type")
@click.option("--agent-id", "-a", help="Specific agent to execute task")
@click.option(
    "--agents", "-A", help="Multiple agents for coordination (comma-separated)"
)
@click.option("--data", "-d", help="Task data (JSON)")
@click.option("--customer-id", "-c", help="Customer ID")
def execute(
    task_type: str,
    agent_id: Optional[str],
    agents: Optional[str],
    data: Optional[str],
    customer_id: Optional[str],
):
    """Execute a task on agent(s)"""

    task_data = {"type": task_type}

    if data:
        try:
            additional_data = json.loads(data)
            task_data.update(additional_data)
        except json.JSONDecodeError:
            console.print("[red]Error:[/red] Invalid JSON in task data")
            return

    if agents:
        agent_list = [a.strip() for a in agents.split(",")]
        console.print(
            f"[blue]⚙️ Coordinating task:[/blue] {task_type} across {len(agent_list)} agents"
        )
        asyncio.run(
            _coordinate_multi_agent_task(task_type, agent_list, task_data, customer_id)
        )
    elif agent_id:
        console.print(f"[blue]⚙️ Executing task:[/blue] {task_type} on {agent_id}")
        asyncio.run(_execute_single_agent_task(agent_id, task_data, customer_id))
    else:
        console.print("[red]Error:[/red] Must specify either --agent-id or --agents")


@agent.command()
@click.option("--customer-id", "-c", help="Customer ID")
@click.option("--live", "-l", is_flag=True, help="Live monitoring mode")
@click.option("--interval", "-i", default=5, help="Update interval in seconds")
def monitor(customer_id: Optional[str], live: bool, interval: int):
    """Monitor agent performance and health"""

    if live:
        console.print(
            "[blue]🔍 Starting live agent monitoring (Press Ctrl+C to stop)[/blue]"
        )
        asyncio.run(_live_monitor_agents(customer_id, interval))
    else:
        console.print(
            Panel.fit(
                "[bold blue]🔍 Agent Performance Monitor[/bold blue]",
                border_style="blue",
            )
        )
        asyncio.run(_monitor_agents(customer_id))


@agent.command()
@click.option("--customer-id", "-c", help="Customer ID")
@click.option(
    "--format", "-f", type=click.Choice(["json", "yaml", "table"]), default="table"
)
def health(customer_id: Optional[str], format: str):
    """Check agent system health"""

    console.print(
        Panel.fit(
            "[bold green]🏥 Agent Health Check[/bold green]", border_style="green"
        )
    )

    asyncio.run(_health_check(customer_id, format))


# Implementation functions


async def _deploy_agents(customer_id: Optional[str], package: str, core_only: bool):
    """Deploy agents implementation"""
    try:
        manager = create_agent_manager(customer_id=customer_id)
        await manager.initialize()

        if core_only:
            console.print("Deploying core agents (Maestro and Victoria)...")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                deploy_task = progress.add_task("Deploying core agents...", total=None)

                results = await deploy_core_agents(manager)

                progress.update(
                    deploy_task, completed=True, description="Core agents deployed"
                )

            # Display results
            _display_deployment_results(results)

        else:
            console.print(f"Deploying {package} agent package...")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                deploy_task = progress.add_task(
                    f"Deploying {package} package...", total=None
                )

                results = await manager.deploy_agent_package(package)

                progress.update(
                    deploy_task,
                    completed=True,
                    description=f"{package} package deployed",
                )

            # Display results
            _display_deployment_results(results)

    except Exception as e:
        console.print(f"[red]Deployment failed:[/red] {e}")


async def _show_agent_status(customer_id: Optional[str], detailed: bool):
    """Show agent status implementation"""
    try:
        manager = create_agent_manager(customer_id=customer_id)
        await manager.initialize()

        status = await manager.get_system_status()

        # Create status table
        table = Table(title="Agent System Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Agents", str(status["total_agents"]))
        table.add_row("Active Agents", str(status["active_agents"]))
        table.add_row("Active Handoffs", str(status["active_handoffs"]))

        if "system_metrics" in status:
            metrics = status["system_metrics"]
            table.add_row(
                "Handoff Success Rate", f"{metrics.get('handoff_success_rate', 0):.1f}%"
            )
            table.add_row(
                "Avg Response Time", f"{metrics.get('average_response_time', 0):.2f}s"
            )

        console.print(table)

        if detailed and "agent_details" in status:
            console.print("\n[bold]Agent Details:[/bold]")

            for agent_id, agent_status in status["agent_details"].items():
                agent_table = Table(title=f"Agent: {agent_id}")
                agent_table.add_column("Property", style="cyan")
                agent_table.add_column("Value", style="white")

                agent_table.add_row("Name", agent_status.get("name", "Unknown"))
                agent_table.add_row("Role", agent_status.get("role", "Unknown"))
                agent_table.add_row("Status", agent_status.get("status", "Unknown"))
                agent_table.add_row(
                    "Active Tasks", str(agent_status.get("active_tasks", 0))
                )

                if "metrics" in agent_status:
                    metrics = agent_status["metrics"]
                    agent_table.add_row(
                        "Success Rate", f"{metrics.get('success_rate', 0):.1f}%"
                    )
                    agent_table.add_row(
                        "Total Tasks", str(metrics.get("total_tasks", 0))
                    )

                console.print(agent_table)
                console.print()

    except Exception as e:
        console.print(f"[red]Status check failed:[/red] {e}")


async def _start_agent(agent_id: str, customer_id: Optional[str]):
    """Start agent implementation"""
    try:
        manager = create_agent_manager(customer_id=customer_id)
        await manager.initialize()

        success = await manager.deploy_agent(agent_id)

        if success:
            console.print(f"[green]✓[/green] Agent {agent_id} started successfully")
        else:
            console.print(f"[red]✗[/red] Failed to start agent {agent_id}")

    except Exception as e:
        console.print(f"[red]Start failed:[/red] {e}")


async def _stop_agent(agent_id: str, customer_id: Optional[str]):
    """Stop agent implementation"""
    try:
        manager = create_agent_manager(customer_id=customer_id)
        await manager.initialize()

        success = await manager.undeploy_agent(agent_id)

        if success:
            console.print(f"[green]✓[/green] Agent {agent_id} stopped successfully")
        else:
            console.print(f"[red]✗[/red] Failed to stop agent {agent_id}")

    except Exception as e:
        console.print(f"[red]Stop failed:[/red] {e}")


async def _stop_all_agents(customer_id: Optional[str]):
    """Stop all agents implementation"""
    try:
        manager = create_agent_manager(customer_id=customer_id)
        await manager.initialize()

        success = await manager.shutdown_all_agents()

        if success:
            console.print("[green]✓[/green] All agents stopped successfully")
        else:
            console.print("[yellow]⚠[/yellow] Some agents may not have stopped cleanly")

    except Exception as e:
        console.print(f"[red]Shutdown failed:[/red] {e}")


async def _list_available_agents():
    """List available agents implementation"""
    try:
        manager = create_agent_manager()
        await manager.initialize()

        available_agents = await manager.list_available_agents()

        for category, agents in available_agents.items():
            if agents:
                table = Table(title=f"Category: {category.title()}")
                table.add_column("Agent ID", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Path", style="dim")

                for agent_info in agents:
                    status = (
                        "Available"
                        if agent_info.get("available", False)
                        else "Unavailable"
                    )
                    table.add_row(
                        agent_info.get("agent_id", "Unknown"),
                        status,
                        agent_info.get("path", ""),
                    )

                console.print(table)
                console.print()

    except Exception as e:
        console.print(f"[red]List failed:[/red] {e}")


async def _initiate_handoff(
    from_agent: str,
    to_agent: str,
    context_data: Dict[str, Any],
    customer_id: Optional[str],
):
    """Initiate handoff implementation"""
    try:
        manager = create_agent_manager(customer_id=customer_id)
        await manager.initialize()

        success = await manager.initiate_handoff(from_agent, to_agent, context_data)

        if success:
            console.print(
                f"[green]✓[/green] Handoff completed: {from_agent} → {to_agent}"
            )
        else:
            console.print(f"[red]✗[/red] Handoff failed: {from_agent} → {to_agent}")

    except Exception as e:
        console.print(f"[red]Handoff failed:[/red] {e}")


async def _execute_single_agent_task(
    agent_id: str, task_data: Dict[str, Any], customer_id: Optional[str]
):
    """Execute single agent task implementation"""
    try:
        manager = create_agent_manager(customer_id=customer_id)
        await manager.initialize()

        result = await manager.execute_agent_task(agent_id, task_data)

        if result.get("success", False):
            console.print(f"[green]✓[/green] Task completed successfully on {agent_id}")
            if "result" in result:
                console.print(f"Result: {result['result']}")
        else:
            console.print(f"[red]✗[/red] Task failed on {agent_id}")
            if "error" in result:
                console.print(f"Error: {result['error']}")

    except Exception as e:
        console.print(f"[red]Task execution failed:[/red] {e}")


async def _coordinate_multi_agent_task(
    task_type: str, agents: list, task_data: Dict[str, Any], customer_id: Optional[str]
):
    """Coordinate multi-agent task implementation"""
    try:
        manager = create_agent_manager(customer_id=customer_id)
        await manager.initialize()

        coordination_data = {
            "type": task_type,
            "agents": agents,
            "objective": task_data.get("objective", f"Execute {task_type}"),
            "agent_tasks": {agent: task_data for agent in agents},
        }

        result = await manager.coordinate_multi_agent_task(coordination_data)

        if result.get("success", False):
            console.print(f"[green]✓[/green] Multi-agent coordination completed")
            console.print(
                f"Coordination type: {result.get('coordination_type', 'unknown')}"
            )
        else:
            console.print(f"[red]✗[/red] Multi-agent coordination failed")

    except Exception as e:
        console.print(f"[red]Coordination failed:[/red] {e}")


async def _monitor_agents(customer_id: Optional[str]):
    """Monitor agents implementation"""
    try:
        manager = create_agent_manager(customer_id=customer_id)
        await manager.initialize()

        status = await manager.get_system_status()

        # Performance metrics table
        perf_table = Table(title="Performance Metrics")
        perf_table.add_column("Agent", style="cyan")
        perf_table.add_column("Success Rate", style="green")
        perf_table.add_column("Avg Response", style="yellow")
        perf_table.add_column("Total Tasks", style="white")

        if "agent_details" in status:
            for agent_id, agent_status in status["agent_details"].items():
                metrics = agent_status.get("metrics", {})
                perf_table.add_row(
                    agent_status.get("name", agent_id),
                    f"{metrics.get('success_rate', 0):.1f}%",
                    f"{metrics.get('avg_response_time', 0):.2f}s",
                    str(metrics.get("total_tasks", 0)),
                )

        console.print(perf_table)

    except Exception as e:
        console.print(f"[red]Monitoring failed:[/red] {e}")


async def _live_monitor_agents(customer_id: Optional[str], interval: int):
    """Live monitor agents implementation"""
    try:
        manager = create_agent_manager(customer_id=customer_id)
        await manager.initialize()

        while True:
            try:
                status = await manager.get_system_status()

                # Create live display
                table = Table(title="Live Agent Monitoring")
                table.add_column("Agent", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Active Tasks", style="yellow")
                table.add_column("Success Rate", style="white")

                if "agent_details" in status:
                    for agent_id, agent_status in status["agent_details"].items():
                        table.add_row(
                            agent_status.get("name", agent_id),
                            agent_status.get("status", "Unknown"),
                            str(agent_status.get("active_tasks", 0)),
                            f"{agent_status.get('metrics', {}).get('success_rate', 0):.1f}%",
                        )

                console.clear()
                console.print(table)
                console.print(f"\nUpdated at: {status.get('last_updated', 'Unknown')}")
                console.print("Press Ctrl+C to stop monitoring")

                await asyncio.sleep(interval)

            except KeyboardInterrupt:
                console.print("\n[yellow]Monitoring stopped[/yellow]")
                break

    except Exception as e:
        console.print(f"[red]Live monitoring failed:[/red] {e}")


async def _health_check(customer_id: Optional[str], format: str):
    """Health check implementation"""
    try:
        manager = create_agent_manager(customer_id=customer_id)
        await manager.initialize()

        status = await manager.get_system_status()

        if format == "json":
            console.print(json.dumps(status, indent=2))
        elif format == "yaml":
            import yaml

            console.print(yaml.dump(status, default_flow_style=False))
        else:
            # Table format
            health_table = Table(title="System Health Check")
            health_table.add_column("Component", style="cyan")
            health_table.add_column("Status", style="green")
            health_table.add_column("Details", style="white")

            # Overall system health
            overall_health = "Healthy" if status["active_agents"] > 0 else "Degraded"
            health_color = "green" if overall_health == "Healthy" else "red"

            health_table.add_row(
                "System",
                f"[{health_color}]{overall_health}[/{health_color}]",
                f"{status['active_agents']}/{status['total_agents']} agents active",
            )

            if "agent_details" in status:
                for agent_id, agent_status in status["agent_details"].items():
                    agent_health = agent_status.get("status", "Unknown")
                    agent_color = "green" if agent_health == "active" else "red"

                    health_table.add_row(
                        agent_status.get("name", agent_id),
                        f"[{agent_color}]{agent_health.title()}[/{agent_color}]",
                        f"Tasks: {agent_status.get('active_tasks', 0)}",
                    )

            console.print(health_table)

    except Exception as e:
        console.print(f"[red]Health check failed:[/red] {e}")


def _display_deployment_results(results: Dict[str, bool]):
    """Display deployment results in a formatted table"""
    table = Table(title="Deployment Results")
    table.add_column("Agent", style="cyan")
    table.add_column("Status", style="green")

    for agent_id, success in results.items():
        status = "[green]✓ Deployed[/green]" if success else "[red]✗ Failed[/red]"
        table.add_row(agent_id, status)

    console.print(table)

    successful = sum(1 for s in results.values() if s)
    total = len(results)

    if successful == total:
        console.print(f"\n[green]🎉 All {total} agents deployed successfully![/green]")
    else:
        console.print(
            f"\n[yellow]⚠ {successful}/{total} agents deployed successfully[/yellow]"
        )
