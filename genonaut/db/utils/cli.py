"""CLI entry point for database utilities.

This separate entry point avoids the RuntimeWarning when running with python -m.
"""

from genonaut.db.utils.utils import main

if __name__ == "__main__":
    main()
