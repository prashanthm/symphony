#!/usr/bin/env python3
"""
Linear Template Validation and Preview System

Validates workspace templates and generates previews before deployment.
"""

import re
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Set

import jsonschema

from .template_models import (
    CustomField,
    FieldType,
    IndustryType,
    Initiative,
    OrganizationSize,
    ProjectTemplate,
    TeamTemplate,
    TemplateValidationResult,
    WorkspacePreview,
    WorkspaceTemplate,
)


class TemplateValidator:
    """Validates Linear workspace templates for correctness and completeness"""

    def __init__(self):
        self.schema = self._get_workspace_schema()
        self.reserved_keys = {
            "LINEAR",
            "ADMIN",
            "API",
            "SYSTEM",
            "ROOT",
            "NULL",
            "UNDEFINED",
        }
        self.max_team_hierarchy_depth = 3
        self.max_initiative_hierarchy_depth = 5
        self.max_team_key_length = 10

    def validate_template(
        self, template: WorkspaceTemplate
    ) -> TemplateValidationResult:
        """Perform comprehensive template validation"""

        errors = []
        warnings = []
        suggestions = []

        try:
            # 1. Schema validation
            schema_errors = self._validate_schema(template)
            errors.extend(schema_errors)

            # 2. Business rule validation
            business_errors, business_warnings = self._validate_business_rules(template)
            errors.extend(business_errors)
            warnings.extend(business_warnings)

            # 3. Linear API constraints validation
            api_errors, api_warnings = self._validate_linear_constraints(template)
            errors.extend(api_errors)
            warnings.extend(api_warnings)

            # 4. Symphony integration validation
            symphony_errors, symphony_suggestions = self._validate_symphony_integration(
                template
            )
            errors.extend(symphony_errors)
            suggestions.extend(symphony_suggestions)

            # 5. Best practices suggestions
            practice_suggestions = self._suggest_best_practices(template)
            suggestions.extend(practice_suggestions)

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return TemplateValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def _validate_schema(self, template: WorkspaceTemplate) -> List[str]:
        """Validate template against JSON schema"""
        errors = []

        try:
            template_dict = self._serialize_template_for_validation(template)
            jsonschema.validate(template_dict, self.schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
        except Exception as e:
            errors.append(f"Schema validation failed: {str(e)}")

        return errors

    def _serialize_template_for_validation(self, template: WorkspaceTemplate) -> Dict[str, Any]:
        """Serialize template to dictionary with enum values converted to strings"""
        template_dict = asdict(template)
        
        # Convert enum values to strings recursively
        def convert_enums(obj):
            if isinstance(obj, dict):
                return {k: convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enums(item) for item in obj]
            elif hasattr(obj, 'value'):  # Enum object
                return obj.value
            else:
                return obj
        
        return convert_enums(template_dict)

    def _validate_business_rules(
        self, template: WorkspaceTemplate
    ) -> tuple[List[str], List[str]]:
        """Validate business logic rules"""
        errors = []
        warnings = []

        # Workspace validation
        if not template.workspace or not template.workspace.get("name"):
            errors.append("Workspace name is required")

        # Team validation
        if not template.teams:
            warnings.append("No teams defined - consider adding at least one team")

        team_keys = set()
        for team in template.teams:
            # Team key validation
            if not team.key:
                errors.append(f"Team '{team.name}' missing key")
            elif team.key in self.reserved_keys:
                errors.append(f"Team key '{team.key}' is reserved")
            elif team.key in team_keys:
                errors.append(f"Duplicate team key '{team.key}'")
            elif len(team.key) > self.max_team_key_length:
                errors.append(
                    f"Team key '{team.key}' exceeds {self.max_team_key_length} characters"
                )
            else:
                team_keys.add(team.key)

            # Team hierarchy depth validation
            team_depth = self._calculate_team_depth(team)
            if team_depth > self.max_team_hierarchy_depth:
                errors.append(
                    f"Team '{team.name}' hierarchy depth ({team_depth}) exceeds maximum ({self.max_team_hierarchy_depth})"
                )

        # Initiative validation
        for initiative in template.initiatives:
            initiative_depth = self._calculate_initiative_depth(initiative)
            if initiative_depth > self.max_initiative_hierarchy_depth:
                errors.append(
                    f"Initiative '{initiative.name}' hierarchy depth ({initiative_depth}) exceeds maximum ({self.max_initiative_hierarchy_depth})"
                )

        # Project validation
        project_names = set()
        for project in template.projects:
            if project.template_name in project_names:
                errors.append(
                    f"Duplicate project template name '{project.template_name}'"
                )
            project_names.add(project.template_name)

            # Validate assignable teams exist
            for team_name in project.assignable_teams:
                if not any(team.name == team_name for team in template.teams):
                    errors.append(
                        f"Project '{project.name}' references non-existent team '{team_name}'"
                    )

        return errors, warnings

    def _validate_linear_constraints(
        self, template: WorkspaceTemplate
    ) -> tuple[List[str], List[str]]:
        """Validate against Linear API constraints"""
        errors = []
        warnings = []

        # Linear workspace limits
        if len(template.teams) > 50:
            warnings.append(
                f"Large number of teams ({len(template.teams)}) may affect performance"
            )

        if len(template.projects) > 100:
            warnings.append(
                f"Large number of projects ({len(template.projects)}) may affect organization"
            )

        # Custom field validation
        for team in template.teams:
            if len(team.custom_fields) > 20:
                warnings.append(
                    f"Team '{team.name}' has many custom fields ({len(team.custom_fields)}) which may clutter the interface"
                )

            for field in team.custom_fields:
                if field.type == FieldType.SELECT and field.options:
                    if len(field.options) > 50:
                        warnings.append(
                            f"Select field '{field.name}' has many options ({len(field.options)})"
                        )

        # Workflow state validation
        for team in template.teams:
            if len(team.workflows) > 15:
                warnings.append(
                    f"Team '{team.name}' has many workflow states ({len(team.workflows)}) which may complicate processes"
                )

        return errors, warnings

    def _validate_symphony_integration(
        self, template: WorkspaceTemplate
    ) -> tuple[List[str], List[str]]:
        """Validate Symphony-specific integration"""
        errors = []
        suggestions = []

        if not template.symphony_integration:
            suggestions.append(
                "Consider adding Symphony integration for automated agent management"
            )
            return errors, suggestions

        integration = template.symphony_integration

        # Validate agent assignments
        if integration.agent_assignments:
            assigned_teams = set(integration.agent_assignments.keys())
            template_teams = set(team.name for team in template.teams)

            missing_teams = assigned_teams - template_teams
            if missing_teams:
                errors.extend(
                    [
                        f"Agent assigned to non-existent team '{team}'"
                        for team in missing_teams
                    ]
                )

            unassigned_teams = template_teams - assigned_teams
            if unassigned_teams:
                suggestions.extend(
                    [
                        f"Consider assigning agents to team '{team}'"
                        for team in unassigned_teams
                    ]
                )

        # Validate Symphony features
        if integration.self_managing and template.organization:
            if template.organization.customer_name.lower() != "symphony":
                warnings = [
                    f"Self-managing enabled for non-Symphony customer '{template.organization.customer_name}'"
                ]

        return errors, suggestions

    def _suggest_best_practices(self, template: WorkspaceTemplate) -> List[str]:
        """Suggest best practices improvements"""
        suggestions = []

        # Team organization suggestions
        if len(template.teams) == 1:
            suggestions.append(
                "Consider organizing work into multiple teams as your organization grows"
            )

        # Initiative suggestions
        if not template.initiatives:
            suggestions.append(
                "Consider adding initiatives to organize strategic goals"
            )

        # Project template suggestions
        if not template.projects:
            suggestions.append(
                "Consider adding project templates for consistent project setup"
            )

        # Milestone suggestions
        for project in template.projects:
            if not project.milestones:
                suggestions.append(
                    f"Consider adding milestones to project template '{project.template_name}'"
                )

        return suggestions

    def _calculate_team_depth(self, team: TeamTemplate, current_depth: int = 1) -> int:
        """Calculate maximum depth of team hierarchy"""
        if not team.sub_teams:
            return current_depth

        max_sub_depth = max(
            self._calculate_team_depth(sub_team, current_depth + 1)
            for sub_team in team.sub_teams
        )
        return max_sub_depth

    def _calculate_initiative_depth(
        self, initiative: Initiative, current_depth: int = 1
    ) -> int:
        """Calculate maximum depth of initiative hierarchy"""
        if not initiative.sub_initiatives:
            return current_depth

        max_sub_depth = max(
            self._calculate_initiative_depth(sub_initiative, current_depth + 1)
            for sub_initiative in initiative.sub_initiatives
        )
        return max_sub_depth

    def _get_workspace_schema(self) -> Dict[str, Any]:
        """Get JSON schema for workspace template validation"""
        return {
            "type": "object",
            "properties": {
                "workspace": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "description": {"type": "string"},
                    },
                    "required": ["name"],
                },
                "organization": {
                    "type": "object",
                    "properties": {
                        "customer_name": {"type": "string", "minLength": 1},
                        "industry": {"type": "string"},
                        "size": {"type": "string"},
                    },
                    "required": ["customer_name", "industry", "size"],
                },
                "teams": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "key": {"type": "string", "pattern": "^[A-Z0-9_]{1,10}$"},
                        },
                        "required": ["name", "key"],
                    },
                },
            },
        }


class WorkspacePreviewGenerator:
    """Generates preview of workspace before deployment"""

    def generate_preview(self, template: WorkspaceTemplate) -> WorkspacePreview:
        """Generate comprehensive workspace preview"""

        # Calculate structure metrics
        team_count = len(template.teams)
        total_teams = team_count + sum(
            len(self._flatten_subteams(team)) for team in template.teams
        )

        project_count = len(template.projects)
        initiative_count = len(template.initiatives) + sum(
            len(self._flatten_subinitiatives(init)) for init in template.initiatives
        )

        # Estimate complexity and setup time
        complexity_score = self._calculate_complexity(template)
        setup_time = self._estimate_setup_time(template)

        # Determine Linear features used
        features_used = self._analyze_features_used(template)

        # Get Symphony agents
        agents_deployed = []
        if (
            template.symphony_integration
            and template.symphony_integration.agent_assignments
        ):
            for team_agents in template.symphony_integration.agent_assignments.values():
                agents_deployed.extend(team_agents)

        # Generate structure summary
        structure_summary = {
            "teams": [
                {
                    "name": team.name,
                    "key": team.key,
                    "sub_teams": len(team.sub_teams),
                    "workflows": len(team.workflows),
                    "custom_fields": len(team.custom_fields),
                }
                for team in template.teams
            ],
            "initiatives": [
                {
                    "name": init.name,
                    "level": init.level,
                    "sub_initiatives": len(init.sub_initiatives),
                }
                for init in template.initiatives
            ],
            "projects": [
                {
                    "template_name": proj.template_name,
                    "name": proj.name,
                    "milestones": len(proj.milestones),
                }
                for proj in template.projects
            ],
        }

        return WorkspacePreview(
            workspace_name=(
                template.workspace.get("name", "Unknown")
                if template.workspace
                else "Unknown"
            ),
            team_count=total_teams,
            project_count=project_count,
            initiative_count=initiative_count,
            estimated_setup_time=setup_time,
            complexity_score=complexity_score,
            linear_features_used=features_used,
            symphony_agents_deployed=list(set(agents_deployed)),
            structure_summary=structure_summary,
        )

    def _flatten_subteams(self, team: TeamTemplate) -> List[TeamTemplate]:
        """Flatten team hierarchy to count all teams"""
        subteams = []
        for subteam in team.sub_teams:
            subteams.append(subteam)
            subteams.extend(self._flatten_subteams(subteam))
        return subteams

    def _flatten_subinitiatives(self, initiative: Initiative) -> List[Initiative]:
        """Flatten initiative hierarchy to count all initiatives"""
        subinits = []
        for subinit in initiative.sub_initiatives:
            subinits.append(subinit)
            subinits.extend(self._flatten_subinitiatives(subinit))
        return subinits

    def _calculate_complexity(self, template: WorkspaceTemplate) -> int:
        """Calculate complexity score (1-10)"""
        score = 1

        # Team complexity
        team_count = len(template.teams)
        if team_count > 10:
            score += 3
        elif team_count > 5:
            score += 2
        elif team_count > 2:
            score += 1

        # Hierarchy complexity
        max_team_depth = max(
            (self._calculate_team_depth(team) for team in template.teams), default=1
        )
        if max_team_depth > 2:
            score += 2

        # Custom fields complexity
        total_custom_fields = sum(len(team.custom_fields) for team in template.teams)
        if total_custom_fields > 20:
            score += 2
        elif total_custom_fields > 10:
            score += 1

        # Initiative complexity
        if template.initiatives:
            max_init_depth = max(
                (
                    self._calculate_initiative_depth(init)
                    for init in template.initiatives
                ),
                default=1,
            )
            if max_init_depth > 3:
                score += 1

        return min(score, 10)

    def _calculate_team_depth(self, team: TeamTemplate, current_depth: int = 1) -> int:
        """Calculate team hierarchy depth"""
        if not team.sub_teams:
            return current_depth
        return max(
            self._calculate_team_depth(sub_team, current_depth + 1)
            for sub_team in team.sub_teams
        )

    def _calculate_initiative_depth(
        self, initiative: Initiative, current_depth: int = 1
    ) -> int:
        """Calculate initiative hierarchy depth"""
        if not initiative.sub_initiatives:
            return current_depth
        return max(
            self._calculate_initiative_depth(sub_init, current_depth + 1)
            for sub_init in initiative.sub_initiatives
        )

    def _estimate_setup_time(self, template: WorkspaceTemplate) -> str:
        """Estimate setup time based on complexity"""
        complexity = self._calculate_complexity(template)
        team_count = len(template.teams)
        project_count = len(template.projects)

        # Base time estimates
        base_minutes = 10  # Basic workspace setup
        team_minutes = team_count * 5  # 5 minutes per team
        project_minutes = project_count * 3  # 3 minutes per project
        complexity_minutes = complexity * 2  # Additional time for complexity

        total_minutes = (
            base_minutes + team_minutes + project_minutes + complexity_minutes
        )

        if total_minutes < 30:
            return "15-30 minutes"
        elif total_minutes < 60:
            return "30-60 minutes"
        elif total_minutes < 120:
            return "1-2 hours"
        else:
            return "2+ hours"

    def _analyze_features_used(self, template: WorkspaceTemplate) -> List[str]:
        """Analyze which Linear features will be used"""
        features = ["Teams", "Projects", "Issues", "Workflows"]

        # Check for advanced features
        if any(team.sub_teams for team in template.teams):
            features.append("Sub-teams")

        if template.initiatives:
            features.append("Initiatives")

        if any(team.custom_fields for team in template.teams):
            features.append("Custom Fields")

        if any(project.milestones for project in template.projects):
            features.append("Milestones")

        # Symphony-specific features
        if template.symphony_integration:
            features.append("Symphony Integration")
            if template.symphony_integration.automation.get("issue_creation"):
                features.append("Automated Issue Creation")

        return features
