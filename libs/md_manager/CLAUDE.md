# Agents Configuration

This file contains configuration for AI agents working on this project.

## Development Guidelines

- Use Test-Driven Development (TDD)
- Write tests first, then implement features
- Keep functions small and focused
- Use clear, descriptive variable and function names
- Follow PEP 8 style guidelines
- Add docstrings for all public functions and classes

## Testing Strategy

- Create comprehensive test data in `test/input/example-notes-dir/`
- Model test data after the actual `notes/` directory structure
- Test both positive and negative cases
- Test edge cases (empty directories, non-markdown files, etc.)
- Use temporary databases for testing to avoid side effects

## Architecture

- CLI interface using Click
- SQLite database for persistence
- Modular design with separate modules for:
  - CLI commands
  - Database operations
  - File scanning logic
  - Utilities