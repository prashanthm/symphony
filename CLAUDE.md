# Claude Configuration for Symphony Autonomous Enterprise Monorepo
*The Ultimate Universal Command Center Configuration*

## 🎯 **MONOREPO IDENTITY**

**CRITICAL UNDERSTANDING**: This is not just a repository - this IS the Symphony Autonomous Enterprise. 

This monorepo is the **single source of truth** for the entire Symphony universe:
- Develops and builds the Symphony platform
- Creates and manages customer organizations
- Handles business operations and customer relationships  
- Manages all documentation (internal and external)
- Coordinates partnerships and integrations
- Monitors global operations and analytics

**Meta-Implementation**: Symphony uses Symphony's own coordination patterns to manage itself - the ultimate self-validating business model.

## 📁 **MONOREPO STRUCTURE - HYBRID ARCHITECTURE** 

### **🎯 Current Implementation Status**
✅ **OPERATIONAL**: Symphony now uses a **hybrid architecture** combining modern Python packaging with the 12-tier organizational structure.

### **12-Tier Universal Command Center** (Current State)
```
symphony/                           # THE Universal Command Center
├── 🚀 workspace/                  # ✅ Active development workspace (created)
├── 🏭 build/                      # ✅ Build system & automation (planned structure)
├── 🎼 core/                       # 🔄 HYBRID: Core platform (planned + existing platform/)
│   ├── agents/                    # 🔄 85+ agents (currently in platform/agents/)
│   ├── orchestration/             # 🔄 Coordination patterns (currently in platform/)
│   └── governance/                # 🔄 Standards & compliance (currently in platform/)
├── 🏢 organizations/              # ✅ Customer organization management
│   ├── defaults/                  # ✅ Pre-built packages (startup, SMB, enterprise, global)
│   ├── customers/                 # ✅ Live customer-specific deployments  
│   └── marketplace/               # ✅ Partner integrations & extensions
├── 📦 releases/                   # ✅ Compiled releases & packages (planned structure)
├── 🛠️ tools/                     # ✅ Development & deployment tools
│   └── symphony                  # ✅ OPERATIONAL Universal CLI
├── 📚 docs/                       # ✅ Multi-audience documentation (existing)
│   ├── internal/                 # ✅ Development team documentation
│   ├── external/                 # ✅ Customer-facing documentation
│   ├── api/                      # ✅ API documentation & references  
│   └── partnerships/             # ✅ Partner & integration documentation
├── 🔧 templates/                  # ✅ Enhanced development templates (existing)
├── 🌍 solutions/                  # ✅ Enhanced industry solutions (existing)
├── 💼 business/                   # ✅ Business operations & CRM
│   ├── customers/                # ✅ Customer relationship management
│   ├── sales/                    # ✅ Sales operations & pipeline
│   ├── marketing/                # ✅ Marketing & lead generation
│   ├── analytics/                # ✅ Business intelligence
│   └── partnerships/             # ✅ Partner relationship management
├── 🔧 ops/                        # ✅ Operations & infrastructure
│   ├── infrastructure/           # ✅ Infrastructure as code
│   ├── monitoring/               # ✅ Platform monitoring
│   ├── security/                 # ✅ Security management
│   ├── compliance/               # ✅ Regulatory compliance
│   └── disaster-recovery/        # ✅ DR & backup procedures
├── 📊 data/                       # ✅ Analytics & business intelligence
│   ├── analytics/                # ✅ Usage & performance data
│   ├── customer-feedback/        # ✅ Customer insights
│   ├── market-research/          # ✅ Market analysis
│   └── benchmarks/               # ✅ Performance benchmarks
└── [EXISTING PYTHON PACKAGES]    # ✅ OPERATIONAL Python monorepo
    ├── libs/                     # ✅ Python libraries (core, integrations, templates)
    ├── apps/                     # ✅ Applications (symphony-cli)
    ├── platform/                # ✅ Live agent implementations
    └── tests/                    # ✅ Test infrastructure
```

### **🔧 Modern Tooling Integration** 
✅ **UV Workspace**: 10-100x faster dependency management  
✅ **Universal CLI**: Single command interface (`./tools/symphony`)  
✅ **Semantic Structure**: All directories with README documentation  
✅ **Hybrid Workflow**: Python packages + organizational structure  
🔄 **Future**: Pants build system, semantic release automation

## ⚡ **UNIVERSAL CLI - YOUR SINGLE COMMAND**

**CRITICAL**: Use `./tools/symphony` for ALL operations. This is your single interface to the entire monorepo.

### **Primary Command Patterns**
```bash
# Universal status and overview
./tools/symphony status

# Platform operations
./tools/symphony platform [build|test|deploy]

# Organization management (THE BUSINESS)
./tools/symphony org [create|deploy|list]

# Documentation operations
./tools/symphony docs [build|serve|publish]

# Business operations
./tools/symphony business [customers|analytics|sales]

# Development operations
./tools/symphony dev [workspace|validate|monitor]
```

## 🛠️ **DEVELOPMENT ENVIRONMENT**

### **UV Workspace Integration**
✅ **OPERATIONAL**: Symphony now uses UV workspaces for 10-100x faster dependency management.

**Setup Commands**:
```bash
# Check current status
./tools/symphony status

# Set up development environment
./tools/symphony dev workspace

# Validate monorepo integrity
./tools/symphony dev validate

# Build all packages
./tools/symphony platform build
```

### **Python Package Architecture**
```
libs/                              # Python libraries (workspace members)
├── symphony-core/                 # Core coordination engine
├── symphony-integrations/         # External tool integrations
└── symphony-templates/            # Template system

apps/                              # Applications (workspace members)  
└── symphony-cli/                  # Command line interface

Workspace Configuration:
├── pyproject.toml                 # Root workspace configuration
├── uv.lock                        # Dependency lock file
└── .venv/                         # Virtual environment
```

### **Modern Development Workflow**
1. **Environment Setup**: `./tools/symphony dev workspace`
2. **Development**: Work in `libs/` and `apps/` with hot reload
3. **Testing**: `./tools/symphony test`
4. **Building**: `./tools/symphony platform build`
5. **Validation**: `./tools/symphony dev validate`

### **Key Development Files**
- **`dev-setup.py`**: Legacy development setup (preserved)
- **`pyproject.toml`**: Modern workspace configuration with UV
- **Individual `pyproject.toml`**: Per-package configuration
- **`.venv/`**: Virtual environment managed by UV

## 👥 **ROLE-BASED WORKFLOWS**

### **👨‍💻 Platform Developer**
**Entry Point**: `/workspace/`
**Primary Commands**:
```bash
cd workspace/
./tools/symphony dev workspace
./tools/symphony dev validate
./tools/symphony platform build
./tools/symphony platform test
```
**Focus**: Core platform development, agent ecosystem, technical architecture

### **🏢 Customer Success Manager**
**Entry Point**: `/organizations/`
**Primary Commands**:
```bash
./tools/symphony business customers
./tools/symphony org create [customer] [type]
./tools/symphony org deploy [customer] [environment]
./tools/symphony dev monitor
```
**Focus**: Customer deployment, organization management, customer satisfaction

### **💼 Business Executive**
**Entry Point**: `/business/`
**Primary Commands**:
```bash
./tools/symphony business analytics
./tools/symphony business customers
./tools/symphony business sales
./tools/symphony status
```
**Focus**: Business performance, customer relationships, revenue operations

### **📚 Documentation Manager**
**Entry Point**: `/docs/`
**Primary Commands**:
```bash
./tools/symphony docs build
./tools/symphony docs publish external
./tools/symphony docs serve
```
**Focus**: Content management, customer-facing documentation, API documentation

### **🔧 Operations Team**
**Entry Point**: `/ops/`
**Primary Commands**:
```bash
./tools/symphony dev monitor
./tools/symphony platform deploy
./tools/symphony dev validate
```
**Focus**: Platform operations, infrastructure, monitoring, security

## 🚫 **ABSOLUTE RULES - NEVER VIOLATE**

### **Structure Integrity**
1. **NEVER** create directories outside the 12-tier monorepo structure
2. **ALWAYS** use the Universal CLI (`./tools/symphony`) for operations
3. **NEVER** break the documentation hierarchy (internal/external/api/partnerships)
4. **ALWAYS** maintain agent directory standards in `/core/agents/`
5. **ALWAYS** verify links work after any file moves

### **Documentation Hierarchy**
1. **Internal Documentation** → `/docs/internal/` (development team)
2. **External Documentation** → `/docs/external/` (customers)
3. **API Documentation** → `/docs/api/` (integrations)
4. **Partnership Documentation** → `/docs/partnerships/` (partners)

### **Conversation Management**
1. **ALWAYS** save important conversations to `/docs/internal/conversations/`
2. **Use timestamped format**: `[topic]-[YYYYMMDD-HHMMSS].md`
3. **Include complete context**: requirements, decisions, outcomes

### **Customer Operations**
1. **Customer organizations** → `/organizations/customers/[customer-id]/`
2. **Default packages** → `/organizations/defaults/[type]/`
3. **Business data** → `/business/` and `/data/`

## 📋 **MANDATORY REFERENCES**

### **First Load Always**
**CRITICAL**: Always load `docs/symphony-structure-guide.md` first in every Claude session.
This contains the complete organizational structure and must never be violated.

### **Key Reference Files**
- **Structure Guide**: `docs/symphony-structure-guide.md` (MANDATORY first reference)
- **Monorepo Overview**: `README.md` (comprehensive monorepo guide)
- **Documentation Hub**: `docs/README.md` (multi-audience documentation)
- **Universal CLI**: `tools/symphony` (single command interface)

## 🏢 **CUSTOMER & ORGANIZATION MANAGEMENT**

### **Organization Packages**
```yaml
Startup Package:    15 agents, $2K-8K/month, 1-2 week implementation
SMB Package:        35 agents, $15K-35K/month, 4-6 week implementation  
Enterprise Package: 65+ agents, $50K+/month, 12-16 week implementation
Global Package:     85+ agents, enterprise+ pricing, 20-24 week implementation
```

### **Customer Workflow**
```bash
# Create customer organization
./tools/symphony org create acme-corp enterprise healthcare

# Deploy to customer environment
./tools/symphony org deploy acme-corp production us-east-1

# Monitor customer health
./tools/symphony dev monitor
./tools/symphony business customers
```

### **Business Operations Integration**
- Customer relationship management in `/business/customers/`
- Sales pipeline tracking in `/business/sales/`
- Marketing and lead generation in `/business/marketing/`
- Business analytics in `/business/analytics/` and `/data/`

## 🛠️ **DEVELOPMENT & BUILD SYSTEM**

### **Build Operations**
```bash
# Build core platform
./tools/symphony platform build

# Build organization packages
./tools/symphony org build [startup|smb|enterprise|global]

# Build documentation
./tools/symphony docs build [internal|external|api|all]
```

### **Validation & Monitoring**
```bash
# Validate monorepo integrity
./tools/symphony dev validate

# Monitor platform health
./tools/symphony dev monitor [init|check|monitor]

# Check overall status
./tools/symphony status
```

## 📚 **DOCUMENTATION MANAGEMENT**

### **Multi-Audience Publishing**
- **Internal** (`/docs/internal/`): Development team documentation
- **External** (`/docs/external/`): Customer-facing documentation
- **API** (`/docs/api/`): Technical integration documentation
- **Partnerships** (`/docs/partnerships/`): Partner resources

### **Documentation Commands**
```bash
# Build all documentation
./tools/symphony docs build

# Build specific audience
./tools/symphony docs build external

# Publish to external channels
./tools/symphony docs publish external

# Start local documentation server
./tools/symphony docs serve
```

## 🎯 **SUCCESS METRICS & VALIDATION**

### **Platform Excellence**
- **99.99%+ uptime** across all customer environments
- **<30 minutes** average decision response time
- **95%+ process automation** for routine operations
- **100% executive-ready** output quality

### **Business Performance**
- **10x operational efficiency** improvement for customers
- **60-80% cost reduction** in operational overhead
- **95%+ customer satisfaction** scores
- **3-18 month** ROI achievement timelines

### **Monorepo Health**
- All validation scripts pass (`./tools/symphony dev validate`)
- Universal CLI operational (`./tools/symphony status`)
- Documentation integrity maintained
- Customer deployment pipeline functional

## 🔄 **PROCESS OPTIMIZATION**

### **During Conversations**
Proactively identify and suggest adding to CLAUDE.md:
- Interesting scenarios that could be standardized
- Repeated tasks that could be automated  
- Workflow patterns that emerge during sessions
- Best practices discovered through iteration

### **Conversation Recording**
Save important conversations to `/docs/internal/conversations/` with:
- Complete context and requirements
- Implementation decisions and rationale
- Outcomes and success metrics
- Future considerations and next steps

### **Link Integrity**
**CRITICAL**: All internal links have been systematically verified and repaired.
- 12-tier monorepo structure maintained
- Documentation hierarchy functional
- Universal CLI operational
- Cross-references working

## ⚡ **QUICK REFERENCE**

### **Common Operations**
```bash
# Get full monorepo overview
./tools/symphony status

# Create and deploy customer
./tools/symphony org create [customer] [type] [industry]
./tools/symphony org deploy [customer] [environment] [region]

# Platform development
./tools/symphony dev workspace
./tools/symphony platform build
./tools/symphony dev validate

# Business operations
./tools/symphony business customers
./tools/symphony business analytics

# Documentation management
./tools/symphony docs build external
./tools/symphony docs publish
```

### **Role-Based Entry Points**
| Role | Entry | Command | Focus |
|------|-------|---------|-------|
| **Developer** | `/workspace/` | `symphony dev workspace` | Platform development |
| **Customer Success** | `/organizations/` | `symphony org create` | Customer deployment |
| **Business** | `/business/` | `symphony business customers` | Customer relationships |
| **Documentation** | `/docs/` | `symphony docs build` | Content management |
| **Operations** | `/ops/` | `symphony dev monitor` | Platform operations |

---

## 🎼 **THE META-IMPLEMENTATION**

**Remember**: This monorepo IS the Symphony Autonomous Enterprise. Every operation within this repository demonstrates Symphony's capabilities:

1. **Symphony agents will manage Symphony's business operations**
2. **Symphony orchestration will coordinate Symphony development**
3. **Symphony automation will deploy Symphony to customers**
4. **Symphony analytics will optimize Symphony performance**
5. **Symphony documentation will explain Symphony to the world**

This is the ultimate self-validating business model where Symphony proves its autonomous enterprise capabilities by being the autonomous enterprise that sells autonomous enterprises.

---

**This monorepo is the single source of truth and universal command center for the entire Symphony autonomous enterprise universe. Every operation should go through the Universal CLI and maintain the integrity of this comprehensive structure.**