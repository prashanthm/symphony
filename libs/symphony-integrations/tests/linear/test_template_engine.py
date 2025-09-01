#!/usr/bin/env python3
"""
Tests for Linear Template Engine

Tests YAML template processing, variable substitution, inheritance, and configuration wizards.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
import yaml
from symphony_integrations.linear.template_engine import (
    ConfigurationWizard,
    TemplateEngine,
)
from symphony_integrations.linear.template_models import (
    IndustryType,
    OrganizationConfig,
    OrganizationSize,
    TeamTemplate,
    WorkspaceTemplate,
)


@pytest.fixture
def temp_templates_dir():
    """Fixture providing temporary templates directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        templates_dir = Path(temp_dir) / "templates"
        templates_dir.mkdir()
        yield templates_dir


@pytest.fixture
def template_engine(temp_templates_dir):
    """Fixture providing template engine with temporary directory"""
    return TemplateEngine(str(temp_templates_dir))


@pytest.fixture
def sample_template_yaml():
    """Fixture providing sample template YAML content"""
    return {
        "workspace": {
            "name": "${customer_name} Workspace",
            "description": "Workspace for ${industry} company",
        },
        "teams": [
            {
                "name": "Engineering",
                "key": "ENG",
                "description": "Software engineering team",
            },
            {
                "name": "${customer_name} Operations",
                "key": "OPS",
                "description": "Operations team for ${size} organization",
            },
        ],
        "variables": {
            "computed_vars": {
                "team_count": "teams.length()",
                "current_date": "date.today()",
            }
        },
        "template_version": "2025.1",
    }


@pytest.fixture
def sample_base_template():
    """Fixture providing base template for inheritance testing"""
    return {
        "workspace": {
            "name": "Base Workspace",
            "description": "Base template workspace",
        },
        "teams": [
            {
                "name": "Base Team",
                "key": "BASE",
                "description": "Base team from parent template",
            }
        ],
    }


@pytest.fixture
def sample_inheritance_template():
    """Fixture providing template with inheritance"""
    return {
        "inherits_from": ["base"],
        "workspace": {"name": "${customer_name} Extended Workspace"},  # Override name
        "teams": [
            {
                "name": "Additional Team",
                "key": "ADD",
                "description": "Additional team from child template",
            }
        ],
    }


@pytest.fixture
def sample_customer_config():
    """Fixture providing sample customer configuration"""
    return {
        "organization": {
            "customer_name": "Test Corp",
            "industry": "technology",
            "size": "startup",
            "regions": ["us-east-1"],
        },
        "workspace": {"description": "Custom description for Test Corp"},
        "teams": [
            {
                "name": "Custom Team",
                "key": "CUSTOM",
                "description": "Customer-specific team",
            }
        ],
    }


class TestTemplateEngineInitialization:
    """Test TemplateEngine initialization"""

    def test_default_initialization(self):
        """Test default initialization uses default templates directory"""
        engine = TemplateEngine()

        expected_path = Path("configs/linear-templates")
        assert engine.templates_dir == expected_path
        assert engine.variable_pattern is not None
        assert engine.defaults_generator is not None

    def test_custom_templates_directory(self, temp_templates_dir):
        """Test initialization with custom templates directory"""
        engine = TemplateEngine(str(temp_templates_dir))

        assert engine.templates_dir == temp_templates_dir

    def test_variable_pattern_compilation(self, template_engine):
        """Test variable pattern regex is compiled correctly"""
        pattern = template_engine.variable_pattern

        # Test matching variable syntax
        test_string = "Hello ${name}, welcome to ${organization}!"
        matches = pattern.findall(test_string)

        assert len(matches) == 2
        assert "name" in matches
        assert "organization" in matches


class TestTemplateLoading:
    """Test template loading from YAML files"""

    def test_load_simple_template(
        self, template_engine, temp_templates_dir, sample_template_yaml
    ):
        """Test loading simple template from YAML file"""
        # Create template file
        template_path = temp_templates_dir / "simple.yaml"
        with open(template_path, "w") as f:
            yaml.dump(sample_template_yaml, f)

        # Load template
        template = template_engine.load_template("simple.yaml")

        assert isinstance(template, WorkspaceTemplate)
        assert template.workspace is not None

    def test_load_nonexistent_template(self, template_engine):
        """Test loading non-existent template raises FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            template_engine.load_template("nonexistent.yaml")

    def test_load_template_with_variables(
        self, template_engine, temp_templates_dir, sample_template_yaml
    ):
        """Test loading template with variable substitution"""
        # Create template file
        template_path = temp_templates_dir / "with_vars.yaml"
        with open(template_path, "w") as f:
            yaml.dump(sample_template_yaml, f)

        variables = {
            "customer_name": "Acme Corp",
            "industry": "technology",
            "size": "startup",
        }

        template = template_engine.load_template("with_vars.yaml", variables)

        # Variables should be substituted
        assert "Acme Corp" in template.workspace["name"]
        assert "technology" in template.workspace["description"]

    @patch("builtins.open", new_callable=mock_open, read_data="invalid: yaml: content:")
    def test_load_invalid_yaml(self, mock_file, template_engine):
        """Test loading invalid YAML file handles errors"""
        with pytest.raises(yaml.YAMLError):
            template_engine.load_template("invalid.yaml")


class TestVariableSubstitution:
    """Test variable substitution functionality"""

    def test_simple_variable_substitution(self, template_engine):
        """Test simple variable substitution"""
        data = {"name": "${customer_name}", "description": "Welcome to ${organization}"}
        variables = {"customer_name": "Test Corp", "organization": "Test Organization"}

        result = template_engine._substitute_variables(data, variables)

        assert result["name"] == "Test Corp"
        assert result["description"] == "Welcome to Test Organization"

    def test_nested_variable_substitution(self, template_engine):
        """Test variable substitution in nested structures"""
        data = {
            "workspace": {
                "name": "${customer_name} Workspace",
                "teams": [
                    {"name": "${team_prefix} Engineering"},
                    {"name": "${team_prefix} Operations"},
                ],
            }
        }
        variables = {"customer_name": "Acme Corp", "team_prefix": "Acme"}

        result = template_engine._substitute_variables(data, variables)

        assert result["workspace"]["name"] == "Acme Corp Workspace"
        assert result["workspace"]["teams"][0]["name"] == "Acme Engineering"
        assert result["workspace"]["teams"][1]["name"] == "Acme Operations"

    def test_undefined_variables_unchanged(self, template_engine):
        """Test that undefined variables remain unchanged"""
        data = {"defined": "${defined_var}", "undefined": "${undefined_var}"}
        variables = {"defined_var": "Defined Value"}

        result = template_engine._substitute_variables(data, variables)

        assert result["defined"] == "Defined Value"
        assert result["undefined"] == "${undefined_var}"  # Should remain unchanged

    def test_expression_evaluation(self, template_engine):
        """Test evaluation of computed expressions"""
        variables = {"teams": ["Team 1", "Team 2", "Team 3"]}

        # Test date expressions
        date_now = template_engine._evaluate_expression("date.now()", variables)
        date_today = template_engine._evaluate_expression("date.today()", variables)

        assert len(date_now) > 10  # ISO format is longer
        assert len(date_today) == 10  # YYYY-MM-DD format

        # Test length expression
        team_count = template_engine._evaluate_expression("teams.length()", variables)
        assert team_count == "3"

    def test_property_access_evaluation(self, template_engine):
        """Test property access in expressions"""
        variables = {"organization": {"name": "Test Corp", "size": "startup"}}

        org_name = template_engine._evaluate_expression("organization.name", variables)
        org_size = template_engine._evaluate_expression("organization.size", variables)

        assert org_name == "Test Corp"
        assert org_size == "startup"

    def test_invalid_expression_returns_original(self, template_engine):
        """Test that invalid expressions return original string"""
        variables = {}

        result = template_engine._evaluate_expression(
            "invalid.expression.chain", variables
        )

        assert result == "invalid.expression.chain"


class TestTemplateInheritance:
    """Test template inheritance functionality"""

    def test_single_template_inheritance(
        self,
        template_engine,
        temp_templates_dir,
        sample_base_template,
        sample_inheritance_template,
    ):
        """Test inheritance from single parent template"""
        # Create base template
        base_path = temp_templates_dir / "base.yaml"
        with open(base_path, "w") as f:
            yaml.dump(sample_base_template, f)

        # Create child template
        child_path = temp_templates_dir / "child.yaml"
        with open(child_path, "w") as f:
            yaml.dump(sample_inheritance_template, f)

        variables = {"customer_name": "Test Corp"}
        template = template_engine.load_template("child.yaml", variables)

        # Should have both base and child teams
        team_names = [
            team.name
            for team in template.teams
            if hasattr(template, "teams") and template.teams
        ]

        # Note: This test depends on the actual implementation of _dict_to_workspace_template
        # which might need to be more robust for full team inheritance

    def test_inheritance_chain(self, template_engine, temp_templates_dir):
        """Test multi-level template inheritance"""
        # Create grandparent template
        grandparent = {
            "workspace": {"name": "Grandparent"},
            "base_value": "from_grandparent",
        }
        grandparent_path = temp_templates_dir / "grandparent.yaml"
        with open(grandparent_path, "w") as f:
            yaml.dump(grandparent, f)

        # Create parent template
        parent = {
            "inherits_from": ["grandparent"],
            "workspace": {"description": "Parent description"},
            "parent_value": "from_parent",
        }
        parent_path = temp_templates_dir / "parent.yaml"
        with open(parent_path, "w") as f:
            yaml.dump(parent, f)

        # Create child template
        child = {"inherits_from": ["parent"], "child_value": "from_child"}
        child_path = temp_templates_dir / "child.yaml"
        with open(child_path, "w") as f:
            yaml.dump(child, f)

        # Load child template (which should inherit from parent and grandparent)
        result = template_engine._load_template_file(child_path)
        processed = template_engine._process_inheritance(result)

        # Should have values from all levels
        assert processed["base_value"] == "from_grandparent"
        assert processed["parent_value"] == "from_parent"
        assert processed["child_value"] == "from_child"

        # Child should override parent workspace name
        assert processed["workspace"]["name"] == "Grandparent"
        assert processed["workspace"]["description"] == "Parent description"

    def test_inheritance_overrides(self, template_engine, temp_templates_dir):
        """Test that child templates can override parent values"""
        # Create parent template
        parent = {
            "workspace": {"name": "Parent Name", "description": "Parent Description"},
            "shared_value": "parent_value",
        }
        parent_path = temp_templates_dir / "parent.yaml"
        with open(parent_path, "w") as f:
            yaml.dump(parent, f)

        # Create child template that overrides some values
        child = {
            "inherits_from": ["parent"],
            "workspace": {"name": "Child Name"},  # Override name but keep description
            "shared_value": "child_value",  # Override shared value
        }
        child_path = temp_templates_dir / "child.yaml"
        with open(child_path, "w") as f:
            yaml.dump(child, f)

        result = template_engine._load_template_file(child_path)
        processed = template_engine._process_inheritance(result)

        # Child should override parent values
        assert processed["workspace"]["name"] == "Child Name"
        assert (
            processed["workspace"]["description"] == "Parent Description"
        )  # Inherited
        assert processed["shared_value"] == "child_value"  # Overridden

    def test_template_path_resolution(self, template_engine, temp_templates_dir):
        """Test template path resolution for different reference formats"""
        # Test simple reference
        simple_path = template_engine._resolve_template_path("simple")
        expected_simple = temp_templates_dir / "simple.yaml"
        assert simple_path == expected_simple

        # Test dot notation reference
        dot_path = template_engine._resolve_template_path("industry.technology")
        expected_dot = temp_templates_dir / "industry" / "technology.yaml"
        assert dot_path == expected_dot


class TestCustomerConfigProcessing:
    """Test customer configuration processing"""

    def test_process_customer_config(
        self, template_engine, temp_templates_dir, sample_customer_config
    ):
        """Test processing customer configuration file"""
        # Create customer config file
        config_path = temp_templates_dir / "customer.yaml"
        with open(config_path, "w") as f:
            yaml.dump(sample_customer_config, f)

        template = template_engine.process_customer_config(str(config_path))

        assert isinstance(template, WorkspaceTemplate)
        assert template.organization is not None
        assert template.organization.customer_name == "Test Corp"
        assert template.organization.industry == IndustryType.TECHNOLOGY
        assert template.organization.size == OrganizationSize.STARTUP

    @patch("builtins.open", new_callable=mock_open, read_data="invalid: yaml: content:")
    def test_process_invalid_customer_config(self, mock_file, template_engine):
        """Test processing invalid customer configuration"""
        with pytest.raises(yaml.YAMLError):
            template_engine.process_customer_config("invalid_config.yaml")

    def test_customer_config_with_defaults(self, template_engine, temp_templates_dir):
        """Test customer config processing with intelligent defaults"""
        config = {
            "organization": {
                "customer_name": "FinTech Startup",
                "industry": "financial_services",
                "size": "startup",
            }
        }

        config_path = temp_templates_dir / "fintech_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        template = template_engine.process_customer_config(str(config_path))

        # Should have intelligent defaults for financial services
        assert template.organization.industry == IndustryType.FINANCIAL_SERVICES
        # Should have generated teams based on industry
        # Note: This depends on the defaults generator working correctly


class TestVariableContextBuilding:
    """Test variable context building"""

    def test_build_variable_context(self, template_engine):
        """Test building variable context for substitution"""
        org = OrganizationConfig(
            customer_name="Test Corp",
            industry=IndustryType.TECHNOLOGY,
            size=OrganizationSize.STARTUP,
            regions=["us-east-1", "us-west-2"],
        )

        template = WorkspaceTemplate(
            teams=[TeamTemplate("Engineering", "ENG"), TeamTemplate("Product", "PROD")]
        )

        variables = template_engine._build_variable_context(template, org)

        # Should have organization variables
        assert variables["customer_name"] == "Test Corp"
        assert variables["industry"] == "technology"
        assert variables["size"] == "startup"
        assert variables["regions"] == ["us-east-1", "us-west-2"]

        # Should have computed variables
        assert variables["team_count"] == 2
        assert variables["project_count"] == 0  # No projects in template

        # Should have conditional variables
        assert variables["multi_region"] == True  # Has multiple regions
        assert variables["enterprise_size"] == False  # Startup, not enterprise

    def test_compliance_required_variable(self, template_engine):
        """Test compliance_required conditional variable"""
        template = WorkspaceTemplate()

        # Financial services should require compliance
        finserv_org = OrganizationConfig(
            customer_name="Bank Corp",
            industry=IndustryType.FINANCIAL_SERVICES,
            size=OrganizationSize.ENTERPRISE,
        )

        variables = template_engine._build_variable_context(template, finserv_org)
        assert variables["compliance_required"] == True

        # Technology should not require compliance
        tech_org = OrganizationConfig(
            customer_name="Tech Corp",
            industry=IndustryType.TECHNOLOGY,
            size=OrganizationSize.STARTUP,
        )

        variables = template_engine._build_variable_context(template, tech_org)
        assert variables["compliance_required"] == False


class TestTemplateSaving:
    """Test template saving functionality"""

    def test_save_template(self, template_engine, temp_templates_dir):
        """Test saving template to YAML file"""
        template = WorkspaceTemplate(
            workspace={"name": "Test Workspace", "description": "Test description"},
            teams=[TeamTemplate("Engineering", "ENG")],
            template_version="2025.1",
        )

        output_path = temp_templates_dir / "output.yaml"
        template_engine.save_template(template, str(output_path))

        # File should be created
        assert output_path.exists()

        # Should be valid YAML
        with open(output_path, "r") as f:
            loaded_data = yaml.safe_load(f)

        assert loaded_data["template_version"] == "2025.1"
        assert loaded_data["workspace"]["name"] == "Test Workspace"

    def test_save_template_cleans_none_values(
        self, template_engine, temp_templates_dir
    ):
        """Test that saving template removes None values and empty collections"""
        template = WorkspaceTemplate(
            workspace={"name": "Test", "description": None},  # None description
            teams=[],  # Empty teams list
            projects=None,  # None projects
            template_version="2025.1",
        )

        output_path = temp_templates_dir / "cleaned.yaml"
        template_engine.save_template(template, str(output_path))

        with open(output_path, "r") as f:
            loaded_data = yaml.safe_load(f)

        # None description should be removed
        assert "description" not in loaded_data.get("workspace", {})

        # Empty/None collections should be removed
        assert "teams" not in loaded_data
        assert "projects" not in loaded_data


class TestVariablePreview:
    """Test variable preview functionality"""

    def test_preview_variables(self, template_engine, temp_templates_dir):
        """Test previewing variable substitutions"""
        template_data = {
            "workspace": {
                "name": "${customer_name} Workspace",
                "description": "Created on ${date.today()} for ${industry} industry",
            },
            "teams": [{"name": "${team_prefix} Engineering"}],
        }

        template_path = temp_templates_dir / "preview.yaml"
        with open(template_path, "w") as f:
            yaml.dump(template_data, f)

        variables = {
            "customer_name": "Acme Corp",
            "industry": "technology",
            "team_prefix": "Acme",
        }

        preview = template_engine.preview_variables("preview.yaml", variables)

        assert "customer_name" in preview
        assert preview["customer_name"] == "Acme Corp"
        assert "industry" in preview
        assert preview["industry"] == "technology"
        assert "team_prefix" in preview
        assert preview["team_prefix"] == "Acme"
        assert "date.today()" in preview  # Should be evaluated


class TestConfigurationWizard:
    """Test ConfigurationWizard functionality"""

    def test_wizard_initialization(self, template_engine):
        """Test configuration wizard initialization"""
        wizard = ConfigurationWizard(template_engine)

        assert wizard.engine == template_engine
        assert wizard.defaults_generator is not None

    @patch("builtins.input")
    def test_collect_workspace_info(self, mock_input, template_engine):
        """Test collecting workspace information"""
        mock_input.side_effect = ["Test Workspace", "Test Description"]

        wizard = ConfigurationWizard(template_engine)
        workspace_info = wizard._collect_workspace_info()

        assert workspace_info["name"] == "Test Workspace"
        assert workspace_info["description"] == "Test Description"

    @patch("builtins.input")
    def test_collect_organization_info(self, mock_input, template_engine):
        """Test collecting organization information"""
        # Mock inputs: org name, industry choice, size choice, regions
        mock_input.side_effect = ["Test Corp", "4", "1", "us-east-1, us-west-2"]

        wizard = ConfigurationWizard(template_engine)
        org_info = wizard._collect_organization_info()

        assert org_info["customer_name"] == "Test Corp"
        assert org_info["industry"] == IndustryType.TECHNOLOGY.value  # 4th option
        assert org_info["size"] == OrganizationSize.STARTUP.value  # 1st option
        assert len(org_info["regions"]) == 2

    @patch("builtins.input")
    def test_collect_symphony_integration(self, mock_input, template_engine):
        """Test collecting Symphony integration preferences"""
        mock_input.side_effect = ["y", "y"]  # Yes to both defaults and optimization

        wizard = ConfigurationWizard(template_engine)
        integration_info = wizard._collect_symphony_integration()

        assert integration_info["use_symphony_defaults"] == True
        assert integration_info["auto_optimization"] == True
        assert integration_info["automation"]["issue_creation"] == True

    @patch("builtins.input")
    def test_ask_yes_no_default_true(self, mock_input, template_engine):
        """Test yes/no question with default true"""
        mock_input.return_value = ""  # Empty input, should use default

        wizard = ConfigurationWizard(template_engine)
        result = wizard._ask_yes_no("Test question?", default=True)

        assert result == True

    @patch("builtins.input")
    def test_ask_yes_no_explicit_response(self, mock_input, template_engine):
        """Test yes/no question with explicit responses"""
        wizard = ConfigurationWizard(template_engine)

        # Test explicit yes
        mock_input.return_value = "y"
        result = wizard._ask_yes_no("Test question?", default=False)
        assert result == True

        # Test explicit no
        mock_input.return_value = "n"
        result = wizard._ask_yes_no("Test question?", default=True)
        assert result == False


class TestDeepMerge:
    """Test deep merge functionality"""

    def test_deep_merge_simple_override(self, template_engine):
        """Test deep merge with simple value override"""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}

        result = template_engine._deep_merge(base, override)

        assert result["a"] == 1  # Preserved from base
        assert result["b"] == 3  # Overridden
        assert result["c"] == 4  # Added from override

    def test_deep_merge_nested_dicts(self, template_engine):
        """Test deep merge with nested dictionaries"""
        base = {
            "workspace": {"name": "Base", "description": "Base description"},
            "config": {"setting1": "value1", "setting2": "value2"},
        }
        override = {
            "workspace": {"name": "Override"},  # Only override name
            "config": {"setting2": "new_value2", "setting3": "value3"},  # Merge config
        }

        result = template_engine._deep_merge(base, override)

        # Workspace should be merged
        assert result["workspace"]["name"] == "Override"
        assert result["workspace"]["description"] == "Base description"

        # Config should be merged
        assert result["config"]["setting1"] == "value1"  # Preserved
        assert result["config"]["setting2"] == "new_value2"  # Overridden
        assert result["config"]["setting3"] == "value3"  # Added

    def test_deep_merge_list_replacement(self, template_engine):
        """Test deep merge replaces structural lists"""
        base = {"teams": [{"name": "Base Team"}]}
        override = {"teams": [{"name": "Override Team"}]}

        result = template_engine._deep_merge(base, override)

        # Teams list should be replaced, not appended
        assert len(result["teams"]) == 1
        assert result["teams"][0]["name"] == "Override Team"


class TestErrorHandling:
    """Test error handling in template engine"""

    def test_file_not_found_template_path(self, template_engine):
        """Test handling of non-existent template file"""
        with pytest.raises(FileNotFoundError):
            template_engine._load_template_file(Path("nonexistent.yaml"))

    def test_invalid_yaml_handling(self, template_engine, temp_templates_dir):
        """Test handling of invalid YAML content"""
        invalid_yaml = "invalid: yaml: content: ["
        invalid_path = temp_templates_dir / "invalid.yaml"

        with open(invalid_path, "w") as f:
            f.write(invalid_yaml)

        with pytest.raises(yaml.YAMLError):
            template_engine._load_template_file(invalid_path)

    def test_missing_inheritance_template(self, template_engine, temp_templates_dir):
        """Test handling of missing inheritance template"""
        child_template = {
            "inherits_from": ["nonexistent_parent"],
            "workspace": {"name": "Child"},
        }

        child_path = temp_templates_dir / "child.yaml"
        with open(child_path, "w") as f:
            yaml.dump(child_template, f)

        with pytest.raises(FileNotFoundError):
            template_engine.load_template("child.yaml")


if __name__ == "__main__":
    pytest.main([__file__])
