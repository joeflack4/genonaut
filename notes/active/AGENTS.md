# Notes & Documentation Guide

This file provides guidance to Claude Code when working with project notes and documentation.

## Note-Taking Standards
**CRITICAL**: Always use proper checkbox formatting for task tracking:
- **Incomplete tasks**: `- [ ] Task description`
- **Completed tasks**: `- [x] Task description`

## Documentation Workflow
### For Major Tasks/Features:
1. **Create comprehensive `.md` files** in `notes/` for design documentation
2. **Include detailed checklists** with proper checkbox syntax
3. **Check off completed tasks** by converting `- [ ]` to `- [x]`
4. **Move relevant todos** from `notes/general-todos.md` to specific feature notes

### Checklist Best Practices:
- Break down complex features into granular, actionable tasks
- Use descriptive task names that clearly indicate what needs to be done
- Group related tasks under clear headings
- Update progress regularly by checking off completed items
- Archive completed checklists or move them to "Done" sections

## Required Documentation:
When creating or updating major features:
1. **Specs and Design**: Document architecture and requirements
2. **Todo Lists**: Use checkbox format for tracking progress
3. **Test Plans**: Include testing checklist items
4. **Implementation Notes**: Document key decisions and gotchas

## Integration with general-todos.md
**IMPORTANT**: Always consult `notes/general-todos.md` when starting new work:
- Review uncategorized todos that may apply to current task
- Move relevant todos to your feature-specific note document
- Check off completed items that you discover are already done
- Keep the general todos file clean and up-to-date

## Example Checklist Format:
```markdown
## Implementation Checklist
- [ ] Create database models
- [ ] Write unit tests for models
- [ ] Implement repository layer
- [ ] Add API endpoints
- [ ] Write integration tests
- [ ] Update documentation
- [ ] Run full test suite
- [x] Initial research and planning
```

## Documentation Standards:
- Use clear headings and structure
- Include code examples where relevant
- Link to relevant files and documentation
- Keep notes up-to-date as work progresses
- Archive or reorganize notes when features are complete

## File Organization:
- Use descriptive filenames (e.g., `comfyui-integration.md`, `pagination-system.md`)
- Group related notes with consistent naming
- Clean up obsolete notes periodically
- Maintain clear relationships between notes and implementation