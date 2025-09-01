#!/bin/bash

# Conversation Export Helper
# Save Claude Code conversation with context

TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
CONVERSATIONS_DIR="claude-protection/conversations"
TOPIC=${1:-"session"}

mkdir -p "$CONVERSATIONS_DIR"

CONVERSATION_FILE="$CONVERSATIONS_DIR/$TIMESTAMP-$TOPIC.md"

echo "# Claude Code Session: $TIMESTAMP - $TOPIC" > "$CONVERSATION_FILE"
echo "" >> "$CONVERSATION_FILE"
echo "## Session Information" >> "$CONVERSATION_FILE"
echo "- **Date**: $(date)" >> "$CONVERSATION_FILE"
echo "- **Project**: $(basename $(pwd))" >> "$CONVERSATION_FILE"
echo "- **Topic**: $TOPIC" >> "$CONVERSATION_FILE"
echo "" >> "$CONVERSATION_FILE"
echo "## Session Objectives" >> "$CONVERSATION_FILE"
echo "- [ ] [Describe what you plan to accomplish]" >> "$CONVERSATION_FILE"
echo "" >> "$CONVERSATION_FILE"
echo "## Changes Made" >> "$CONVERSATION_FILE"
echo "- [ ] [Document all changes as they happen]" >> "$CONVERSATION_FILE"
echo "" >> "$CONVERSATION_FILE"
echo "## Decisions and Reasoning" >> "$CONVERSATION_FILE"
echo "- [ ] [Record decision rationale]" >> "$CONVERSATION_FILE"
echo "" >> "$CONVERSATION_FILE"
echo "## Outcomes" >> "$CONVERSATION_FILE"
echo "- [ ] [Document final results]" >> "$CONVERSATION_FILE"
echo "" >> "$CONVERSATION_FILE"
echo "## Next Steps" >> "$CONVERSATION_FILE"
echo "- [ ] [Note follow-up work needed]" >> "$CONVERSATION_FILE"

echo "✅ Conversation template created: $CONVERSATION_FILE"
echo ""
echo "📝 Remember to:"
echo "1. Fill in session objectives at the start"
echo "2. Document changes as you make them"
echo "3. Record decision reasoning"
echo "4. Note outcomes and next steps"
echo ""
echo "💡 Add this to your Claude conversation for reference!"

