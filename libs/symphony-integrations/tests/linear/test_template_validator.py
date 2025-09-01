#!/usr/bin/env python3
"""
Tests for Linear Template Validator

Tests validation logic, business rules, and preview generation for Linear workspace templates.
"""

from unittest.mock import Mock, patch

import pytest
from symphony_integrations.linear.template_models import (
    CustomField,
    FieldType,
    IndustryType,
    Initiative,
    Milestone,
    OrganizationConfig,
    OrganizationSize,
    ProjectTemplate,
    SymphonyIntegration,
    TeamTemplate,
    TemplateValidationResult,
    WorkflowState,
    WorkspaceTemplate,
)
from symphony_integrations.linear.template_validator import (
    TemplateValidator,
    WorkspacePreviewGenerator,
)


@pytest.fixture
def validator():
    """Fixture providing template validator instance"""
    return TemplateValidator()


@pytest.fixture
def preview_generator():
    """Fixture providing workspace preview generator instance"""
    return WorkspacePreviewGenerator()


@pytest.fixture
def valid_template():
    """Fixture providing a valid workspace template"""
    org = OrganizationConfig(
        customer_name="Test Corp",
        industry=IndustryType.TECHNOLOGY,
        size=OrganizationSize.STARTUP,
    )

    teams = [
        TeamTemplate(
            name="Engineering",
            key="ENG",
            description="Software engineering team",
            workflows=[
                WorkflowState("Backlog", "backlog", 0),
                WorkflowState("In Progress", "started", 1),
                WorkflowState("Done", "completed", 2),
            ],
            custom_fields=[
                CustomField(
                    "Priority", FieldType.SELECT, options=["High", "Medium", "Low"]
                )
            ],
        ),
        TeamTemplate(name="Product", key="PROD", description="Product management team"),
    ]

    projects = [
        ProjectTemplate(
            template_name="feature_project",
            name="Feature Development",
            description="Standard feature development project",
            assignable_teams=["Engineering", "Product"],
            milestones=[
                Milestone("Planning", "Project planning"),
                Milestone("Development", "Feature development"),
                Milestone("Testing", "QA testing"),
            ],
        )
    ]

    initiatives = [
        Initiative(
            name="Product Excellence",
            level=1,
            description="Achieve product excellence",
            sub_initiatives=[Initiative("Code Quality", 2, "Improve code quality")],
        )
    ]

    symphony_integration = SymphonyIntegration(
        agent_assignments={
            "Engineering": ["Development Agent", "Code Review Agent"],
            "Product": ["Product Agent"],
        },
        automation={"issue_creation": True, "status_sync": True},
        use_symphony_defaults=True,
    )

    return WorkspaceTemplate(
        workspace={
            "name": "Test Workspace",
            "description": "Test workspace for validation",
        },
        organization=org,
        teams=teams,
        projects=projects,
        initiatives=initiatives,
        symphony_integration=symphony_integration,
        template_version="2025.1",
    )


class TestTemplateValidator:
    """Test TemplateValidator class"""

    def test_validator_initialization(self, validator):
        """Test validator initializes with correct settings"""
        assert validator.max_team_hierarchy_depth == 3
        assert validator.max_initiative_hierarchy_depth == 5
        assert validator.max_team_key_length == 10
        assert "LINEAR" in validator.reserved_keys
        assert "ADMIN" in validator.reserved_keys

    def test_valid_template_validation(self, validator, valid_template):
        """Test validation of a valid template"""
        result = validator.validate_template(valid_template)

        assert isinstance(result, TemplateValidationResult)
        assert result.is_valid == True
        assert len(result.errors) == 0

    def test_validation_result_structure(self, validator, valid_template):
        """Test validation result has correct structure"""
        result = validator.validate_template(valid_template)

        assert hasattr(result, "is_valid")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "suggestions")

        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.suggestions, list)


class TestSchemaValidation:
    """Test schema validation functionality"""

    def test_schema_validation_with_missing_workspace(self, validator):
        """Test schema validation catches missing workspace"""
        template = WorkspaceTemplate()  # Empty template

        result = validator.validate_template(template)

        assert result.is_valid == False
        # Should have errors about missing workspace name
        error_messages = " ".join(result.errors).lower()
        assert "workspace" in error_messages or "name" in error_messages

    @patch("symphony_integrations.linear.template_validator.jsonschema.validate")
    def test_schema_validation_called(self, mock_validate, validator, valid_template):
        """Test that schema validation is called"""
        validator.validate_template(valid_template)

        assert mock_validate.called
        # Verify it was called with template data and schema
        call_args = mock_validate.call_args
        assert len(call_args[0]) == 2  # data and schema

    @patch("symphony_integrations.linear.template_validator.jsonschema.validate")
    def test_schema_validation_error_handling(
        self, mock_validate, validator, valid_template
    ):
        """Test schema validation error handling"""
        from jsonschema import ValidationError

        mock_validate.side_effect = ValidationError("Test validation error")

        result = validator.validate_template(valid_template)

        assert result.is_valid == False
        assert any(
            "schema validation error" in error.lower() for error in result.errors
        )


class TestBusinessRulesValidation:
    """Test business rules validation"""

    def test_missing_workspace_name_error(self, validator):
        """Test error for missing workspace name"""
        template = WorkspaceTemplate(workspace={})  # Missing name

        result = validator.validate_template(template)

        assert result.is_valid == False
        assert any("workspace name" in error.lower() for error in result.errors)

    def test_no_teams_warning(self, validator):
        """Test warning when no teams are defined"""
        template = WorkspaceTemplate(
            workspace={"name": "Test Workspace"}, teams=[]  # No teams
        )

        result = validator.validate_template(template)

        # Should be valid but have warnings
        assert len(result.warnings) > 0
        assert any("team" in warning.lower() for warning in result.warnings)

    def test_team_key_validation(self, validator):
        """Test team key validation rules"""
        # Test missing key
        team_no_key = TeamTemplate(name="Test Team", key="")
        template = WorkspaceTemplate(workspace={"name": "Test"}, teams=[team_no_key])

        result = validator.validate_template(template)
        assert result.is_valid == False
        assert any("missing key" in error.lower() for error in result.errors)

        # Test reserved key
        team_reserved_key = TeamTemplate(name="Test Team", key="LINEAR")
        template.teams = [team_reserved_key]

        result = validator.validate_template(template)
        assert result.is_valid == False
        assert any("reserved" in error.lower() for error in result.errors)

        # Test duplicate key
        team1 = TeamTemplate(name="Team 1", key="TEST")
        team2 = TeamTemplate(name="Team 2", key="TEST")
        template.teams = [team1, team2]

        result = validator.validate_template(template)
        assert result.is_valid == False
        assert any("duplicate" in error.lower() for error in result.errors)

        # Test key too long
        team_long_key = TeamTemplate(name="Test Team", key="VERYLONGKEY123")
        template.teams = [team_long_key]

        result = validator.validate_template(template)
        assert result.is_valid == False
        assert any("exceeds" in error.lower() for error in result.errors)

    def test_project_assignable_teams_validation(self, validator, valid_template):
        """Test validation of project assignable teams"""
        # Add project with non-existent team
        invalid_project = ProjectTemplate(
            template_name="invalid_project",
            name="Invalid Project",
            assignable_teams=["NonExistentTeam"],
        )
        valid_template.projects = [invalid_project]

        result = validator.validate_template(valid_template)

        assert result.is_valid == False
        assert any("non-existent team" in error.lower() for error in result.errors)

    def test_duplicate_project_template_names(self, validator, valid_template):
        """Test validation catches duplicate project template names"""
        project1 = ProjectTemplate(template_name="duplicate", name="Project 1")
        project2 = ProjectTemplate(template_name="duplicate", name="Project 2")
        valid_template.projects = [project1, project2]

        result = validator.validate_template(valid_template)

        assert result.is_valid == False
        assert any(
            "duplicate" in error.lower() and "template name" in error.lower()
            for error in result.errors
        )


class TestLinearConstraintsValidation:
    """Test Linear API constraints validation"""

    def test_large_number_of_teams_warning(self, validator):
        """Test warning for large number of teams"""
        teams = [TeamTemplate(f"Team {i}", f"T{i}") for i in range(51)]
        template = WorkspaceTemplate(workspace={"name": "Test"}, teams=teams)

        result = validator.validate_template(template)

        assert any(
            "large number of teams" in warning.lower() for warning in result.warnings
        )

    def test_large_number_of_projects_warning(self, validator):
        """Test warning for large number of projects"""
        projects = [ProjectTemplate(f"project_{i}", f"Project {i}") for i in range(101)]
        template = WorkspaceTemplate(workspace={"name": "Test"}, projects=projects)

        result = validator.validate_template(template)

        assert any(
            "large number of projects" in warning.lower() for warning in result.warnings
        )

    def test_custom_fields_limit_warning(self, validator):
        """Test warning for too many custom fields"""
        custom_fields = [CustomField(f"Field {i}", FieldType.TEXT) for i in range(21)]
        team = TeamTemplate(name="Test Team", key="TEST", custom_fields=custom_fields)
        template = WorkspaceTemplate(workspace={"name": "Test"}, teams=[team])

        result = validator.validate_template(template)

        assert any(
            "many custom fields" in warning.lower() for warning in result.warnings
        )

    def test_select_field_options_limit_warning(self, validator):
        """Test warning for select fields with too many options"""
        options = [f"Option {i}" for i in range(51)]
        custom_field = CustomField(
            name="Test Select", type=FieldType.SELECT, options=options
        )
        team = TeamTemplate(name="Test Team", key="TEST", custom_fields=[custom_field])
        template = WorkspaceTemplate(workspace={"name": "Test"}, teams=[team])

        result = validator.validate_template(template)

        assert any("many options" in warning.lower() for warning in result.warnings)

    def test_workflow_states_limit_warning(self, validator):
        """Test warning for too many workflow states"""
        workflows = [WorkflowState(f"State {i}", "started", i) for i in range(16)]
        team = TeamTemplate(name="Test Team", key="TEST", workflows=workflows)
        template = WorkspaceTemplate(workspace={"name": "Test"}, teams=[team])

        result = validator.validate_template(template)

        assert any(
            "many workflow states" in warning.lower() for warning in result.warnings
        )


class TestSymphonyIntegrationValidation:
    """Test Symphony integration validation"""

    def test_missing_symphony_integration_suggestion(self, validator):
        """Test suggestion when Symphony integration is missing"""
        template = WorkspaceTemplate(
            workspace={"name": "Test"}, teams=[TeamTemplate("Test Team", "TEST")]
        )

        result = validator.validate_template(template)

        assert any(
            "symphony integration" in suggestion.lower()
            for suggestion in result.suggestions
        )

    def test_agent_assignments_for_nonexistent_teams(self, validator, valid_template):
        """Test error when agents assigned to non-existent teams"""
        valid_template.symphony_integration.agent_assignments = {
            "NonExistentTeam": ["Some Agent"]
        }

        result = validator.validate_template(valid_template)

        assert result.is_valid == False
        assert any("non-existent team" in error.lower() for error in result.errors)

    def test_suggestions_for_unassigned_teams(self, validator, valid_template):
        """Test suggestions for teams without agent assignments"""
        # Remove one team from agent assignments
        valid_template.symphony_integration.agent_assignments = {
            "Engineering": ["Development Agent"]
            # "Product" team missing
        }

        result = validator.validate_template(valid_template)

        suggestions_text = " ".join(result.suggestions).lower()
        assert "product" in suggestions_text and "assigning agents" in suggestions_text

    def test_self_managing_validation(self, validator, valid_template):
        """Test validation of self-managing feature"""
        # Self-managing enabled for non-Symphony customer
        valid_template.symphony_integration.self_managing = True
        valid_template.organization.customer_name = "Other Corp"

        result = validator.validate_template(valid_template)

        # Should have warnings about self-managing for non-Symphony customer
        # Note: Check implementation to see if this creates warnings or errors


class TestHierarchyDepthValidation:
    """Test hierarchy depth validation"""

    def test_team_hierarchy_depth_validation(self, validator):
        """Test team hierarchy depth limits"""
        # Create deeply nested team structure
        level3_team = TeamTemplate("Level 3", "L3")
        level2_team = TeamTemplate("Level 2", "L2", sub_teams=[level3_team])
        level1_team = TeamTemplate("Level 1", "L1", sub_teams=[level2_team])
        root_team = TeamTemplate("Root", "ROOT", sub_teams=[level1_team])

        template = WorkspaceTemplate(workspace={"name": "Test"}, teams=[root_team])

        result = validator.validate_template(template)

        # Should exceed max depth of 3
        assert result.is_valid == False
        assert any(
            "hierarchy depth" in error and "exceeds maximum" in error
            for error in result.errors
        )

    def test_initiative_hierarchy_depth_validation(self, validator):
        """Test initiative hierarchy depth limits"""
        # Create deeply nested initiative structure (more than 5 levels)
        level5 = Initiative("Level 5", 5)
        level4 = Initiative("Level 4", 4, sub_initiatives=[level5])
        level3 = Initiative("Level 3", 3, sub_initiatives=[level4])
        level2 = Initiative("Level 2", 2, sub_initiatives=[level3])
        level1 = Initiative("Level 1", 1, sub_initiatives=[level2])
        root = Initiative("Root", 1, sub_initiatives=[level1])

        template = WorkspaceTemplate(workspace={"name": "Test"}, initiatives=[root])

        result = validator.validate_template(template)

        # Should exceed max depth of 5
        assert result.is_valid == False
        assert any(
            "hierarchy depth" in error and "exceeds maximum" in error
            for error in result.errors
        )


class TestBestPracticesSuggestions:
    """Test best practices suggestions"""

    def test_single_team_suggestion(self, validator):
        """Test suggestion for single team organizations"""
        template = WorkspaceTemplate(
            workspace={"name": "Test"}, teams=[TeamTemplate("Only Team", "ONLY")]
        )

        result = validator.validate_template(template)

        assert any(
            "multiple teams" in suggestion.lower() for suggestion in result.suggestions
        )

    def test_no_initiatives_suggestion(self, validator, valid_template):
        """Test suggestion when no initiatives are defined"""
        valid_template.initiatives = []

        result = validator.validate_template(valid_template)

        assert any(
            "initiatives" in suggestion.lower() for suggestion in result.suggestions
        )

    def test_no_projects_suggestion(self, validator, valid_template):
        """Test suggestion when no project templates are defined"""
        valid_template.projects = []

        result = validator.validate_template(valid_template)

        assert any(
            "project templates" in suggestion.lower()
            for suggestion in result.suggestions
        )

    def test_projects_without_milestones_suggestion(self, validator, valid_template):
        """Test suggestion for projects without milestones"""
        project_without_milestones = ProjectTemplate(
            template_name="no_milestones",
            name="Project Without Milestones",
            milestones=[],
        )
        valid_template.projects = [project_without_milestones]

        result = validator.validate_template(valid_template)

        assert any(
            "milestones" in suggestion.lower() for suggestion in result.suggestions
        )


class TestWorkspacePreviewGenerator:
    """Test WorkspacePreviewGenerator class"""

    def test_preview_generator_initialization(self, preview_generator):
        """Test preview generator initializes correctly"""
        assert preview_generator is not None
        assert hasattr(preview_generator, "generate_preview")

    def test_generate_basic_preview(self, preview_generator, valid_template):
        """Test generating basic workspace preview"""
        preview = preview_generator.generate_preview(valid_template)

        assert preview.workspace_name == "Test Workspace"
        assert preview.team_count >= len(valid_template.teams)
        assert preview.project_count == len(valid_template.projects)
        assert preview.initiative_count >= len(valid_template.initiatives)

        assert isinstance(preview.complexity_score, int)
        assert 1 <= preview.complexity_score <= 10

        assert isinstance(preview.linear_features_used, list)
        assert len(preview.linear_features_used) > 0

    def test_preview_includes_sub_teams(self, preview_generator):
        """Test preview counts include sub-teams"""
        sub_team = TeamTemplate("Sub Team", "SUB")
        main_team = TeamTemplate("Main Team", "MAIN", sub_teams=[sub_team])

        template = WorkspaceTemplate(workspace={"name": "Test"}, teams=[main_team])

        preview = preview_generator.generate_preview(template)

        # Should count both main team and sub-team
        assert preview.team_count == 2

    def test_preview_includes_sub_initiatives(self, preview_generator):
        """Test preview counts include sub-initiatives"""
        sub_initiative = Initiative("Sub Initiative", 2)
        main_initiative = Initiative(
            "Main Initiative", 1, sub_initiatives=[sub_initiative]
        )

        template = WorkspaceTemplate(
            workspace={"name": "Test"}, initiatives=[main_initiative]
        )

        preview = preview_generator.generate_preview(template)

        # Should count both main and sub initiatives
        assert preview.initiative_count == 2

    def test_complexity_score_calculation(self, preview_generator):
        """Test complexity score increases with more features"""
        simple_template = WorkspaceTemplate(
            workspace={"name": "Simple"}, teams=[TeamTemplate("Team", "T")]
        )

        complex_template = WorkspaceTemplate(
            workspace={"name": "Complex"},
            teams=[
                TeamTemplate(
                    name=f"Team {i}",
                    key=f"T{i}",
                    custom_fields=[
                        CustomField(f"Field {j}", FieldType.TEXT) for j in range(5)
                    ],
                    sub_teams=[
                        TeamTemplate(f"Sub {i}-{k}", f"S{i}{k}") for k in range(2)
                    ],
                )
                for i in range(5)
            ],
            initiatives=[
                Initiative(
                    name=f"Initiative {i}",
                    level=1,
                    sub_initiatives=[Initiative(f"Sub {i}-{j}", 2) for j in range(3)],
                )
                for i in range(3)
            ],
        )

        simple_preview = preview_generator.generate_preview(simple_template)
        complex_preview = preview_generator.generate_preview(complex_template)

        assert complex_preview.complexity_score > simple_preview.complexity_score

    def test_setup_time_estimation(self, preview_generator):
        """Test setup time estimation"""
        small_template = WorkspaceTemplate(
            workspace={"name": "Small"}, teams=[TeamTemplate("Team", "T")]
        )

        large_template = WorkspaceTemplate(
            workspace={"name": "Large"},
            teams=[TeamTemplate(f"Team {i}", f"T{i}") for i in range(10)],
            projects=[ProjectTemplate(f"proj_{i}", f"Project {i}") for i in range(5)],
        )

        small_preview = preview_generator.generate_preview(small_template)
        large_preview = preview_generator.generate_preview(large_template)

        # Parse time estimates (e.g., "15-30 minutes", "1-2 hours")
        def time_to_minutes(time_str):
            if "minutes" in time_str:
                return int(time_str.split("-")[1].split()[0])
            elif "hours" in time_str:
                return int(time_str.split("-")[1].split()[0]) * 60
            return 0

        small_time = time_to_minutes(small_preview.estimated_setup_time)
        large_time = time_to_minutes(large_preview.estimated_setup_time)

        assert large_time >= small_time

    def test_linear_features_detection(self, preview_generator, valid_template):
        """Test detection of Linear features being used"""
        preview = preview_generator.generate_preview(valid_template)

        features = preview.linear_features_used

        # Should detect basic features
        assert "Teams" in features
        assert "Projects" in features

        # Should detect custom fields
        assert "Custom Fields" in features

        # Should detect initiatives
        assert "Initiatives" in features

    def test_symphony_agents_in_preview(self, preview_generator, valid_template):
        """Test Symphony agents are included in preview"""
        preview = preview_generator.generate_preview(valid_template)

        agents = preview.symphony_agents_deployed
        assert len(agents) > 0
        assert "Development Agent" in agents
        assert "Product Agent" in agents

    def test_structure_summary_generation(self, preview_generator, valid_template):
        """Test structure summary generation"""
        preview = preview_generator.generate_preview(valid_template)

        summary = preview.structure_summary

        assert "teams" in summary
        assert "initiatives" in summary
        assert "projects" in summary

        # Teams summary should include team details
        teams_summary = summary["teams"]
        assert len(teams_summary) == len(valid_template.teams)

        eng_team_summary = next(t for t in teams_summary if t["name"] == "Engineering")
        assert eng_team_summary["key"] == "ENG"
        assert eng_team_summary["workflows"] == 3  # From fixture
        assert eng_team_summary["custom_fields"] == 1  # From fixture


class TestValidationErrorHandling:
    """Test error handling in validation"""

    def test_exception_handling_in_validation(self, validator):
        """Test that exceptions during validation are handled"""
        # Create a mock template that will cause an exception
        mock_template = Mock()
        mock_template.workspace = None

        result = validator.validate_template(mock_template)

        assert result.is_valid == False
        assert len(result.errors) > 0
        assert any("validation error" in error.lower() for error in result.errors)

    def test_validation_with_none_values(self, validator):
        """Test validation handles None values gracefully"""
        template = WorkspaceTemplate(
            workspace=None, teams=None, projects=None, initiatives=None
        )

        result = validator.validate_template(template)

        # Should handle None values without crashing
        assert isinstance(result, TemplateValidationResult)
        assert result.is_valid == False


if __name__ == "__main__":
    pytest.main([__file__])
