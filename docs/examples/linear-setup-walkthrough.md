# Linear Setup Walkthrough - Complete Example

## Step 1: Environment Setup

```bash
# 1. Set up your Linear API token
export LINEAR_API_TOKEN="your_linear_api_token_here"

# 2. Verify Symphony CLI is working
./tools/symphony status

# 3. Check Linear integration status
./tools/symphony integration status --integration linear
```

## Step 2: Customer Configuration

```bash
# Option A: Use existing customer (ACME Corp)
customer_config="organizations/customers/acme-corp/config/customer-config.yaml"

# Option B: Create new customer configuration
./tools/symphony customer create healthcare-startup startup healthcare
```

## Step 3: Linear Workspace Setup (CLI Method)

```bash
# Navigate to the CLI directory
cd apps/symphony-cli

# Method A: Deploy with existing customer config
python3 -m symphony_cli.commands.linear_hierarchy deploy \
  --config "../../organizations/customers/acme-corp/config/customer-config.yaml" \
  --linear-token $LINEAR_API_TOKEN

# Method B: Interactive configuration wizard  
python3 -m symphony_cli.commands.linear_hierarchy configure --interactive

# Method C: Generate defaults and preview
python3 -m symphony_cli.commands.linear_hierarchy generate \
  --customer "TechCorp" \
  --industry technology \
  --size enterprise \
  --preview
```

## Step 4: Verify Linear Workspace Creation

The deployment will create:

### For ACME Corp (Healthcare + Enterprise):
- **ACME Corp - Healthcare Compliance**: Regulatory and compliance management
- **ACME Corp - Digital Health Innovation**: Digital transformation in healthcare  
- **ACME Corp - Enterprise Architecture**: Large-scale system design
- **ACME Corp - Clinical Operations**: Healthcare service delivery

### Template Variables Applied:
- `${customer_name}` → "ACME Corp" 
- `${industry}` → "healthcare"
- `${size}` → "enterprise"
- `${current_year}` → "2025"

## Step 5: Programmatic API Usage

```python
import asyncio
from symphony_integrations.linear.client import SymphonyLinearIntegration

async def setup_customer_workspace():
    # Initialize Linear integration
    integration = SymphonyLinearIntegration(api_token="your_token_here")
    
    # Method 1: With customer configuration
    workspace = await integration.initialize_workspace(
        organization_name="TechCorp",
        template_path="configs/linear-templates/enterprise/technology.yaml",
        industry="technology",
        size="enterprise"
    )
    
    # Method 2: With customer config file
    customer_config = {
        "customer_profile": {
            "organization_name": "TechCorp",
            "industry": "technology"
        },
        "agent_configuration": {
            "selected_package": "enterprise"
        }
    }
    
    workspace = await integration.initialize_workspace(
        organization_name="TechCorp",
        customer_config=customer_config
    )
    
    return workspace

# Run the setup
workspace_config = asyncio.run(setup_customer_workspace())
print(f"Created workspace: {workspace_config['organization_name']}")
print(f"Projects created: {list(workspace_config['projects'].keys())}")
```

## Step 6: Validation and Monitoring

```bash
# Validate configuration
python3 -m symphony_cli.commands.linear_hierarchy validate \
  "../../organizations/customers/acme-corp/config/customer-config.yaml"

# Preview what would be created
python3 -m symphony_cli.commands.linear_hierarchy preview \
  "../../organizations/customers/acme-corp/config/customer-config.yaml" \
  --detailed

# Monitor deployment status
./tools/symphony dev monitor --integration linear
```

## Expected Output Flow

### 1. Pre-deployment Validation:
```
🔍 Validating Workspace Configuration
✅ Configuration is valid!
💡 Suggestions:
  • Consider adding healthcare-specific custom fields
  • Configure HIPAA compliance workflows
```

### 2. Deployment Process:
```
🚀 Deploying Linear Workspace
Deploying for: ACME Corp
Industry: healthcare
Package: enterprise (enterprise)

Creating Linear workspace...
✓ Created workspace: ACME Corp
✓ Created 4 projects:
  • ACME Corp - Healthcare Compliance
  • ACME Corp - Digital Health Innovation  
  • ACME Corp - Enterprise Architecture
  • ACME Corp - Clinical Operations
✓ Using team: Operations (OPS)
✓ Configured 5 workflow states
🎉 Workspace deployed successfully!
```

### 3. Generated Linear Projects Structure:
```
ACME Corp Operations Team
├── ACME Corp - Healthcare Compliance
│   ├── HIPAA Compliance Tracking
│   ├── FDA Regulatory Requirements  
│   └── Patient Data Protection
├── ACME Corp - Digital Health Innovation
│   ├── Telemedicine Platform Development
│   ├── Patient Portal Enhancement
│   └── Clinical Decision Support
├── ACME Corp - Enterprise Architecture
│   ├── System Integration Planning
│   ├── Scalability Architecture
│   └── Security Framework Design
└── ACME Corp - Clinical Operations
    ├── Patient Flow Optimization
    ├── Clinical Workflow Automation
    └── Quality Metrics Tracking
```

## Advanced Usage Examples

### Custom Template Variables:
```python
custom_variables = {
    "customer_name": "ACME Corp",
    "industry": "healthcare", 
    "region": "us-east-1",
    "compliance_requirements": ["HIPAA", "SOX", "GDPR"],
    "current_year": 2025,
    "deployment_phase": "Phase 1"
}

workspace = await integration.initialize_workspace(
    organization_name="ACME Corp",
    template_path="custom-healthcare-template.yaml",
    customer_config={
        "template_variables": custom_variables
    }
)
```

### Error Handling and Fallback:
```python
try:
    # Try template-based approach
    workspace = await integration.initialize_workspace(
        organization_name="ACME Corp",
        template_path="healthcare-template.yaml"
    )
except Exception as e:
    print(f"Template failed: {e}")
    # Automatically falls back to core projects:
    # - ACME Corp - Agent Ecosystem
    # - ACME Corp - Tool Integration  
    # - ACME Corp - Deployment Phases
    # - ACME Corp - Validation & Testing
```

## Troubleshooting Common Issues

### Issue 1: Template Not Found
```bash
# Check available templates
find configs/linear-templates -name "*.yaml" -type f

# Validate template syntax
python3 -c "import yaml; print(yaml.safe_load(open('template.yaml')))"
```

### Issue 2: Linear API Authentication
```bash
# Test Linear connection
curl -H "Authorization: $LINEAR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST -d '{"query":"query { viewer { id name } }"}' \
  https://api.linear.app/graphql
```

### Issue 3: Variable Substitution Issues  
```bash
# Debug template variables
python3 -m symphony_cli.commands.linear_hierarchy preview \
  customer-config.yaml --detailed
```

## Integration with Symphony Ecosystem

Once Linear workspace is created, it integrates with:

- **Agent Assignments**: Projects get assigned to relevant Symphony agents
- **Workflow Automation**: Issues auto-created based on deployment phases  
- **Monitoring**: Linear workspace health tracked in Symphony monitoring
- **Reporting**: Project progress included in customer dashboards
- **Templates**: Projects structure feeds back into template improvements