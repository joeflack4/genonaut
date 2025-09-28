"""Test utilities for database testing and management.

This module provides utilities for loading test data from TSV files,
managing test schemas, and cleaning up test databases.
"""

import csv
import json
import os
import re
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from genonaut.db.schema import Base, User, ContentItem, ContentItemAuto, UserInteraction, Recommendation, GenerationJob


def get_admin_database_url(demo: bool = False) -> str:
    """Get database URL with admin credentials for schema management.
    
    Returns:
        Database URL string with admin user credentials
        
    Raises:
        ValueError: If required environment variables are not set
    """
    admin_password = os.getenv('DB_PASSWORD_ADMIN')
    if not admin_password:
        raise ValueError("Admin password must be provided via DB_PASSWORD_ADMIN environment variable")

    target_db = os.getenv('DB_NAME_DEMO' if demo else 'DB_NAME', 'genonaut_demo' if demo else 'genonaut')
    url_env_key = 'DATABASE_URL_DEMO' if demo else 'DATABASE_URL'
    database_url = os.getenv(url_env_key)

    if database_url and database_url.strip():
        url_obj = make_url(database_url.strip())
        url_obj = url_obj.set(username='genonaut_admin', password=admin_password, database=target_db)
        return str(url_obj)

    # Fall back to main DATABASE_URL when demo-specific value is absent
    if demo:
        base_url = os.getenv('DATABASE_URL')
        if base_url and base_url.strip():
            url_obj = make_url(base_url.strip())
            url_obj = url_obj.set(username='genonaut_admin', password=admin_password, database=target_db)
            return str(url_obj)

    # Otherwise, construct from individual components with admin user
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')

    return f"postgresql://genonaut_admin:{admin_password}@{host}:{port}/{target_db}"


def load_tsv_data(file_path: str) -> List[Dict[str, Any]]:
    """Load data from a TSV file and return as list of dictionaries.
    
    Args:
        file_path: Path to the TSV file
        
    Returns:
        List of dictionaries representing the rows
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file cannot be parsed
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"TSV file not found: {file_path}")
    
    rows = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                # Process JSON fields
                processed_row = {}
                for key, value in row.items():
                    if value is None or value.strip() == '':
                        processed_row[key] = None
                    elif value.startswith('{') or value.startswith('['):
                        try:
                            processed_row[key] = json.loads(value)
                        except json.JSONDecodeError:
                            processed_row[key] = value
                    elif value.lower() in ('true', 'false'):
                        processed_row[key] = value.lower() == 'true'
                    else:
                        try:
                            # Try to convert to number if possible
                            if '.' in value:
                                processed_row[key] = float(value)
                            else:
                                processed_row[key] = int(value)
                        except (ValueError, TypeError):
                            processed_row[key] = value
                
                rows.append(processed_row)
    except Exception as e:
        raise ValueError(f"Error parsing TSV file {file_path}: {e}")
    
    return rows


def _normalize_json_field(value: Any, default: Any) -> Any:
    """Return JSON-compatible data regardless of whether the input is encoded or already parsed."""

    if value is None:
        return default

    if isinstance(value, (dict, list)):
        return value

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return default

    return value


def _handle_admin_user_for_demo_test_db(users_df: pd.DataFrame, database_name: str) -> pd.DataFrame:
    """Handle special Admin user logic for demo and test databases.

    Args:
        users_df: DataFrame containing user data from users.tsv
        database_name: Name of the target database

    Returns:
        Modified DataFrame with Admin user UUID properly set

    Raises:
        RuntimeError: If multiple Admin users found or DB_USER_ADMIN_UUID not set
    """
    # Check if this is a demo or test database
    if not (database_name.endswith('_demo') or database_name.endswith('_test')):
        return users_df

    # Find Admin user(s) - case insensitive
    admin_mask = users_df['username'].str.lower() == 'admin'
    admin_rows = users_df[admin_mask]

    if len(admin_rows) == 0:
        # No Admin user found, return as-is
        return users_df

    if len(admin_rows) > 1:
        raise RuntimeError(
            f"Multiple Admin users found in users.tsv. Expected exactly 1 row with username 'Admin' or 'admin', "
            f"but found {len(admin_rows)} rows."
        )

    # Get the static UUID from environment variable
    admin_uuid_str = os.getenv('DB_USER_ADMIN_UUID')

    if not admin_uuid_str:
        # Generate a random UUID for the error message
        suggested_uuid = str(uuid.uuid4())
        raise RuntimeError(
            f"DB_USER_ADMIN_UUID must be set in the users .env for developers "
            f"(for those using demo and test databases). "
            f"It has randomly generated a UUID for them to use, for their convenience: "
            f"DB_USER_ADMIN_UUID={suggested_uuid}"
        )

    # Validate the UUID format
    try:
        admin_uuid = uuid.UUID(admin_uuid_str)
    except ValueError:
        raise RuntimeError(
            f"DB_USER_ADMIN_UUID environment variable contains invalid UUID format: {admin_uuid_str}"
        )

    # Create a copy of the DataFrame and set the Admin user's ID
    result_df = users_df.copy()
    admin_index = admin_rows.index[0]

    # Add the 'id' column if it doesn't exist, or update it
    if 'id' not in result_df.columns:
        result_df['id'] = None

    result_df.loc[admin_index, 'id'] = str(admin_uuid)

    return result_df


def seed_database_from_tsv(session, test_input_dir: str = None, schema_name: Optional[str] = None, database_name: Optional[str] = None) -> None:
    """Seed database with data from TSV files.

    Args:
        session: SQLAlchemy session
        test_input_dir: Directory containing TSV files (defaults to test/io/rdbms_init/)
        schema_name: Optional schema name for table operations
        database_name: Name of the target database (used for demo/test special handling)

    Raises:
        SQLAlchemyError: If seeding fails
        RuntimeError: If Admin user handling fails for demo/test databases
    """
    if test_input_dir is None:
        # Get the directory containing this utils.py file, then go to input/rdbms_init/
        test_input_dir = os.path.join(os.path.dirname(__file__), 'input', 'rdbms_init_v1')

    # If we have a schema name, we'll set the search path in the session (PostgreSQL only)
    need_to_reset_search_path = False
    if schema_name:
        try:
            # Check if this is PostgreSQL by trying to set search_path
            session.execute(text(f"SET search_path TO {schema_name}, public"))
            session.commit()
            need_to_reset_search_path = True
        except Exception:
            # SQLite or other DB that doesn't support search_path
            print(f"Warning: Database doesn't support schemas, seeding in default schema")

    try:
        # Define file paths
        users_path = os.path.join(test_input_dir, 'users.tsv')
        content_items_path = os.path.join(test_input_dir, 'content_items.tsv')
        content_items_auto_path = os.path.join(test_input_dir, 'content_item_autos.tsv')
        interactions_path = os.path.join(test_input_dir, 'user_interactions.tsv')
        recommendations_path = os.path.join(test_input_dir, 'recommendations.tsv')
        jobs_path = os.path.join(test_input_dir, 'generation_jobs.tsv')

        # Load and create users first
        # Use DataFrame approach for special Admin user handling
        users_df = pd.read_csv(users_path, sep='\t')

        # Handle special Admin user logic for demo/test databases
        if database_name:
            users_df = _handle_admin_user_for_demo_test_db(users_df, database_name)

        users = []
        username_to_user = {}

        for _, row in users_df.iterrows():
            # Convert row to dict and handle JSON/bool fields like load_tsv_data does
            user_data = row.to_dict()

            # Process fields similar to load_tsv_data
            for key, value in user_data.items():
                if pd.isna(value) or (isinstance(value, str) and value.strip() == ''):
                    user_data[key] = None
                elif isinstance(value, str):
                    if value.startswith('{') or value.startswith('['):
                        try:
                            user_data[key] = json.loads(value)
                        except json.JSONDecodeError:
                            pass
                    elif value.lower() in ('true', 'false'):
                        user_data[key] = value.lower() == 'true'

            # Create User object, handling pre-assigned ID for Admin user
            user_kwargs = {
                'username': user_data['username'],
                'email': user_data['email'],
                'preferences': user_data.get('preferences', {}),
                'is_active': user_data.get('is_active', True)
            }

            # If this user has a pre-assigned ID (Admin user), use it
            if 'id' in user_data and user_data['id'] is not None:
                user_kwargs['id'] = uuid.UUID(user_data['id'])

            user = User(**user_kwargs)
            users.append(user)
            username_to_user[user.username] = user

        session.add_all(users)
        session.flush()  # Get user IDs
        
        # Update username_to_user mapping with IDs
        for user in users:
            username_to_user[user.username] = user
        
        # Load and create content items
        content_data = load_tsv_data(content_items_path)
        content_items = []
        title_to_content = {}
        content_id_map: Dict[str, ContentItem] = {}
        
        for i, content_row in enumerate(content_data):
            # Handle both creator_username (old format) and creator_id (new format)
            if 'creator_username' in content_row:
                try:
                    creator = username_to_user[content_row['creator_username']]
                except KeyError:
                    raise ValueError(
                        f"Error in '{os.path.basename(content_items_path)}' (row {i + 2}): "
                        f"creator_username '{content_row.get('creator_username')}' not found in {os.path.basename(users_path)}. "
                        f"Row data: {content_row}"
                    )
            else:
                # Use creator_id directly
                creator_id = content_row['creator_id']
                # Find creator by ID
                creator = None
                for user in users:
                    if str(user.id) == str(creator_id):
                        creator = user
                        break
                if not creator:
                    raise ValueError(
                        f"Error in '{os.path.basename(content_items_path)}' (row {i + 2}): "
                        f"creator_id '{creator_id}' not found. Row data: {content_row}"
                    )
            content = ContentItem(
                id=int(content_row['id']) if content_row.get('id') is not None else None,
                title=content_row['title'],
                content_type=content_row['content_type'],
                content_data=content_row['content_data'],
                item_metadata=content_row.get('item_metadata', {}),
                creator_id=creator.id,
                tags=content_row.get('tags', []),
                quality_score=content_row.get('quality_score', 0.0),
                is_private=content_row.get('is_private', False)
            )
            content_items.append(content)
            title_to_content[content.title] = content
            if content_row.get('id') is not None:
                content_id_map[str(content_row['id'])] = content
        
        session.add_all(content_items)
        session.flush()  # Get content IDs

        # Update title_to_content mapping with IDs
        for content in content_items:
            title_to_content[content.title] = content
            content_id_map[str(content.id)] = content

        # Load and create auto content items
        if os.path.exists(content_items_auto_path):
            auto_content_data = load_tsv_data(content_items_auto_path)
            auto_content_items = []

            for i, auto_content_row in enumerate(auto_content_data):
                # Handle both creator_username (old format) and creator_id (new format)
                if 'creator_username' in auto_content_row:
                    try:
                        creator = username_to_user[auto_content_row['creator_username']]
                    except KeyError:
                        raise ValueError(
                            f"Error in '{os.path.basename(content_items_auto_path)}' (row {i + 2}): "
                            f"creator_username '{auto_content_row.get('creator_username')}' not found in {os.path.basename(users_path)}. "
                            f"Row data: {auto_content_row}"
                        )
                else:
                    # Use creator_id directly
                    creator_id = auto_content_row['creator_id']
                    # Find creator by ID
                    creator = None
                    for user in users:
                        if str(user.id) == str(creator_id):
                            creator = user
                            break
                    if not creator:
                        raise ValueError(
                            f"Error in '{os.path.basename(content_items_auto_path)}' (row {i + 2}): "
                            f"creator_id '{creator_id}' not found. Row data: {auto_content_row}"
                        )
                auto_content = ContentItemAuto(
                    id=int(auto_content_row['id']) if auto_content_row.get('id') is not None else None,
                    title=auto_content_row['title'],
                    content_type=auto_content_row['content_type'],
                    content_data=auto_content_row['content_data'],
                    item_metadata=_normalize_json_field(auto_content_row.get('item_metadata'), {}),
                    creator_id=creator.id,
                    tags=_normalize_json_field(auto_content_row.get('tags'), []),
                    quality_score=float(auto_content_row.get('quality_score', 0.0)),
                    is_private=auto_content_row.get('is_private', False)
                )
                auto_content_items.append(auto_content)
                # Add to title mapping for potential references
                title_to_content[auto_content.title] = auto_content
                if auto_content_row.get('id') is not None:
                    content_id_map[str(auto_content_row['id'])] = auto_content

            session.add_all(auto_content_items)
            session.flush()  # Get auto content IDs

            for auto_content in auto_content_items:
                title_to_content[auto_content.title] = auto_content
                content_id_map[str(auto_content.id)] = auto_content
        
        # Load and create user interactions
        interactions_data = load_tsv_data(interactions_path)
        interactions = []
        
        for i, interaction_row in enumerate(interactions_data):
            user = None
            if interaction_row.get('user_username'):
                user = username_to_user.get(interaction_row['user_username'])
            elif interaction_row.get('user_id'):
                for candidate in users:
                    if str(candidate.id) == str(interaction_row['user_id']):
                        user = candidate
                        break
            if not user:
                raise ValueError(
                    f"Error in '{os.path.basename(interactions_path)}' (row {i + 2}): "
                    f"user reference '{interaction_row.get('user_username') or interaction_row.get('user_id')}' not found in {os.path.basename(users_path)}. "
                    f"Row data: {interaction_row}"
                )

            content = None
            if interaction_row.get('content_title'):
                content = title_to_content.get(interaction_row['content_title'])
            elif interaction_row.get('content_item_id'):
                content = content_id_map.get(str(interaction_row['content_item_id']))
            if not content:
                raise ValueError(
                    f"Error in '{os.path.basename(interactions_path)}' (row {i + 2}): "
                    f"content reference '{interaction_row.get('content_title') or interaction_row.get('content_item_id')}' not found in {os.path.basename(content_items_path)}. "
                    f"Row data: {interaction_row}"
                )
            
            interaction = UserInteraction(
                user_id=user.id,
                content_item_id=content.id,
                interaction_type=interaction_row['interaction_type'],
                rating=interaction_row.get('rating'),
                duration=interaction_row.get('duration'),
                interaction_metadata=interaction_row.get('interaction_metadata', {})
            )
            interactions.append(interaction)
        
        session.add_all(interactions)
        
        # Load and create recommendations
        recommendations_data = load_tsv_data(recommendations_path)
        recommendations = []
        
        for i, rec_row in enumerate(recommendations_data):
            user = None
            if rec_row.get('user_username'):
                user = username_to_user.get(rec_row['user_username'])
            elif rec_row.get('user_id'):
                for candidate in users:
                    if str(candidate.id) == str(rec_row['user_id']):
                        user = candidate
                        break
            if not user:
                raise ValueError(
                    f"Error in '{os.path.basename(recommendations_path)}' (row {i + 2}): "
                    f"user reference '{rec_row.get('user_username') or rec_row.get('user_id')}' not found in {os.path.basename(users_path)}. "
                    f"Row data: {rec_row}"
                )

            content = None
            if rec_row.get('content_title'):
                content = title_to_content.get(rec_row['content_title'])
            elif rec_row.get('content_item_id'):
                content = content_id_map.get(str(rec_row['content_item_id']))
            if not content:
                raise ValueError(
                    f"Error in '{os.path.basename(recommendations_path)}' (row {i + 2}): "
                    f"content reference '{rec_row.get('content_title') or rec_row.get('content_item_id')}' not found in {os.path.basename(content_items_path)}. "
                    f"Row data: {rec_row}"
                )
            
            recommendation = Recommendation(
                user_id=user.id,
                content_item_id=content.id,
                recommendation_score=rec_row['recommendation_score'],
                algorithm_version=rec_row['algorithm_version'],
                is_served=rec_row.get('is_served', False),
                rec_metadata=rec_row.get('rec_metadata', {})
            )
            recommendations.append(recommendation)
        
        session.add_all(recommendations)
        
        # Load and create generation jobs
        jobs_data = load_tsv_data(jobs_path)
        generation_jobs = []
        
        for i, job_row in enumerate(jobs_data):
            user = None
            if job_row.get('user_username'):
                user = username_to_user.get(job_row['user_username'])
            elif job_row.get('user_id'):
                for candidate in users:
                    if str(candidate.id) == str(job_row['user_id']):
                        user = candidate
                        break
            if not user:
                raise ValueError(
                    f"Error in '{os.path.basename(jobs_path)}' (row {i + 2}): "
                    f"user reference '{job_row.get('user_username') or job_row.get('user_id')}' not found in {os.path.basename(users_path)}. "
                    f"Row data: {job_row}"
                )

            # Handle result content if specified
            result_content_id = None
            if job_row.get('result_content_title'):
                result_content = title_to_content.get(job_row['result_content_title'])
                if result_content:
                    result_content_id = result_content.id
            elif job_row.get('result_content_id'):
                content = content_id_map.get(str(job_row['result_content_id']))
                if content:
                    result_content_id = content.id
                else:
                    result_content_id = int(job_row['result_content_id'])
            
            # Set timestamps for completed jobs
            started_at = job_row.get('started_at')
            if isinstance(started_at, str) and started_at:
                started_at = datetime.fromisoformat(started_at)
            else:
                started_at = None

            completed_at = job_row.get('completed_at')
            if isinstance(completed_at, str) and completed_at:
                completed_at = datetime.fromisoformat(completed_at)
            else:
                completed_at = None
            
            job = GenerationJob(
                user_id=user.id,
                job_type=job_row['job_type'],
                prompt=job_row['prompt'],
                parameters=job_row.get('parameters', {}),
                status=job_row['status'],
                result_content_id=result_content_id,
                started_at=started_at,
                completed_at=completed_at,
                error_message=job_row.get('error_message')
            )
            generation_jobs.append(job)
        
        session.add_all(generation_jobs)
        session.commit()
        
    except (ValueError, KeyError, FileNotFoundError) as e:
        session.rollback()
        raise SQLAlchemyError(f"Failed to seed database from TSV files: {e}")
    finally:
        # Reset search path if we changed it
        if need_to_reset_search_path:
            session.execute(text("SET search_path TO public"))
            session.commit()


def get_next_test_schema_name(database_url: str) -> str:
    """Get the next available test schema name (test1, test2, etc.).
    
    Args:
        database_url: Database connection URL
        
    Returns:
        Next available test schema name
        
    Raises:
        SQLAlchemyError: If unable to connect to database
    """
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Query existing schemas that match pattern test\d+
            result = conn.execute(text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name ~ '^test[0-9]+$'
                ORDER BY schema_name
            """))
            
            existing_schemas = [row[0] for row in result]
            
            # Extract numbers and find the highest
            max_num = 0
            for schema in existing_schemas:
                match = re.match(r'test(\d+)', schema)
                if match:
                    num = int(match.group(1))
                    max_num = max(max_num, num)
            
            return f"test{max_num + 1}"
            
    except SQLAlchemyError as e:
        # If we can't connect or query fails, default to test1
        return "test1"
    finally:
        if 'engine' in locals():
            engine.dispose()


def clear_excess_test_schemas(database_url: str, keep_latest: int = 1) -> None:
    """Delete old test schemas, keeping only the most recent ones.
    
    Args:
        database_url: Database connection URL
        keep_latest: Number of most recent schemas to keep (default: 1)
        
    Raises:
        SQLAlchemyError: If unable to delete schemas
    """
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Get all test schemas ordered by name (which corresponds to creation order)
            result = conn.execute(text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name ~ '^test[0-9]+$'
                ORDER BY schema_name DESC
            """))
            
            all_test_schemas = [row[0] for row in result]
            
            # Keep only the latest N schemas
            schemas_to_delete = all_test_schemas[keep_latest:]
            
            # Delete excess schemas
            for schema in schemas_to_delete:
                conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
                print(f"Deleted test schema: {schema}")
            
            conn.commit()
            
            if schemas_to_delete:
                print(f"Cleared {len(schemas_to_delete)} excess test schemas, kept {keep_latest} latest")
            else:
                print("No excess test schemas to clear")
                
    except SQLAlchemyError as e:
        raise SQLAlchemyError(f"Failed to clear excess test schemas: {e}")
    finally:
        if 'engine' in locals():
            engine.dispose()


def create_test_database_url(base_url: str, schema_name: str) -> str:
    """Create a database URL for a specific test schema.
    
    Args:
        base_url: Base database URL
        schema_name: Name of the test schema
        
    Returns:
        Database URL configured for the test schema
    """
    # For PostgreSQL, we can use the same database but different schema
    # For SQLite, we'll create a separate file
    if base_url.startswith('sqlite://'):
        # Create a separate SQLite file for the test
        if base_url == 'sqlite:///:memory:':
            return 'sqlite:///:memory:'
        else:
            base_path = base_url.replace('sqlite:///', '')
            test_path = f"{os.path.splitext(base_path)[0]}_{schema_name}.db"
            return f"sqlite:///{test_path}"
    else:
        # For PostgreSQL, append schema search path
        if '?' in base_url:
            return f"{base_url}&options=-csearch_path%3D{schema_name}"
        else:
            return f"{base_url}?options=-csearch_path%3D{schema_name}"


def export_demo_data_to_test_tsvs(output_dir: str = None, max_content_items: int = 1000, max_auto_items: int = 1000, max_other_rows: int = 1000, max_file_size_mb: int = 50) -> None:
    """Export data from demo database to test TSV files.

    This function extracts data from the demo database using a user-based iteration
    approach to maintain realistic data relationships. It exports:
    - Users (sorted by username)
    - Content items and auto content items for each user until reaching target counts
    - Other tables (first N rows)

    Args:
        output_dir: Directory to write TSV files (defaults to test/db/input/rdbms_init/)
        max_content_items: Maximum number of content_items to export
        max_auto_items: Maximum number of content_items_auto to export
        max_other_rows: Maximum number of rows for other tables
        max_file_size_mb: Maximum file size in MB before warning

    Raises:
        ValueError: If required environment variables are not set
        SQLAlchemyError: If database operations fail
    """
    import argparse

    # Set default output directory
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), 'input', 'rdbms_init')

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    print(f"Exporting demo data to: {output_dir}")
    print(f"Target: {max_content_items} content_items, {max_auto_items} auto items, {max_other_rows} other rows")

    try:
        # Connect to demo database
        demo_url = get_admin_database_url(demo=True)
        engine = create_engine(demo_url)

        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()

        # Import models
        from genonaut.db.schema import User, ContentItem, ContentItemAuto, UserInteraction, Recommendation, GenerationJob, AvailableModel, ComfyUIGenerationRequest

        # Track collected data
        collected_users = []
        collected_content_items = []
        collected_auto_items = []

        print("Starting user-based iteration...")

        # Get users sorted by username
        users = session.query(User).order_by(User.username).all()
        print(f"Found {len(users)} users in demo database")

        content_count = 0
        auto_count = 0

        # Iterate through users and collect their content
        for user in users:
            collected_users.append(user)

            # Get content items for this user
            user_content = session.query(ContentItem).filter(ContentItem.creator_id == user.id).all()
            for item in user_content:
                if content_count < max_content_items:
                    collected_content_items.append(item)
                    content_count += 1

            # Get auto content items for this user
            user_auto_content = session.query(ContentItemAuto).filter(ContentItemAuto.creator_id == user.id).all()
            for item in user_auto_content:
                if auto_count < max_auto_items:
                    collected_auto_items.append(item)
                    auto_count += 1

            # Stop when we have enough content
            if content_count >= max_content_items and auto_count >= max_auto_items:
                break

        print(f"Collected: {len(collected_users)} users, {len(collected_content_items)} content_items, {len(collected_auto_items)} auto items")

        # Helper function to write TSV
        def write_tsv(filename: str, data: list, columns: list):
            filepath = os.path.join(output_dir, filename)

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerow(columns)

                for row_data in data:
                    writer.writerow(row_data)

            # Check file size
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"Wrote {filepath}: {len(data)} rows, {file_size_mb:.2f} MB")

            if file_size_mb > max_file_size_mb:
                print(f"WARNING: {filename} exceeds {max_file_size_mb}MB limit!")

        # Export users
        user_data = []
        for user in collected_users:
            user_data.append([
                str(user.id),
                user.username,
                user.email,
                user.created_at.isoformat() if user.created_at else '',
                user.updated_at.isoformat() if user.updated_at else '',
                json.dumps(user.preferences) if user.preferences else '{}',
                user.is_active
            ])

        write_tsv('users.tsv', user_data, [
            'id', 'username', 'email', 'created_at', 'updated_at', 'preferences', 'is_active'
        ])

        # Export content items
        content_data = []
        for item in collected_content_items:
            content_data.append([
                item.id,
                item.title,
                item.content_type,
                item.content_data,
                json.dumps(item.item_metadata) if item.item_metadata else '{}',
                str(item.creator_id),
                item.created_at.isoformat() if item.created_at else '',
                item.updated_at.isoformat() if item.updated_at else '',
                json.dumps(item.tags) if item.tags else '[]',
                item.quality_score,
                item.is_private
            ])

        write_tsv('content_items.tsv', content_data, [
            'id', 'title', 'content_type', 'content_data', 'item_metadata', 'creator_id',
            'created_at', 'updated_at', 'tags', 'quality_score', 'is_private'
        ])

        # Export auto content items
        auto_data = []
        for item in collected_auto_items:
            auto_data.append([
                item.id,
                item.title,
                item.content_type,
                item.content_data,
                json.dumps(item.item_metadata) if item.item_metadata else '{}',
                str(item.creator_id),
                item.created_at.isoformat() if item.created_at else '',
                item.updated_at.isoformat() if item.updated_at else '',
                json.dumps(item.tags) if item.tags else '[]',
                item.quality_score,
                item.is_private
            ])

        write_tsv('content_item_autos.tsv', auto_data, [
            'id', 'title', 'content_type', 'content_data', 'item_metadata', 'creator_id',
            'created_at', 'updated_at', 'tags', 'quality_score', 'is_private'
        ])

        # Export other tables (first N rows)
        user_ids = [str(user.id) for user in collected_users]
        content_ids = [item.id for item in collected_content_items]
        auto_content_ids = [item.id for item in collected_auto_items]

        # User interactions - only for collected users and content
        interactions = session.query(UserInteraction).filter(
            UserInteraction.user_id.in_([user.id for user in collected_users])
        ).limit(max_other_rows).all()

        interaction_data = []
        for interaction in interactions:
            # Only include if the content item is also in our dataset
            if (interaction.content_item_id in content_ids if interaction.content_item_id else True):
                interaction_data.append([
                    interaction.id,
                    str(interaction.user_id),
                    interaction.content_item_id,
                    interaction.interaction_type,
                    interaction.interaction_value,
                    interaction.timestamp.isoformat() if interaction.timestamp else '',
                    json.dumps(interaction.interaction_metadata) if interaction.interaction_metadata else '{}'
                ])

        write_tsv('user_interactions.tsv', interaction_data, [
            'id', 'user_id', 'content_item_id', 'interaction_type', 'interaction_value', 'timestamp', 'interaction_metadata'
        ])

        # Recommendations - only for collected users and content
        recommendations = session.query(Recommendation).filter(
            Recommendation.user_id.in_([user.id for user in collected_users])
        ).limit(max_other_rows).all()

        rec_data = []
        for rec in recommendations:
            # Only include if the content item is also in our dataset
            if rec.content_item_id in content_ids:
                rec_data.append([
                    rec.id,
                    str(rec.user_id),
                    rec.content_item_id,
                    rec.recommendation_score,
                    rec.algorithm_version,
                    rec.created_at.isoformat() if rec.created_at else '',
                    rec.is_served,
                    json.dumps(rec.rec_metadata) if rec.rec_metadata else '{}'
                ])

        write_tsv('recommendations.tsv', rec_data, [
            'id', 'user_id', 'content_item_id', 'recommendation_score', 'algorithm_version', 'created_at', 'is_served', 'rec_metadata'
        ])

        # Generation jobs - only for collected users
        jobs = session.query(GenerationJob).filter(
            GenerationJob.user_id.in_([user.id for user in collected_users])
        ).limit(max_other_rows).all()

        job_data = []
        for job in jobs:
            job_data.append([
                job.id,
                str(job.user_id),
                job.job_type,
                job.prompt,
                json.dumps(job.parameters) if job.parameters else '{}',
                job.status,
                job.created_at.isoformat() if job.created_at else '',
                job.updated_at.isoformat() if job.updated_at else '',
                job.started_at.isoformat() if job.started_at else '',
                job.completed_at.isoformat() if job.completed_at else '',
                job.result_content_id,
                job.error_message or ''
            ])

        write_tsv('generation_jobs.tsv', job_data, [
            'id', 'user_id', 'job_type', 'prompt', 'parameters', 'status', 'created_at', 'updated_at', 'started_at', 'completed_at', 'result_content_id', 'error_message'
        ])

        print(f"\nData export completed successfully!")
        print(f"Files written to: {output_dir}")

    except Exception as e:
        print(f"Error exporting demo data: {e}")
        raise
    finally:
        if 'session' in locals():
            session.close()
        if 'engine' in locals():
            engine.dispose()


def check_playwright_fixtures(database_url: str = None, min_unified_content: int = 200) -> bool:
    """Check if the SQLite test database meets Playwright pagination requirements.

    This function validates that the test database has enough unified content
    (content_items + content_items_auto) to support realistic pagination testing.

    Args:
        database_url: Database connection URL (defaults to test database)
        min_unified_content: Minimum number of unified content items required

    Returns:
        True if requirements are met, False otherwise

    Raises:
        SQLAlchemyError: If database connection fails
    """
    try:
        # Use test database if not specified
        if database_url is None:
            from genonaut.db.utils import get_database_url
            database_url = get_database_url(environment="test")

        engine = create_engine(database_url)

        with engine.connect() as conn:
            # Check if tables exist
            tables_query = text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ('content_items', 'content_items_auto')
            """)
            existing_tables = [row[0] for row in conn.execute(tables_query)]

            if not existing_tables:
                print("❌ No content tables found in test database")
                return False

            # Count unified content items
            total_content = 0

            if 'content_items' in existing_tables:
                content_count_query = text("SELECT COUNT(*) FROM content_items")
                content_count = conn.execute(content_count_query).scalar()
                total_content += content_count
                print(f"✓ Found {content_count} regular content items")

            if 'content_items_auto' in existing_tables:
                auto_count_query = text("SELECT COUNT(*) FROM content_items_auto")
                auto_count = conn.execute(auto_count_query).scalar()
                total_content += auto_count
                print(f"✓ Found {auto_count} auto content items")

            print(f"📊 Total unified content: {total_content}")

            # Check if we meet minimum requirements
            if total_content < min_unified_content:
                print(f"❌ Insufficient content for pagination testing")
                print(f"   Required: {min_unified_content}, Found: {total_content}")
                print("   Run 'make refresh-test-data' to regenerate fixtures")
                return False

            # Calculate pagination capabilities
            pages_10_per_page = total_content // 10
            pages_20_per_page = total_content // 20

            print(f"✅ Pagination test capabilities:")
            print(f"   - {pages_10_per_page} pages with 10 items per page")
            print(f"   - {pages_20_per_page} pages with 20 items per page")

            # Additional checks for realistic testing
            if pages_10_per_page < 20:
                print("⚠️  Warning: Less than 20 pages available for pagination testing")
                print("   Consider increasing content count for more thorough testing")

            return True

    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False
    finally:
        if 'engine' in locals():
            engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database test utilities")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Export demo data command
    export_parser = subparsers.add_parser('export-demo-data', help='Export demo database data to test TSV files')
    export_parser.add_argument('--output-dir', type=str, help='Output directory for TSV files')
    export_parser.add_argument('--max-content-items', type=int, default=1000, help='Maximum content_items to export')
    export_parser.add_argument('--max-auto-items', type=int, default=1000, help='Maximum content_items_auto to export')
    export_parser.add_argument('--max-other-rows', type=int, default=1000, help='Maximum rows for other tables')
    export_parser.add_argument('--max-file-size-mb', type=int, default=50, help='Maximum file size in MB')

    # Check Playwright fixtures command
    check_parser = subparsers.add_parser('check-playwright-fixtures', help='Check if SQLite dataset meets pagination requirements')
    check_parser.add_argument('--database-url', type=str, help='Database URL (defaults to test database)')
    check_parser.add_argument('--min-content', type=int, default=200, help='Minimum unified content items required')

    args = parser.parse_args()

    if args.command == 'export-demo-data':
        export_demo_data_to_test_tsvs(
            output_dir=args.output_dir,
            max_content_items=args.max_content_items,
            max_auto_items=args.max_auto_items,
            max_other_rows=args.max_other_rows,
            max_file_size_mb=args.max_file_size_mb
        )
    elif args.command == 'check-playwright-fixtures':
        success = check_playwright_fixtures(
            database_url=args.database_url,
            min_unified_content=args.min_content
        )
        exit(0 if success else 1)
    else:
        parser.print_help()
