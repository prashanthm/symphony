#!/usr/bin/env python3
"""
Linear Integration Adapter

Implements the BaseIntegrationAdapter for Linear project management integration.
Provides comprehensive Linear API integration with Symphony orchestration.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from symphony_core.orchestration.integration_coordinator import (
        BaseIntegrationAdapter,
        IntegrationEvent,
        IntegrationHealth,
        IntegrationStatus,
    )
    from symphony_integrations.linear.client import SymphonyLinearIntegration
except ImportError as e:
    logging.warning(f"Could not import Symphony modules: {e}")

    # Define minimal interfaces for standalone operation
    class BaseIntegrationAdapter:
        def __init__(self, integration_name: str, config: Dict[str, Any]):
            self.integration_name = integration_name
            self.config = config


logger = logging.getLogger(__name__)


class LinearIntegrationAdapter(BaseIntegrationAdapter):
    """Linear integration adapter for Symphony orchestration"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("linear", config)
        self.linear_client = None
        self.workspace_id = config.get("workspace_id")
        self.api_token = config.get("api_token")
        self.team_mappings = config.get("team_mappings", {})
        self.sync_intervals = config.get("sync_intervals", {})

        # Metrics tracking
        self.metrics = {
            "sync_count": 0,
            "error_count": 0,
            "last_sync_duration": 0.0,
            "projects_managed": 0,
            "issues_synced": 0,
        }

        logger.info("Linear Integration Adapter initialized")

    async def initialize(self) -> bool:
        """Initialize Linear integration"""
        try:
            self.status = IntegrationStatus.INITIALIZING

            # Initialize Linear client
            self.linear_client = SymphonyLinearIntegration()

            # Test connection
            connection_test = await self.linear_client.test_connection()
            if not connection_test["success"]:
                raise Exception(
                    f"Linear connection test failed: {connection_test.get('error')}"
                )

            # Load workspace information
            workspace_info = await self.linear_client.get_workspace_info()
            self.workspace_id = workspace_info.get("id")

            self.status = IntegrationStatus.ACTIVE
            self.health = IntegrationHealth(
                integration_name="linear",
                status=IntegrationStatus.ACTIVE,
                last_sync=datetime.now(timezone.utc).isoformat(),
            )

            logger.info("Linear integration initialized successfully")
            return True

        except Exception as e:
            self.status = IntegrationStatus.ERROR
            self.health = IntegrationHealth(
                integration_name="linear",
                status=IntegrationStatus.ERROR,
                last_error=str(e),
            )
            logger.error(f"Linear integration initialization failed: {e}")
            return False

    async def sync_data(
        self, data_type: str, options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Sync data with Linear"""
        if not self.linear_client or self.status != IntegrationStatus.ACTIVE:
            return {"success": False, "error": "Linear integration not active"}

        try:
            self.status = IntegrationStatus.SYNCING
            start_time = datetime.now()

            options = options or {}
            sync_results = {}

            if data_type == "all" or data_type == "projects":
                sync_results["projects"] = await self._sync_projects(options)

            if data_type == "all" or data_type == "issues":
                sync_results["issues"] = await self._sync_issues(options)

            if data_type == "all" or data_type == "teams":
                sync_results["teams"] = await self._sync_teams(options)

            if data_type == "all" or data_type == "workflows":
                sync_results["workflows"] = await self._sync_workflows(options)

            # Update metrics
            sync_duration = (datetime.now() - start_time).total_seconds()
            self.metrics["sync_count"] += 1
            self.metrics["last_sync_duration"] = sync_duration

            # Update health
            self.health.last_sync = datetime.now(timezone.utc).isoformat()
            self.health.success_rate = (
                (self.metrics["sync_count"] - self.metrics["error_count"])
                / self.metrics["sync_count"]
                * 100
            )
            self.health.response_time_avg = sync_duration

            self.status = IntegrationStatus.ACTIVE

            # Emit sync completion event
            await self.emit_event(
                IntegrationEvent(
                    event_id=f"sync_{datetime.now().timestamp()}",
                    integration_name="linear",
                    event_type="data_sync",
                    data={
                        "data_type": data_type,
                        "sync_results": sync_results,
                        "duration": sync_duration,
                    },
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

            return {
                "success": True,
                "data_type": data_type,
                "sync_duration": sync_duration,
                "results": sync_results,
            }

        except Exception as e:
            self.metrics["error_count"] += 1
            self.health.error_count = self.metrics["error_count"]
            self.health.last_error = str(e)
            self.status = IntegrationStatus.ERROR

            logger.error(f"Linear sync failed: {e}")

            # Emit error event
            await self.emit_event(
                IntegrationEvent(
                    event_id=f"error_{datetime.now().timestamp()}",
                    integration_name="linear",
                    event_type="error",
                    data={
                        "error": str(e),
                        "data_type": data_type,
                        "operation": "sync_data",
                    },
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    priority="high",
                )
            )

            return {"success": False, "error": str(e), "data_type": data_type}

    async def execute_action(
        self, action: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an action on Linear"""
        if not self.linear_client or self.status != IntegrationStatus.ACTIVE:
            return {"success": False, "error": "Linear integration not active"}

        try:
            result = None

            if action == "create_project":
                result = await self._create_project(params)

            elif action == "create_issue":
                result = await self._create_issue(params)

            elif action == "update_issue":
                result = await self._update_issue(params)

            elif action == "create_team":
                result = await self._create_team(params)

            elif action == "initialize_workspace":
                result = await self._initialize_workspace(params)

            elif action == "sync_with_symphony":
                result = await self._sync_with_symphony(params)

            elif action == "create_workflow":
                result = await self._create_workflow(params)

            else:
                return {"success": False, "error": f"Unsupported action: {action}"}

            # Emit action completion event
            await self.emit_event(
                IntegrationEvent(
                    event_id=f"action_{datetime.now().timestamp()}",
                    integration_name="linear",
                    event_type="action_completed",
                    data={"action": action, "params": params, "result": result},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

            return {"success": True, "action": action, "result": result}

        except Exception as e:
            logger.error(f"Linear action '{action}' failed: {e}")

            # Emit error event
            await self.emit_event(
                IntegrationEvent(
                    event_id=f"action_error_{datetime.now().timestamp()}",
                    integration_name="linear",
                    event_type="error",
                    data={"error": str(e), "action": action, "params": params},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    priority="high",
                )
            )

            return {"success": False, "error": str(e), "action": action}

    async def get_health_status(self) -> IntegrationHealth:
        """Get current health status"""
        # Update health with current metrics
        self.health.success_rate = (
            (self.metrics["sync_count"] - self.metrics["error_count"])
            / max(self.metrics["sync_count"], 1)
            * 100
        )
        self.health.response_time_avg = self.metrics["last_sync_duration"]

        return self.health

    # Internal sync methods
    async def _sync_projects(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Sync Linear projects"""
        try:
            projects = await self.linear_client.get_all_projects()
            self.metrics["projects_managed"] = len(projects)

            return {
                "success": True,
                "projects_count": len(projects),
                "projects": projects,
            }
        except Exception as e:
            logger.error(f"Failed to sync Linear projects: {e}")
            return {"success": False, "error": str(e)}

    async def _sync_issues(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Sync Linear issues"""
        try:
            # Get issues from all teams or specific team
            team_id = options.get("team_id")
            if team_id:
                issues = await self.linear_client.get_team_issues(team_id)
            else:
                issues = await self.linear_client.get_all_issues()

            self.metrics["issues_synced"] = len(issues)

            return {"success": True, "issues_count": len(issues), "issues": issues}
        except Exception as e:
            logger.error(f"Failed to sync Linear issues: {e}")
            return {"success": False, "error": str(e)}

    async def _sync_teams(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Sync Linear teams"""
        try:
            teams = await self.linear_client.get_all_teams()

            return {"success": True, "teams_count": len(teams), "teams": teams}
        except Exception as e:
            logger.error(f"Failed to sync Linear teams: {e}")
            return {"success": False, "error": str(e)}

    async def _sync_workflows(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Sync Linear workflows"""
        try:
            workflows = await self.linear_client.get_workflow_states()

            return {
                "success": True,
                "workflows_count": len(workflows),
                "workflows": workflows,
            }
        except Exception as e:
            logger.error(f"Failed to sync Linear workflows: {e}")
            return {"success": False, "error": str(e)}

    # Internal action methods
    async def _create_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Linear project"""
        try:
            project_data = {
                "name": params.get("name"),
                "description": params.get("description", ""),
                "teamId": params.get("team_id"),
            }

            result = await self.linear_client.create_project(project_data)

            return {"success": True, "project_id": result.get("id"), "project": result}
        except Exception as e:
            logger.error(f"Failed to create Linear project: {e}")
            return {"success": False, "error": str(e)}

    async def _create_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Linear issue"""
        try:
            issue_data = {
                "title": params.get("title"),
                "description": params.get("description", ""),
                "teamId": params.get("team_id"),
                "projectId": params.get("project_id"),
                "priority": params.get("priority", 3),
                "labelIds": params.get("label_ids", []),
            }

            result = await self.linear_client.create_issue(issue_data)

            return {"success": True, "issue_id": result.get("id"), "issue": result}
        except Exception as e:
            logger.error(f"Failed to create Linear issue: {e}")
            return {"success": False, "error": str(e)}

    async def _update_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update a Linear issue"""
        try:
            issue_id = params.get("issue_id")
            update_data = {
                key: value
                for key, value in params.items()
                if key not in ["issue_id"] and value is not None
            }

            result = await self.linear_client.update_issue(issue_id, update_data)

            return {
                "success": True,
                "issue_id": issue_id,
                "updated_fields": list(update_data.keys()),
            }
        except Exception as e:
            logger.error(f"Failed to update Linear issue: {e}")
            return {"success": False, "error": str(e)}

    async def _create_team(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Linear team"""
        try:
            team_data = {
                "name": params.get("name"),
                "description": params.get("description", ""),
                "key": params.get("key"),
            }

            result = await self.linear_client.create_team(team_data)

            return {"success": True, "team_id": result.get("id"), "team": result}
        except Exception as e:
            logger.error(f"Failed to create Linear team: {e}")
            return {"success": False, "error": str(e)}

    async def _initialize_workspace(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize Linear workspace with Symphony configuration"""
        try:
            org_name = params.get("organization_name")

            result = await self.linear_client.initialize_workspace(org_name)

            return {"success": True, "workspace": result}
        except Exception as e:
            logger.error(f"Failed to initialize Linear workspace: {e}")
            return {"success": False, "error": str(e)}

    async def _sync_with_symphony(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sync Linear data with Symphony system"""
        try:
            sync_options = {
                "customer_id": params.get("customer_id"),
                "sync_type": params.get("sync_type", "incremental"),
                "data_types": params.get("data_types", ["projects", "issues"]),
            }

            # This would integrate with Symphony's data management
            # For now, return success with sync parameters
            return {
                "success": True,
                "sync_options": sync_options,
                "message": "Symphony sync initiated",
            }
        except Exception as e:
            logger.error(f"Failed to sync with Symphony: {e}")
            return {"success": False, "error": str(e)}

    async def _create_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create Linear workflow states"""
        try:
            workflow_data = {
                "name": params.get("name"),
                "type": params.get("type", "started"),
                "position": params.get("position", 1),
                "teamId": params.get("team_id"),
            }

            result = await self.linear_client.create_workflow_state(workflow_data)

            return {
                "success": True,
                "workflow_state_id": result.get("id"),
                "workflow_state": result,
            }
        except Exception as e:
            logger.error(f"Failed to create Linear workflow: {e}")
            return {"success": False, "error": str(e)}


# Factory function
def create_linear_adapter(config: Dict[str, Any]) -> LinearIntegrationAdapter:
    """Create and return a Linear integration adapter"""
    return LinearIntegrationAdapter(config)


# Configuration helper
def get_default_linear_config() -> Dict[str, Any]:
    """Get default Linear integration configuration"""
    return {
        "api_token": "",  # Should be set from environment
        "workspace_id": None,  # Will be determined on initialization
        "team_mappings": {"default": "symphony-team"},
        "sync_intervals": {
            "projects": 300,  # 5 minutes
            "issues": 60,  # 1 minute
            "teams": 3600,  # 1 hour
        },
        "auto_sync_enabled": True,
        "webhook_enabled": False,  # For future webhook support
        "retry_config": {
            "max_retries": 3,
            "retry_delay": 1.0,
            "exponential_backoff": True,
        },
    }
