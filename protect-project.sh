#!/bin/bash

# Universal Project Protection Script
# Use with ANY Claude Code project to prevent disaster

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛡️  Universal Claude Code Project Protection${NC}"
echo "=================================================="

# Get project directory (current directory by default)
PROJECT_DIR=${1:-$(pwd)}
PROJECT_NAME=$(basename "$PROJECT_DIR")
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")

echo -e "${BLUE}Project:${NC} $PROJECT_NAME"
echo -e "${BLUE}Location:${NC} $PROJECT_DIR"
echo -e "${BLUE}Protection Time:${NC} $TIMESTAMP"
echo ""

# Create protection directory structure
PROTECTION_DIR="$PROJECT_DIR/claude-protection"
BACKUPS_DIR="$PROTECTION_DIR/backups"
CONVERSATIONS_DIR="$PROTECTION_DIR/conversations"
SNAPSHOTS_DIR="$PROTECTION_DIR/snapshots"

echo -e "${YELLOW}📁 Creating protection directories...${NC}"
mkdir -p "$BACKUPS_DIR" "$CONVERSATIONS_DIR" "$SNAPSHOTS_DIR"

# Create project snapshot
echo -e "${YELLOW}📸 Creating project snapshot...${NC}"
SNAPSHOT_FILE="$SNAPSHOTS_DIR/project-snapshot-$TIMESTAMP.tar.gz"

# Create comprehensive backup excluding protection directory itself
tar --exclude="$PROTECTION_DIR" \
    --exclude=".git" \
    --exclude="node_modules" \
    --exclude="*.log" \
    --exclude="*.tmp" \
    -czf "$SNAPSHOT_FILE" \
    -C "$PROJECT_DIR" .

echo -e "${GREEN}✅ Snapshot created:${NC} $SNAPSHOT_FILE"

# Create directory structure documentation
echo -e "${YELLOW}📋 Documenting project structure...${NC}"
STRUCTURE_FILE="$SNAPSHOTS_DIR/structure-$TIMESTAMP.txt"

# Document directory structure
echo "Project Structure - $TIMESTAMP" > "$STRUCTURE_FILE"
echo "=================================================" >> "$STRUCTURE_FILE"
echo "" >> "$STRUCTURE_FILE"
tree "$PROJECT_DIR" -I "claude-protection|.git|node_modules|*.log|*.tmp" >> "$STRUCTURE_FILE" 2>/dev/null || find "$PROJECT_DIR" -type d -not -path "*/claude-protection/*" -not -path "*/.git/*" -not -path "*/node_modules/*" | sort >> "$STRUCTURE_FILE"

echo -e "${GREEN}✅ Structure documented:${NC} $STRUCTURE_FILE"

# Create file inventory with sizes
echo -e "${YELLOW}📊 Creating file inventory...${NC}"
INVENTORY_FILE="$SNAPSHOTS_DIR/inventory-$TIMESTAMP.txt"

echo "File Inventory - $TIMESTAMP" > "$INVENTORY_FILE"
echo "=================================================" >> "$INVENTORY_FILE"
echo "" >> "$INVENTORY_FILE"

find "$PROJECT_DIR" -type f \
    -not -path "*/claude-protection/*" \
    -not -path "*/.git/*" \
    -not -path "*/node_modules/*" \
    -not -name "*.log" \
    -not -name "*.tmp" \
    -exec ls -lh {} \; >> "$INVENTORY_FILE"

echo -e "${GREEN}✅ Inventory created:${NC} $INVENTORY_FILE"

# Check for existing project identity
IDENTITY_FILE="$PROJECT_DIR/PROJECT-IDENTITY.md"
if [ ! -f "$IDENTITY_FILE" ]; then
    echo -e "${YELLOW}⚠️  Creating PROJECT-IDENTITY.md template...${NC}"
    
    cat > "$IDENTITY_FILE" << 'EOF'
# Project Identity & Protection Framework
**🚨 CRITICAL PROJECT PROTECTION DOCUMENT - READ FIRST IN EVERY CLAUDE SESSION 🚨**

---

## 🎯 **PROJECT IDENTITY**

**Project Name**: [PROJECT_NAME]
**Development Time**: [Estimate development time invested]
**Business Value**: [Estimate business or personal value]
**Intellectual Property**: [Describe key components and their importance]
**Recovery Status**: [Note any previous disasters or clean recovery state]

---

## 🚨 **DISASTER PREVENTION**

### **NEVER DELETE WITHOUT**
1. Reading this document completely
2. Creating backup using ./protect-project.sh
3. Following PROTECTION-CHECKLIST.md
4. Getting explicit user approval
5. Testing rollback capability

### **🚫 ABSOLUTELY PROTECTED DIRECTORIES**
```
[List your critical directories here - update based on project]
project/
├── src/                    # 🔒 PROTECTED: Core source code
├── docs/                   # 🔒 PROTECTED: Documentation
├── config/                 # 🔒 PROTECTED: Configuration
├── data/                   # 🔒 PROTECTED: Important data
└── claude-protection/      # 🔒 PROTECTED: Backup system
```

---

## 📋 **PROTECTION STATUS**

- **Backup System**: ✅ Active (./protect-project.sh)
- **Conversation Export**: ✅ Active (claude-protection/conversations/)
- **Project Snapshots**: ✅ Active (claude-protection/snapshots/)
- **Protection Checklist**: ✅ Available (PROTECTION-CHECKLIST.md)

---

## 🎯 **SUCCESS CRITERIA**

- **Zero Data Loss**: No accidental deletion of critical components
- **Complete Traceability**: Every change documented and reversible
- **User Control**: Explicit confirmation required for structural changes
- **Rapid Recovery**: Complete project restoration within 1 hour

---

**🔒 PROJECT PROTECTION STATUS: ACTIVE**
**📅 Last Updated**: [DATE]
**🛡️ Protection Level**: MAXIMUM SECURITY
EOF

    # Replace placeholder with actual project name
    sed -i.bak "s/\[PROJECT_NAME\]/$PROJECT_NAME/g" "$IDENTITY_FILE"
    rm "$IDENTITY_FILE.bak" 2>/dev/null || true
    
    echo -e "${GREEN}✅ PROJECT-IDENTITY.md created:${NC} $IDENTITY_FILE"
else
    echo -e "${GREEN}✅ PROJECT-IDENTITY.md exists:${NC} $IDENTITY_FILE"
fi

# Check for protection checklist
CHECKLIST_FILE="$PROJECT_DIR/PROTECTION-CHECKLIST.md"
if [ ! -f "$CHECKLIST_FILE" ]; then
    echo -e "${YELLOW}⚠️  Creating PROTECTION-CHECKLIST.md...${NC}"
    
    cat > "$CHECKLIST_FILE" << 'EOF'
# Protection Checklist - Claude Code Session Safeguards
**🚨 MANDATORY CHECKLIST - USE BEFORE EVERY STRUCTURAL CHANGE 🚨**

## 📋 **PRE-SESSION CHECKLIST**

**☐ 1. Read Project Identity**
- [ ] Read `PROJECT-IDENTITY.md` to understand project value
- [ ] Review protected components and disaster history

**☐ 2. Export Conversation**
- [ ] Save conversation to `claude-protection/conversations/`
- [ ] Include session objectives and scope

**☐ 3. Verify Structure**
- [ ] Confirm all protected directories intact
- [ ] Check critical files present and uncorrupted

## 🚨 **PRE-DELETION CHECKLIST**

**☐ 1. IMPACT ASSESSMENT**
- [ ] What exactly will be deleted/moved/changed?
- [ ] How much development time does this represent?
- [ ] What business or personal value is at risk?

**☐ 2. BACKUP VERIFICATION**
- [ ] Run `./protect-project.sh` to create fresh backup
- [ ] Verify backup complete and restorable
- [ ] Test restoration procedure

**☐ 3. USER APPROVAL**
- [ ] Show user EXACTLY what will be changed/deleted
- [ ] Explain risks and recovery options
- [ ] Get explicit written confirmation

**☐ 4. PROCEED WITH CAUTION**
- [ ] Make changes incrementally
- [ ] Test after each step
- [ ] Document all actions taken

## 🔍 **RISK LEVELS**

- **🟢 SAFE**: Creating files, editing content
- **🟡 CAUTION**: Moving files, renaming directories
- **🔴 DANGER**: Deleting directories, major reorganization
- **💀 CATASTROPHIC**: Mass deletion, "cleanup" operations

## 🚨 **EMERGENCY STOP**

**Stop immediately if:**
- Unexpected errors occur
- Functionality breaks
- Data loss detected
- Scope larger than planned

**Recovery:**
1. Stop all changes
2. Restore from backup
3. Validate restoration
4. Analyze what happened
5. Update protection

---

**Use this checklist religiously. Every check prevents disaster.**
EOF
    
    echo -e "${GREEN}✅ PROTECTION-CHECKLIST.md created:${NC} $CHECKLIST_FILE"
else
    echo -e "${GREEN}✅ PROTECTION-CHECKLIST.md exists:${NC} $CHECKLIST_FILE"
fi

# Create quick restore script
echo -e "${YELLOW}🔧 Creating restore script...${NC}"
RESTORE_SCRIPT="$PROJECT_DIR/restore-project.sh"

cat > "$RESTORE_SCRIPT" << 'EOF'
#!/bin/bash

# Quick Project Restore Script
# Restore from the most recent backup

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR=$(pwd)
SNAPSHOTS_DIR="claude-protection/snapshots"

echo -e "${RED}🚨 PROJECT RESTORE${NC}"
echo "=================================================="

if [ ! -d "$SNAPSHOTS_DIR" ]; then
    echo -e "${RED}❌ No snapshots directory found!${NC}"
    echo "Run ./protect-project.sh first to create backups."
    exit 1
fi

# Find most recent snapshot
LATEST_SNAPSHOT=$(ls -t "$SNAPSHOTS_DIR"/project-snapshot-*.tar.gz 2>/dev/null | head -n 1)

if [ -z "$LATEST_SNAPSHOT" ]; then
    echo -e "${RED}❌ No snapshots found!${NC}"
    exit 1
fi

echo -e "${YELLOW}Latest snapshot:${NC} $LATEST_SNAPSHOT"
echo ""
echo -e "${RED}⚠️  WARNING: This will restore the entire project to the snapshot state!${NC}"
echo -e "${RED}⚠️  Current changes will be lost!${NC}"
echo ""
read -p "Are you sure you want to restore? (type 'YES' to confirm): " CONFIRM

if [ "$CONFIRM" != "YES" ]; then
    echo -e "${YELLOW}Restore cancelled.${NC}"
    exit 0
fi

echo -e "${YELLOW}🔄 Restoring project...${NC}"

# Create backup of current state before restore
CURRENT_BACKUP="claude-protection/pre-restore-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
echo -e "${YELLOW}📦 Backing up current state...${NC}"
tar --exclude="claude-protection" -czf "$CURRENT_BACKUP" . 2>/dev/null || true

# Restore from snapshot (exclude protection directory)
echo -e "${YELLOW}📤 Extracting snapshot...${NC}"
tar --exclude="claude-protection" -xzf "$LATEST_SNAPSHOT" -C "$PROJECT_DIR"

echo -e "${GREEN}✅ Project restored successfully!${NC}"
echo -e "${BLUE}Previous state backed up to:${NC} $CURRENT_BACKUP"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Verify project functionality"
echo "2. Test critical features"
echo "3. Run ./protect-project.sh to create new backup"

EOF

chmod +x "$RESTORE_SCRIPT"
echo -e "${GREEN}✅ Restore script created:${NC} $RESTORE_SCRIPT"

# Create conversation export helper
echo -e "${YELLOW}💬 Creating conversation export helper...${NC}"
EXPORT_SCRIPT="$PROJECT_DIR/export-conversation.sh"

cat > "$EXPORT_SCRIPT" << 'EOF'
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

EOF

chmod +x "$EXPORT_SCRIPT"
echo -e "${GREEN}✅ Export script created:${NC} $EXPORT_SCRIPT"

# Display protection summary
echo ""
echo -e "${GREEN}🎉 PROJECT PROTECTION COMPLETE!${NC}"
echo "=================================================="
echo -e "${BLUE}Protection Level:${NC} Maximum Security"
echo -e "${BLUE}Snapshot Size:${NC} $(ls -lh "$SNAPSHOT_FILE" | awk '{print $5}')"
echo -e "${BLUE}Files Protected:${NC} $(wc -l < "$INVENTORY_FILE") files"
echo ""
echo -e "${YELLOW}📋 Quick Commands:${NC}"
echo "  ./protect-project.sh          # Create new backup"
echo "  ./restore-project.sh          # Restore from backup"
echo "  ./export-conversation.sh      # Export conversation"
echo ""
echo -e "${YELLOW}📚 Next Steps:${NC}"
echo "1. Read PROJECT-IDENTITY.md before any changes"
echo "2. Use PROTECTION-CHECKLIST.md for structural changes"
echo "3. Export conversations regularly"
echo "4. Create backups before major changes"
echo ""
echo -e "${RED}🚨 REMEMBER:${NC} This system prevents disasters like the Symphony cleanup catastrophe."
echo -e "${RED}   Use it religiously with every Claude Code project!${NC}"

exit 0