"""Tests for the static seed data loader."""

import csv
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from genonaut.db.demo.seed_data_gen.static_data_loader import StaticDataLoader
from genonaut.db.schema import Base, User, UserNotification


@pytest.fixture
def db_session():
    """Provide an in-memory SQLite session for testing."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_dynamic_model_mapping_includes_user_notifications(db_session, tmp_path):
    """Loader should discover the UserNotification model automatically."""
    loader = StaticDataLoader(db_session, Path(tmp_path))
    assert 'user_notifications' in loader.table_model_map


def test_loads_user_notifications_csv(db_session, tmp_path):
    """CSV rows for user_notifications should be inserted successfully."""
    loader = StaticDataLoader(db_session, Path(tmp_path))

    user = User(
        id=uuid4(),
        username='test-user',
        email='test@example.com',
        preferences={'notifications_enabled': True},
    )
    db_session.add(user)
    db_session.commit()

    csv_path = Path(tmp_path) / 'user_notifications.csv'
    with csv_path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                'user_id',
                'title',
                'message',
                'notification_type',
                'read_status',
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                'user_id': str(user.id),
                'title': 'Seeded notification',
                'message': 'Loaded from CSV',
                'notification_type': 'system',
                'read_status': 'false',
            }
        )

    inserted = loader._load_csv_file(csv_path)
    assert inserted == 1

    notifications = db_session.query(UserNotification).all()
    assert len(notifications) == 1
    loaded_notification = notifications[0]
    assert loaded_notification.title == 'Seeded notification'
    assert loaded_notification.read_status is False
