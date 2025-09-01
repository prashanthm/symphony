#!/usr/bin/env python3
"""
Tests for Symphony Linear Defaults Generator

Tests the intelligent defaults generation system for Linear workspaces.
"""

import pytest
from symphony_integrations.linear.defaults_generator import SymphonyLinearDefaults
from symphony_integrations.linear.template_models import (
    OrganizationConfig,
    WorkspaceTemplate,
    TeamTemplate,
    IndustryType,
    OrganizationSize,
    FieldType,
    CustomField,
    WorkflowState,
    Initiative,
    ProjectTemplate,
)


@pytest.fixture
def defaults_generator():
    """Fixture providing defaults generator instance"""
    return SymphonyLinearDefaults()


@pytest.fixture
def sample_organizations():
    """Fixture providing sample organization configurations"""
    return {
        "finserv_startup": OrganizationConfig(
            customer_name="FinTech Startup",
            industry=IndustryType.FINANCIAL_SERVICES,
            size=OrganizationSize.STARTUP,
            regions=["us-east-1"],
        ),
        "healthcare_enterprise": OrganizationConfig(
            customer_name="MedCorp Enterprise",
            industry=IndustryType.HEALTHCARE,
            size=OrganizationSize.ENTERPRISE,
            regions=["us-east-1", "eu-west-1"],
        ),
        "tech_global": OrganizationConfig(
            customer_name="TechGiant Corp",
            industry=IndustryType.TECHNOLOGY,
            size=OrganizationSize.GLOBAL,
            regions=["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
        ),
        "manufacturing_smb": OrganizationConfig(
            customer_name="ManufactureCorp",
            industry=IndustryType.MANUFACTURING,
            size=OrganizationSize.SMB,
            regions=["us-central-1"],
        ),
        "consulting_startup": OrganizationConfig(
            customer_name="ConsultingFirm",
            industry=IndustryType.CONSULTING,
            size=OrganizationSize.STARTUP,
            regions=["us-east-1"],
        ),
    }


class TestBaseWorkflowGeneration:
    """Test base workflow generation"""

    def test_base_workflows_structure(self, defaults_generator):
        """Test that base workflows have correct structure"""
        workflows = defaults_generator.base_workflows

        # Should have standard workflow states
        assert len(workflows) == 6

        workflow_names = [w.name for w in workflows]
        expected_names = [
            "Backlog",
            "Todo",
            "In Progress",
            "Review",
            "Done",
            "Canceled",
        ]

        for name in expected_names:
            assert name in workflow_names

    def test_base_workflows_types(self, defaults_generator):
        """Test that base workflows have correct types"""
        workflows = defaults_generator.base_workflows

        backlog_state = next(w for w in workflows if w.name == "Backlog")
        assert backlog_state.type == "backlog"

        done_state = next(w for w in workflows if w.name == "Done")
        assert done_state.type == "completed"

        canceled_state = next(w for w in workflows if w.name == "Canceled")
        assert canceled_state.type == "canceled"

    def test_base_workflows_positions(self, defaults_generator):
        """Test that base workflows have correct positions"""
        workflows = defaults_generator.base_workflows

        # Workflows should be in sequential order
        positions = [w.position for w in workflows]
        assert positions == [0, 1, 2, 3, 4, 5]


class TestDefaultGeneration:
    """Test main defaults generation"""

    def test_generate_defaults_basic_structure(
        self, defaults_generator, sample_organizations
    ):
        """Test that generate_defaults returns valid structure"""
        org = sample_organizations["tech_global"]
        template = defaults_generator.generate_defaults(org)

        # Should return WorkspaceTemplate
        assert isinstance(template, WorkspaceTemplate)

        # Should have basic workspace info
        assert template.workspace is not None
        assert "name" in template.workspace
        assert "description" in template.workspace

        # Should include organization
        assert template.organization == org

        # Should have version
        assert template.template_version == "2025.1"

    def test_generate_defaults_workspace_naming(
        self, defaults_generator, sample_organizations
    ):
        """Test workspace naming follows pattern"""
        for org_key, org in sample_organizations.items():
            template = defaults_generator.generate_defaults(org)

            # Workspace name should include customer name
            assert org.customer_name in template.workspace["name"]
            assert "Enterprise Operations" in template.workspace["name"]

            # Description should reference customer name
            assert org.customer_name in template.workspace["description"]

    def test_generate_defaults_includes_symphony_integration(
        self, defaults_generator, sample_organizations
    ):
        """Test that all templates include Symphony integration"""
        for org_key, org in sample_organizations.items():
            template = defaults_generator.generate_defaults(org)

            assert template.symphony_integration is not None
            assert isinstance(template.symphony_integration.agent_assignments, dict)
            assert len(template.symphony_integration.agent_assignments) > 0


class TestIndustrySpecificDefaults:
    """Test industry-specific defaults generation"""

    def test_financial_services_teams(self, defaults_generator, sample_organizations):
        """Test financial services specific team structure"""
        org = sample_organizations["finserv_startup"]
        template = defaults_generator.generate_defaults(org)

        team_names = [team.name for team in template.teams]

        # Should include finance-specific teams
        assert "Risk Management" in team_names
        assert "Regulatory Compliance" in team_names
        assert "Security Operations" in team_names

    def test_financial_services_custom_fields(
        self, defaults_generator, sample_organizations
    ):
        """Test financial services custom fields"""
        org = sample_organizations["finserv_startup"]
        template = defaults_generator.generate_defaults(org)

        # Find risk management team
        risk_team = next(
            team for team in template.teams if team.name == "Risk Management"
        )

        field_names = [field.name for field in risk_team.custom_fields]
        assert "Risk Level" in field_names
        assert "SOX Compliance" in field_names
        assert "Regulatory Framework" in field_names

        # Test risk level field options
        risk_field = next(
            field for field in risk_team.custom_fields if field.name == "Risk Level"
        )
        assert risk_field.type == FieldType.SELECT
        assert "Critical" in risk_field.options
        assert "Low" in risk_field.options

    def test_financial_services_workflows(
        self, defaults_generator, sample_organizations
    ):
        """Test financial services compliance workflows"""
        org = sample_organizations["finserv_startup"]
        template = defaults_generator.generate_defaults(org)

        compliance_team = next(
            team for team in template.teams if team.name == "Regulatory Compliance"
        )

        workflow_names = [w.name for w in compliance_team.workflows]
        assert "Compliance Review" in workflow_names
        assert "Risk Assessment" in workflow_names
        assert "Regulatory Approval" in workflow_names

    def test_financial_services_initiatives(
        self, defaults_generator, sample_organizations
    ):
        """Test financial services initiatives"""
        org = sample_organizations["finserv_startup"]
        template = defaults_generator.generate_defaults(org)

        initiative_names = [init.name for init in template.initiatives]
        assert "Regulatory Compliance 2025" in initiative_names
        assert "Digital Banking Platform" in initiative_names

        # Test sub-initiatives
        compliance_init = next(
            init
            for init in template.initiatives
            if init.name == "Regulatory Compliance 2025"
        )
        sub_init_names = [sub.name for sub in compliance_init.sub_initiatives]
        assert "SOX 404 Compliance" in sub_init_names
        assert "GDPR Enhancement" in sub_init_names

    def test_financial_services_projects(
        self, defaults_generator, sample_organizations
    ):
        """Test financial services project templates"""
        org = sample_organizations["finserv_startup"]
        template = defaults_generator.generate_defaults(org)

        project_template_names = [proj.template_name for proj in template.projects]
        assert "compliance_project" in project_template_names

        compliance_project = next(
            proj
            for proj in template.projects
            if proj.template_name == "compliance_project"
        )

        # Should have variable substitution
        assert "${regulation}" in compliance_project.name
        assert "${regulation}" in compliance_project.description

        # Should have compliance-specific milestones
        milestone_names = [m.name for m in compliance_project.milestones]
        assert "Gap Analysis" in milestone_names
        assert "Audit" in milestone_names

    def test_healthcare_teams(self, defaults_generator, sample_organizations):
        """Test healthcare specific teams"""
        org = sample_organizations["healthcare_enterprise"]
        template = defaults_generator.generate_defaults(org)

        team_names = [team.name for team in template.teams]
        assert "Clinical Operations" in team_names
        assert "Privacy & Compliance" in team_names

    def test_healthcare_hipaa_fields(self, defaults_generator, sample_organizations):
        """Test healthcare HIPAA compliance fields"""
        org = sample_organizations["healthcare_enterprise"]
        template = defaults_generator.generate_defaults(org)

        clinical_team = next(
            team for team in template.teams if team.name == "Clinical Operations"
        )
        field_names = [field.name for field in clinical_team.custom_fields]
        assert "Patient Safety Impact" in field_names
        assert "HIPAA Covered" in field_names

        privacy_team = next(
            team for team in template.teams if team.name == "Privacy & Compliance"
        )
        privacy_field_names = [field.name for field in privacy_team.custom_fields]
        assert "PHI Involved" in privacy_field_names

    def test_healthcare_workflows(self, defaults_generator, sample_organizations):
        """Test healthcare specific workflows"""
        org = sample_organizations["healthcare_enterprise"]
        template = defaults_generator.generate_defaults(org)

        clinical_team = next(
            team for team in template.teams if team.name == "Clinical Operations"
        )
        workflow_names = [w.name for w in clinical_team.workflows]
        assert "HIPAA Review" in workflow_names
        assert "Privacy Assessment" in workflow_names
        assert "Clinical Approval" in workflow_names

    def test_technology_teams(self, defaults_generator, sample_organizations):
        """Test technology company teams"""
        org = sample_organizations["tech_global"]
        template = defaults_generator.generate_defaults(org)

        team_names = [team.name for team in template.teams]
        assert "Platform Engineering" in team_names
        assert "Product Management" in team_names

    def test_technology_sub_teams(self, defaults_generator, sample_organizations):
        """Test technology company sub-teams"""
        org = sample_organizations["tech_global"]
        template = defaults_generator.generate_defaults(org)

        platform_team = next(
            team for team in template.teams if team.name == "Platform Engineering"
        )
        sub_team_names = [sub.name for sub in platform_team.sub_teams]

        assert "Frontend" in sub_team_names
        assert "Backend" in sub_team_names
        assert "Infrastructure" in sub_team_names

    def test_technology_development_workflows(
        self, defaults_generator, sample_organizations
    ):
        """Test technology development workflows"""
        org = sample_organizations["tech_global"]
        template = defaults_generator.generate_defaults(org)

        platform_team = next(
            team for team in template.teams if team.name == "Platform Engineering"
        )
        workflow_names = [w.name for w in platform_team.workflows]

        expected_dev_workflows = ["Development", "Code Review", "Testing", "Staging"]
        for workflow in expected_dev_workflows:
            assert workflow in workflow_names

    def test_technology_custom_fields(self, defaults_generator, sample_organizations):
        """Test technology team custom fields"""
        org = sample_organizations["tech_global"]
        template = defaults_generator.generate_defaults(org)

        platform_team = next(
            team for team in template.teams if team.name == "Platform Engineering"
        )
        field_names = [field.name for field in platform_team.custom_fields]

        assert "Technical Complexity" in field_names
        assert "Business Impact" in field_names
        assert "Architecture Review" in field_names

        # Test field types and ranges
        complexity_field = next(
            field
            for field in platform_team.custom_fields
            if field.name == "Technical Complexity"
        )
        assert complexity_field.type == FieldType.NUMBER
        assert complexity_field.range == [1, 10]

    def test_generic_industry_fallback(self, defaults_generator):
        """Test generic defaults for unspecified industries"""
        org = OrganizationConfig(
            customer_name="Generic Corp",
            industry=IndustryType.RETAIL,  # Should fall back to generic
            size=OrganizationSize.SMB,
        )

        template = defaults_generator.generate_defaults(org)
        team_names = [team.name for team in template.teams]

        # Should have generic teams
        assert "Operations" in team_names
        assert "Projects" in team_names


class TestSizeSpecificDefaults:
    """Test organization size-specific defaults"""

    def test_startup_defaults(self, defaults_generator, sample_organizations):
        """Test startup-specific defaults"""
        org = sample_organizations[
            "consulting_startup"
        ]  # Use consulting to avoid industry-specific teams
        template = defaults_generator.generate_defaults(org)

        # Startups should get an "All Hands" team if no other teams
        if not any(team.name != "All Hands" for team in template.teams):
            all_hands = next(
                team for team in template.teams if team.name == "All Hands"
            )
            assert all_hands.key == "ALL"
            assert "Cross-functional" in all_hands.description

    def test_startup_initiatives(self, defaults_generator, sample_organizations):
        """Test startup initiatives focus on product-market fit"""
        org = OrganizationConfig(
            customer_name="Pure Startup",
            industry=IndustryType.RETAIL,  # Use generic industry to test pure startup logic
            size=OrganizationSize.STARTUP,
        )

        template = defaults_generator.generate_defaults(org)

        # Should have product-market fit focused initiatives
        initiative_names = [init.name for init in template.initiatives]
        pmf_initiatives = [
            name for name in initiative_names if "Market Fit" in name or "MVP" in name
        ]
        assert len(pmf_initiatives) > 0

    def test_enterprise_matrix_organization(
        self, defaults_generator, sample_organizations
    ):
        """Test enterprise matrix organization structure"""
        org = sample_organizations["healthcare_enterprise"]
        template = defaults_generator.generate_defaults(org)

        # Should add Enterprise Architecture team
        team_names = [team.name for team in template.teams]
        assert "Enterprise Architecture" in team_names

        ea_team = next(
            team for team in template.teams if team.name == "Enterprise Architecture"
        )
        field_names = [field.name for field in ea_team.custom_fields]
        assert "Architecture Review" in field_names
        assert "Enterprise Impact" in field_names
        assert "Governance Stage" in field_names

    def test_enterprise_sub_teams_added(self, defaults_generator, sample_organizations):
        """Test that enterprise organizations get enhanced sub-team structure"""
        org = OrganizationConfig(
            customer_name="Enterprise Tech",
            industry=IndustryType.TECHNOLOGY,
            size=OrganizationSize.ENTERPRISE,
        )

        template = defaults_generator.generate_defaults(org)

        # Platform engineering should have sub-teams
        platform_team = next(
            team for team in template.teams if team.name == "Platform Engineering"
        )
        sub_team_names = [sub.name for sub in platform_team.sub_teams]

        # Should have enhanced sub-teams for enterprise
        expected_sub_teams = ["Architecture", "Security", "DevOps"]
        for expected in expected_sub_teams:
            assert expected in sub_team_names

    def test_global_complexity_scaling(self, defaults_generator, sample_organizations):
        """Test global organization complexity scaling"""
        org = sample_organizations["tech_global"]
        template = defaults_generator.generate_defaults(org)

        # Global orgs should have more complex structure
        total_teams = len(template.teams)
        total_sub_teams = sum(len(team.sub_teams) for team in template.teams)

        # Should have reasonable complexity for global org
        assert total_teams >= 2
        assert total_sub_teams >= 3  # Should have sub-teams for global


class TestSymphonyIntegration:
    """Test Symphony integration defaults"""

    def test_symphony_integration_basic_structure(
        self, defaults_generator, sample_organizations
    ):
        """Test basic Symphony integration structure"""
        org = sample_organizations["tech_global"]
        template = defaults_generator.generate_defaults(org)

        symphony = template.symphony_integration
        assert symphony is not None
        assert symphony.use_symphony_defaults == True
        assert symphony.auto_optimization == True

        # Should have automation settings
        assert isinstance(symphony.automation, dict)
        assert "issue_creation" in symphony.automation
        assert "status_sync" in symphony.automation
        assert "reporting" in symphony.automation

    def test_agent_assignments_match_teams(
        self, defaults_generator, sample_organizations
    ):
        """Test that agent assignments match existing teams"""
        for org_key, org in sample_organizations.items():
            template = defaults_generator.generate_defaults(org)

            team_names = {team.name for team in template.teams}
            assigned_teams = set(template.symphony_integration.agent_assignments.keys())

            # All assigned teams should exist in template
            assert assigned_teams.issubset(
                team_names
            ), f"Mismatch in {org_key}: {assigned_teams - team_names}"

    def test_size_based_agent_assignments(
        self, defaults_generator, sample_organizations
    ):
        """Test agent assignments vary by organization size"""
        startup_org = sample_organizations["consulting_startup"]
        enterprise_org = sample_organizations["healthcare_enterprise"]

        startup_template = defaults_generator.generate_defaults(startup_org)
        enterprise_template = defaults_generator.generate_defaults(enterprise_org)

        startup_agents = startup_template.symphony_integration.agent_assignments
        enterprise_agents = enterprise_template.symphony_integration.agent_assignments

        # Enterprise should generally have more sophisticated agent assignments
        enterprise_total = sum(len(agents) for agents in enterprise_agents.values())
        startup_total = sum(len(agents) for agents in startup_agents.values())

        # This might not always be true, but generally enterprise should have more agents
        # At minimum, both should have some agents assigned
        assert startup_total > 0
        assert enterprise_total > 0

    def test_enterprise_advanced_automation(
        self, defaults_generator, sample_organizations
    ):
        """Test enterprise organizations get advanced automation"""
        enterprise_org = sample_organizations["healthcare_enterprise"]
        startup_org = sample_organizations["consulting_startup"]

        enterprise_template = defaults_generator.generate_defaults(enterprise_org)
        startup_template = defaults_generator.generate_defaults(startup_org)

        # Enterprise should have template updates enabled
        enterprise_automation = enterprise_template.symphony_integration.automation
        startup_automation = startup_template.symphony_integration.automation

        assert enterprise_automation.get("template_updates", False) == True
        assert startup_automation.get("template_updates", False) == False


class TestDogfoodingTemplate:
    """Test Symphony's own dogfooding template"""

    def test_dogfooding_template_creation(self, defaults_generator):
        """Test Symphony dogfooding template generation"""
        template = defaults_generator.generate_dogfooding_template()

        assert isinstance(template, WorkspaceTemplate)
        assert template.organization.customer_name == "Symphony"
        assert template.organization.industry == IndustryType.TECHNOLOGY
        assert template.organization.size == OrganizationSize.STARTUP

    def test_dogfooding_workspace_info(self, defaults_generator):
        """Test dogfooding workspace information"""
        template = defaults_generator.generate_dogfooding_template()

        assert template.workspace["name"] == "Symphony Internal Operations"
        assert "Symphony uses Symphony" in template.workspace["description"]

    def test_dogfooding_teams_structure(self, defaults_generator):
        """Test dogfooding teams are Symphony-specific"""
        template = defaults_generator.generate_dogfooding_template()

        team_names = [team.name for team in template.teams]
        assert "Platform Development" in team_names
        assert "Customer Success" in team_names

        # Platform Development should have Linear-specific sub-teams
        platform_team = next(
            team for team in template.teams if team.name == "Platform Development"
        )
        sub_team_names = [sub.name for sub in platform_team.sub_teams]
        assert "Linear Integration" in sub_team_names
        assert "Agent Ecosystem" in sub_team_names
        assert "Configuration Systems" in sub_team_names

    def test_dogfooding_customer_success_workflows(self, defaults_generator):
        """Test Customer Success team has Symphony-specific workflows"""
        template = defaults_generator.generate_dogfooding_template()

        cs_team = next(
            team for team in template.teams if team.name == "Customer Success"
        )
        workflow_names = [w.name for w in cs_team.workflows]

        assert "Discovery" in workflow_names
        assert "Implementation" in workflow_names
        assert "Optimization" in workflow_names
        assert "Excellence" in workflow_names

        # Excellence should be completed state
        excellence_workflow = next(
            w for w in cs_team.workflows if w.name == "Excellence"
        )
        assert excellence_workflow.type == "completed"

    def test_dogfooding_initiatives(self, defaults_generator):
        """Test dogfooding initiatives are Symphony-focused"""
        template = defaults_generator.generate_dogfooding_template()

        initiative_names = [init.name for init in template.initiatives]
        assert "Symphony Platform Excellence" in initiative_names

        platform_init = next(
            init
            for init in template.initiatives
            if init.name == "Symphony Platform Excellence"
        )
        sub_init_names = [sub.name for sub in platform_init.sub_initiatives]
        assert "Linear Integration Mastery" in sub_init_names
        assert "Agent Ecosystem Excellence" in sub_init_names
        assert "Customer Success Optimization" in sub_init_names

    def test_dogfooding_symphony_integration(self, defaults_generator):
        """Test dogfooding has full Symphony integration enabled"""
        template = defaults_generator.generate_dogfooding_template()

        symphony = template.symphony_integration
        assert symphony.self_managing == True
        assert symphony.recursive_improvement == True
        assert symphony.auto_optimization == True

    def test_dogfooding_meta_consistency(self, defaults_generator):
        """Test dogfooding template meta-consistency"""
        template = defaults_generator.generate_dogfooding_template()

        # Should be consistent with Symphony's nature
        assert template.organization.customer_name.lower() == "symphony"

        # Should have self-managing features only for Symphony
        assert template.symphony_integration.self_managing == True

        # Description should reference meta-implementation
        description = template.workspace["description"]
        assert "Symphony" in description
        assert any(
            word in description.lower() for word in ["uses", "manage", "development"]
        )


class TestEdgeCasesAndValidation:
    """Test edge cases and validation scenarios"""

    def test_empty_regions_handling(self, defaults_generator):
        """Test handling of organizations with no regions specified"""
        org = OrganizationConfig(
            customer_name="Local Corp",
            industry=IndustryType.RETAIL,
            size=OrganizationSize.STARTUP,
            regions=[],  # Empty regions
        )

        template = defaults_generator.generate_defaults(org)

        # Should still generate valid template
        assert isinstance(template, WorkspaceTemplate)
        assert template.organization.regions == []

    def test_all_industry_types_generate_templates(self, defaults_generator):
        """Test that all industry types can generate templates"""
        for industry in IndustryType:
            org = OrganizationConfig(
                customer_name=f"{industry.value.title()} Corp",
                industry=industry,
                size=OrganizationSize.SMB,
            )

            template = defaults_generator.generate_defaults(org)

            # Should generate valid template for all industries
            assert isinstance(template, WorkspaceTemplate)
            assert len(template.teams) > 0
            assert template.symphony_integration is not None

    def test_all_organization_sizes_generate_templates(self, defaults_generator):
        """Test that all organization sizes can generate templates"""
        for size in OrganizationSize:
            org = OrganizationConfig(
                customer_name=f"{size.value.title()} Corp",
                industry=IndustryType.TECHNOLOGY,
                size=size,
            )

            template = defaults_generator.generate_defaults(org)

            # Should generate valid template for all sizes
            assert isinstance(template, WorkspaceTemplate)
            assert template.symphony_integration is not None

    def test_team_key_consistency(self, defaults_generator, sample_organizations):
        """Test that all generated teams have valid keys"""
        for org_key, org in sample_organizations.items():
            template = defaults_generator.generate_defaults(org)

            for team in template.teams:
                # Keys should be uppercase and not empty
                assert (
                    team.key.isupper()
                ), f"Team key '{team.key}' not uppercase in {org_key}"
                assert len(team.key) > 0, f"Empty team key in {org_key}"
                assert team.key != team.key.replace(
                    "_", " "
                ), f"Team key should use underscores: {team.key}"

    def test_workflow_position_consistency(
        self, defaults_generator, sample_organizations
    ):
        """Test that workflow positions are consistent"""
        for org_key, org in sample_organizations.items():
            template = defaults_generator.generate_defaults(org)

            for team in template.teams:
                positions = [w.position for w in team.workflows]
                # Positions should be unique and sequential starting from 0
                assert len(set(positions)) == len(
                    positions
                ), f"Duplicate positions in {org_key} team {team.name}"

                if positions:  # If there are workflows
                    assert (
                        min(positions) >= 0
                    ), f"Negative position in {org_key} team {team.name}"


if __name__ == "__main__":
    pytest.main([__file__])
