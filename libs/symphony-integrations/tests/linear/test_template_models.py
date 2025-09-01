#!/usr/bin/env python3
"""
Tests for Linear Template Models

Tests data classes, validation, and model interactions for the Linear workspace templates.
"""

import pytest
from dataclasses import FrozenInstanceError
from symphony_integrations.linear.template_models import (
    WorkspaceTemplate,
    OrganizationConfig,
    TeamTemplate,
    ProjectTemplate,
    Initiative,
    CustomField,
    WorkflowState,
    Milestone,
    SymphonyIntegration,
    IndustryType,
    OrganizationSize,
    FieldType,
    TemplateValidationResult,
    WorkspacePreview,
    BrandingConfig,
    VariableConfig,
)


class TestIndustryType:
    """Test IndustryType enum"""

    def test_industry_types_available(self):
        """Test all expected industry types are available"""
        expected_industries = [
            "financial_services",
            "healthcare",
            "manufacturing",
            "technology",
            "consulting",
            "retail",
            "education",
            "government",
        ]

        actual_industries = [industry.value for industry in IndustryType]

        for industry in expected_industries:
            assert industry in actual_industries

    def test_industry_type_creation(self):
        """Test creating IndustryType from string values"""
        assert IndustryType.FINANCIAL_SERVICES.value == "financial_services"
        assert IndustryType("technology") == IndustryType.TECHNOLOGY
        assert IndustryType("healthcare") == IndustryType.HEALTHCARE


class TestOrganizationSize:
    """Test OrganizationSize enum"""

    def test_organization_sizes_available(self):
        """Test all expected organization sizes are available"""
        expected_sizes = ["startup", "smb", "enterprise", "global"]
        actual_sizes = [size.value for size in OrganizationSize]

        for size in expected_sizes:
            assert size in actual_sizes

    def test_organization_size_creation(self):
        """Test creating OrganizationSize from string values"""
        assert OrganizationSize.STARTUP.value == "startup"
        assert OrganizationSize("enterprise") == OrganizationSize.ENTERPRISE


class TestFieldType:
    """Test FieldType enum"""

    def test_field_types_available(self):
        """Test all expected field types are supported"""
        expected_types = [
            "text",
            "number",
            "select",
            "multi_select",
            "date",
            "boolean",
            "url",
        ]
        actual_types = [field_type.value for field_type in FieldType]

        for field_type in expected_types:
            assert field_type in actual_types


class TestCustomField:
    """Test CustomField model"""

    def test_basic_custom_field(self):
        """Test basic custom field creation"""
        field = CustomField(
            name="Priority", type=FieldType.SELECT, options=["High", "Medium", "Low"]
        )

        assert field.name == "Priority"
        assert field.type == FieldType.SELECT
        assert field.options == ["High", "Medium", "Low"]
        assert field.required == False  # default value
        assert field.default_value is None  # default value

    def test_custom_field_with_all_options(self):
        """Test custom field with all options set"""
        field = CustomField(
            name="Budget",
            type=FieldType.NUMBER,
            description="Project budget in USD",
            required=True,
            range=[1000, 100000],
            default_value=5000,
        )

        assert field.name == "Budget"
        assert field.type == FieldType.NUMBER
        assert field.description == "Project budget in USD"
        assert field.required == True
        assert field.range == [1000, 100000]
        assert field.default_value == 5000

    def test_select_field_without_options(self):
        """Test that select fields can be created without options (validation happens elsewhere)"""
        field = CustomField(name="Category", type=FieldType.SELECT)

        assert field.options is None


class TestWorkflowState:
    """Test WorkflowState model"""

    def test_basic_workflow_state(self):
        """Test basic workflow state creation"""
        state = WorkflowState(name="In Progress", type="started", position=2)

        assert state.name == "In Progress"
        assert state.type == "started"
        assert state.position == 2
        assert state.description is None  # default
        assert state.color is None  # default

    def test_workflow_state_with_all_options(self):
        """Test workflow state with all options"""
        state = WorkflowState(
            name="Review",
            type="started",
            position=3,
            description="Under peer review",
            color="#FF6B35",
        )

        assert state.description == "Under peer review"
        assert state.color == "#FF6B35"


class TestTeamTemplate:
    """Test TeamTemplate model"""

    def test_basic_team_template(self):
        """Test basic team template creation"""
        team = TeamTemplate(
            name="Engineering", key="ENG", description="Software engineering team"
        )

        assert team.name == "Engineering"
        assert team.key == "ENG"
        assert team.description == "Software engineering team"
        assert team.workflows == []  # default empty list
        assert team.sub_teams == []  # default empty list
        assert team.custom_fields == []  # default empty list
        assert team.permissions == {}  # default empty dict

    def test_team_key_normalization(self):
        """Test that team keys are normalized to uppercase"""
        team = TeamTemplate(
            name="Engineering",
            key="eng",  # lowercase
        )

        assert team.key == "ENG"  # should be converted to uppercase

    def test_team_key_space_replacement(self):
        """Test that spaces in team keys are replaced with underscores"""
        team = TeamTemplate(
            name="Product Management",
            key="Product Mgmt",  # has space
        )

        assert team.key == "PRODUCT_MGMT"

    def test_team_with_workflows_and_fields(self):
        """Test team with workflows and custom fields"""
        workflows = [
            WorkflowState("Backlog", "backlog", 0),
            WorkflowState("In Progress", "started", 1),
        ]

        custom_fields = [
            CustomField("Priority", FieldType.SELECT, options=["High", "Low"]),
            CustomField("Estimate", FieldType.NUMBER, range=[1, 21]),
        ]

        team = TeamTemplate(
            name="Engineering",
            key="ENG",
            workflows=workflows,
            custom_fields=custom_fields,
        )

        assert len(team.workflows) == 2
        assert len(team.custom_fields) == 2
        assert team.workflows[0].name == "Backlog"
        assert team.custom_fields[0].name == "Priority"

    def test_team_with_sub_teams(self):
        """Test team with sub-teams"""
        sub_teams = [TeamTemplate("Frontend", "FE"), TeamTemplate("Backend", "BE")]

        team = TeamTemplate(name="Engineering", key="ENG", sub_teams=sub_teams)

        assert len(team.sub_teams) == 2
        assert team.sub_teams[0].name == "Frontend"
        assert team.sub_teams[1].key == "BE"


class TestMilestone:
    """Test Milestone model"""

    def test_basic_milestone(self):
        """Test basic milestone creation"""
        milestone = Milestone(
            name="Beta Release",
            description="Initial beta version",
            target_date="2025-03-15",
            position=1,
        )

        assert milestone.name == "Beta Release"
        assert milestone.description == "Initial beta version"
        assert milestone.target_date == "2025-03-15"
        assert milestone.position == 1


class TestProjectTemplate:
    """Test ProjectTemplate model"""

    def test_basic_project_template(self):
        """Test basic project template creation"""
        project = ProjectTemplate(
            template_name="compliance_project",
            name="GDPR Compliance Implementation",
            description="Implement GDPR compliance measures",
        )

        assert project.template_name == "compliance_project"
        assert project.name == "GDPR Compliance Implementation"
        assert project.description == "Implement GDPR compliance measures"
        assert project.assignable_teams == []  # default
        assert project.milestones == []  # default
        assert project.auto_create == False  # default

    def test_project_template_with_variables(self):
        """Test project template with variable substitution syntax"""
        project = ProjectTemplate(
            template_name="customer_onboarding",
            name="${customer_name} Onboarding",
            description="Onboard ${customer_name} with ${package_type} package",
        )

        assert "${customer_name}" in project.name
        assert "${customer_name}" in project.description
        assert "${package_type}" in project.description

    def test_project_template_with_milestones(self):
        """Test project template with milestones"""
        milestones = [
            Milestone("Planning", "Project planning phase"),
            Milestone("Development", "Development phase"),
            Milestone("Testing", "Testing and QA phase"),
        ]

        project = ProjectTemplate(
            template_name="standard_project",
            name="Standard Project",
            milestones=milestones,
            timeline="12 weeks",
        )

        assert len(project.milestones) == 3
        assert project.timeline == "12 weeks"


class TestInitiative:
    """Test Initiative model"""

    def test_basic_initiative(self):
        """Test basic initiative creation"""
        initiative = Initiative(
            name="Digital Transformation",
            level=1,
            description="Complete digital transformation initiative",
        )

        assert initiative.name == "Digital Transformation"
        assert initiative.level == 1
        assert initiative.description == "Complete digital transformation initiative"
        assert initiative.sub_initiatives == []  # default
        assert initiative.linked_projects == []  # default

    def test_initiative_with_sub_initiatives(self):
        """Test initiative with sub-initiatives"""
        sub_initiatives = [
            Initiative("Cloud Migration", 2, "Migrate to cloud infrastructure"),
            Initiative("Process Automation", 2, "Automate manual processes"),
        ]

        initiative = Initiative(
            name="Digital Transformation", level=1, sub_initiatives=sub_initiatives
        )

        assert len(initiative.sub_initiatives) == 2
        assert initiative.sub_initiatives[0].level == 2
        assert initiative.sub_initiatives[1].name == "Process Automation"

    def test_initiative_hierarchy_levels(self):
        """Test that initiative levels work correctly"""
        level_3_init = Initiative("Task Automation", 3)
        level_2_init = Initiative(
            "Process Automation", 2, sub_initiatives=[level_3_init]
        )
        level_1_init = Initiative(
            "Digital Transformation", 1, sub_initiatives=[level_2_init]
        )

        assert level_1_init.level == 1
        assert level_1_init.sub_initiatives[0].level == 2
        assert level_1_init.sub_initiatives[0].sub_initiatives[0].level == 3


class TestBrandingConfig:
    """Test BrandingConfig model"""

    def test_branding_config(self):
        """Test branding configuration"""
        branding = BrandingConfig(
            colors={"primary": "#007AFF", "secondary": "#FF6B35"},
            logo_url="https://example.com/logo.png",
            favicon_url="https://example.com/favicon.ico",
        )

        assert branding.colors["primary"] == "#007AFF"
        assert branding.logo_url == "https://example.com/logo.png"
        assert branding.favicon_url == "https://example.com/favicon.ico"


class TestSymphonyIntegration:
    """Test SymphonyIntegration model"""

    def test_basic_symphony_integration(self):
        """Test basic Symphony integration configuration"""
        integration = SymphonyIntegration(
            agent_assignments={"Engineering": ["Development Agent", "Test Agent"]},
            automation={"issue_creation": True, "status_sync": False},
        )

        assert "Engineering" in integration.agent_assignments
        assert len(integration.agent_assignments["Engineering"]) == 2
        assert integration.automation["issue_creation"] == True
        assert integration.automation["status_sync"] == False
        assert integration.use_symphony_defaults == True  # default

    def test_symphony_dogfooding_features(self):
        """Test Symphony self-managing features"""
        integration = SymphonyIntegration(
            self_managing=True, recursive_improvement=True, auto_optimization=True
        )

        assert integration.self_managing == True
        assert integration.recursive_improvement == True
        assert integration.auto_optimization == True


class TestOrganizationConfig:
    """Test OrganizationConfig model"""

    def test_basic_organization_config(self):
        """Test basic organization configuration"""
        org = OrganizationConfig(
            customer_name="Acme Corp",
            industry=IndustryType.TECHNOLOGY,
            size=OrganizationSize.STARTUP,
            regions=["us-east-1", "eu-west-1"],
        )

        assert org.customer_name == "Acme Corp"
        assert org.industry == IndustryType.TECHNOLOGY
        assert org.size == OrganizationSize.STARTUP
        assert len(org.regions) == 2
        assert "us-east-1" in org.regions

    def test_organization_with_locale_info(self):
        """Test organization with timezone and locale"""
        org = OrganizationConfig(
            customer_name="Global Corp",
            industry=IndustryType.FINANCIAL_SERVICES,
            size=OrganizationSize.GLOBAL,
            timezone="America/New_York",
            locale="en-US",
        )

        assert org.timezone == "America/New_York"
        assert org.locale == "en-US"


class TestWorkspaceTemplate:
    """Test WorkspaceTemplate model"""

    def test_basic_workspace_template(self):
        """Test basic workspace template creation"""
        template = WorkspaceTemplate(
            workspace={"name": "Test Workspace", "description": "Test workspace"},
            teams=[TeamTemplate("Engineering", "ENG")],
            template_version="2025.1",
        )

        assert template.workspace["name"] == "Test Workspace"
        assert len(template.teams) == 1
        assert template.teams[0].name == "Engineering"
        assert template.template_version == "2025.1"
        assert template.initiatives == []  # default
        assert template.projects == []  # default

    def test_complete_workspace_template(self):
        """Test workspace template with all components"""
        org = OrganizationConfig(
            customer_name="Test Corp",
            industry=IndustryType.TECHNOLOGY,
            size=OrganizationSize.STARTUP,
        )

        teams = [TeamTemplate("Engineering", "ENG"), TeamTemplate("Product", "PROD")]

        initiatives = [Initiative("Product Excellence", 1)]

        projects = [ProjectTemplate("mvp_project", "MVP Development")]

        symphony_integration = SymphonyIntegration(
            use_symphony_defaults=True, auto_optimization=True
        )

        template = WorkspaceTemplate(
            workspace={"name": "Complete Workspace"},
            organization=org,
            teams=teams,
            initiatives=initiatives,
            projects=projects,
            symphony_integration=symphony_integration,
        )

        assert len(template.teams) == 2
        assert len(template.initiatives) == 1
        assert len(template.projects) == 1
        assert template.organization.customer_name == "Test Corp"
        assert template.symphony_integration.auto_optimization == True

    def test_template_inheritance(self):
        """Test template inheritance configuration"""
        template = WorkspaceTemplate(
            inherits_from=["base", "industry.technology", "size.startup"]
        )

        assert len(template.inherits_from) == 3
        assert "base" in template.inherits_from
        assert "industry.technology" in template.inherits_from


class TestTemplateValidationResult:
    """Test TemplateValidationResult model"""

    def test_valid_template_result(self):
        """Test validation result for valid template"""
        result = TemplateValidationResult(is_valid=True)

        assert result.is_valid == True
        assert result.errors == []  # default
        assert result.warnings == []  # default
        assert result.suggestions == []  # default

    def test_invalid_template_result(self):
        """Test validation result for invalid template"""
        result = TemplateValidationResult(
            is_valid=False,
            errors=["Missing workspace name", "Invalid team key"],
            warnings=["Large number of teams"],
            suggestions=["Consider adding milestones"],
        )

        assert result.is_valid == False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert len(result.suggestions) == 1


class TestWorkspacePreview:
    """Test WorkspacePreview model"""

    def test_workspace_preview(self):
        """Test workspace preview creation"""
        preview = WorkspacePreview(
            workspace_name="Test Workspace",
            team_count=5,
            project_count=3,
            initiative_count=2,
            estimated_setup_time="30-60 minutes",
            complexity_score=6,
            linear_features_used=["Teams", "Projects", "Custom Fields"],
            symphony_agents_deployed=["Development Agent", "Test Agent"],
            structure_summary={"teams": [], "projects": []},
        )

        assert preview.workspace_name == "Test Workspace"
        assert preview.team_count == 5
        assert preview.complexity_score == 6
        assert len(preview.linear_features_used) == 3
        assert "Development Agent" in preview.symphony_agents_deployed


class TestModelIntegration:
    """Test integration between models"""

    def test_team_with_custom_fields_and_workflows(self):
        """Test team with both custom fields and workflows"""
        workflows = [
            WorkflowState("Backlog", "backlog", 0),
            WorkflowState("In Progress", "started", 1),
            WorkflowState("Review", "started", 2),
            WorkflowState("Done", "completed", 3),
        ]

        custom_fields = [
            CustomField("Priority", FieldType.SELECT, options=["P0", "P1", "P2"]),
            CustomField("Story Points", FieldType.NUMBER, range=[1, 21]),
            CustomField(
                "Component",
                FieldType.MULTI_SELECT,
                options=["Frontend", "Backend", "Database"],
            ),
        ]

        team = TeamTemplate(
            name="Engineering",
            key="ENG",
            description="Software engineering team",
            workflows=workflows,
            custom_fields=custom_fields,
        )

        # Verify workflows
        assert len(team.workflows) == 4
        assert team.workflows[0].type == "backlog"
        assert team.workflows[-1].type == "completed"

        # Verify custom fields
        assert len(team.custom_fields) == 3
        priority_field = next(f for f in team.custom_fields if f.name == "Priority")
        assert priority_field.type == FieldType.SELECT
        assert "P0" in priority_field.options

        story_points_field = next(
            f for f in team.custom_fields if f.name == "Story Points"
        )
        assert story_points_field.type == FieldType.NUMBER
        assert story_points_field.range == [1, 21]

    def test_project_template_with_team_assignment(self):
        """Test project template assigned to specific teams"""
        teams = [
            TeamTemplate("Engineering", "ENG"),
            TeamTemplate("Design", "DES"),
            TeamTemplate("Product", "PROD"),
        ]

        project = ProjectTemplate(
            template_name="feature_project",
            name="New Feature Development",
            assignable_teams=["Engineering", "Design"],
            milestones=[
                Milestone("Design Complete", "UX/UI design finalized"),
                Milestone("Development Complete", "Feature implementation done"),
                Milestone("Testing Complete", "QA testing completed"),
            ],
        )

        # Verify team assignments
        assert len(project.assignable_teams) == 2
        assert "Engineering" in project.assignable_teams
        assert "Design" in project.assignable_teams
        assert "Product" not in project.assignable_teams

        # Verify milestones
        assert len(project.milestones) == 3
        design_milestone = next(m for m in project.milestones if "Design" in m.name)
        assert design_milestone.description == "UX/UI design finalized"

    def test_workspace_template_consistency(self):
        """Test consistency across workspace template components"""
        # Create organization
        org = OrganizationConfig(
            customer_name="Symphony Test Corp",
            industry=IndustryType.TECHNOLOGY,
            size=OrganizationSize.STARTUP,
        )

        # Create teams
        teams = [TeamTemplate("Engineering", "ENG"), TeamTemplate("Product", "PROD")]

        # Create project that references existing teams
        project = ProjectTemplate(
            template_name="startup_mvp",
            name="Startup MVP Development",
            assignable_teams=["Engineering", "Product"],  # References teams above
            timeline="8 weeks",
        )

        # Create initiative that could link to project
        initiative = Initiative(
            name="Product Market Fit",
            level=1,
            linked_projects=["startup_mvp"],  # References project template above
        )

        # Create symphony integration with agent assignments for existing teams
        symphony = SymphonyIntegration(
            agent_assignments={
                "Engineering": ["Development Agent", "Code Review Agent"],
                "Product": ["Product Agent", "Analytics Agent"],
            }
        )

        # Create complete workspace template
        template = WorkspaceTemplate(
            workspace={
                "name": f"{org.customer_name} Workspace",
                "description": f"Workspace for {org.industry.value} {org.size.value} company",
            },
            organization=org,
            teams=teams,
            projects=[project],
            initiatives=[initiative],
            symphony_integration=symphony,
        )

        # Verify consistency
        assert template.organization.customer_name in template.workspace["name"]
        assert len(template.teams) == 2

        # All project assignable teams should exist in template teams
        team_names = {team.name for team in template.teams}
        for assignable_team in project.assignable_teams:
            assert assignable_team in team_names

        # All symphony agent assignments should be for existing teams
        for team_name in symphony.agent_assignments.keys():
            assert team_name in team_names

        # Initiative should reference existing project
        assert initiative.linked_projects[0] == project.template_name


if __name__ == "__main__":
    pytest.main([__file__])
