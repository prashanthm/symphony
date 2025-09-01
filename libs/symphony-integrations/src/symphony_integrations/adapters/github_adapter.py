#!/usr/bin/env python3
"""
GitHub Integration Adapter

Implements the BaseIntegrationAdapter for GitHub repository and development workflow integration.
Provides comprehensive GitHub API integration with Symphony orchestration.
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
    from symphony_integrations.github.client import GitHubAPIClient
except ImportError as e:
    logging.warning(f"Could not import Symphony modules: {e}")

    # Define minimal interfaces for standalone operation
    class BaseIntegrationAdapter:
        def __init__(self, integration_name: str, config: Dict[str, Any]):
            self.integration_name = integration_name
            self.config = config


logger = logging.getLogger(__name__)


class GitHubIntegrationAdapter(BaseIntegrationAdapter):
    """GitHub integration adapter for Symphony orchestration"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("github", config)
        self.github_client = None
        self.organization = config.get("organization")
        self.token = config.get("token")
        self.repository_mappings = config.get("repository_mappings", {})
        self.webhook_config = config.get("webhook_config", {})

        # Metrics tracking
        self.metrics = {
            "sync_count": 0,
            "error_count": 0,
            "last_sync_duration": 0.0,
            "repositories_managed": 0,
            "issues_synced": 0,
            "pull_requests_synced": 0,
            "workflows_tracked": 0,
        }

        logger.info("GitHub Integration Adapter initialized")

    async def initialize(self) -> bool:
        """Initialize GitHub integration"""
        try:
            self.status = IntegrationStatus.INITIALIZING

            # Initialize GitHub client
            self.github_client = GitHubAPIClient(
                token=self.token, organization=self.organization
            )

            # Test connection
            connection_test = await self.github_client.test_connection()
            if not connection_test["success"]:
                raise Exception(
                    f"GitHub connection test failed: {connection_test.get('error')}"
                )

            # Get organization information
            org_info = await self.github_client.get_organization_info()
            if org_info:
                self.organization = org_info.get("login", self.organization)

            self.status = IntegrationStatus.ACTIVE
            self.health = IntegrationHealth(
                integration_name="github",
                status=IntegrationStatus.ACTIVE,
                last_sync=datetime.now(timezone.utc).isoformat(),
            )

            logger.info("GitHub integration initialized successfully")
            return True

        except Exception as e:
            self.status = IntegrationStatus.ERROR
            self.health = IntegrationHealth(
                integration_name="github",
                status=IntegrationStatus.ERROR,
                last_error=str(e),
            )
            logger.error(f"GitHub integration initialization failed: {e}")
            return False

    async def sync_data(
        self, data_type: str, options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Sync data with GitHub"""
        if not self.github_client or self.status != IntegrationStatus.ACTIVE:
            return {"success": False, "error": "GitHub integration not active"}

        try:
            self.status = IntegrationStatus.SYNCING
            start_time = datetime.now()

            options = options or {}
            sync_results = {}

            if data_type == "all" or data_type == "repositories":
                sync_results["repositories"] = await self._sync_repositories(options)

            if data_type == "all" or data_type == "issues":
                sync_results["issues"] = await self._sync_issues(options)

            if data_type == "all" or data_type == "pull_requests":
                sync_results["pull_requests"] = await self._sync_pull_requests(options)

            if data_type == "all" or data_type == "workflows":
                sync_results["workflows"] = await self._sync_workflows(options)

            if data_type == "all" or data_type == "releases":
                sync_results["releases"] = await self._sync_releases(options)

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
                    integration_name="github",
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

            logger.error(f"GitHub sync failed: {e}")

            # Emit error event
            await self.emit_event(
                IntegrationEvent(
                    event_id=f"error_{datetime.now().timestamp()}",
                    integration_name="github",
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
        """Execute an action on GitHub"""
        if not self.github_client or self.status != IntegrationStatus.ACTIVE:
            return {"success": False, "error": "GitHub integration not active"}

        try:
            result = None

            if action == "create_repository":
                result = await self._create_repository(params)

            elif action == "create_issue":
                result = await self._create_issue(params)

            elif action == "create_pull_request":
                result = await self._create_pull_request(params)

            elif action == "create_release":
                result = await self._create_release(params)

            elif action == "update_issue":
                result = await self._update_issue(params)

            elif action == "merge_pull_request":
                result = await self._merge_pull_request(params)

            elif action == "create_webhook":
                result = await self._create_webhook(params)

            elif action == "trigger_workflow":
                result = await self._trigger_workflow(params)

            elif action == "sync_with_symphony":
                result = await self._sync_with_symphony(params)

            else:
                return {"success": False, "error": f"Unsupported action: {action}"}

            # Emit action completion event
            await self.emit_event(
                IntegrationEvent(
                    event_id=f"action_{datetime.now().timestamp()}",
                    integration_name="github",
                    event_type="action_completed",
                    data={"action": action, "params": params, "result": result},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

            return {"success": True, "action": action, "result": result}

        except Exception as e:
            logger.error(f"GitHub action '{action}' failed: {e}")

            # Emit error event
            await self.emit_event(
                IntegrationEvent(
                    event_id=f"action_error_{datetime.now().timestamp()}",
                    integration_name="github",
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
    async def _sync_repositories(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Sync GitHub repositories"""
        try:
            repositories = await self.github_client.get_repositories()
            self.metrics["repositories_managed"] = len(repositories)

            return {
                "success": True,
                "repositories_count": len(repositories),
                "repositories": repositories,
            }
        except Exception as e:
            logger.error(f"Failed to sync GitHub repositories: {e}")
            return {"success": False, "error": str(e)}

    async def _sync_issues(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Sync GitHub issues"""
        try:
            repository = options.get("repository")
            if repository:
                issues = await self.github_client.get_repository_issues(repository)
            else:
                # Get issues from all repositories
                issues = []
                repositories = await self.github_client.get_repositories()
                for repo in repositories[:5]:  # Limit to prevent rate limiting
                    repo_issues = await self.github_client.get_repository_issues(
                        repo["name"]
                    )
                    issues.extend(repo_issues)

            self.metrics["issues_synced"] = len(issues)

            return {"success": True, "issues_count": len(issues), "issues": issues}
        except Exception as e:
            logger.error(f"Failed to sync GitHub issues: {e}")
            return {"success": False, "error": str(e)}

    async def _sync_pull_requests(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Sync GitHub pull requests"""
        try:
            repository = options.get("repository")
            if repository:
                prs = await self.github_client.get_pull_requests(repository)
            else:
                # Get PRs from all repositories
                prs = []
                repositories = await self.github_client.get_repositories()
                for repo in repositories[:5]:  # Limit to prevent rate limiting
                    repo_prs = await self.github_client.get_pull_requests(repo["name"])
                    prs.extend(repo_prs)

            self.metrics["pull_requests_synced"] = len(prs)

            return {
                "success": True,
                "pull_requests_count": len(prs),
                "pull_requests": prs,
            }
        except Exception as e:
            logger.error(f"Failed to sync GitHub pull requests: {e}")
            return {"success": False, "error": str(e)}

    async def _sync_workflows(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Sync GitHub Actions workflows"""
        try:
            repository = options.get("repository")
            workflows = []

            if repository:
                workflows = await self.github_client.get_workflows(repository)
            else:
                # Get workflows from all repositories
                repositories = await self.github_client.get_repositories()
                for repo in repositories[:3]:  # Limit to prevent rate limiting
                    repo_workflows = await self.github_client.get_workflows(
                        repo["name"]
                    )
                    workflows.extend(repo_workflows)

            self.metrics["workflows_tracked"] = len(workflows)

            return {
                "success": True,
                "workflows_count": len(workflows),
                "workflows": workflows,
            }
        except Exception as e:
            logger.error(f"Failed to sync GitHub workflows: {e}")
            return {"success": False, "error": str(e)}

    async def _sync_releases(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Sync GitHub releases"""
        try:
            repository = options.get("repository")
            releases = []

            if repository:
                releases = await self.github_client.get_releases(repository)
            else:
                # Get releases from all repositories
                repositories = await self.github_client.get_repositories()
                for repo in repositories[:5]:  # Limit to prevent rate limiting
                    repo_releases = await self.github_client.get_releases(repo["name"])
                    releases.extend(repo_releases)

            return {
                "success": True,
                "releases_count": len(releases),
                "releases": releases,
            }
        except Exception as e:
            logger.error(f"Failed to sync GitHub releases: {e}")
            return {"success": False, "error": str(e)}

    # Internal action methods
    async def _create_repository(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitHub repository"""
        try:
            repo_data = {
                "name": params.get("name"),
                "description": params.get("description", ""),
                "private": params.get("private", True),
                "auto_init": params.get("auto_init", True),
                "gitignore_template": params.get("gitignore_template"),
                "license_template": params.get("license_template"),
            }

            result = await self.github_client.create_repository(repo_data)

            return {
                "success": True,
                "repository_id": result.get("id"),
                "repository": result,
            }
        except Exception as e:
            logger.error(f"Failed to create GitHub repository: {e}")
            return {"success": False, "error": str(e)}

    async def _create_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitHub issue"""
        try:
            repository = params.get("repository")
            issue_data = {
                "title": params.get("title"),
                "body": params.get("body", ""),
                "labels": params.get("labels", []),
                "assignees": params.get("assignees", []),
                "milestone": params.get("milestone"),
            }

            result = await self.github_client.create_issue(repository, issue_data)

            return {
                "success": True,
                "issue_id": result.get("id"),
                "issue_number": result.get("number"),
                "issue": result,
            }
        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {e}")
            return {"success": False, "error": str(e)}

    async def _create_pull_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitHub pull request"""
        try:
            repository = params.get("repository")
            pr_data = {
                "title": params.get("title"),
                "body": params.get("body", ""),
                "head": params.get("head"),  # source branch
                "base": params.get("base", "main"),  # target branch
                "draft": params.get("draft", False),
            }

            result = await self.github_client.create_pull_request(repository, pr_data)

            return {
                "success": True,
                "pull_request_id": result.get("id"),
                "pull_request_number": result.get("number"),
                "pull_request": result,
            }
        except Exception as e:
            logger.error(f"Failed to create GitHub pull request: {e}")
            return {"success": False, "error": str(e)}

    async def _create_release(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitHub release"""
        try:
            repository = params.get("repository")
            release_data = {
                "tag_name": params.get("tag_name"),
                "name": params.get("name"),
                "body": params.get("body", ""),
                "draft": params.get("draft", False),
                "prerelease": params.get("prerelease", False),
            }

            result = await self.github_client.create_release(repository, release_data)

            return {"success": True, "release_id": result.get("id"), "release": result}
        except Exception as e:
            logger.error(f"Failed to create GitHub release: {e}")
            return {"success": False, "error": str(e)}

    async def _update_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update a GitHub issue"""
        try:
            repository = params.get("repository")
            issue_number = params.get("issue_number")
            update_data = {
                key: value
                for key, value in params.items()
                if key not in ["repository", "issue_number"] and value is not None
            }

            result = await self.github_client.update_issue(
                repository, issue_number, update_data
            )

            return {
                "success": True,
                "issue_number": issue_number,
                "updated_fields": list(update_data.keys()),
            }
        except Exception as e:
            logger.error(f"Failed to update GitHub issue: {e}")
            return {"success": False, "error": str(e)}

    async def _merge_pull_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Merge a GitHub pull request"""
        try:
            repository = params.get("repository")
            pr_number = params.get("pr_number")
            merge_data = {
                "commit_title": params.get("commit_title"),
                "commit_message": params.get("commit_message"),
                "merge_method": params.get("merge_method", "merge"),
            }

            result = await self.github_client.merge_pull_request(
                repository, pr_number, merge_data
            )

            return {
                "success": True,
                "pr_number": pr_number,
                "merged": result.get("merged", False),
                "sha": result.get("sha"),
            }
        except Exception as e:
            logger.error(f"Failed to merge GitHub pull request: {e}")
            return {"success": False, "error": str(e)}

    async def _create_webhook(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitHub webhook"""
        try:
            repository = params.get("repository")
            webhook_data = {
                "name": "web",
                "config": {
                    "url": params.get("webhook_url"),
                    "content_type": params.get("content_type", "json"),
                    "secret": params.get("secret"),
                },
                "events": params.get("events", ["push", "pull_request"]),
                "active": params.get("active", True),
            }

            result = await self.github_client.create_webhook(repository, webhook_data)

            return {"success": True, "webhook_id": result.get("id"), "webhook": result}
        except Exception as e:
            logger.error(f"Failed to create GitHub webhook: {e}")
            return {"success": False, "error": str(e)}

    async def _trigger_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a GitHub Actions workflow"""
        try:
            repository = params.get("repository")
            workflow_id = params.get("workflow_id")
            ref = params.get("ref", "main")
            inputs = params.get("inputs", {})

            result = await self.github_client.trigger_workflow(
                repository, workflow_id, ref, inputs
            )

            return {
                "success": True,
                "workflow_run_id": result.get("id"),
                "workflow_run": result,
            }
        except Exception as e:
            logger.error(f"Failed to trigger GitHub workflow: {e}")
            return {"success": False, "error": str(e)}

    async def _sync_with_symphony(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sync GitHub data with Symphony system"""
        try:
            sync_options = {
                "customer_id": params.get("customer_id"),
                "repositories": params.get("repositories", []),
                "sync_type": params.get("sync_type", "incremental"),
                "data_types": params.get(
                    "data_types", ["repositories", "issues", "pull_requests"]
                ),
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


# Factory function
def create_github_adapter(config: Dict[str, Any]) -> GitHubIntegrationAdapter:
    """Create and return a GitHub integration adapter"""
    return GitHubIntegrationAdapter(config)


# Configuration helper
def get_default_github_config() -> Dict[str, Any]:
    """Get default GitHub integration configuration"""
    return {
        "token": "",  # Should be set from environment
        "organization": "",  # GitHub organization name
        "repository_mappings": {"default": "symphony-repo"},
        "webhook_config": {
            "enabled": False,
            "events": ["push", "pull_request", "issues"],
            "secret": "",  # Should be set from environment
        },
        "sync_intervals": {
            "repositories": 3600,  # 1 hour
            "issues": 300,  # 5 minutes
            "pull_requests": 300,  # 5 minutes
            "workflows": 1800,  # 30 minutes
        },
        "auto_sync_enabled": True,
        "rate_limit_config": {"requests_per_hour": 5000, "respect_rate_limits": True},
        "retry_config": {
            "max_retries": 3,
            "retry_delay": 2.0,
            "exponential_backoff": True,
        },
    }
