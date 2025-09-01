Claude Configuration for Symphony Autonomous Enterprise Platform
🎯 MANDATORY FIRST REFERENCE
CRITICAL: Always load docs/symphony-structure-guide.md first in every Claude session.

This file contains the complete organizational structure that must NEVER be violated.

📁 Project Structure Overview
symphony/
├── docs/                           # Pure human documentation
├── platform/                      # Core operational components  
├── templates/                      # Development scaffolding
└── solutions/                      # Industry & deployment specific
🎼 Symphony Context
Project: Symphony Autonomous Enterprise Platform
Purpose: AI agent coordination system for autonomous enterprises
Architecture: 4-tier scale-aware structure
Documentation: 5-category hierarchy (36+ dirs → 5 logical categories)
Agent Ecosystem: 85,300+ tokens across 25+ agents
Scale Target: Thousands of agents across multiple industries
🚫 ABSOLUTE RULES
ALWAYS reference docs/symphony-structure-guide.md first
NEVER create directories outside the 4-tier structure
NEVER break the 5-category documentation hierarchy
ALWAYS maintain agent directory standards
ALWAYS verify links work after any file moves
⚙️ Key Operational Components
Platform (/platform/)
Agents: Live agent implementations in /platform/agents/
Orchestration: Coordination patterns in /platform/orchestration/
Governance: Standards and compliance in /platform/governance/
Load Script: Use /platform/load-agents.sh to load agents into Claude Code
Documentation (/docs/)
Structure Guide: symphony-structure-guide.md (MANDATORY reference)
Main Navigation: README.md (master navigation hub)
Platform Docs: autonomous-enterprise/ (5-category hierarchy)
Development (/templates/)
Agent Templates: Scaffolding tools in /templates/agent-templates/
Enterprise Setup: Organization setup in /templates/enterprise-setup/
Customization: Frameworks in /templates/customization/
🔗 Link Integrity Status
✅ All internal links systematically verified and working

36+ scattered directories consolidated into logical organization
12+ broken relative path references fixed during reorganization
0 broken links remaining - full navigation functionality restored
🏆 Reorganization Achievement
This project has been completely reorganized from chaos to scale-ready architecture:

Before: 36+ scattered directories with broken navigation
After: 4-tier structure with 5-category documentation hierarchy
Status: ✅ COMPLETE - Ready for autonomous enterprise scale
📝 Prompt Management
When user requests a prompt, automatically save it as a timestamped file in /claude/prompts/ directory with format: [topic]-[YYYYMMDD-HHMMSS].md

🔄 Process Optimization
During conversations, proactively identify and suggest adding to CLAUDE.md:

Interesting scenarios that could be standardized
Repeated tasks that could be automated
Workflow patterns that emerge during sessions
Best practices discovered through iteration
Remember: This structure is the operational foundation for Symphony's autonomous enterprise platform. Any violations will break agent coordination, documentation integrity, and platform scalability.