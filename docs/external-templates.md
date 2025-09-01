# Symphony External Templates

This guide explains how to use external template files with the Symphony CLI onboarding system to create customized Linear workspaces and workflows.

## Overview

The Symphony CLI supports external template files that define:
- Linear workspace configurations
- Team structures and workflows  
- Project templates
- Symphony agent assignments
- Custom workflow steps

## Template File Formats

### 1. Linear Workspace Templates

Use your existing Linear workspace template format:

```yaml
workspace:
  name: "${customer_name} Autonomous Enterprise"
  organization:
    name: "${customer_name}"
    
teams:
  - name: "Strategic Leadership"
    key: "STRAT"
    workflows:
      - name: "Vision & Strategy"
        type: "started"
        position: 1
        
projects:
  enterprise_deployment:
    name: "Enterprise Deployment"
    description: "Full enterprise autonomous platform deployment"
    
symphony_integration:
  agent_assignments:
    "Strategic Leadership":
      - "Maestro Coordinator"
      - "Victoria Strategic Intelligence"
```

### 2. Custom Workflow Templates

Define custom workflow steps:

```yaml
workflow_template:
  package_type: enterprise
  steps:
    - id: environment_validation
      name: "Environment Setup"
      description: "Validate development environment"
      required: true
      estimated_duration: 300
      dependencies: []
      
    - id: integration_setup
      name: "Integration Configuration"  
      description: "Setup Linear and GitHub integrations"
      required: true
      estimated_duration: 600
      dependencies: ["environment_validation"]
```

## CLI Usage

### Basic Template Usage

```bash
# Use template file with onboarding
symphony onboard start mycorp --config-file /path/to/template.yaml

# Specify package and industry
symphony onboard start mycorp --package enterprise --industry financial --config-file template.yaml
```

### Template Validation

```bash
# Validate template file
symphony onboard validate-template /path/to/template.yaml

# Preview template structure
symphony onboard validate-template template.yaml --preview

# Test with specific customer data
symphony onboard validate-template template.yaml --customer "Acme Corp" --package enterprise
```

### Authentication Setup

Before using Linear templates, authenticate with the services:

```bash
# Authenticate with Linear
symphony auth login --service linear

# Authenticate with GitHub  
symphony auth login --service github

# Check authentication status
symphony auth status
```

## Template Variables

Templates support variable substitution using `${variable_name}` syntax:

### Available Variables
- `${customer_name}` - Customer/organization name
- `${package_type}` - Package type (startup, smb, enterprise, global)
- `${organization_name}` - Organization name (defaults to customer_name)

### Example Usage
```yaml
workspace:
  name: "${customer_name} Workspace"
  description: "Autonomous enterprise platform for ${organization_name}"
  
teams:
  - name: "${customer_name} Engineering"
    description: "Engineering team for ${package_type} deployment"
```

## Integration with Existing Templates

Your existing template file at `/Users/pmuniraju/play/sandbox/symphony/configs/linear-templates/enterprise/symphony-autonomous-enterprise.yaml` works directly with the Symphony CLI:

```bash
# Use your enterprise template
symphony onboard start acme-corp --config-file /Users/pmuniraju/play/sandbox/symphony/configs/linear-templates/enterprise/symphony-autonomous-enterprise.yaml

# Validate your template
symphony onboard validate-template /Users/pmuniraju/play/sandbox/symphony/configs/linear-templates/enterprise/symphony-autonomous-enterprise.yaml --preview
```

## What Happens During Onboarding

When you use an external template:

1. **Template Loading**: CLI loads and validates the template file
2. **Variable Substitution**: Replaces variables with customer-specific values
3. **Workflow Enhancement**: Enhances the integration setup step with template data
4. **Linear Workspace Creation**: Creates Linear workspace with teams, workflows, and projects
5. **Agent Deployment**: Deploys Symphony agents according to team assignments

## Template Processing Flow

1. **Detection**: CLI detects template type (Linear workspace vs. explicit workflow)
2. **Parsing**: Parses YAML and validates structure
3. **Enhancement**: Enhances standard workflow steps with template metadata
4. **Execution**: During integration setup step:
   - Authenticates with Linear
   - Creates workspace structure from template
   - Sets up team assignments and workflows
   - Configures Symphony agent integration

## Error Handling

- **Template not found**: Falls back to built-in templates
- **Invalid YAML**: Reports parsing errors with line numbers
- **Missing authentication**: Guides user to authenticate with required services
- **API failures**: Provides detailed error messages and continues with simulation

## Advanced Usage

### Multiple Template Inheritance

Your templates support inheritance:

```yaml
inherits_from: "/path/to/base-template.yaml"

# Override specific sections
workspace:
  name: "${customer_name} Custom Workspace"
```

### Custom Validation

Add custom validation to templates:

```yaml
validation:
  required_services: ["linear", "github"]
  minimum_package: "enterprise"  
  supported_industries: ["financial", "healthcare", "technology"]
```

## Example Complete Workflow

```bash
# 1. Authenticate with services
symphony auth login --service linear
symphony auth login --service github

# 2. Validate template
symphony onboard validate-template enterprise-template.yaml --customer "Acme Corp"

# 3. Start onboarding with template
symphony onboard start acme-corp --package enterprise --config-file enterprise-template.yaml

# 4. Monitor progress
symphony onboard status acme-corp-[workflow-id]
```

This creates a complete Linear workspace with your enterprise template structure and deploys Symphony agents according to the team assignments defined in your template.