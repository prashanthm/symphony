# 🎼 Core

Core Symphony platform components - the heart of the autonomous enterprise.

## Purpose
Central coordination hub for all Symphony platform functionality:
- Agent orchestration and coordination patterns  
- Governance frameworks and compliance systems
- Platform-wide standards and protocols
- Core business logic and operations

## Current Status
🔄 **Hybrid** - Core functionality exists in `libs/` and `platform/`, planned restructuring

## Current Core Components
The core functionality is currently distributed across:
- `libs/symphony-core/` - Core Python package with agent coordination
- `platform/agents/` - 85+ agent ecosystem implementations
- `platform/orchestration/` - Coordination patterns and handoff protocols
- `platform/governance/` - Standards, compliance, security boundaries

## Planned Structure
```
core/
├── agents/              # Agent ecosystem (migrate from platform/agents/)
├── orchestration/       # Coordination patterns (migrate from platform/orchestration/)  
├── governance/          # Governance and compliance (migrate from platform/governance/)
├── standards/           # Platform-wide standards and protocols
├── protocols/           # Communication and handoff protocols
└── foundation/          # Core foundational services
```

## Integration
- Works with Universal CLI: `./tools/symphony platform` operations
- Provides foundation for `organizations/` customer deployments
- Interfaces with `business/` operations and analytics
- Supports `ops/` infrastructure and monitoring

## Migration Plan
1. **Phase 1**: Create new `core/` structure alongside existing `libs/` and `platform/`
2. **Phase 2**: Gradually migrate functionality from `platform/` to `core/`
3. **Phase 3**: Restructure `libs/symphony-core` to integrate with new `core/` structure
4. **Phase 4**: Update all references and documentation

## Next Steps
1. Define migration strategy for existing platform components
2. Create governance framework for core component management
3. Establish protocols for core-to-organization deployment
4. Implement monitoring and health checks for core components