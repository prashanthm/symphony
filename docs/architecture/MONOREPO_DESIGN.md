# Symphony Monorepo Architecture Design
*Clean, scalable monorepo structure for Symphony autonomous enterprise platform*

---

## 🎯 **Design Principles**

1. **Clear Separation of Concerns**: Apps, Libraries, Tools, Configurations
2. **Scalable Package Management**: Python packages with proper dependencies
3. **CI/CD Ready**: Structure supports automated testing and deployment
4. **Linear + GitHub Integration**: Repository structure aligned with issue tracking
5. **Development Workflow**: Clear development, testing, and deployment paths

---

## 📁 **New Monorepo Structure**

```
symphony/
├── README.md                           # Main repository README
├── CONTRIBUTING.md                     # Development workflow and guidelines
├── pyproject.toml                      # Python project configuration
├── requirements.txt                    # Root dependencies
├── .github/                            # GitHub workflows and templates
│   ├── workflows/                      # CI/CD pipelines
│   ├── ISSUE_TEMPLATE/                 # Linear integration templates
│   └── PULL_REQUEST_TEMPLATE.md        # PR template
├── .env.example                        # Environment configuration template
├── .gitignore                          # Git ignore rules
│
├── apps/                               # Deployable applications
│   ├── symphony-cli/                   # Command line interface
│   │   ├── src/symphony_cli/           # CLI source code
│   │   ├── requirements.txt            # CLI dependencies
│   │   └── setup.py                    # CLI package setup
│   ├── api-server/                     # Symphony API server
│   │   ├── src/symphony_api/           # API source code
│   │   ├── requirements.txt            # API dependencies
│   │   └── Dockerfile                  # API container
│   └── web-dashboard/                  # Web interface (if needed)
│
├── libs/                               # Reusable libraries
│   ├── symphony-core/                  # Core Symphony functionality
│   │   ├── src/symphony_core/          # Core library code
│   │   │   ├── __init__.py
│   │   │   ├── agents/                 # Agent system
│   │   │   ├── coordination/           # Agent coordination
│   │   │   ├── integrations/           # External tool integrations
│   │   │   └── processors/             # Configuration processors
│   │   ├── requirements.txt            # Core dependencies
│   │   └── setup.py                    # Core package setup
│   ├── symphony-integrations/          # Integration libraries
│   │   ├── src/symphony_integrations/  # Integration code
│   │   │   ├── __init__.py
│   │   │   ├── linear/                 # Linear API integration
│   │   │   ├── github/                 # GitHub API integration
│   │   │   ├── slack/                  # Slack integration
│   │   │   └── common/                 # Common integration utilities
│   │   ├── requirements.txt            # Integration dependencies
│   │   └── setup.py                    # Integration package setup
│   └── symphony-templates/             # Template system
│       ├── src/symphony_templates/     # Template processing
│       ├── templates/                  # Template files
│       │   ├── linear-workspaces/      # Linear workspace templates
│       │   ├── github-repos/           # GitHub repository templates
│       │   └── enterprise-setups/      # Complete enterprise setups
│       ├── requirements.txt            # Template dependencies
│       └── setup.py                    # Template package setup
│
├── tools/                              # Development and operational tools
│   ├── scripts/                        # Utility scripts
│   ├── validators/                     # Configuration validators
│   ├── generators/                     # Code and config generators
│   └── deployment/                     # Deployment automation
│
├── docs/                               # Documentation
│   ├── api/                           # API documentation
│   ├── user-guides/                   # User documentation
│   ├── developer-guides/              # Developer documentation
│   ├── architecture/                  # System architecture docs
│   └── examples/                      # Usage examples
│
├── tests/                              # Test suites
│   ├── unit/                          # Unit tests
│   ├── integration/                   # Integration tests
│   ├── e2e/                           # End-to-end tests
│   └── fixtures/                      # Test data and fixtures
│
├── configs/                            # Configuration files
│   ├── environments/                   # Environment-specific configs
│   ├── templates/                      # Configuration templates
│   └── schemas/                        # Configuration schemas
│
└── data/                               # Data and assets
    ├── examples/                       # Example data
    ├── schemas/                        # Data schemas
    └── migrations/                     # Data migrations
```

---

## 📦 **Package Management Strategy**

### **Root Level** (`pyproject.toml`)
```toml
[project]
name = "symphony"
version = "0.1.0"
description = "Symphony Autonomous Enterprise Platform"
readme = "README.md"
requires-python = ">=3.9"

[project.optional-dependencies]
dev = ["pytest", "black", "flake8", "mypy"]
cli = ["symphony-cli"]
api = ["symphony-api"]
all = ["symphony-cli", "symphony-api", "symphony-core", "symphony-integrations"]

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["libs/*/src", "apps/*/src"]
```

### **Individual Package Setup** (example: `libs/symphony-core/setup.py`)
```python
from setuptools import setup, find_packages

setup(
    name="symphony-core",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "asyncio",
    ],
    extras_require={
        "dev": ["pytest", "pytest-asyncio"],
    },
    python_requires=">=3.9",
)
```

---

## 🔄 **Migration Plan**

### **Phase 1: Create New Structure**
1. Create new monorepo directory structure
2. Set up package management configuration
3. Initialize proper Python packages

### **Phase 2: Migrate Existing Code**
```bash
# Current → New location mapping
core/integrations/linear-api-client.py → libs/symphony-integrations/src/symphony_integrations/linear/
core/integrations/github-api-client.py → libs/symphony-integrations/src/symphony_integrations/github/
core/integrations/linear-cli.py → apps/symphony-cli/src/symphony_cli/commands/linear.py
core/integrations/github-cli.py → apps/symphony-cli/src/symphony_cli/commands/github.py
core/utils/env_loader.py → libs/symphony-core/src/symphony_core/utils/env_loader.py
core/processors/config-processor.py → libs/symphony-core/src/symphony_core/processors/config.py
tools/symphony → apps/symphony-cli/src/symphony_cli/main.py
```

### **Phase 3: Update Import Paths**
- Update all import statements to use new package structure
- Fix relative imports and dependencies
- Update CLI entry points

### **Phase 4: Configure Development Environment**
- Set up development dependencies
- Configure testing framework
- Set up CI/CD pipelines

---

## 🛠 **Development Workflow**

### **Local Development Setup**
```bash
# Clone and setup
git clone <symphony-repo>
cd symphony

# Install in development mode
pip install -e .
pip install -e ".[dev]"

# Install individual packages
pip install -e libs/symphony-core/
pip install -e libs/symphony-integrations/
pip install -e apps/symphony-cli/
```

### **Testing**
```bash
# Run all tests
pytest tests/

# Run specific package tests
pytest libs/symphony-core/tests/
pytest libs/symphony-integrations/tests/
```

### **Building and Deployment**
```bash
# Build all packages
python -m build libs/symphony-core/
python -m build libs/symphony-integrations/
python -m build apps/symphony-cli/

# Install built packages
pip install dist/symphony_core-*.whl
```

---

## 🔗 **GitHub Integration**

### **Repository Structure**
- Single repository for entire Symphony platform
- Package-based organization enables focused development
- CI/CD pipelines handle testing and deployment of individual packages

### **Linear Integration**
- Issues can target specific packages/modules
- Labels can indicate affected components
- Branch naming convention: `feature/linear-123-description`

---

## 🎯 **Benefits of This Structure**

1. **Clear Ownership**: Each package has clear boundaries and responsibilities
2. **Independent Development**: Teams can work on different packages simultaneously
3. **Reusable Components**: Libraries can be shared across applications
4. **Testing Strategy**: Each package can have its own test suite
5. **Deployment Flexibility**: Individual packages can be deployed independently
6. **Scalability**: New packages and applications can be added easily

---

This monorepo structure provides the foundation for disciplined development where every code change flows through Linear issues and GitHub integration, while maintaining clear package boundaries and enabling scalable development practices.