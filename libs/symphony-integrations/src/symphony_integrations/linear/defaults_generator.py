#!/usr/bin/env python3
"""
Symphony Intelligent Defaults Generator

Generates intelligent Linear workspace defaults based on customer profile,
industry, and organization size.
"""

from dataclasses import asdict
from typing import Any, Dict, List

from .template_models import (
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
    WorkflowState,
    WorkspaceTemplate,
)


class SymphonyLinearDefaults:
    """Generate intelligent Linear workspace defaults for Symphony customers"""

    def __init__(self):
        self.base_workflows = [
            WorkflowState("Backlog", "backlog", 0, "Items in backlog"),
            WorkflowState("Todo", "unstarted", 1, "Ready to start"),
            WorkflowState("In Progress", "started", 2, "Active work"),
            WorkflowState("Review", "started", 3, "Under review"),
            WorkflowState("Done", "completed", 4, "Completed work"),
            WorkflowState("Canceled", "canceled", 5, "Canceled work"),
        ]

    def generate_defaults(self, organization: OrganizationConfig) -> WorkspaceTemplate:
        """Generate complete workspace defaults based on organization profile"""

        # Generate base template
        template = WorkspaceTemplate(
            workspace={
                "name": f"{organization.customer_name} Enterprise Operations",
                "description": f"Autonomous enterprise coordination for {organization.customer_name}",
            },
            organization=organization,
            template_version="2025.1",
        )

        # Add industry-specific defaults
        template = self._add_industry_defaults(template, organization.industry)

        # Add size-specific defaults
        template = self._add_size_defaults(template, organization.size)

        # Add Symphony integration defaults
        template.symphony_integration = self._generate_symphony_integration(
            organization
        )

        return template

    def _add_industry_defaults(
        self, template: WorkspaceTemplate, industry: IndustryType
    ) -> WorkspaceTemplate:
        """Add industry-specific team structures and workflows"""

        if industry == IndustryType.FINANCIAL_SERVICES:
            return self._add_finserv_defaults(template)
        elif industry == IndustryType.HEALTHCARE:
            return self._add_healthcare_defaults(template)
        elif industry == IndustryType.MANUFACTURING:
            return self._add_manufacturing_defaults(template)
        elif industry == IndustryType.TECHNOLOGY:
            return self._add_technology_defaults(template)
        elif industry == IndustryType.CONSULTING:
            return self._add_consulting_defaults(template)
        else:
            return self._add_generic_defaults(template)

    def _add_finserv_defaults(self, template: WorkspaceTemplate) -> WorkspaceTemplate:
        """Financial services specific defaults"""

        # Add compliance workflows
        compliance_workflows = self.base_workflows + [
            WorkflowState(
                "Compliance Review", "started", 2.5, "Regulatory compliance review"
            ),
            WorkflowState("Risk Assessment", "started", 2.7, "Risk analysis required"),
            WorkflowState(
                "Regulatory Approval", "started", 3.5, "Awaiting regulatory approval"
            ),
        ]

        # Financial services teams
        template.teams.extend(
            [
                TeamTemplate(
                    name="Risk Management",
                    key="RISK",
                    description="Risk assessment and management",
                    workflows=compliance_workflows,
                    custom_fields=[
                        CustomField(
                            "Risk Level",
                            FieldType.SELECT,
                            options=["Low", "Medium", "High", "Critical"],
                        ),
                        CustomField("SOX Compliance", FieldType.BOOLEAN),
                        CustomField(
                            "Regulatory Framework",
                            FieldType.SELECT,
                            options=["SOX", "GDPR", "PCI-DSS", "Basel III"],
                        ),
                    ],
                ),
                TeamTemplate(
                    name="Regulatory Compliance",
                    key="COMP",
                    description="Regulatory compliance and audit",
                    workflows=compliance_workflows,
                    custom_fields=[
                        CustomField("Audit Trail Required", FieldType.BOOLEAN),
                        CustomField("Compliance Officer", FieldType.TEXT),
                        CustomField("Review Date", FieldType.DATE),
                    ],
                ),
                TeamTemplate(
                    name="Security Operations",
                    key="SEC",
                    description="Information security and cybersecurity",
                    workflows=self.base_workflows,
                    custom_fields=[
                        CustomField(
                            "Security Classification",
                            FieldType.SELECT,
                            options=[
                                "Public",
                                "Internal",
                                "Confidential",
                                "Restricted",
                            ],
                        )
                    ],
                ),
            ]
        )

        # Financial services initiatives
        template.initiatives.extend(
            [
                Initiative(
                    name="Regulatory Compliance 2025",
                    level=1,
                    description="Maintain regulatory compliance across all frameworks",
                    sub_initiatives=[
                        Initiative(
                            "SOX 404 Compliance", 2, "Sarbanes-Oxley compliance"
                        ),
                        Initiative("GDPR Enhancement", 2, "Enhanced GDPR compliance"),
                        Initiative(
                            "Cybersecurity Framework",
                            2,
                            "NIST cybersecurity implementation",
                        ),
                    ],
                ),
                Initiative(
                    name="Digital Banking Platform",
                    level=1,
                    description="Modern digital banking infrastructure",
                    sub_initiatives=[
                        Initiative("API Banking Platform", 2, "Core banking APIs"),
                        Initiative(
                            "Customer Experience Portal",
                            2,
                            "Digital customer interface",
                        ),
                        Initiative(
                            "Real-time Risk Management", 2, "Automated risk assessment"
                        ),
                    ],
                ),
            ]
        )

        # Financial services projects
        template.projects.extend(
            [
                ProjectTemplate(
                    template_name="compliance_project",
                    name="${regulation} Compliance Implementation",
                    description="Implementation of ${regulation} regulatory requirements",
                    assignable_teams=["Risk Management", "Regulatory Compliance"],
                    milestones=[
                        Milestone("Gap Analysis", "Identify compliance gaps"),
                        Milestone("Control Design", "Design compliance controls"),
                        Milestone("Implementation", "Implement compliance measures"),
                        Milestone("Testing", "Test compliance controls"),
                        Milestone("Audit", "External audit and certification"),
                    ],
                    timeline="16 weeks",
                )
            ]
        )

        return template

    def _add_healthcare_defaults(
        self, template: WorkspaceTemplate
    ) -> WorkspaceTemplate:
        """Healthcare industry specific defaults"""

        # HIPAA compliance workflows
        hipaa_workflows = self.base_workflows + [
            WorkflowState("HIPAA Review", "started", 2.5, "HIPAA compliance review"),
            WorkflowState(
                "Privacy Assessment", "started", 2.7, "Privacy impact assessment"
            ),
            WorkflowState(
                "Clinical Approval", "started", 3.5, "Clinical stakeholder approval"
            ),
        ]

        template.teams.extend(
            [
                TeamTemplate(
                    name="Clinical Operations",
                    key="CLIN",
                    description="Clinical workflow and patient care",
                    workflows=hipaa_workflows,
                    custom_fields=[
                        CustomField(
                            "Patient Safety Impact",
                            FieldType.SELECT,
                            options=["None", "Low", "Medium", "High", "Critical"],
                        ),
                        CustomField("HIPAA Covered", FieldType.BOOLEAN),
                        CustomField("Clinical Validation Required", FieldType.BOOLEAN),
                    ],
                ),
                TeamTemplate(
                    name="Privacy & Compliance",
                    key="PRIV",
                    description="HIPAA and healthcare privacy compliance",
                    workflows=hipaa_workflows,
                    custom_fields=[
                        CustomField("PHI Involved", FieldType.BOOLEAN),
                        CustomField("Privacy Officer Review", FieldType.BOOLEAN),
                        CustomField(
                            "Compliance Framework",
                            FieldType.SELECT,
                            options=["HIPAA", "HITECH", "FDA", "CMS"],
                        ),
                    ],
                ),
            ]
        )

        template.initiatives.extend(
            [
                Initiative(
                    name="Digital Health Platform",
                    level=1,
                    description="Comprehensive digital health solution",
                    sub_initiatives=[
                        Initiative(
                            "Electronic Health Records", 2, "EHR system implementation"
                        ),
                        Initiative(
                            "Telemedicine Platform", 2, "Remote care capabilities"
                        ),
                        Initiative(
                            "Patient Engagement Portal",
                            2,
                            "Patient self-service platform",
                        ),
                    ],
                )
            ]
        )

        return template

    def _add_technology_defaults(
        self, template: WorkspaceTemplate
    ) -> WorkspaceTemplate:
        """Technology company specific defaults"""

        # Development workflows
        dev_workflows = [
            WorkflowState("Backlog", "backlog", 0, "Product backlog"),
            WorkflowState("Planning", "unstarted", 1, "Sprint planning"),
            WorkflowState("Development", "started", 2, "Active development"),
            WorkflowState("Code Review", "started", 3, "Peer code review"),
            WorkflowState("Testing", "started", 4, "QA testing"),
            WorkflowState("Staging", "started", 5, "Staging environment"),
            WorkflowState("Done", "completed", 6, "Deployed to production"),
        ]

        template.teams.extend(
            [
                TeamTemplate(
                    name="Platform Engineering",
                    key="PLAT",
                    description="Core platform development and infrastructure",
                    workflows=dev_workflows,
                    sub_teams=[
                        TeamTemplate(
                            "Frontend", "FE", "Frontend development", dev_workflows
                        ),
                        TeamTemplate(
                            "Backend", "BE", "Backend services", dev_workflows
                        ),
                        TeamTemplate(
                            "Infrastructure",
                            "INFRA",
                            "DevOps and infrastructure",
                            dev_workflows,
                        ),
                    ],
                    custom_fields=[
                        CustomField(
                            "Technical Complexity", FieldType.NUMBER, range=[1, 10]
                        ),
                        CustomField(
                            "Business Impact",
                            FieldType.SELECT,
                            options=["Low", "Medium", "High", "Critical"],
                        ),
                        CustomField("Architecture Review", FieldType.BOOLEAN),
                    ],
                ),
                TeamTemplate(
                    name="Product Management",
                    key="PM",
                    description="Product strategy and management",
                    workflows=self.base_workflows,
                    custom_fields=[
                        CustomField(
                            "Customer Segment",
                            FieldType.SELECT,
                            options=["Enterprise", "SMB", "Startup", "Individual"],
                        ),
                        CustomField(
                            "Feature Priority",
                            FieldType.SELECT,
                            options=["P0", "P1", "P2", "P3"],
                        ),
                        CustomField(
                            "User Story Points", FieldType.NUMBER, range=[1, 21]
                        ),
                    ],
                ),
            ]
        )

        template.initiatives.extend(
            [
                Initiative(
                    name="Platform Excellence 2025",
                    level=1,
                    description="Technical platform excellence and scalability",
                    sub_initiatives=[
                        Initiative(
                            "Microservices Architecture", 2, "Service decomposition"
                        ),
                        Initiative(
                            "Observability Platform", 2, "Monitoring and observability"
                        ),
                        Initiative(
                            "Developer Experience", 2, "Internal developer tools"
                        ),
                    ],
                )
            ]
        )

        return template

    def _add_size_defaults(
        self, template: WorkspaceTemplate, size: OrganizationSize
    ) -> WorkspaceTemplate:
        """Add size-specific team structures and complexity"""

        if size == OrganizationSize.STARTUP:
            return self._add_startup_defaults(template)
        elif size == OrganizationSize.SMB:
            return self._add_smb_defaults(template)
        elif size == OrganizationSize.ENTERPRISE:
            return self._add_enterprise_defaults(template)
        elif size == OrganizationSize.GLOBAL:
            return self._add_global_defaults(template)

        return template

    def _add_startup_defaults(self, template: WorkspaceTemplate) -> WorkspaceTemplate:
        """Startup-specific simplifications"""

        # Add simple all-hands team if no teams exist
        if not template.teams:
            template.teams.append(
                TeamTemplate(
                    name="All Hands",
                    key="ALL",
                    description="Cross-functional startup team",
                    workflows=self.base_workflows,
                    custom_fields=[
                        CustomField(
                            "Priority",
                            FieldType.SELECT,
                            options=["High", "Medium", "Low"],
                        ),
                        CustomField(
                            "Effort",
                            FieldType.SELECT,
                            options=["XS", "S", "M", "L", "XL"],
                        ),
                    ],
                )
            )

        # Simple initiatives
        if not template.initiatives:
            template.initiatives.append(
                Initiative(
                    name="Product Market Fit",
                    level=1,
                    description="Achieve product-market fit and initial growth",
                    sub_initiatives=[
                        Initiative("MVP Development", 2, "Minimum viable product"),
                        Initiative(
                            "Customer Validation", 2, "Validate product with customers"
                        ),
                        Initiative("Growth Optimization", 2, "Optimize for growth"),
                    ],
                )
            )

        return template

    def _add_enterprise_defaults(
        self, template: WorkspaceTemplate
    ) -> WorkspaceTemplate:
        """Enterprise-specific enhancements"""

        # Add matrix organization support
        for team in template.teams:
            if not team.sub_teams:  # Add sub-teams to main teams
                if "Engineering" in team.name or "Platform" in team.name:
                    team.sub_teams.extend(
                        [
                            TeamTemplate(
                                "Architecture", "ARCH", "Technical architecture"
                            ),
                            TeamTemplate("Security", "SEC", "Security engineering"),
                            TeamTemplate("DevOps", "DEVOPS", "Development operations"),
                        ]
                    )

        # Add enterprise governance
        template.teams.append(
            TeamTemplate(
                name="Enterprise Architecture",
                key="EA",
                description="Enterprise architecture and governance",
                workflows=self.base_workflows,
                custom_fields=[
                    CustomField("Architecture Review", FieldType.BOOLEAN),
                    CustomField(
                        "Enterprise Impact",
                        FieldType.SELECT,
                        options=["Department", "Division", "Enterprise", "External"],
                    ),
                    CustomField(
                        "Governance Stage",
                        FieldType.SELECT,
                        options=["Concept", "Planning", "Execution", "Review"],
                    ),
                ],
            )
        )

        return template

    def _add_generic_defaults(self, template: WorkspaceTemplate) -> WorkspaceTemplate:
        """Generic defaults for other industries"""

        template.teams.extend(
            [
                TeamTemplate(
                    name="Operations",
                    key="OPS",
                    description="Business operations and coordination",
                    workflows=self.base_workflows,
                    custom_fields=[
                        CustomField(
                            "Priority",
                            FieldType.SELECT,
                            options=["High", "Medium", "Low"],
                        ),
                        CustomField("Business Unit", FieldType.TEXT),
                    ],
                ),
                TeamTemplate(
                    name="Projects",
                    key="PROJ",
                    description="Project management and delivery",
                    workflows=self.base_workflows,
                    custom_fields=[
                        CustomField(
                            "Project Phase",
                            FieldType.SELECT,
                            options=[
                                "Initiation",
                                "Planning",
                                "Execution",
                                "Monitoring",
                                "Closure",
                            ],
                        ),
                        CustomField(
                            "Budget Impact",
                            FieldType.SELECT,
                            options=["None", "Low", "Medium", "High"],
                        ),
                    ],
                ),
            ]
        )

        return template

    def _add_global_defaults(self, template: WorkspaceTemplate) -> WorkspaceTemplate:
        """Global organization-specific defaults"""

        # Add global-scale organizational structure
        if not any("Enterprise Architecture" in team.name for team in template.teams):
            template.teams.append(
                TeamTemplate(
                    name="Global Operations",
                    key="GLOBAL_OPS",
                    description="Global operations coordination and governance",
                    workflows=self.base_workflows,
                    custom_fields=[
                        CustomField(
                            "Region",
                            FieldType.SELECT,
                            options=["AMER", "EMEA", "APAC", "Global"],
                        ),
                        CustomField(
                            "Compliance Region",
                            FieldType.MULTI_SELECT,
                            options=["US", "EU", "UK", "APAC", "Other"],
                        ),
                        CustomField(
                            "Priority Level",
                            FieldType.SELECT,
                            options=["Local", "Regional", "Global", "Critical"],
                        ),
                    ],
                )
            )

        return template

    def _add_smb_defaults(self, template: WorkspaceTemplate) -> WorkspaceTemplate:
        """SMB-specific defaults"""

        # Add departmental structure for SMBs
        if not template.teams or len(template.teams) < 2:
            template.teams.extend(
                [
                    TeamTemplate(
                        name="Operations",
                        key="OPS",
                        description="Business operations and coordination",
                        workflows=self.base_workflows,
                    ),
                    TeamTemplate(
                        name="Growth",
                        key="GROWTH",
                        description="Growth and business development",
                        workflows=self.base_workflows,
                    ),
                ]
            )

        return template

    def _generate_symphony_integration(
        self, organization: OrganizationConfig
    ) -> SymphonyIntegration:
        """Generate Symphony-specific integration configuration"""

        base_agents = [
            "Configuration Management Agent",
            "Workspace Setup Agent",
            "Template Generation Agent",
        ]

        if organization.size == OrganizationSize.STARTUP:
            agent_assignments = {
                "All Hands": base_agents
                + [
                    "Development Assistant Agent",
                    "Project Tracking Agent",
                    "Basic Reporting Agent",
                ]
            }
        elif organization.size == OrganizationSize.ENTERPRISE:
            agent_assignments = {
                "Platform Engineering": base_agents
                + [
                    "Linear Integration Agent",
                    "Development Coordinator Agent",
                    "Architecture Agent",
                ],
                "Enterprise Architecture": [
                    "Enterprise Orchestration Agent",
                    "Governance Agent",
                    "Compliance Monitoring Agent",
                ],
            }
        else:
            agent_assignments = {
                "Operations": base_agents
                + ["Operations Coordinator Agent", "Analytics Agent"]
            }

        return SymphonyIntegration(
            agent_assignments=agent_assignments,
            automation={
                "issue_creation": True,
                "status_sync": True,
                "reporting": True,
                "template_updates": organization.size
                in [OrganizationSize.ENTERPRISE, OrganizationSize.GLOBAL],
            },
            defaults_override={
                "use_symphony_defaults": True,
                "allow_customization": True,
                "auto_sync": True,
            },
            use_symphony_defaults=True,
            self_managing=organization.customer_name.lower() == "symphony",
            recursive_improvement=organization.customer_name.lower() == "symphony",
            auto_optimization=True,
        )

    def generate_dogfooding_template(self) -> WorkspaceTemplate:
        """Generate Symphony's own workspace template (eating our own dogfood)"""

        symphony_org = OrganizationConfig(
            customer_name="Symphony",
            industry=IndustryType.TECHNOLOGY,
            size=OrganizationSize.STARTUP,
            regions=["global"],
        )

        template = self.generate_defaults(symphony_org)

        # Override with Symphony-specific structure
        template.workspace = {
            "name": "Symphony Internal Operations",
            "description": "Symphony uses Symphony to manage Symphony development",
        }

        template.teams = [
            TeamTemplate(
                name="Platform Development",
                key="DEV",
                description="Symphony platform development",
                workflows=self.base_workflows,
                sub_teams=[
                    TeamTemplate(
                        "Linear Integration", "LINEAR", "Linear workspace management"
                    ),
                    TeamTemplate(
                        "Agent Ecosystem",
                        "AGENTS",
                        "Agent development and coordination",
                    ),
                    TeamTemplate(
                        "Configuration Systems",
                        "CONFIG",
                        "Template and configuration systems",
                    ),
                ],
            ),
            TeamTemplate(
                name="Customer Success",
                key="CS",
                description="Symphony customer implementations",
                workflows=[
                    WorkflowState(
                        "Discovery", "unstarted", 1, "Customer needs analysis"
                    ),
                    WorkflowState(
                        "Implementation", "started", 2, "Symphony deployment"
                    ),
                    WorkflowState(
                        "Optimization", "started", 3, "Performance optimization"
                    ),
                    WorkflowState(
                        "Excellence", "completed", 4, "Autonomous excellence achieved"
                    ),
                ],
            ),
        ]

        template.initiatives = [
            Initiative(
                name="Symphony Platform Excellence",
                level=1,
                description="Perfect autonomous enterprise platform",
                sub_initiatives=[
                    Initiative(
                        "Linear Integration Mastery",
                        2,
                        "Perfect Linear workspace management",
                    ),
                    Initiative(
                        "Agent Ecosystem Excellence",
                        2,
                        "85+ agent coordination perfection",
                    ),
                    Initiative(
                        "Customer Success Optimization",
                        2,
                        "Perfect customer implementations",
                    ),
                ],
            )
        ]

        # Enable full dogfooding
        template.symphony_integration.self_managing = True
        template.symphony_integration.recursive_improvement = True
        template.symphony_integration.auto_optimization = True

        return template
