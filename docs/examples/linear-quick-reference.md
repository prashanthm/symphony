# Linear Setup - Quick Reference Guide

## 🚀 Quick Start Commands

### 1. **Preview Setup** (Safe - No Changes)
```bash
python3 -m symphony_cli.commands.linear_hierarchy preview \
  ./organizations/customers/acme-corp/config/customer-config.yaml
```

### 2. **Validate Configuration** 
```bash
python3 -m symphony_cli.commands.linear_hierarchy validate \
  ./organizations/customers/acme-corp/config/customer-config.yaml
```

### 3. **Deploy to Linear** (Requires Token)
```bash
export LINEAR_API_TOKEN='your_linear_api_token'
python3 -m symphony_cli.commands.linear_hierarchy deploy \
  --config ./organizations/customers/acme-corp/config/customer-config.yaml \
  --linear-token $LINEAR_API_TOKEN
```

### 4. **Interactive Setup**
```bash
python3 -m symphony_cli.commands.linear_hierarchy configure --interactive
```

### 5. **Generate New Customer Defaults**
```bash
python3 -m symphony_cli.commands.linear_hierarchy generate \
  --customer "YourCompany" \
  --industry healthcare \
  --size enterprise \
  --preview
```

## 🏥 Healthcare Example (ACME Corp)

**Generated Projects:**
- `acme-corp - Healthcare Compliance` - HIPAA, regulatory requirements
- `acme-corp - Clinical Operations` - Patient flow, workflows, quality metrics  
- `acme-corp - Digital Health Innovation` - Telemedicine, patient portals
- `acme-corp - Enterprise Architecture` - System design, scalability
- `acme-corp - Compliance & Security` - Security frameworks, risk management

## 💻 Technology Company Example

**Generated Projects:**
- `TechCorp - Product Development` - Features, roadmap, innovation
- `TechCorp - Platform Engineering` - Infrastructure, DevOps, reliability
- `TechCorp - Customer Success` - Onboarding, support, feedback
- `TechCorp - Enterprise Architecture` - System design, integrations
- `TechCorp - Compliance & Security` - Security, compliance monitoring

## 🔧 Programmatic Usage

```python
import asyncio
from symphony_integrations.linear.client import SymphonyLinearIntegration

async def setup_linear_workspace():
    integration = SymphonyLinearIntegration(api_token="your_token")
    
    workspace = await integration.initialize_workspace(
        organization_name="ACME Corp",
        industry="healthcare",
        size="enterprise",
        customer_config={
            "customer_profile": {
                "organization_name": "ACME Corp",
                "industry": "healthcare"
            },
            "agent_configuration": {
                "selected_package": "enterprise"
            }
        }
    )
    
    print(f"Created {len(workspace['projects'])} projects")
    return workspace

# Run it
workspace_config = asyncio.run(setup_linear_workspace())
```

## 📋 Template Variables

**Available Variables:**
- `${customer_name}` - Organization name
- `${industry}` - Industry sector (healthcare, technology, etc.)
- `${size}` - Organization size (startup, smb, enterprise, global)
- `${current_year}` - Current year
- `${region}` - Geographic region

**Example Template:**
```yaml
projects:
  - name: "${customer_name} - ${industry} Compliance"
    description: "Regulatory compliance for ${customer_name}"
  - name: "${customer_name} - Digital Transformation"  
    description: "Digital initiatives for ${size} organization"
```

## 🎯 Industry-Specific Projects

### Healthcare
- Healthcare Compliance (HIPAA, FDA)
- Clinical Operations
- Digital Health Innovation
- Patient Data Management

### Technology  
- Product Development
- Platform Engineering
- Customer Success
- Technical Architecture

### Financial Services
- Regulatory Compliance (SOX, PCI)
- Risk Management
- Digital Banking
- Fraud Prevention

### Manufacturing
- Production Optimization
- Supply Chain Management
- Quality Control
- Safety & Compliance

## 📊 Package Sizes

### Startup (5-20 people)
- 2-3 core projects
- Basic workflow states
- Essential integrations

### SMB (20-100 people)
- 3-4 departmental projects  
- Advanced workflows
- Multi-team coordination

### Enterprise (100-500 people)
- 4-6 comprehensive projects
- Complex workflows
- Enterprise architecture focus

### Global (500+ people)
- 6+ specialized projects
- Multi-region workflows
- Advanced compliance & security

## ⚡ Troubleshooting

### Issue: "Template not found"
```bash
# Check available templates
find configs/linear-templates -name "*.yaml"
```

### Issue: "Linear API authentication failed"  
```bash
# Test Linear connection
curl -H "Authorization: $LINEAR_API_TOKEN" \
  -X POST https://api.linear.app/graphql \
  -d '{"query":"query { viewer { name } }"}'
```

### Issue: "Configuration validation errors"
```bash
# Debug with detailed preview
python3 -m symphony_cli.commands.linear_hierarchy preview \
  customer-config.yaml --detailed
```

## 🔄 Workflow States Created

**Standard Workflow:**
1. **Backlog** - Items waiting for prioritization
2. **Todo** - Ready to start
3. **In Progress** - Active work
4. **Done** - Completed work

**Enterprise Workflow (Additional):**
5. **Review** - Under review
6. **Testing** - Quality assurance
7. **Deploy** - Production deployment

## 📈 Next Steps After Setup

1. **Assign Symphony Agents** to projects
2. **Create initial issues** for deployment phases
3. **Configure team permissions** and access
4. **Set up automation rules** for issue management
5. **Integrate with monitoring** for real-time updates