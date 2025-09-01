#!/bin/bash

# Symphony Platform Agent Loader
# Load operational agents into Claude Code for live coordination

echo "🎼 Symphony Platform Agent Loader"
echo "================================="

# Set Symphony root directory
SYMPHONY_ROOT="/Users/pmuniraju/play/sandbox/symphony"
PLATFORM_DIR="$SYMPHONY_ROOT/platform"

echo "Symphony Root: $SYMPHONY_ROOT"
echo "Platform Directory: $PLATFORM_DIR"

# Check if platform directory exists
if [ ! -d "$PLATFORM_DIR" ]; then
    echo "❌ Platform directory not found: $PLATFORM_DIR"
    exit 1
fi

echo ""
echo "📁 Available Agent Categories:"
echo "├── coordinators/  - Business coordination agents"
echo "├── leads/         - Technical leadership agents"  
echo "├── managers/      - Management tier agents"
echo "├── specialists/   - Domain specialist agents"
echo "└── maestro/       - Ultimate coordination agent"

echo ""
echo "🚀 Agent Loading Status:"

# Load coordinators
if [ -d "$PLATFORM_DIR/agents/coordinators" ]; then
    COORD_COUNT=$(find "$PLATFORM_DIR/agents/coordinators" -maxdepth 1 -type d | wc -l | xargs)
    echo "✅ Coordinators: $((COORD_COUNT - 1)) agents available"
else
    echo "⚠️  Coordinators: Directory not found"
fi

# Load leads  
if [ -d "$PLATFORM_DIR/agents/leads" ]; then
    LEADS_COUNT=$(find "$PLATFORM_DIR/agents/leads" -maxdepth 1 -type d | wc -l | xargs)
    echo "✅ Leads: $((LEADS_COUNT - 1)) agents available"
else
    echo "⚠️  Leads: Directory not found"
fi

# Load managers
if [ -d "$PLATFORM_DIR/agents/managers" ]; then
    MGRS_COUNT=$(find "$PLATFORM_DIR/agents/managers" -maxdepth 1 -type d | wc -l | xargs)
    echo "✅ Managers: $((MGRS_COUNT - 1)) agents available"
else
    echo "⚠️  Managers: Directory not found"
fi

# Load specialists
if [ -d "$PLATFORM_DIR/agents/specialists" ]; then
    SPEC_COUNT=$(find "$PLATFORM_DIR/agents/specialists" -maxdepth 1 -type d | wc -l | xargs)
    echo "✅ Specialists: $((SPEC_COUNT - 1)) agents available"
else
    echo "⚠️  Specialists: Directory not found"
fi

# Load maestro
if [ -d "$PLATFORM_DIR/agents/maestro" ]; then
    MAESTRO_COUNT=$(find "$PLATFORM_DIR/agents/maestro" -maxdepth 1 -type d | wc -l | xargs)
    echo "✅ Maestro: $((MAESTRO_COUNT - 1)) agents available"
else
    echo "⚠️  Maestro: Directory not found"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Add agent implementations to platform/agents/"
echo "2. Configure agent coordination in platform/orchestration/"
echo "3. Set governance standards in platform/governance/"
echo "4. Use Symphony CLI: symphony agent status"

echo ""
echo "📋 Agent Implementation Status: Setting up framework..."