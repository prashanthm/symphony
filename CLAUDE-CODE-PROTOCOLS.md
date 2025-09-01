# Claude Code Session Protocols
**MANDATORY protocols to prevent disasters and ensure productive sessions**

---

## 🎯 **PURPOSE**

These protocols prevent disasters like the Symphony cleanup catastrophe and ensure every Claude Code session is productive, safe, and preserves valuable work. Use these protocols with EVERY Claude Code project.

---

## 🚀 **SESSION INITIALIZATION PROTOCOL**

### **MANDATORY Pre-Session Checklist**

**Every Claude Code session MUST begin with these steps:**

#### **Step 1: Project Identity Review** (2-3 minutes)
```markdown
☐ Read PROJECT-IDENTITY.md completely
☐ Understand project value and disaster history  
☐ Review protected components and their importance
☐ Check current project health status
```

#### **Step 2: Protection Verification** (2-3 minutes)
```markdown
☐ Confirm protection system is active
☐ Verify backup availability and currency
☐ Check that recovery scripts are executable
☐ Validate conversation export system working
```

#### **Step 3: Session Preparation** (3-5 minutes)
```markdown
☐ Export conversation start state: ./export-conversation.sh [topic]
☐ Create project snapshot: ./protect-project.sh
☐ Document session objectives and scope
☐ Set clear success criteria and boundaries
☐ Plan rollback approach if needed
```

#### **Step 4: Context Loading** (2-3 minutes)
```markdown
☐ Review recent conversation history
☐ Check memory index for relevant past sessions
☐ Understand current project state and recent changes
☐ Identify any dependencies or constraints
```

**Total initialization time: 10-15 minutes per session**

---

## 🛡️ **CHANGE ANALYSIS PROTOCOL**

### **Before ANY File System Changes**

#### **Step 1: Change Classification** (1-2 minutes)
```markdown
Risk Level Assessment:
☐ 🟢 SAFE: Creating files, editing content, documentation
☐ 🟡 CAUTION: Moving files, renaming, minor reorganization  
☐ 🔴 DANGER: Deleting directories, major restructuring
☐ 💀 CATASTROPHIC: Mass deletion, "cleanup" operations
```

#### **Step 2: Impact Analysis** (3-5 minutes)
```markdown
For CAUTION/DANGER/CATASTROPHIC changes:
☐ What exactly will be changed/deleted/moved?
☐ How much development time does this represent?
☐ What business/personal value is at risk?
☐ What dependencies might be affected?
☐ Are there non-obvious integrations that could break?
```

#### **Step 3: Protection Measures** (5-10 minutes)
```markdown
For DANGER/CATASTROPHIC changes:
☐ Create comprehensive backup: ./protect-project.sh
☐ Document current state and what will change
☐ Test backup restoration capability
☐ Show user EXACTLY what will be changed/deleted
☐ Get explicit written user confirmation
☐ Prepare detailed rollback plan
```

#### **Step 4: Implementation Approach** (Variable)
```markdown
☐ Make changes incrementally in small steps
☐ Test after each incremental change
☐ Document each step and its impact
☐ Verify functionality remains intact
☐ Be ready to stop and rollback at any sign of problems
```

---

## 🔄 **DECISION DOCUMENTATION PROTOCOL**

### **For Every Significant Decision**

#### **Decision Context** (2-3 minutes)
```markdown
☐ What problem or opportunity triggered this decision?
☐ What constraints or requirements must be considered?
☐ Who/what is affected by this decision?
☐ What information is available for decision-making?
```

#### **Options Analysis** (5-10 minutes)
```markdown
☐ Document at least 2-3 alternative approaches
☐ List pros/cons for each option
☐ Assess risks and implementation effort
☐ Consider long-term implications
```

#### **Decision Recording** (3-5 minutes)
```markdown
☐ Document chosen solution and clear rationale
☐ Note key factors that influenced the decision
☐ Record trade-offs accepted and assumptions made
☐ Save to conversations/decisions/[timestamp]-[topic].md
```

---

## 💬 **CONVERSATION EXPORT PROTOCOL**

### **During Session** (Ongoing)
```markdown
☐ Document key insights and decisions as they happen
☐ Record reasoning behind technical choices
☐ Note any problems encountered and how they were solved
☐ Capture user feedback and course corrections
```

### **End of Session** (5-10 minutes)
```markdown
☐ Update conversation file with final outcomes
☐ Document what was accomplished vs original objectives
☐ Note any remaining work or follow-up needed
☐ Record lessons learned and best practices discovered
☐ Update project memory index with session summary
```

### **Session Quality Check** (2-3 minutes)
```markdown
☐ Can someone else understand what was done and why?
☐ Is there enough information to continue work in next session?
☐ Are all major decisions explained with rationale?
☐ Would this information help in disaster recovery?
```

---

## 🚨 **EMERGENCY PROTOCOLS**

### **If Something Goes Wrong**

#### **Immediate Response** (< 1 minute)
```markdown
☐ STOP - Don't make the situation worse
☐ Assess the scope of the problem quickly
☐ Check if rollback is needed immediately
☐ Communicate situation to user clearly
```

#### **Damage Assessment** (2-5 minutes)
```markdown
☐ What exactly went wrong?
☐ What functionality or data was affected?
☐ How serious is the impact on project objectives?
☐ What backup/recovery options are available?
```

#### **Recovery Action** (Variable)
```markdown
☐ Choose appropriate recovery method based on damage
☐ Execute recovery using available backups or tools
☐ Validate that recovery was successful
☐ Test critical functionality to ensure no hidden issues
```

#### **Post-Incident** (5-10 minutes)
```markdown
☐ Document what happened and why
☐ Identify root cause and prevention measures
☐ Update protection systems based on lessons learned
☐ Communicate incident outcome and prevention steps to user
```

---

## 📊 **QUALITY ASSURANCE PROTOCOL**

### **Session Validation Checklist**

#### **Technical Quality** 
```markdown
☐ All changes tested and validated
☐ No broken functionality or integrations
☐ Code quality meets project standards
☐ Documentation updated for any changes
```

#### **Protection Quality**
```markdown
☐ Backup system used appropriately for risk level
☐ All structural changes approved by user
☐ Recovery capability tested and confirmed
☐ Emergency procedures available if needed
```

#### **Communication Quality**
```markdown
☐ User clearly understands what was done
☐ Rationale provided for all significant decisions
☐ Risks and trade-offs communicated honestly  
☐ Next steps and follow-up clearly defined
```

#### **Documentation Quality**
```markdown
☐ Session conversation exported with complete context
☐ Major decisions recorded with rationale
☐ Knowledge preserved for future sessions
☐ Memory index updated with session summary
```

---

## 🎯 **SESSION TYPES AND PROTOCOLS**

### **Routine Development Sessions**
- **Initialization**: Standard protocol (10-15 minutes)
- **Change Analysis**: Required for any file modifications
- **Documentation**: Standard conversation export
- **Protection**: Regular backup cadence

### **Architecture/Design Sessions** 
- **Initialization**: Extended context review (15-20 minutes)
- **Decision Documentation**: Comprehensive decision records required
- **User Involvement**: Higher approval threshold for decisions
- **Documentation**: Detailed analysis and rationale preservation

### **Emergency/Recovery Sessions**
- **Initialization**: Abbreviated (5-10 minutes) - focus on problem
- **Assessment**: Immediate damage analysis and response planning
- **Protection**: Enhanced backup before any recovery actions
- **Documentation**: Detailed incident record and lessons learned

### **"Cleanup" or Reorganization Sessions**
- **⚠️ HIGH RISK ALERT**: These sessions caused the Symphony disaster
- **Initialization**: MANDATORY comprehensive review (20+ minutes)
- **User Approval**: Required for EVERY structural change
- **Protection**: MAXIMUM - backup, test restore, document everything
- **Implementation**: Small incremental changes with testing

---

## 📋 **PROTOCOL COMPLIANCE VERIFICATION**

### **Self-Assessment Questions**

#### **Before Starting Work**
```markdown
☐ Have I read and understood the project identity?
☐ Do I know what components are critical and protected?
☐ Have I created appropriate backups for my planned changes?
☐ Do I have user approval for any structural modifications?
☐ Am I prepared to rollback if problems occur?
```

#### **During Work**
```markdown
☐ Am I documenting decisions and reasoning as I go?
☐ Am I testing changes incrementally to catch problems early?
☐ Am I staying within the scope I communicated to the user?
☐ Am I following the risk-appropriate protection measures?
```

#### **After Work**  
```markdown
☐ Have I validated that everything still works correctly?
☐ Have I documented what was accomplished and how?
☐ Have I preserved knowledge for future sessions?
☐ Have I updated protection systems with new project state?
```

---

## 🏆 **SUCCESS METRICS**

### **Protocol Effectiveness Indicators**
- **Zero data loss incidents** across all projects using these protocols
- **Complete session traceability** with full conversation archives
- **Successful project continuity** across multiple Claude sessions
- **User confidence** in Claude Code interactions
- **Rapid problem resolution** when issues do occur

### **Quality Benchmarks**
- **100% compliance** with initialization protocol
- **Complete documentation** for all significant decisions
- **User approval** for all structural changes  
- **Tested rollback capability** for all major modifications
- **Comprehensive conversation archives** enabling project reconstruction

---

## 🎼 **SYMPHONY-SPECIFIC ENHANCEMENTS**

### **Additional Symphony Safeguards**
Given the disaster history, Symphony projects require:
- **Mandatory structure guide review**: Always load `docs/symphony-structure-guide.md` first
- **Enhanced agent protection**: Never modify agent directories without explicit user approval
- **Business value awareness**: Understand Symphony's commercial and IP value before any changes
- **Meta-implementation considerations**: Changes affect Symphony's own operational capabilities

### **Symphony Recovery Resources**
- **Manual restore archive**: 28 critical files containing complete IP recovery capability
- **Conversation archives**: Complete disaster recovery documentation and lessons learned
- **Working architecture**: Proven 4-tier structure with 5-category documentation hierarchy
- **Agent specifications**: Complete ecosystem definitions for reconstruction

---

## 📝 **PROTOCOL CUSTOMIZATION**

### **Adapting for Different Projects**
These protocols can be customized based on:
- **Project complexity**: Simple projects may need fewer checkpoints
- **Risk tolerance**: High-value projects need maximum protection
- **Team size**: Multi-person projects need enhanced communication
- **Development stage**: Early projects may accept more risk than mature ones

### **Protocol Evolution**
- **Learn from experience**: Update protocols based on what works
- **Address new risks**: Add protections for newly discovered problem patterns  
- **Improve efficiency**: Streamline protocols while maintaining safety
- **Share knowledge**: Document improvements for use across all projects

---

**These protocols transform Claude Code from a powerful but potentially dangerous tool into a safe, predictable, and highly productive development environment that preserves and builds upon valuable work.**

---

**🔒 PROTOCOL STATUS: MANDATORY FOR ALL CLAUDE CODE SESSIONS**  
**📅 Created**: September 1, 2025  
**🛡️ Purpose**: Prevent disasters and ensure productive, safe sessions  
**✅ Validation**: Based on comprehensive disaster analysis and recovery experience**