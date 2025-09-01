#!/usr/bin/env python3
"""
Linear Template Engine

YAML-based template processing with inheritance, variable substitution,
and dynamic content generation.
"""

import os
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from .defaults_generator import SymphonyLinearDefaults
from .template_models import (
    IndustryType,
    Initiative,
    OrganizationConfig,
    OrganizationSize,
    ProjectTemplate,
    TeamTemplate,
    WorkspaceTemplate,
)


class TemplateEngine:
    """YAML-based template processing engine with variable substitution"""

    def __init__(self, templates_dir: Optional[str] = None):
        self.templates_dir = (
            Path(templates_dir) if templates_dir else Path("configs/linear-templates")
        )
        self.variable_pattern = re.compile(r"\$\{([^}]+)\}")
        self.defaults_generator = SymphonyLinearDefaults()

    def load_template(
        self, template_path: str, variables: Optional[Dict[str, Any]] = None
    ) -> WorkspaceTemplate:
        """Load and process a template from YAML file"""

        # Load raw YAML
        full_path = self.templates_dir / template_path
        if not full_path.exists():
            raise FileNotFoundError(f"Template not found: {full_path}")

        with open(full_path, "r") as f:
            template_data = yaml.safe_load(f)

        # Process template inheritance
        if "inherits_from" in template_data:
            template_data = self._process_inheritance(template_data)

        # Process variables
        if variables:
            template_data = self._substitute_variables(template_data, variables)

        # Convert to WorkspaceTemplate object
        return self._dict_to_workspace_template(template_data)

    def process_customer_config(self, config_path: str) -> WorkspaceTemplate:
        """Process customer configuration file with intelligent defaults"""

        # Load customer configuration
        with open(config_path, "r") as f:
            customer_config = yaml.safe_load(f)

        # Extract organization info
        org_data = customer_config.get("organization", {})
        organization = OrganizationConfig(
            customer_name=org_data.get("customer_name", "Unknown"),
            industry=IndustryType(org_data.get("industry", "technology")),
            size=OrganizationSize(org_data.get("size", "startup")),
            regions=org_data.get("regions", []),
            timezone=org_data.get("timezone"),
            locale=org_data.get("locale"),
        )

        # Generate intelligent defaults
        defaults_template = self.defaults_generator.generate_defaults(organization)

        # Merge customer config with defaults
        merged_template = self._merge_templates(defaults_template, customer_config)

        # Process variables
        variables = self._build_variable_context(merged_template, organization)
        template_dict = asdict(merged_template)
        processed_dict = self._substitute_variables(template_dict, variables)

        return self._dict_to_workspace_template(processed_dict)

    def _process_inheritance(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process template inheritance chain"""

        result = {}
        inherits_list = template_data.get("inherits_from", [])

        # Process inheritance chain in order
        for parent_template in inherits_list:
            parent_path = self._resolve_template_path(parent_template)
            parent_data = self._load_template_file(parent_path)

            # Recursive inheritance
            if "inherits_from" in parent_data:
                parent_data = self._process_inheritance(parent_data)

            # Merge parent into result
            result = self._deep_merge(result, parent_data)

        # Merge current template (overrides parents)
        result = self._deep_merge(result, template_data)

        # Remove inheritance metadata
        result.pop("inherits_from", None)

        return result

    def _substitute_variables(self, data: Any, variables: Dict[str, Any]) -> Any:
        """Recursively substitute variables in template data"""

        if isinstance(data, str):
            return self._substitute_string_variables(data, variables)
        elif isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Substitute in key
                new_key = (
                    self._substitute_string_variables(key, variables)
                    if isinstance(key, str)
                    else key
                )
                # Substitute in value
                result[new_key] = self._substitute_variables(value, variables)
            return result
        elif isinstance(data, list):
            return [self._substitute_variables(item, variables) for item in data]
        else:
            return data

    def _substitute_string_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in a string using ${variable} syntax"""

        def replace_var(match):
            var_expr = match.group(1)

            # Handle computed expressions
            if "." in var_expr:
                return self._evaluate_expression(var_expr, variables)

            # Simple variable lookup
            if var_expr in variables:
                return str(variables[var_expr])

            # Return unchanged if variable not found
            return match.group(0)

        return self.variable_pattern.sub(replace_var, text)

    def _evaluate_expression(self, expression: str, variables: Dict[str, Any]) -> str:
        """Evaluate simple expressions like date.now(), teams.length, etc."""

        if expression == "date.now()":
            return datetime.now().isoformat()
        elif expression == "date.today()":
            return datetime.now().strftime("%Y-%m-%d")

        # Handle object property access
        parts = expression.split(".")
        current = variables

        try:
            for part in parts:
                if part.endswith("()"):
                    # Method call
                    method = part[:-2]
                    if method == "length" and isinstance(current, (list, dict)):
                        return str(len(current))
                    elif method == "total_count" and isinstance(current, dict):
                        # Special method for counting nested items
                        total = sum(
                            len(v) if isinstance(v, list) else 1
                            for v in current.values()
                        )
                        return str(total)
                else:
                    # Property access
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        return expression  # Return original if can't evaluate

            return str(current)
        except:
            return expression  # Return original if evaluation fails

    def _build_variable_context(
        self, template: WorkspaceTemplate, organization: OrganizationConfig
    ) -> Dict[str, Any]:
        """Build variable context for substitution"""

        variables = {
            # Organization variables
            "customer_name": organization.customer_name,
            "industry": organization.industry.value,
            "size": organization.size.value,
            "regions": organization.regions,
            # Date variables
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "current_year": datetime.now().year,
            # Template structure variables
            "teams": [asdict(team) for team in template.teams],
            "initiatives": [asdict(init) for init in template.initiatives],
            "projects": [asdict(proj) for proj in template.projects],
        }

        # Add computed variables
        variables.update(
            {
                "team_count": len(template.teams),
                "project_count": len(template.projects),
                "initiative_count": len(template.initiatives),
            }
        )

        # Add conditional variables
        variables.update(
            {
                "compliance_required": organization.industry
                in [
                    IndustryType.FINANCIAL_SERVICES,
                    IndustryType.HEALTHCARE,
                    IndustryType.GOVERNMENT,
                ],
                "multi_region": len(organization.regions) > 1,
                "enterprise_size": organization.size
                in [OrganizationSize.ENTERPRISE, OrganizationSize.GLOBAL],
            }
        )

        # Add Symphony integration variables
        if template.symphony_integration:
            variables["symphony"] = {
                "agent_assignments": template.symphony_integration.agent_assignments,
                "self_managing": template.symphony_integration.self_managing,
                "auto_optimization": template.symphony_integration.auto_optimization,
            }

        return variables

    def _merge_templates(
        self, base_template: WorkspaceTemplate, customer_config: Dict[str, Any]
    ) -> WorkspaceTemplate:
        """Merge customer configuration with base template"""

        # Convert base template to dict for easier manipulation
        base_dict = asdict(base_template)

        # Deep merge customer config
        merged_dict = self._deep_merge(base_dict, customer_config)

        return self._dict_to_workspace_template(merged_dict)

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence"""

        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            elif (
                key in result
                and isinstance(result[key], list)
                and isinstance(value, list)
            ):
                # For lists, append or replace based on strategy
                if key in ["teams", "initiatives", "projects"]:
                    # Replace for structural elements
                    result[key] = value
                else:
                    # Append for other lists
                    result[key] = result[key] + value
            else:
                result[key] = value

        return result

    def _resolve_template_path(self, template_ref: str) -> Path:
        """Resolve template reference to full path"""

        # Handle dot notation like "industry.financial_services"
        if "." in template_ref:
            parts = template_ref.split(".")
            path = self.templates_dir / parts[0] / f"{parts[1]}.yaml"
        else:
            path = self.templates_dir / f"{template_ref}.yaml"

        return path

    def _load_template_file(self, path: Path) -> Dict[str, Any]:
        """Load template file from path"""

        if not path.exists():
            raise FileNotFoundError(f"Template not found: {path}")

        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _dict_to_workspace_template(self, data: Dict[str, Any]) -> WorkspaceTemplate:
        """Convert dictionary to WorkspaceTemplate object"""

        # This is a simplified conversion - in a full implementation,
        # you'd want proper deserialization with validation

        template = WorkspaceTemplate()

        # Basic workspace info
        if "workspace" in data:
            template.workspace = data["workspace"]

        # Organization
        if "organization" in data:
            org_data = data["organization"]
            template.organization = OrganizationConfig(
                customer_name=org_data.get("customer_name", "Unknown"),
                industry=IndustryType(org_data.get("industry", "technology")),
                size=OrganizationSize(org_data.get("size", "startup")),
                regions=org_data.get("regions", []),
            )

        # Teams (simplified - would need full deserialization)
        if "teams" in data:
            template.teams = []
            for team_data in data["teams"]:
                team = TeamTemplate(
                    name=team_data.get("name", ""),
                    key=team_data.get("key", ""),
                    description=team_data.get("description"),
                )
                template.teams.append(team)

        # Add other fields as needed...

        return template

    def save_template(self, template: WorkspaceTemplate, output_path: str) -> None:
        """Save template to YAML file"""

        template_dict = asdict(template)

        # Clean up None values and empty lists
        cleaned_dict = self._clean_dict(template_dict)

        with open(output_path, "w") as f:
            yaml.dump(cleaned_dict, f, default_flow_style=False, indent=2)

    def _clean_dict(self, data: Any) -> Any:
        """Remove None values and empty collections from dictionary"""

        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                cleaned_value = self._clean_dict(value)
                if (
                    cleaned_value is not None
                    and cleaned_value != []
                    and cleaned_value != {}
                ):
                    result[key] = cleaned_value
            return result
        elif isinstance(data, list):
            return [self._clean_dict(item) for item in data if item is not None]
        else:
            return data

    def preview_variables(
        self, template_path: str, variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Preview how variables will be substituted in template"""

        # Load raw template
        full_path = self.templates_dir / template_path
        with open(full_path, "r") as f:
            template_data = yaml.safe_load(f)

        # Find all variables in template
        template_str = yaml.dump(template_data)
        variable_matches = self.variable_pattern.findall(template_str)

        preview = {}
        for var_expr in set(variable_matches):
            if var_expr in variables:
                preview[var_expr] = variables[var_expr]
            elif "." in var_expr:
                preview[var_expr] = self._evaluate_expression(var_expr, variables)
            else:
                preview[var_expr] = f"<undefined: {var_expr}>"

        return preview


class ConfigurationWizard:
    """Interactive configuration wizard for customer workspace setup"""

    def __init__(self, template_engine: TemplateEngine):
        self.engine = template_engine
        self.defaults_generator = SymphonyLinearDefaults()

    def run_interactive_wizard(self) -> Dict[str, Any]:
        """Run interactive configuration wizard"""

        print("🎼 Symphony Linear Workspace Configuration Wizard")
        print("=" * 50)

        config = {}

        # Basic workspace info
        config["workspace"] = self._collect_workspace_info()

        # Organization info
        config["organization"] = self._collect_organization_info()

        # Structure customization
        if self._ask_yes_no(
            "Would you like to customize team structure?", default=False
        ):
            config["teams"] = self._collect_team_customization()

        if self._ask_yes_no(
            "Would you like to define custom initiatives?", default=False
        ):
            config["initiatives"] = self._collect_initiative_customization()

        # Symphony integration
        config["symphony_integration"] = self._collect_symphony_integration()

        return config

    def _collect_workspace_info(self) -> Dict[str, str]:
        """Collect basic workspace information"""

        workspace_name = input("Workspace name: ")
        description = input("Workspace description (optional): ")

        return {"name": workspace_name, "description": description}

    def _collect_organization_info(self) -> Dict[str, Any]:
        """Collect organization information"""

        customer_name = input("Organization name: ")

        print("\nIndustry options:")
        industries = list(IndustryType)
        for i, industry in enumerate(industries, 1):
            print(f"  {i}. {industry.value.replace('_', ' ').title()}")

        industry_choice = int(input("Select industry (number): ")) - 1
        industry = industries[industry_choice]

        print("\nOrganization size options:")
        sizes = list(OrganizationSize)
        for i, size in enumerate(sizes, 1):
            print(f"  {i}. {size.value.upper()}")

        size_choice = int(input("Select size (number): ")) - 1
        size = sizes[size_choice]

        regions = input("Regions (comma-separated, optional): ").split(",")
        regions = [r.strip() for r in regions if r.strip()]

        return {
            "customer_name": customer_name,
            "industry": industry.value,
            "size": size.value,
            "regions": regions,
        }

    def _collect_symphony_integration(self) -> Dict[str, Any]:
        """Collect Symphony integration preferences"""

        use_defaults = self._ask_yes_no(
            "Use Symphony intelligent defaults?", default=True
        )
        auto_optimization = self._ask_yes_no("Enable auto-optimization?", default=True)

        return {
            "use_symphony_defaults": use_defaults,
            "automation": {
                "issue_creation": True,
                "status_sync": True,
                "reporting": True,
            },
            "auto_optimization": auto_optimization,
        }

    def _ask_yes_no(self, question: str, default: bool = True) -> bool:
        """Ask yes/no question with default"""

        default_str = "Y/n" if default else "y/N"
        answer = input(f"{question} [{default_str}]: ").lower()

        if not answer:
            return default
        return answer.startswith("y")

    def _collect_team_customization(self) -> List[Dict[str, Any]]:
        """Collect custom team configuration"""
        # Simplified for now - would implement full team customization
        return []

    def _collect_initiative_customization(self) -> List[Dict[str, Any]]:
        """Collect custom initiative configuration"""
        # Simplified for now - would implement full initiative customization
        return []
