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

