# Documentation Standards

## File Organization

### Directory Structure
```
docs/
├── README.md                    # Main navigation
├── concepts/                    # Brainstorming and ideas
├── analysis/                    # Technical analysis and comparisons
├── guides/                      # Standards, templates, and implementation guides
└── work_sessions/              # LLM session documentation
```

### File Naming Conventions
- **Work Sessions:** `YYYY-MM-DD_feature_name.md`
- **Analysis:** `descriptive_name_analysis.md`
- **Guides:** `feature_name_guide.md` or `feature_name.md`
- **Concepts:** `topic_brainstorming.md` or `topic_ideas.md`

## Content Standards

### Headers and Structure
- Use `#` for main title
- Use `##` for major sections
- Use `###` for subsections
- Use `####` sparingly for detailed breakdowns

### Code Examples
- Always use proper syntax highlighting
- Include complete, runnable examples when possible
- Show both "before" and "after" states for changes
- Add comments explaining complex logic

### Status Indicators
Use consistent symbols:
- ✅ **Implemented/Complete**
- ❌ **Missing/Not Implemented**
- ⚠️ **Partially Implemented/Needs Work**
- 🔄 **In Progress**
- 💡 **Idea/Concept**

### Cross-References
- Link to related documents using relative paths
- Use descriptive link text
- Maintain a consistent linking style

## LLM Session Documentation

### Required Sections
1. **Session Header** - Date, duration, objective
2. **Problem Statement** - What you're solving
3. **Design Decisions** - Key choices made
4. **Implementation Details** - What was built
5. **Files Modified** - Complete change list
6. **Conclusion** - Summary and assessment

### Best Practices
- Document decisions and rationale, not just implementation
- Include failed approaches and why they didn't work
- Capture insights and lessons learned
- Update related analysis documents when new information emerges

## Maintenance

### Regular Updates
- Update comparison documents when new features are added
- Refresh analysis when external frameworks change
- Archive outdated work sessions but keep for reference
- Update the main README when structure changes

### Quality Checks
- Ensure all links work
- Verify code examples are current
- Check that status indicators are accurate
- Maintain consistent formatting across documents