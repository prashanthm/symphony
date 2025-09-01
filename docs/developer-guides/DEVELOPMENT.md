# Symphony Development Guide
*Getting started with Symphony monorepo development*

---

## 🚀 **Quick Start**

### **1. Clone and Setup**
```bash
# Navigate to Symphony directory
cd /Users/pmuniraju/play/sandbox/symphony

# Install all packages in development mode
python setup.py

# Setup environment configuration
cp .env.example .env
# Edit .env and add your API tokens

# Verify installation
symphony --version
symphony status
```

### **2. Development Environment**
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
black libs/ apps/
isort libs/ apps/

# Type checking
mypy libs/symphony-core/src/
```

---

## 📁 **Monorepo Structure**

```
symphony/
├── apps/                               # Deployable applications
│   └── symphony-cli/                   # Command line interface
├── libs/                               # Reusable libraries
│   ├── symphony-core/                  # Core functionality
│   ├── symphony-integrations/          # External tool integrations
│   └── symphony-templates/             # Template system
├── tests/                              # Test suites
├── configs/                            # Configuration files
└── docs/                               # Documentation
```

---

## 🔧 **Development Workflow**

### **Adding New Features**

1. **Create Linear Issue**: All development starts with a Linear issue
2. **Create Branch**: `git checkout -b feature/linear-123-description`
3. **Develop**: Make changes in appropriate package
4. **Test**: Run tests for affected packages
5. **Commit**: Reference Linear issue in commit message
6. **Pull Request**: Create PR with Linear issue reference

### **Package Development**

#### **Core Library** (`libs/symphony-core/`)
```bash
# Work on core functionality
cd libs/symphony-core/

# Install in development mode
pip install -e .

# Run tests
pytest tests/

# Core handles: agents, coordination, processors, utilities
```

#### **Integrations Library** (`libs/symphony-integrations/`)
```bash
# Work on tool integrations
cd libs/symphony-integrations/

# Install in development mode
pip install -e .

# Test integrations
pytest tests/

# Integrations handle: Linear, GitHub, Slack, etc.
```

#### **CLI Application** (`apps/symphony-cli/`)
```bash
# Work on CLI interface
cd apps/symphony-cli/

# Install in development mode
pip install -e .

# Test CLI commands
symphony --help
symphony status

# CLI provides: user interface for all Symphony functionality
```

---

## 📋 **Linear + GitHub Integration Workflow**

### **From Linear Issue to Code**

1. **Linear Issue Created**
   - Issue: "Build Symphony Linear template system"
   - ID: LIN-123
   - Assigned to developer

2. **Branch Creation**
   ```bash
   git checkout -b feature/lin-123-linear-template-system
   ```

3. **Development**
   - Code changes in appropriate packages
   - Tests for new functionality
   - Documentation updates

4. **GitHub Integration**
   ```bash
   # Commit with Linear reference
   git commit -m "feat: build Linear template system (LIN-123)
   
   - Add template processor for Linear workspaces
   - Implement Symphony organizational hierarchy mapping
   - Add CLI commands for template deployment
   
   Fixes LIN-123"
   
   # Push and create PR
   git push -u origin feature/lin-123-linear-template-system
   gh pr create --title "Build Symphony Linear template system (LIN-123)" --body "..."
   ```

5. **Code Review & Merge**
   - PR review process
   - Linear issue automatically updated
   - Merge to main branch

---

## 🧪 **Testing Strategy**

### **Test Structure**
```
tests/
├── unit/                               # Unit tests
│   ├── core/                          # Core library tests
│   ├── integrations/                  # Integration tests
│   └── cli/                           # CLI tests
├── integration/                       # Integration tests
│   ├── linear_api/                    # Linear API integration tests
│   └── github_api/                    # GitHub API integration tests
├── e2e/                               # End-to-end tests
│   └── full_workflow/                 # Complete workflow tests
└── fixtures/                          # Test data and fixtures
```

### **Running Tests**
```bash
# All tests
pytest

# Specific package
pytest tests/unit/core/
pytest tests/unit/integrations/

# With coverage
pytest --cov=symphony_core --cov=symphony_integrations

# Integration tests (requires API tokens)
pytest tests/integration/ --slow
```

---

## 🔗 **API Integration Development**

### **Linear Integration**
```python
# Development with Linear API
from symphony_integrations.linear import LinearAPIClient

async def test_linear_integration():
    async with LinearAPIClient() as client:
        teams = await client.get_teams()
        print(f"Found {len(teams)} teams")
```

### **GitHub Integration**
```python
# Development with GitHub API
from symphony_integrations.github import GitHubAPIClient

client = GitHubAPIClient()
repo = client.create_repository("test-repo", private=True)
```

---

## 📦 **Package Management**

### **Dependencies**
- **Root Level**: Common dependencies in `pyproject.toml`
- **Package Level**: Specific dependencies in each `setup.py`
- **Development**: Dev dependencies in `pyproject.toml`

### **Adding Dependencies**
```bash
# Add to specific package
cd libs/symphony-core/
# Edit setup.py install_requires

# Add development dependency
# Edit pyproject.toml [project.optional-dependencies] dev section

# Reinstall in development mode
pip install -e .
```

### **Building Packages**
```bash
# Build individual packages
python -m build libs/symphony-core/
python -m build apps/symphony-cli/

# Install built packages
pip install dist/symphony_core-*.whl
```

---

## 🎯 **Best Practices**

### **Code Style**
- Use `black` for formatting
- Use `isort` for import sorting
- Follow PEP 8 naming conventions
- Add type hints for all functions
- Write docstrings for all public functions

### **Git Workflow**
- Always reference Linear issues in commits
- Use conventional commit messages
- Create small, focused PRs
- Write descriptive PR descriptions
- Review code before merging

### **Testing**
- Write tests for all new functionality
- Maintain test coverage above 80%
- Use fixtures for test data
- Mock external API calls in unit tests
- Test error conditions

### **Documentation**
- Update README.md for significant changes
- Add docstrings for all public APIs
- Update DEVELOPMENT.md for workflow changes
- Keep architecture documentation current

---

## 🐛 **Debugging**

### **Common Issues**
```bash
# Import errors
export PYTHONPATH=/path/to/symphony:$PYTHONPATH

# Package not found
pip install -e libs/symphony-core/

# API authentication
symphony setup env
# Check .env file has correct tokens

# CLI not working
pip install -e apps/symphony-cli/
# Verify entry point installed correctly
```

### **Development Tools**
```bash
# Interactive debugging
python -m pdb script.py

# Rich logging
export LOG_LEVEL=DEBUG

# Test with verbose output
pytest -v -s
```

---

This development guide provides the foundation for disciplined development using the monorepo structure with Linear + GitHub integration workflow.