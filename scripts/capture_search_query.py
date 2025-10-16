#!/usr/bin/env python
"""Capture SQL query for search term."""
import logging
import sys
from uuid import UUID
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from genonaut.api.services.content_service import ContentService
from genonaut.api.models.requests import PaginationRequest
from genonaut.db.utils.utils import get_database_url

# Set up SQL logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Connect to database
db_url = get_database_url("demo")
engine = create_engine(db_url, echo=True)
SessionLocal = sessionmaker(bind=engine)

# Track queries
queries = []

@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    queries.append({
        'statement': statement,
        'parameters': parameters
    })

# Make the request
db = SessionLocal()
try:
    service = ContentService(db)

    # Simulate the frontend request
    pagination = PaginationRequest(page=1, page_size=10)
    user_id = UUID("121e194b-4caa-4b81-ad4f-86ca3919d5b9")
    search_term = '"grumpy cat"'

    result = service.get_unified_content_paginated(
        pagination=pagination,
        content_types=["regular", "auto"],
        creator_filter="all",
        user_id=user_id,
        search_term=search_term,
        sort_field="created_at",
        sort_order="desc",
        tags=None,
        tag_match="any",
    )

    print("\n" + "="*80)
    print("CAPTURED QUERIES:")
    print("="*80)
    for i, q in enumerate(queries, 1):
        print(f"\nQuery {i}:")
        print(q['statement'])
        if q['parameters']:
            print(f"Parameters: {q['parameters']}")

finally:
    db.close()
