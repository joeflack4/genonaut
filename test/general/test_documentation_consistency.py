"""Tests for documentation consistency across the project."""

import hashlib
from pathlib import Path


class TestDocumentationConsistency:
    """Tests for ensuring documentation files are consistent."""

    def test_agents_md_and_claude_md_are_identical(self):
        """Test that AGENTS.md and CLAUDE.md have identical contents.

        These files should be kept in sync as they both provide guidance
        for AI assistants working with the codebase.
        """
        # Get project root (3 levels up from this test file)
        project_root = Path(__file__).parent.parent.parent

        agents_md_path = project_root / "AGENTS.md"
        claude_md_path = project_root / "CLAUDE.md"

        # Ensure both files exist
        assert agents_md_path.exists(), f"AGENTS.md not found at {agents_md_path}"
        assert claude_md_path.exists(), f"CLAUDE.md not found at {claude_md_path}"

        # Calculate MD5 hash of AGENTS.md
        with open(agents_md_path, 'rb') as f:
            agents_md_hash = hashlib.md5(f.read()).hexdigest()

        # Calculate MD5 hash of CLAUDE.md
        with open(claude_md_path, 'rb') as f:
            claude_md_hash = hashlib.md5(f.read()).hexdigest()

        # Assert they are identical
        assert agents_md_hash == claude_md_hash, (
            f"AGENTS.md and CLAUDE.md have different contents.\n"
            f"AGENTS.md MD5: {agents_md_hash}\n"
            f"CLAUDE.md MD5: {claude_md_hash}\n"
            f"These files should be kept in sync."
        )
