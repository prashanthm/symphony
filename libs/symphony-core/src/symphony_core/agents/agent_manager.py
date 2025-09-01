#!/usr/bin/env python3
"""
Agent Management System for Symphony Autonomous Enterprise

Manages the complete agent ecosystem including deployment, coordination,
monitoring, and lifecycle management of all Symphony agents.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Type
from datetime import datetime, timezone
from pathlib import Path
import json
import yaml

from .base_agent import BaseAgent, AgentStatus, HandoffContext
from .maestro_agent import MaestroAgent, create_maestro_agent
from .victoria_agent import VictoriaAgent, create_victoria_agent

logger = logging.getLogger(__name__)


class AgentManager:
    """Central management system for all Symphony agents"""

    def __init__(
        self, symphony_root: Optional[str] = None, customer_id: Optional[str] = None
    ):
        self.symphony_root = Path(symphony_root) if symphony_root else Path.cwd()
        self.customer_id = customer_id

        # Agent registry and state management
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_configs: Dict[str, Dict[str, Any]] = {}
        self.deployment_status: Dict[str, str] = {}

        # Orchestration state
        self.active_handoffs: Dict[str, HandoffContext] = {}
        self.coordination_queue: List[Dict[str, Any]] = []

        # Performance tracking
        self.system_metrics = {
            "total_agents": 0,
            "active_agents": 0,
            "handoff_success_rate": 0.0,
            "average_response_time": 0.0,
            "system_uptime": 0.0,
        }

        # Configuration paths
        self.config_dir = self.symphony_root / "organizations" / "config"
        self.agents_dir = self.symphony_root / "platform" / "agents"

        # Agent factory registry
        self.agent_factories = {
            "maestro-ultimate-coordinator": create_maestro_agent,
            "victoria-strategic-intelligence": create_victoria_agent,
        }

        logger.info(
            f"Agent Manager initialized for customer: {customer_id or 'system'}"
        )

    async def initialize(self) -> bool:
        """Initialize the agent management system"""
        try:
            logger.info("Initializing Agent Management System...")

            # Create necessary directories
            self._ensure_directories()

            # Load agent configurations
            await self._load_agent_configurations()

            # Initialize system metrics
            self._initialize_metrics()

            logger.info("Agent Management System initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Agent Manager initialization failed: {e}")
            return False

    async def deploy_agent(
        self, agent_id: str, agent_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Deploy a specific agent"""
        try:
            logger.info(f"Deploying agent: {agent_id}")

            # Check if agent already deployed
            if agent_id in self.agents:
                logger.warning(f"Agent {agent_id} already deployed")
                return True

            # Get or create agent configuration
            if not agent_config:
                agent_config = await self._get_agent_config(agent_id)

            # Create agent instance
            agent = await self._create_agent_instance(agent_id, agent_config)
            if not agent:
                raise Exception(f"Failed to create agent instance: {agent_id}")

            # Initialize agent
            if not await agent.initialize():
                raise Exception(f"Agent initialization failed: {agent_id}")

            # Register agent
            self.agents[agent_id] = agent
            self.deployment_status[agent_id] = "deployed"

            # Setup event handlers
            self._setup_agent_event_handlers(agent)

            # Update system metrics
            self._update_system_metrics()

            logger.info(f"Agent {agent_id} deployed successfully")
            return True

        except Exception as e:
            logger.error(f"Agent deployment failed for {agent_id}: {e}")
            self.deployment_status[agent_id] = "failed"
            return False

    async def undeploy_agent(self, agent_id: str) -> bool:
        """Undeploy a specific agent"""
        try:
            logger.info(f"Undeploying agent: {agent_id}")

            if agent_id not in self.agents:
                logger.warning(f"Agent {agent_id} not found for undeployment")
                return True

            agent = self.agents[agent_id]

            # Gracefully shutdown agent
            if not await agent.shutdown():
                logger.warning(
                    f"Agent {agent_id} shutdown had issues, but continuing..."
                )

            # Remove from registry
            del self.agents[agent_id]
            self.deployment_status[agent_id] = "undeployed"

            # Update system metrics
            self._update_system_metrics()

            logger.info(f"Agent {agent_id} undeployed successfully")
            return True

        except Exception as e:
            logger.error(f"Agent undeployment failed for {agent_id}: {e}")
            return False

    async def deploy_agent_package(self, package_type: str) -> Dict[str, bool]:
        """Deploy a complete agent package (startup, smb, enterprise, global)"""
        logger.info(f"Deploying {package_type} agent package")

        # Get package configuration
        package_config = await self._get_package_config(package_type)
        if not package_config:
            logger.error(f"Package configuration not found: {package_type}")
            return {}

        deployment_results = {}

        # Deploy agents by category in order
        deployment_order = ["maestro", "coordination", "leadership", "specialists"]

        for category in deployment_order:
            if category in package_config.get("agents", {}):
                category_agents = package_config["agents"][category]

                for agent_config in category_agents:
                    agent_id = agent_config.get("agent", "")
                    if agent_id:
                        result = await self.deploy_agent(agent_id, agent_config)
                        deployment_results[agent_id] = result

                        # Small delay between deployments
                        await asyncio.sleep(1)

        successful_deployments = sum(
            1 for success in deployment_results.values() if success
        )
        logger.info(
            f"Package deployment complete: {successful_deployments}/{len(deployment_results)} agents deployed"
        )

        return deployment_results

    async def execute_agent_task(
        self, agent_id: str, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a task on a specific agent"""
        if agent_id not in self.agents:
            return {"success": False, "error": f"Agent not found: {agent_id}"}

        agent = self.agents[agent_id]

        try:
            result = await agent.execute_task(task_data)
            logger.info(f"Task executed on {agent_id}: {result.get('success', False)}")
            return result

        except Exception as e:
            logger.error(f"Task execution failed on {agent_id}: {e}")
            return {"success": False, "error": str(e)}

    async def initiate_handoff(
        self, from_agent_id: str, to_agent_id: str, context_data: Dict[str, Any]
    ) -> bool:
        """Initiate handoff between agents"""
        logger.info(f"Initiating handoff: {from_agent_id} -> {to_agent_id}")

        if from_agent_id not in self.agents or to_agent_id not in self.agents:
            logger.error("One or both agents not found for handoff")
            return False

        from_agent = self.agents[from_agent_id]
        to_agent = self.agents[to_agent_id]

        try:
            # Create handoff context
            handoff_context = await from_agent.initiate_handoff(
                to_agent_id, context_data
            )

            # Store handoff for tracking
            self.active_handoffs[handoff_context.handoff_id] = handoff_context

            # Process handoff on receiving agent
            success = await to_agent.handle_handoff(handoff_context)

            if success:
                logger.info(
                    f"Handoff {handoff_context.handoff_id} completed successfully"
                )
                # Remove from active handoffs
                if handoff_context.handoff_id in self.active_handoffs:
                    del self.active_handoffs[handoff_context.handoff_id]
            else:
                logger.error(f"Handoff {handoff_context.handoff_id} failed")

            return success

        except Exception as e:
            logger.error(f"Handoff initiation failed: {e}")
            return False

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        agent_statuses = {}

        for agent_id, agent in self.agents.items():
            agent_statuses[agent_id] = agent.get_status()

        return {
            "system_metrics": self.system_metrics,
            "total_agents": len(self.agents),
            "active_agents": len(
                [a for a in self.agents.values() if a.status == AgentStatus.ACTIVE]
            ),
            "deployment_status": self.deployment_status,
            "active_handoffs": len(self.active_handoffs),
            "agent_details": agent_statuses,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific agent"""
        if agent_id not in self.agents:
            return None

        return self.agents[agent_id].get_status()

    async def list_available_agents(self) -> Dict[str, Any]:
        """List all available agent types and their configurations"""
        available_agents = {}

        # Load agent configurations from platform directory
        if self.agents_dir.exists():
            for category_dir in self.agents_dir.iterdir():
                if category_dir.is_dir():
                    category_name = category_dir.name
                    available_agents[category_name] = []

                    for agent_dir in category_dir.iterdir():
                        if agent_dir.is_dir():
                            agent_info = await self._load_agent_info(agent_dir)
                            if agent_info:
                                available_agents[category_name].append(agent_info)

        return available_agents

    async def coordinate_multi_agent_task(
        self, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Coordinate a task across multiple agents"""
        required_agents = task_data.get("agents", [])
        coordination_type = task_data.get("type", "sequential")

        logger.info(
            f"Coordinating multi-agent task: {coordination_type} with {len(required_agents)} agents"
        )

        # Check if Maestro is available for coordination
        maestro_available = any(
            agent.role == "Ultimate Coordinator" for agent in self.agents.values()
        )

        if maestro_available and len(required_agents) > 2:
            # Use Maestro for complex coordination
            maestro_agent = next(
                agent
                for agent in self.agents.values()
                if agent.role == "Ultimate Coordinator"
            )

            coordination_result = await maestro_agent.execute_task(
                {
                    "type": "coordinate_agents",
                    "agents": required_agents,
                    "objective": task_data.get("objective", ""),
                    "coordination_type": coordination_type,
                }
            )

            return coordination_result

        else:
            # Simple coordination without Maestro
            results = {}

            if coordination_type == "sequential":
                # Execute tasks sequentially
                for agent_id in required_agents:
                    if agent_id in self.agents:
                        agent_task_data = task_data.get("agent_tasks", {}).get(
                            agent_id, {}
                        )
                        result = await self.execute_agent_task(
                            agent_id, agent_task_data
                        )
                        results[agent_id] = result

            elif coordination_type == "parallel":
                # Execute tasks in parallel
                tasks = []
                for agent_id in required_agents:
                    if agent_id in self.agents:
                        agent_task_data = task_data.get("agent_tasks", {}).get(
                            agent_id, {}
                        )
                        task = self.execute_agent_task(agent_id, agent_task_data)
                        tasks.append((agent_id, task))

                # Wait for all tasks to complete
                for agent_id, task in tasks:
                    result = await task
                    results[agent_id] = result

            return {
                "coordination_type": coordination_type,
                "results": results,
                "success": all(r.get("success", False) for r in results.values()),
            }

    async def shutdown_all_agents(self) -> bool:
        """Shutdown all agents gracefully"""
        logger.info("Shutting down all agents...")

        shutdown_results = {}

        # Shutdown in reverse order (specialists first, maestro last)
        agent_list = list(self.agents.items())
        agent_list.reverse()

        for agent_id, agent in agent_list:
            try:
                success = await agent.shutdown()
                shutdown_results[agent_id] = success

                if success:
                    self.deployment_status[agent_id] = "shutdown"
                else:
                    self.deployment_status[agent_id] = "shutdown_failed"

            except Exception as e:
                logger.error(f"Error shutting down agent {agent_id}: {e}")
                shutdown_results[agent_id] = False
                self.deployment_status[agent_id] = "shutdown_error"

        # Clear agent registry
        self.agents.clear()

        # Update metrics
        self._update_system_metrics()

        successful_shutdowns = sum(
            1 for success in shutdown_results.values() if success
        )
        logger.info(
            f"Agent shutdown complete: {successful_shutdowns}/{len(shutdown_results)} agents shutdown successfully"
        )

        return all(shutdown_results.values())

    # Internal helper methods

    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.config_dir,
            self.symphony_root / "organizations" / "customers",
            self.symphony_root / "platform" / "agents",
            self.symphony_root / "logs",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    async def _load_agent_configurations(self):
        """Load agent configurations from config files"""
        config_file = self.config_dir / "agent-configs.yaml"

        if config_file.exists():
            with open(config_file, "r") as f:
                self.agent_configs = yaml.safe_load(f) or {}

        logger.info(f"Loaded {len(self.agent_configs)} agent configurations")

    def _initialize_metrics(self):
        """Initialize system metrics"""
        self.system_metrics = {
            "total_agents": 0,
            "active_agents": 0,
            "handoff_success_rate": 0.0,
            "average_response_time": 0.0,
            "system_uptime": 0.0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    def _update_system_metrics(self):
        """Update system performance metrics"""
        self.system_metrics.update(
            {
                "total_agents": len(self.agents),
                "active_agents": len(
                    [a for a in self.agents.values() if a.status == AgentStatus.ACTIVE]
                ),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def _get_agent_config(self, agent_id: str) -> Dict[str, Any]:
        """Get configuration for a specific agent"""
        if agent_id in self.agent_configs:
            return self.agent_configs[agent_id]

        # Return default configuration
        return {"agent_id": agent_id, "enabled": True, "auto_start": True}

    async def _create_agent_instance(
        self, agent_id: str, config: Dict[str, Any]
    ) -> Optional[BaseAgent]:
        """Create an agent instance"""
        if agent_id in self.agent_factories:
            factory_function = self.agent_factories[agent_id]
            return factory_function(customer_id=self.customer_id)

        logger.error(f"No factory function found for agent: {agent_id}")
        return None

    def _setup_agent_event_handlers(self, agent: BaseAgent):
        """Setup event handlers for agent monitoring"""
        agent.add_event_handler("task_completed", self._on_agent_task_completed)
        agent.add_event_handler("task_failed", self._on_agent_task_failed)
        agent.add_event_handler("error_occurred", self._on_agent_error)

    def _on_agent_task_completed(self, event_data: Dict[str, Any]):
        """Handle agent task completion events"""
        logger.debug(f"Agent task completed: {event_data}")

    def _on_agent_task_failed(self, event_data: Dict[str, Any]):
        """Handle agent task failure events"""
        logger.warning(f"Agent task failed: {event_data}")

    def _on_agent_error(self, event_data: Dict[str, Any]):
        """Handle agent error events"""
        logger.error(f"Agent error occurred: {event_data}")

    async def _get_package_config(self, package_type: str) -> Optional[Dict[str, Any]]:
        """Get package configuration for agent deployment"""
        package_file = (
            self.symphony_root
            / "organizations"
            / "defaults"
            / package_type
            / "package-config.yaml"
        )

        if package_file.exists():
            with open(package_file, "r") as f:
                return yaml.safe_load(f)

        logger.error(f"Package configuration not found: {package_type}")
        return None

    async def _load_agent_info(self, agent_dir: Path) -> Optional[Dict[str, Any]]:
        """Load agent information from agent directory"""
        readme_file = agent_dir / "docs" / "README.md"

        if readme_file.exists():
            return {
                "agent_id": agent_dir.name,
                "category": agent_dir.parent.name,
                "path": str(agent_dir),
                "available": True,
            }

        return None


# Factory function to create agent manager
def create_agent_manager(
    symphony_root: Optional[str] = None, customer_id: Optional[str] = None
) -> AgentManager:
    """Create a configured agent manager"""
    return AgentManager(symphony_root=symphony_root, customer_id=customer_id)


# Utility functions
async def deploy_core_agents(manager: AgentManager) -> Dict[str, bool]:
    """Deploy core agents (Maestro and Victoria)"""
    logger.info("Deploying core agents...")

    results = {}

    # Deploy Maestro first
    results["maestro-ultimate-coordinator"] = await manager.deploy_agent(
        "maestro-ultimate-coordinator"
    )

    # Deploy Victoria
    results["victoria-strategic-intelligence"] = await manager.deploy_agent(
        "victoria-strategic-intelligence"
    )

    return results
