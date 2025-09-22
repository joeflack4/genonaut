"""Test utilities for database testing and management.

This module provides utilities for loading test data from TSV files,
managing test schemas, and cleaning up test databases.
"""

import csv
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from genonaut.db.schema import Base, User, ContentItem, UserInteraction, Recommendation, GenerationJob


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


def seed_database_from_tsv(session, test_input_dir: str = None, schema_name: Optional[str] = None) -> None:
    """Seed database with data from TSV files.
    
    Args:
        session: SQLAlchemy session
        test_input_dir: Directory containing TSV files (defaults to test/io/rdbms_init/)
        schema_name: Optional schema name for table operations
        
    Raises:
        SQLAlchemyError: If seeding fails
    """
    if test_input_dir is None:
        # Get the directory containing this utils.py file, then go to input/rdbms_init/
        test_input_dir = os.path.join(os.path.dirname(__file__), 'input', 'rdbms_init')

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
        interactions_path = os.path.join(test_input_dir, 'user_interactions.tsv')
        recommendations_path = os.path.join(test_input_dir, 'recommendations.tsv')
        jobs_path = os.path.join(test_input_dir, 'generation_jobs.tsv')

        # Load and create users first
        users_data = load_tsv_data(users_path)
        users = []
        username_to_user = {}
        
        for user_data in users_data:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                preferences=user_data.get('preferences', {}),
                is_active=user_data.get('is_active', True)
            )
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
        
        for i, content_row in enumerate(content_data):
            try:
                creator = username_to_user[content_row['creator_username']]
            except KeyError:
                raise ValueError(
                    f"Error in '{os.path.basename(content_items_path)}' (row {i + 2}): "
                    f"creator_username '{content_row.get('creator_username')}' not found in {os.path.basename(users_path)}. "
                    f"Row data: {content_row}"
                )
            content = ContentItem(
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
        
        session.add_all(content_items)
        session.flush()  # Get content IDs
        
        # Update title_to_content mapping with IDs
        for content in content_items:
            title_to_content[content.title] = content
        
        # Load and create user interactions
        interactions_data = load_tsv_data(interactions_path)
        interactions = []
        
        for i, interaction_row in enumerate(interactions_data):
            try:
                user = username_to_user[interaction_row['user_username']]
            except KeyError:
                raise ValueError(
                    f"Error in '{os.path.basename(interactions_path)}' (row {i + 2}): "
                    f"user_username '{interaction_row.get('user_username')}' not found in {os.path.basename(users_path)}. "
                    f"Row data: {interaction_row}"
                )
            try:
                content = title_to_content[interaction_row['content_title']]
            except KeyError:
                raise ValueError(
                    f"Error in '{os.path.basename(interactions_path)}' (row {i + 2}): "
                    f"content_title '{interaction_row.get('content_title')}' not found in {os.path.basename(content_items_path)}. "
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
            try:
                user = username_to_user[rec_row['user_username']]
            except KeyError:
                raise ValueError(
                    f"Error in '{os.path.basename(recommendations_path)}' (row {i + 2}): "
                    f"user_username '{rec_row.get('user_username')}' not found in {os.path.basename(users_path)}. "
                    f"Row data: {rec_row}"
                )
            try:
                content = title_to_content[rec_row['content_title']]
            except KeyError:
                raise ValueError(
                    f"Error in '{os.path.basename(recommendations_path)}' (row {i + 2}): "
                    f"content_title '{rec_row.get('content_title')}' not found in {os.path.basename(content_items_path)}. "
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
            try:
                user = username_to_user[job_row['user_username']]
            except KeyError:
                raise ValueError(
                    f"Error in '{os.path.basename(jobs_path)}' (row {i + 2}): "
                    f"user_username '{job_row.get('user_username')}' not found in {os.path.basename(users_path)}. "
                    f"Row data: {job_row}"
                )

            # Handle result content if specified
            result_content_id = None
            if job_row.get('result_content_title'):
                result_content = title_to_content.get(job_row['result_content_title'])
                if result_content:
                    result_content_id = result_content.id
            
            # Set timestamps for completed jobs
            started_at = None
            completed_at = None
            if job_row['status'] == 'completed':
                started_at = datetime.utcnow()
                completed_at = datetime.utcnow()
            
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
