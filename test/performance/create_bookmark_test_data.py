"""Create test data for bookmark performance testing."""

import random
from sqlalchemy import text
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.config import get_settings


def create_test_data(db: Session, num_bookmarks: int = 1000):
    """Create test bookmarks for performance testing."""

    print(f"Creating {num_bookmarks} test bookmarks...")

    # Get a sample user (or create one)
    result = db.execute(text("SELECT id FROM users LIMIT 1"))
    user_id = result.scalar()

    if not user_id:
        # Create a test user
        db.execute(text("""
            INSERT INTO users (id, username, email, preferences, created_at, updated_at, is_active)
            VALUES (gen_random_uuid(), 'perf_test_user', 'perf@test.com', '{}', NOW(), NOW(), true)
            RETURNING id
        """))
        result = db.execute(text("SELECT id FROM users WHERE username = 'perf_test_user'"))
        user_id = result.scalar()

    print(f"Using user_id: {user_id}")

    # Get sample content items
    result = db.execute(text("""
        SELECT id, source_type
        FROM content_items_all
        WHERE source_type = 'items'
        ORDER BY RANDOM()
        LIMIT :limit
    """), {"limit": num_bookmarks})
    content_items = list(result)

    if len(content_items) < num_bookmarks:
        print(f"WARNING: Only {len(content_items)} content items available")
        num_bookmarks = len(content_items)

    # Create bookmarks
    print("Creating bookmarks...")
    for i, (content_id, source_type) in enumerate(content_items):
        try:
            db.execute(text("""
                INSERT INTO bookmarks (id, user_id, content_id, content_source_type, pinned, is_public, created_at, updated_at)
                VALUES (gen_random_uuid(), :user_id, :content_id, :source_type, :pinned, :is_public, NOW(), NOW())
                ON CONFLICT DO NOTHING
            """), {
                "user_id": user_id,
                "content_id": content_id,
                "source_type": source_type,
                "pinned": random.choice([True, False]) if i % 10 == 0 else False,
                "is_public": random.choice([True, False])
            })

            if (i + 1) % 100 == 0:
                db.commit()
                print(f"  Created {i + 1}/{num_bookmarks} bookmarks")

        except Exception as e:
            print(f"Error creating bookmark {i}: {e}")
            db.rollback()

    db.commit()

    # Create a few categories
    print("\nCreating test categories...")
    category_ids = []
    for i in range(5):
        result = db.execute(text("""
            INSERT INTO bookmark_categories (id, user_id, name, is_public, created_at, updated_at)
            VALUES (gen_random_uuid(), :user_id, :name, false, NOW(), NOW())
            RETURNING id
        """), {
            "user_id": user_id,
            "name": f"Test Category {i}"
        })
        category_id = result.scalar()
        category_ids.append(category_id)

    db.commit()
    print(f"Created {len(category_ids)} categories")

    # Add some bookmarks to categories
    print("\nAdding bookmarks to categories...")
    result = db.execute(text("SELECT id FROM bookmarks WHERE user_id = :user_id LIMIT 500"), {"user_id": user_id})
    bookmark_ids = [row[0] for row in result]

    for i, bookmark_id in enumerate(bookmark_ids):
        category_id = random.choice(category_ids)
        try:
            db.execute(text("""
                INSERT INTO bookmark_category_members (bookmark_id, category_id, user_id)
                VALUES (:bookmark_id, :category_id, :user_id)
                ON CONFLICT DO NOTHING
            """), {
                "bookmark_id": bookmark_id,
                "category_id": category_id,
                "user_id": user_id
            })

            if (i + 1) % 100 == 0:
                db.commit()
                print(f"  Added {i + 1}/{len(bookmark_ids)} memberships")

        except Exception as e:
            print(f"Error adding membership {i}: {e}")
            db.rollback()

    db.commit()

    # Create some user interactions (ratings)
    print("\nCreating user interactions...")
    for i in range(min(200, len(bookmark_ids))):
        bookmark_id = bookmark_ids[i]
        # Get content_id for this bookmark
        result = db.execute(text("SELECT content_id FROM bookmarks WHERE id = :id"), {"id": bookmark_id})
        content_id = result.scalar()

        if content_id:
            try:
                db.execute(text("""
                    INSERT INTO user_interactions (user_id, content_item_id, interaction_type, rating, created_at)
                    VALUES (:user_id, :content_id, 'rating', :rating, NOW())
                    ON CONFLICT DO NOTHING
                """), {
                    "user_id": user_id,
                    "content_id": content_id,
                    "rating": random.randint(1, 5)
                })
            except Exception as e:
                print(f"Error creating interaction {i}: {e}")
                db.rollback()

    db.commit()

    # Print summary
    print("\n" + "=" * 80)
    print("TEST DATA CREATION COMPLETE")
    print("=" * 80)

    result = db.execute(text("SELECT COUNT(*) FROM bookmarks WHERE user_id = :user_id"), {"user_id": user_id})
    print(f"Total bookmarks created: {result.scalar()}")

    result = db.execute(text("SELECT COUNT(*) FROM bookmark_categories WHERE user_id = :user_id"), {"user_id": user_id})
    print(f"Total categories created: {result.scalar()}")

    result = db.execute(text("SELECT COUNT(*) FROM bookmark_category_members WHERE user_id = :user_id"), {"user_id": user_id})
    print(f"Total category memberships: {result.scalar()}")

    result = db.execute(text("SELECT COUNT(*) FROM user_interactions WHERE user_id = :user_id"), {"user_id": user_id})
    print(f"Total user interactions: {result.scalar()}")


if __name__ == "__main__":
    settings = get_settings()
    print(f"Environment: {settings.env_target}")
    print()

    db_gen = get_database_session()
    db = next(db_gen)

    try:
        create_test_data(db, num_bookmarks=1000)
    finally:
        db.close()
