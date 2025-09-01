#!/usr/bin/env python3
"""
Linear API Client for Symphony

Implements Linear API integration with proper error handling, authentication,
and Symphony-specific functionality.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import aiohttp
import yaml

# Import from symphony-core
try:
    from symphony_core.utils.env_loader import get_linear_token
except ImportError:
    # Fallback for development/testing
    def get_linear_token():
        token = os.getenv('LINEAR_API_TOKEN')
        if not token:
            raise ValueError("LINEAR_API_TOKEN environment variable is required")
        return token

from .models import LinearTeam, LinearProject, LinearIssue, LinearWorkflow

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LinearAPIClient:
    """Linear API client for Symphony documentation capture and deployment tracking"""
    
    def __init__(self, api_token: str = None):
        try:
            self.api_token = api_token or get_linear_token()
        except Exception:
            # Fallback to direct environment variable
            self.api_token = api_token or os.getenv('LINEAR_API_TOKEN')
        
        if not self.api_token:
            raise ValueError(
                "LINEAR_API_TOKEN is required. Please:\n"
                "1. Copy .env.example to .env in Symphony root\n"
                "2. Set your Linear API token in the .env file\n"
                "3. Or set LINEAR_API_TOKEN environment variable"
            )
        
        self.base_url = "https://api.linear.app/graphql"
        
        # Linear API expects just the token, not "Bearer <token>"
        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json"
        }
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def execute_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute GraphQL query against Linear API"""
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        async with self.session.post(self.base_url, json=payload) as response:
            result = await response.json()
            
            if response.status != 200:
                logger.error(f"Linear API error: {response.status} - {result}")
                raise Exception(f"Linear API error: {response.status}")
            
            if "errors" in result:
                logger.error(f"GraphQL errors: {result['errors']}")
                raise Exception(f"GraphQL errors: {result['errors']}")
            
            return result.get("data", {})
    
    async def get_teams(self) -> List[LinearTeam]:
        """Get all teams in the Linear workspace"""
        query = """
        query GetTeams {
            teams {
                nodes {
                    id
                    name
                    key
                }
            }
        }
        """
        
        result = await self.execute_query(query)
        teams = []
        
        for team_data in result["teams"]["nodes"]:
            teams.append(LinearTeam(
                id=team_data["id"],
                name=team_data["name"],
                key=team_data["key"]
            ))
        
        return teams
    
    async def create_project(self, name: str, description: str, team_id: str) -> LinearProject:
        """Create a new project in Linear"""
        query = """
        mutation CreateProject($input: ProjectCreateInput!) {
            projectCreate(input: $input) {
                project {
                    id
                    name
                    description
                    url
                }
            }
        }
        """
        
        variables = {
            "input": {
                "name": name,
                "description": description,
                "teamIds": [team_id]
            }
        }
        
        result = await self.execute_query(query, variables)
        project_data = result["projectCreate"]["project"]
        
        return LinearProject(
            id=project_data["id"],
            name=project_data["name"],
            description=project_data["description"],
            team_id=team_id,
            url=project_data["url"]
        )
    
    async def get_workflow_states(self, team_id: str) -> List[Dict[str, Any]]:
        """Get workflow states for a team"""
        query = """
        query GetWorkflowStates($teamId: String!) {
            team(id: $teamId) {
                states {
                    nodes {
                        id
                        name
                        type
                        color
                    }
                }
            }
        }
        """
        
        result = await self.execute_query(query, {"teamId": team_id})
        return result["team"]["states"]["nodes"]
    
    async def create_issue(self, title: str, description: str, team_id: str, 
                          project_id: str = None, assignee_id: str = None, 
                          priority: int = 2, labels: List[str] = None) -> LinearIssue:
        """Create a new issue in Linear"""
        query = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                issue {
                    id
                    title
                    description
                    url
                    state {
                        id
                    }
                }
            }
        }
        """
        
        issue_input = {
            "title": title,
            "description": description,
            "teamId": team_id,
            "priority": priority
        }
        
        if project_id:
            issue_input["projectId"] = project_id
        if assignee_id:
            issue_input["assigneeId"] = assignee_id
        if labels:
            # Note: Label handling would need label IDs, simplified for now
            pass
        
        variables = {"input": issue_input}
        
        result = await self.execute_query(query, variables)
        issue_data = result["issueCreate"]["issue"]
        
        return LinearIssue(
            id=issue_data["id"],
            title=issue_data["title"],
            description=issue_data["description"],
            project_id=project_id,
            assignee_id=assignee_id,
            state_id=issue_data["state"]["id"],
            priority=priority,
            url=issue_data["url"]
        )
    
    async def update_issue(self, issue_id: str, updates: Dict[str, Any]) -> LinearIssue:
        """Update an existing Linear issue"""
        query = """
        mutation UpdateIssue($issueId: String!, $input: IssueUpdateInput!) {
            issueUpdate(id: $issueId, input: $input) {
                issue {
                    id
                    title
                    description
                    url
                    state {
                        id
                    }
                }
            }
        }
        """
        
        variables = {
            "issueId": issue_id,
            "input": updates
        }
        
        result = await self.execute_query(query, variables)
        issue_data = result["issueUpdate"]["issue"]
        
        return LinearIssue(
            id=issue_data["id"],
            title=issue_data["title"],
            description=issue_data["description"],
            project_id=None,  # Would need additional query to get project
            assignee_id=None,  # Would need additional query to get assignee
            state_id=issue_data["state"]["id"],
            priority=2,  # Would need additional query to get priority
            url=issue_data["url"]
        )


class SymphonyLinearIntegration:
    """Symphony-specific Linear integration for documentation capture and deployment tracking"""
    
    def __init__(self, api_token: str = None, config_dir: Path = None):
        self.client = LinearAPIClient(api_token)
        # Updated for monorepo structure
        if config_dir is None:
            # Try to find configs directory in monorepo
            current = Path(__file__).parent
            while current.parent != current:
                if (current / "configs").exists():
                    config_dir = current / "configs"
                    break
                current = current.parent
            # Fallback
            if config_dir is None:
                config_dir = Path.cwd() / "configs"
                
        self.config_dir = config_dir
        self.workspace_config = None
        
    async def initialize_workspace(self, organization_name: str) -> Dict[str, Any]:
        """Initialize Linear workspace for Symphony deployment"""
        async with self.client as client:
            # Get teams
            teams = await client.get_teams()
            logger.info(f"Found {len(teams)} teams in Linear workspace")
            
            # Find or create Symphony team
            symphony_team = None
            for team in teams:
                if "symphony" in team.name.lower() or team.name == organization_name:
                    symphony_team = team
                    break
            
            if not symphony_team and teams:
                # Use the first available team for now
                symphony_team = teams[0]
                logger.info(f"Using team: {symphony_team.name} ({symphony_team.key})")
            
            if not symphony_team:
                raise Exception("No teams available in Linear workspace")
            
            # Get workflow states
            workflow_states = await client.get_workflow_states(symphony_team.id)
            logger.info(f"Found {len(workflow_states)} workflow states")
            
            # Create core projects
            projects = await self._create_core_projects(client, symphony_team, organization_name)
            
            self.workspace_config = {
                "team": asdict(symphony_team),
                "projects": {project.name: asdict(project) for project in projects},
                "workflow_states": workflow_states,
                "initialized_at": datetime.now().isoformat(),
                "organization_name": organization_name
            }
            
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Save workspace configuration
            config_file = self.config_dir / f"{organization_name.lower().replace(' ', '_')}_linear_workspace.json"
            with open(config_file, 'w') as f:
                json.dump(self.workspace_config, f, indent=2)
            
            logger.info(f"Linear workspace initialized for {organization_name}")
            logger.info(f"Configuration saved to {config_file}")
            
            return self.workspace_config
    
    async def _create_core_projects(self, client: LinearAPIClient, team: LinearTeam, org_name: str) -> List[LinearProject]:
        """Create core Symphony projects in Linear"""
        projects = []
        
        core_projects = [
            {
                "name": f"{org_name} - Agent Ecosystem",
                "description": "Agent deployment, coordination, and performance tracking"
            },
            {
                "name": f"{org_name} - Tool Integration",
                "description": "Tool integration setup, configuration, and monitoring"
            },
            {
                "name": f"{org_name} - Deployment Phases",
                "description": "Foundation, Optimization, and Excellence phase tracking"
            },
            {
                "name": f"{org_name} - Validation & Testing",
                "description": "Quality assurance, testing, and validation tracking"
            }
        ]
        
        for project_config in core_projects:
            try:
                project = await client.create_project(
                    name=project_config["name"],
                    description=project_config["description"],
                    team_id=team.id
                )
                projects.append(project)
                logger.info(f"Created project: {project.name}")
            except Exception as e:
                logger.error(f"Failed to create project {project_config['name']}: {e}")
        
        return projects