#!/usr/bin/env python3
"""
Tests for Symphony Dogfooding Configuration

Tests Symphony's own workspace configuration - the ultimate test of eating our own dogfood.
"""

import pytest
from pathlib import Path
from symphony_integrations.linear.defaults_generator import SymphonyLinearDefaults
from symphony_integrations.linear.template_engine import TemplateEngine
from symphony_integrations.linear.template_validator import TemplateValidator, WorkspacePreviewGenerator
from symphony_integrations.linear.template_models import (
    IndustryType, OrganizationSize
)


@pytest.fixture
def defaults_generator():
    """Fixture providing defaults generator"""
    return SymphonyLinearDefaults()


@pytest.fixture
def template_engine():
    """Fixture providing template engine"""
    return TemplateEngine()


@pytest.fixture
def validator():
    """Fixture providing template validator"""
    return TemplateValidator()


@pytest.fixture
def preview_generator():
    """Fixture providing preview generator"""
    return WorkspacePreviewGenerator()


@pytest.fixture
def dogfood_config_path():
    """Fixture providing path to dogfood configuration"""
    return Path(__file__).parent / "fixtures" / "symphony_dogfood.yaml"


class TestDogfoodingGeneration:
    """Test dogfooding template generation"""
    
    def test_generate_dogfooding_template(self, defaults_generator):
        """Test generating Symphony's own template"""
        template = defaults_generator.generate_dogfooding_template()
        
        # Verify basic structure
        assert template.organization.customer_name == "Symphony"
        assert template.organization.industry == IndustryType.TECHNOLOGY
        assert template.organization.size == OrganizationSize.STARTUP
        assert template.organization.regions == ["global"]
    
    def test_dogfooding_workspace_info(self, defaults_generator):
        """Test dogfooding workspace information is Symphony-specific"""
        template = defaults_generator.generate_dogfooding_template()
        
        assert template.workspace["name"] == "Symphony Internal Operations"
        assert "Symphony uses Symphony" in template.workspace["description"]
        assert "Symphony" in template.workspace["description"]
    
    def test_dogfooding_teams_structure(self, defaults_generator):
        """Test dogfooding has Symphony-specific teams"""
        template = defaults_generator.generate_dogfooding_template()
        
        team_names = [team.name for team in template.teams]
        
        # Should have Symphony-specific teams
        assert "Platform Development" in team_names
        assert "Customer Success" in team_names
        
        # Verify Platform Development sub-teams
        platform_team = next(team for team in template.teams if team.name == "Platform Development")
        sub_team_names = [sub.name for sub in platform_team.sub_teams]
        assert "Linear Integration" in sub_team_names
        assert "Agent Ecosystem" in sub_team_names
        assert "Configuration Systems" in sub_team_names
    
    def test_dogfooding_customer_success_workflows(self, defaults_generator):
        """Test Customer Success team has Symphony-specific workflows"""
        template = defaults_generator.generate_dogfooding_template()
        
        cs_team = next(team for team in template.teams if team.name == "Customer Success")
        workflow_names = [w.name for w in cs_team.workflows]
        
        # Should have Symphony customer journey workflows
        assert "Discovery" in workflow_names
        assert "Implementation" in workflow_names
        assert "Optimization" in workflow_names
        assert "Excellence" in workflow_names
        
        # Excellence should be the completed state
        excellence_workflow = next(w for w in cs_team.workflows if w.name == "Excellence")
        assert excellence_workflow.type == "completed"
        assert "autonomous excellence" in excellence_workflow.description.lower()
    
    def test_dogfooding_initiatives_focus(self, defaults_generator):
        """Test dogfooding initiatives focus on Symphony excellence"""
        template = defaults_generator.generate_dogfooding_template()
        
        initiative_names = [init.name for init in template.initiatives]
        assert "Symphony Platform Excellence" in initiative_names
        
        # Verify sub-initiatives are Symphony-focused
        platform_init = next(init for init in template.initiatives 
                            if init.name == "Symphony Platform Excellence")
        sub_init_names = [sub.name for sub in platform_init.sub_initiatives]
        
        expected_sub_initiatives = [
            "Linear Integration Mastery",
            "Agent Ecosystem Excellence", 
            "Customer Success Optimization"
        ]
        
        for expected in expected_sub_initiatives:
            assert expected in sub_init_names
    
    def test_dogfooding_symphony_integration(self, defaults_generator):
        """Test dogfooding has maximum Symphony integration"""
        template = defaults_generator.generate_dogfooding_template()
        
        symphony = template.symphony_integration
        
        # Should have full dogfooding features enabled
        assert symphony.self_managing == True
        assert symphony.recursive_improvement == True
        assert symphony.auto_optimization == True
        
        # Should have comprehensive agent assignments
        assert len(symphony.agent_assignments) > 0
        
        # All teams should have agents assigned
        team_names = {team.name for team in template.teams}
        assigned_teams = set(symphony.agent_assignments.keys())
        
        # Should have significant overlap (at least main teams assigned)
        main_teams = {"Platform Development", "Customer Success"}
        assert main_teams.issubset(assigned_teams)
    
    def test_dogfooding_meta_consistency(self, defaults_generator):
        """Test dogfooding demonstrates meta-implementation consistency"""
        template = defaults_generator.generate_dogfooding_template()
        
        # Should only have self-managing features for Symphony
        assert template.organization.customer_name.lower() == "symphony"
        assert template.symphony_integration.self_managing == True
        
        # Description should reference the meta-nature
        description = template.workspace["description"]
        meta_keywords = ["symphony", "manage", "development"]
        
        description_lower = description.lower()
        for keyword in meta_keywords:
            assert keyword in description_lower


class TestDogfoodingValidation:
    """Test dogfooding template validation"""
    
    def test_dogfooding_template_is_valid(self, defaults_generator, validator):
        """Test that dogfooding template passes validation"""
        template = defaults_generator.generate_dogfooding_template()
        result = validator.validate_template(template)
        
        # Should be valid (no critical errors)
        assert result.is_valid == True
        
        # May have suggestions but should not have blocking errors
        assert len([error for error in result.errors if "missing" in error.lower()]) == 0
    
    def test_dogfooding_complexity_appropriate(self, defaults_generator, preview_generator):
        """Test that dogfooding template has appropriate complexity"""
        template = defaults_generator.generate_dogfooding_template()
        preview = preview_generator.generate_preview(template)
        
        # Should be reasonably complex but not overwhelming
        assert preview.complexity_score >= 4  # Non-trivial
        assert preview.complexity_score <= 8  # But not overwhelming
        
        # Should have multiple teams and meaningful structure
        assert preview.team_count >= 2
        assert preview.initiative_count >= 1
    
    def test_dogfooding_symphony_agents_deployed(self, defaults_generator, preview_generator):
        """Test that dogfooding has Symphony agents deployed"""
        template = defaults_generator.generate_dogfooding_template()
        preview = preview_generator.generate_preview(template)
        
        # Should have Symphony agents deployed
        assert len(preview.symphony_agents_deployed) > 0
        
        # Should have sophisticated agent names
        agent_names = " ".join(preview.symphony_agents_deployed).lower()
        symphony_keywords = ["symphony", "agent", "coordination", "template"]
        
        # Should have at least some Symphony-specific agents
        assert any(keyword in agent_names for keyword in symphony_keywords)
    
    def test_dogfooding_features_used(self, defaults_generator, preview_generator):
        """Test that dogfooding uses advanced Linear features"""
        template = defaults_generator.generate_dogfooding_template()
        preview = preview_generator.generate_preview(template)
        
        features = preview.linear_features_used
        
        # Should use advanced features
        advanced_features = ["Sub-teams", "Initiatives", "Custom Fields", "Symphony Integration"]
        
        for feature in advanced_features:
            assert feature in features


class TestDogfoodingConfigFile:
    """Test the dogfooding configuration file"""
    
    def test_dogfood_config_exists(self, dogfood_config_path):
        """Test that dogfood configuration file exists"""
        assert dogfood_config_path.exists()
        assert dogfood_config_path.is_file()
        assert dogfood_config_path.suffix == ".yaml"
    
    def test_load_dogfood_config(self, template_engine, dogfood_config_path):
        """Test loading dogfood configuration file"""
        if dogfood_config_path.exists():
            template = template_engine.process_customer_config(str(dogfood_config_path))
            
            # Should load successfully
            assert template is not None
            assert template.organization.customer_name == "Symphony"
    
    def test_dogfood_config_validation(self, template_engine, validator, dogfood_config_path):
        """Test that dogfood configuration file is valid"""
        if dogfood_config_path.exists():
            template = template_engine.process_customer_config(str(dogfood_config_path))
            result = validator.validate_template(template)
            
            # Should be valid or have only minor warnings
            if not result.is_valid:
                # Print errors for debugging
                print("Dogfood config validation errors:")
                for error in result.errors:
                    print(f"  - {error}")
            
            # At minimum, should not have critical structural errors
            critical_errors = [
                error for error in result.errors 
                if any(keyword in error.lower() for keyword in ["missing", "required", "invalid"])
            ]
            assert len(critical_errors) == 0, f"Critical errors in dogfood config: {critical_errors}"
    
    def test_dogfood_config_meta_features(self, template_engine, dogfood_config_path):
        """Test dogfood configuration has meta-implementation features"""
        if dogfood_config_path.exists():
            template = template_engine.process_customer_config(str(dogfood_config_path))
            
            # Should have self-managing features
            if template.symphony_integration:
                assert template.symphony_integration.self_managing == True
                assert template.symphony_integration.recursive_improvement == True
                assert template.symphony_integration.auto_optimization == True


class TestDogfoodingIntegration:
    """Test integration aspects of dogfooding"""
    
    def test_dogfooding_vs_regular_customer(self, defaults_generator):
        """Test that dogfooding is different from regular customers"""
        # Generate regular customer template
        regular_org = defaults_generator.defaults_generator.generate_defaults(
            defaults_generator.defaults_generator.OrganizationConfig(
                customer_name="Regular Corp",
                industry=IndustryType.TECHNOLOGY,
                size=OrganizationSize.STARTUP
            )
        )
        
        # Generate dogfooding template
        dogfood_template = defaults_generator.generate_dogfooding_template()
        
        # Dogfooding should have unique features
        assert dogfood_template.symphony_integration.self_managing == True
        assert regular_org.symphony_integration.self_managing == False
        
        # Dogfooding should have Symphony-specific teams
        dogfood_teams = {team.name for team in dogfood_template.teams}
        regular_teams = {team.name for team in regular_org.teams}
        
        symphony_specific_teams = {"Platform Development", "Customer Success"}
        assert symphony_specific_teams.issubset(dogfood_teams)
        # Regular org might not have these exact teams
    
    def test_dogfooding_template_saves_and_loads(self, defaults_generator, template_engine):
        """Test that dogfooding template can be saved and loaded"""
        import tempfile
        
        # Generate dogfooding template
        template = defaults_generator.generate_dogfooding_template()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            template_engine.save_template(template, f.name)
            
            # Load it back
            loaded_template = template_engine.process_customer_config(f.name)
            
            # Should maintain key characteristics
            assert loaded_template.organization.customer_name == "Symphony"
            assert loaded_template.organization.industry == IndustryType.TECHNOLOGY
    
    def test_dogfooding_variable_substitution(self, defaults_generator, template_engine):
        """Test that dogfooding works with variable substitution"""
        template = defaults_generator.generate_dogfooding_template()
        
        # Build variable context
        variables = template_engine._build_variable_context(template, template.organization)
        
        # Should have Symphony-specific variables
        assert variables["customer_name"] == "Symphony"
        assert variables["industry"] == "technology"
        
        # Should work with conditional variables for Symphony
        assert "compliance_required" in variables
        assert "enterprise_size" in variables


class TestDogfoodingEdgeCases:
    """Test edge cases and boundary conditions for dogfooding"""
    
    def test_multiple_dogfood_generation_consistent(self, defaults_generator):
        """Test that multiple dogfood generations are consistent"""
        template1 = defaults_generator.generate_dogfooding_template()
        template2 = defaults_generator.generate_dogfooding_template()
        
        # Should be consistent across generations
        assert template1.organization.customer_name == template2.organization.customer_name
        assert template1.workspace["name"] == template2.workspace["name"]
        assert len(template1.teams) == len(template2.teams)
    
    def test_dogfood_with_customization(self, defaults_generator):
        """Test that dogfooding template can be customized"""
        template = defaults_generator.generate_dogfooding_template()
        
        # Should be a proper WorkspaceTemplate that can be modified
        assert hasattr(template, 'teams')
        assert hasattr(template, 'initiatives')
        assert hasattr(template, 'projects')
        
        # Should allow modifications (not frozen)
        original_team_count = len(template.teams)
        # This should not raise an exception
        template.teams = template.teams[:1]  # Reduce teams for test
        assert len(template.teams) != original_team_count
    
    def test_dogfood_organization_consistency(self, defaults_generator):
        """Test organization configuration consistency"""
        template = defaults_generator.generate_dogfooding_template()
        
        # Organization should be consistent with Symphony's nature
        org = template.organization
        assert org.customer_name == "Symphony"
        assert org.industry == IndustryType.TECHNOLOGY
        assert org.size == OrganizationSize.STARTUP
        assert "global" in org.regions


class TestDogfoodingDocumentation:
    """Test dogfooding documentation and examples"""
    
    def test_dogfood_config_has_documentation(self, dogfood_config_path):
        """Test that dogfood config file has adequate documentation"""
        if dogfood_config_path.exists():
            with open(dogfood_config_path, 'r') as f:
                content = f.read()
            
            # Should have comments explaining the meta-nature
            assert "#" in content  # Has comments
            assert "Symphony" in content  # References Symphony
            assert "dogfood" in content.lower() or "meta" in content.lower()  # Explains concept
    
    def test_dogfood_demonstrates_features(self, defaults_generator, preview_generator):
        """Test that dogfooding demonstrates Symphony's key features"""
        template = defaults_generator.generate_dogfooding_template()
        preview = preview_generator.generate_preview(template)
        
        # Should demonstrate sophisticated use of Linear features
        assert "Symphony Integration" in preview.linear_features_used
        
        # Should have meaningful complexity
        assert preview.complexity_score > 1
        
        # Should show substantial Symphony agent deployment
        assert len(preview.symphony_agents_deployed) >= 3


if __name__ == "__main__":
    pytest.main([__file__])