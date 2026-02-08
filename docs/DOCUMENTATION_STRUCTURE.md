# Documentation Structure

This document explains the documentation organization for the Lingua-Local project.

## Core Documentation Files

### User-Facing Docs (Root Level)
- **README.md** - Main project documentation, architecture, features, goals
- **QUICKSTART.md** - 5-minute setup guide for new users
- **SETUP.md** - Comprehensive setup instructions, troubleshooting, performance tuning
- **HTTPS_SETUP.md** - HTTPS/SSL certificate setup (kept separate due to complexity)

### Project Status
- **IMPLEMENTATION_SUMMARY.md** - Project completion status and implementation details

### Technical Deep-Dives (docs/)
- **docs/STREAMING_ARCHITECTURE.md** - Technical architecture diagrams and streaming implementation details
- **docs/DOCUMENTATION_STRUCTURE.md** - This file

## Documentation Principles

### What Goes Where

**README.md:**
- Project overview and goals
- Architecture diagrams
- Technology stack
- Feature list
- Links to other docs

**QUICKSTART.md:**
- Minimal setup steps
- Quick commands
- Basic troubleshooting
- Getting started fast

**SETUP.md:**
- Detailed setup instructions
- Hardware-specific configurations
- Troubleshooting guide
- Performance tuning
- Model selection guidance
- All "how-to" information

**HTTPS_SETUP.md:**
- SSL certificate setup
- HTTPS configuration
- Browser security requirements

**docs/STREAMING_ARCHITECTURE.md:**
- Technical architecture diagrams
- Streaming protocol details
- Code flow explanations
- Implementation deep-dives

### What NOT to Create

**Never create:**
- `BUGFIX_*.md` - Add to SETUP.md troubleshooting instead
- `OPTIMIZATION_*.md` - Add to SETUP.md performance section instead
- `QUICK_REFERENCE_*.md` - Use QUICKSTART.md instead
- `CHANGELOG_*.md` - Use git commits/history instead
- `TIMING_ANALYSIS.md` - Add to SETUP.md if needed
- Temporary documentation files

**Exception:** Complex technical topics that warrant a separate deep-dive can go in `docs/`, but should be linked from main docs.

## Maintenance Guidelines

### When Adding New Information

1. **Bug fixes**: Add to SETUP.md → Troubleshooting section
2. **Performance tips**: Add to SETUP.md → Performance Tuning section
3. **New features**: Update README.md and relevant setup sections
4. **Quick commands**: Add to QUICKSTART.md
5. **Technical details**: Add to docs/ only if complex enough

### When Updating Docs

- Keep information consolidated
- Avoid duplication across files
- Cross-reference related sections
- Keep docs up-to-date with code changes

## File Naming

- Use descriptive names: `SETUP.md`, `QUICKSTART.md`
- Avoid version numbers: `SETUP_v2.md` ❌
- Avoid dates: `SETUP_2026.md` ❌
- Use consistent casing: All caps for main docs

## Cursor AI Rules

See `.cursorrules` for guidelines on how AI assistants should handle documentation in this project.

