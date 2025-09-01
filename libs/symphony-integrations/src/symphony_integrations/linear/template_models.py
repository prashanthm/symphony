#!/usr/bin/env python3
"""
Linear Workspace Template Models

Data classes for configurable Linear workspace templates and customer configurations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class IndustryType(Enum):
    """Supported industry types for template customization"""

    FINANCIAL_SERVICES = "financial_services"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    TECHNOLOGY = "technology"
    CONSULTING = "consulting"
    RETAIL = "retail"
    EDUCATION = "education"
    GOVERNMENT = "government"


class OrganizationSize(Enum):
    """Organization sizes for template scaling"""

    STARTUP = "startup"  # 5-20 people
    SMB = "smb"  # 20-100 people
    ENTERPRISE = "enterprise"  # 100-500 people
    GLOBAL = "global"  # 500+ people


class FieldType(Enum):
    """Custom field types supported in Linear"""

    TEXT = "text"
    NUMBER = "number"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    DATE = "date"
    BOOLEAN = "boolean"
    URL = "url"


@dataclass
class CustomField:
    """Custom field configuration"""

    name: str
    type: FieldType
    description: Optional[str] = None
    required: bool = False
    options: Optional[List[str]] = None  # For select fields
    range: Optional[List[Union[int, float]]] = None  # For number fields
    default_value: Optional[Any] = None


@dataclass
class WorkflowState:
    """Workflow state configuration"""

    name: str
    type: str = "started"  # backlog, unstarted, started, completed, canceled
    position: int = 0
    description: Optional[str] = None
    color: Optional[str] = None


@dataclass
class TeamTemplate:
    """Team template configuration"""

    name: str
    key: str
    description: Optional[str] = None
    workflows: List[WorkflowState] = field(default_factory=list)
    sub_teams: List["TeamTemplate"] = field(default_factory=list)
    custom_fields: List[CustomField] = field(default_factory=list)
    permissions: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Ensure key is uppercase and valid
        self.key = self.key.upper().replace(" ", "_")


@dataclass
class Milestone:
    """Project milestone configuration"""

    name: str
    description: Optional[str] = None
    target_date: Optional[str] = None
    position: int = 0


@dataclass
class ProjectTemplate:
    """Project template configuration"""

    template_name: str
    name: str  # Can include variables like ${customer_name}
    description: Optional[str] = None
    assignable_teams: List[str] = field(default_factory=list)
    milestones: List[Milestone] = field(default_factory=list)
    custom_fields: List[CustomField] = field(default_factory=list)
    timeline: Optional[str] = None  # e.g., "12 weeks", "3 months"
    auto_create: bool = False


@dataclass
class Initiative:
    """Initiative configuration for strategic goal organization"""

    name: str
    level: int = 1  # 1-5, with 1 being top level
    description: Optional[str] = None
    owner: Optional[str] = None
    timeline: Optional[str] = None  # e.g., "2025-Q4"
    sub_initiatives: List["Initiative"] = field(default_factory=list)
    linked_projects: List[str] = field(default_factory=list)


@dataclass
class BrandingConfig:
    """Workspace branding configuration"""

    colors: Dict[str, str] = field(default_factory=dict)  # primary, secondary, etc.
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None


@dataclass
class VariableConfig:
    """Variable configuration for template substitution"""

    global_vars: Dict[str, Any] = field(default_factory=dict)
    computed_vars: Dict[str, str] = field(
        default_factory=dict
    )  # Expressions to compute
    conditional_vars: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class SymphonyIntegration:
    """Symphony-specific integration configuration"""

    agent_assignments: Dict[str, List[str]] = field(default_factory=dict)
    automation: Dict[str, bool] = field(default_factory=dict)
    defaults_override: Dict[str, Any] = field(default_factory=dict)
    use_symphony_defaults: bool = True
    custom_templates_path: Optional[str] = None

    # Symphony autonomous features
    self_managing: bool = False
    recursive_improvement: bool = False
    auto_optimization: bool = False


@dataclass
class OrganizationConfig:
    """Customer organization configuration"""

    customer_name: str
    industry: IndustryType
    size: OrganizationSize
    regions: List[str] = field(default_factory=list)
    timezone: Optional[str] = None
    locale: Optional[str] = None


@dataclass
class WorkspaceTemplate:
    """Complete workspace template configuration"""

    # Core workspace info
    workspace: Dict[str, str] = field(default_factory=dict)  # name, description
    organization: Optional[OrganizationConfig] = None
    branding: Optional[BrandingConfig] = None

    # Structure configuration
    teams: List[TeamTemplate] = field(default_factory=list)
    initiatives: List[Initiative] = field(default_factory=list)
    projects: List[ProjectTemplate] = field(default_factory=list)

    # Template system
    variables: Optional[VariableConfig] = None
    symphony_integration: Optional[SymphonyIntegration] = None

    # Template inheritance
    inherits_from: List[str] = field(default_factory=list)
    template_version: str = "2025.1"
    created_by: Optional[str] = None
    created_date: Optional[str] = None


@dataclass
class TemplateValidationResult:
    """Result of template validation"""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class WorkspacePreview:
    """Preview of what will be created"""

    workspace_name: str
    team_count: int
    project_count: int
    initiative_count: int
    estimated_setup_time: str
    complexity_score: int  # 1-10
    linear_features_used: List[str]
    symphony_agents_deployed: List[str]

    structure_summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemplateInheritance:
    """Template inheritance configuration"""

    base_templates: List[str] = field(default_factory=list)
    industry_template: Optional[str] = None
    size_template: Optional[str] = None
    custom_overrides: Optional[str] = None
    merge_strategy: str = "override"  # override, merge, append


@dataclass
class DeploymentConfig:
    """Configuration for workspace deployment"""

    linear_api_token: str
    workspace_id: Optional[str] = None
    dry_run: bool = False
    rollback_on_error: bool = True
    validate_before_deploy: bool = True

    # Deployment options
    create_teams_first: bool = True
    create_initiatives_second: bool = True
    create_projects_third: bool = True
    assign_agents_last: bool = True
