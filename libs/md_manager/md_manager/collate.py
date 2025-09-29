"""Collate module for scanning markdown files and managing database."""

import sqlite3
import os
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Set, Tuple, Optional

from .github_schema import migrate_database


def is_issue_file(file_path: str) -> bool:
    """
    Determine if a file is an issue based on its path.

    Args:
        file_path: Relative path to the file

    Returns:
        True if the file is in an issues/ directory or descendant
    """
    if not file_path:
        return False

    # Convert to Path for easier manipulation
    path = Path(file_path)

    # Must have at least 2 parts (directory + filename) and have a file extension
    if len(path.parts) < 2 or not path.suffix:
        return False

    # Check if any part of the path (except the filename) is exactly "issues" (case insensitive)
    for part in path.parts[:-1]:  # Exclude the filename itself
        if part.lower() == "issues":
            return True

    return False


def create_database(db_path: str) -> None:
    """Create the SQLite database with the files table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            filename TEXT NOT NULL,
            root TEXT NOT NULL,
            path TEXT NOT NULL,
            created_datetime TEXT NOT NULL,
            updated_datetime TEXT NOT NULL,
            is_deleted INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

    # Ensure GitHub schema is also created
    migrate_database(db_path)


def scan_directory(root_dir: str, recursive: bool = True) -> List[str]:
    """
    Scan a directory for markdown files.

    Args:
        root_dir: Directory to scan
        recursive: If True, scan subdirectories recursively

    Returns:
        List of absolute paths to markdown files
    """
    root_path = Path(root_dir)
    markdown_files = []

    if recursive:
        # Use rglob for recursive search
        for md_file in root_path.rglob("*.md"):
            if md_file.is_file():
                markdown_files.append(str(md_file))
    else:
        # Use glob for non-recursive search
        for md_file in root_path.glob("*.md"):
            if md_file.is_file():
                markdown_files.append(str(md_file))

    return sorted(markdown_files)


def get_next_id(db_path: str) -> int:
    """Get the next available ID for new files."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(id) FROM files")
    result = cursor.fetchone()
    max_id = result[0] if result[0] is not None else 0

    conn.close()
    return max_id + 1


def get_existing_files(db_path: str, root_dir: str) -> Set[str]:
    """Get set of existing file paths for a given root directory."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT path FROM files WHERE root = ? AND is_deleted = 0", (root_dir,))
    existing_files = {row[0] for row in cursor.fetchall()}

    conn.close()
    return existing_files


def mark_files_as_deleted(db_path: str, root_dir: str, deleted_paths: Set[str]) -> None:
    """Mark files as deleted in the database."""
    if not deleted_paths:
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    current_time = datetime.now().isoformat()

    for path in deleted_paths:
        cursor.execute('''
            UPDATE files
            SET is_deleted = 1, updated_datetime = ?
            WHERE root = ? AND path = ?
        ''', (current_time, root_dir, path))

    conn.commit()
    conn.close()


def insert_github_entry(db_path: str, file_id: int, relative_path: str) -> None:
    """Insert a new GitHub table entry for a file."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    is_issue = is_issue_file(relative_path)

    cursor.execute('''
        INSERT INTO github (md_file_id, is_issue)
        VALUES (?, ?)
    ''', (file_id, is_issue))

    conn.commit()
    conn.close()


def update_github_entry(db_path: str, file_id: int, relative_path: str) -> None:
    """Update an existing GitHub table entry for a file."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    is_issue = is_issue_file(relative_path)

    cursor.execute('''
        UPDATE github SET is_issue = ? WHERE md_file_id = ?
    ''', (is_issue, file_id))

    conn.commit()
    conn.close()


def ensure_github_entries(db_path: str) -> None:
    """Ensure all files have corresponding GitHub table entries."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Find files without github entries
    cursor.execute('''
        SELECT f.id, f.path
        FROM files f
        LEFT JOIN github g ON f.id = g.md_file_id
        WHERE g.md_file_id IS NULL
    ''')

    missing_entries = cursor.fetchall()

    for file_id, relative_path in missing_entries:
        is_issue = is_issue_file(relative_path)
        cursor.execute('''
            INSERT INTO github (md_file_id, is_issue)
            VALUES (?, ?)
        ''', (file_id, is_issue))

    conn.commit()
    conn.close()


def insert_new_files(db_path: str, root_dir: str, new_files: List[Tuple[str, str]]) -> None:
    """Insert new files into the database."""
    if not new_files:
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    next_id = get_next_id(db_path)
    current_time = datetime.now().isoformat()

    for i, (file_path, relative_path) in enumerate(new_files):
        filename = Path(file_path).stem  # Get filename without extension
        file_id = next_id + i

        cursor.execute('''
            INSERT INTO files (id, filename, root, path, created_datetime, updated_datetime, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (file_id, filename, root_dir, relative_path, current_time, current_time))

        # Insert corresponding github entry
        is_issue = is_issue_file(relative_path)
        cursor.execute('''
            INSERT INTO github (md_file_id, is_issue)
            VALUES (?, ?)
        ''', (file_id, is_issue))

    conn.commit()
    conn.close()


def update_existing_files(db_path: str, root_dir: str, existing_paths: Set[str]) -> None:
    """Update the updated_datetime for existing files."""
    if not existing_paths:
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    current_time = datetime.now().isoformat()

    for path in existing_paths:
        cursor.execute('''
            UPDATE files
            SET updated_datetime = ?
            WHERE root = ? AND path = ? AND is_deleted = 0
        ''', (current_time, root_dir, path))

        # Update corresponding github entry
        cursor.execute('''
            SELECT id FROM files
            WHERE root = ? AND path = ? AND is_deleted = 0
        ''', (root_dir, path))

        result = cursor.fetchone()
        if result:
            file_id = result[0]
            is_issue = is_issue_file(path)
            cursor.execute('''
                UPDATE github SET is_issue = ? WHERE md_file_id = ?
            ''', (is_issue, file_id))

    conn.commit()
    conn.close()


def collate_files(directories: List[str], db_path: str = "md_manager.db", recursive: bool = True, overwrite: bool = False) -> None:
    """
    Collate markdown files from directories into database.

    Args:
        directories: List of directory paths to scan
        db_path: Path to SQLite database
        recursive: If True, scan subdirectories recursively
        overwrite: If True, delete existing database and recreate from scratch
    """
    # If overwrite is True, delete the existing database file
    if overwrite and os.path.exists(db_path):
        os.unlink(db_path)

    create_database(db_path)

    for directory in directories:
        root_dir = os.path.abspath(directory)
        root_path = Path(root_dir)

        # Scan for markdown files
        markdown_files = scan_directory(root_dir, recursive)

        # Get relative paths
        current_files = set()
        new_files = []

        for file_path in markdown_files:
            relative_path = str(Path(file_path).relative_to(root_path))
            current_files.add(relative_path)

        if overwrite:
            # When overwriting, treat all files as new
            for file_path in markdown_files:
                relative_path = str(Path(file_path).relative_to(root_path))
                new_files.append((file_path, relative_path))

            # Insert all files as new (no sync logic needed)
            insert_new_files(db_path, root_dir, new_files)
        else:
            # Normal sync logic
            # Get existing files from database
            existing_files = get_existing_files(db_path, root_dir)

            # Find new files (in current scan but not in database)
            new_file_paths = current_files - existing_files
            for relative_path in new_file_paths:
                absolute_path = str(root_path / relative_path)
                new_files.append((absolute_path, relative_path))

            # Find deleted files (in database but not in current scan)
            deleted_files = existing_files - current_files

            # Find existing files that are still present
            still_existing = existing_files & current_files

            # Update database
            insert_new_files(db_path, root_dir, new_files)
            mark_files_as_deleted(db_path, root_dir, deleted_files)
            update_existing_files(db_path, root_dir, still_existing)

        # Ensure all files have GitHub entries (in case of schema updates)
        ensure_github_entries(db_path)


def export_database(db_path: str, export_path: Optional[str] = None) -> None:
    """
    Export database tables to TSV files in a directory.

    Args:
        db_path: Path to SQLite database
        export_path: Directory to create for export files. If None, creates 'export' in current directory.
    """
    if export_path is None:
        export_path = os.path.join(os.getcwd(), "export")

    # Create export directory
    os.makedirs(export_path, exist_ok=True)

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    for table_name in tables:
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]

        # Get all data from table
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        # Write to TSV file
        tsv_path = os.path.join(export_path, f"{table_name}.tsv")
        with open(tsv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')

            # Write header
            writer.writerow(columns)

            # Write data rows
            for row in rows:
                writer.writerow(row)

    conn.close()