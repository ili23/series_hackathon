"""
Pytest configuration and fixtures
"""
import pytest
import os
import tempfile
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Import database components
import sys
# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from backend.db.database import Base
from backend.db.models import User, Language, VoiceMessage


@pytest.fixture(scope='function')
def test_db():
    """Create a temporary test database for each test"""
    # Create temporary database file
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test_parsing.db')
    db_url = f'sqlite:///{db_path}'
    
    # Create engine and session
    engine = create_engine(
        db_url,
        connect_args={'check_same_thread': False}
    )
    SessionLocal = scoped_session(sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    ))
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Yield session factory
    yield SessionLocal
    
    # Cleanup
    SessionLocal.remove()
    engine.dispose()
    shutil.rmtree(temp_dir)


@pytest.fixture
def db_session(test_db):
    """Get a database session for testing"""
    session = test_db()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        'phone_number': '+15551234567',
        'f_name': 'Test',
        'l_name': 'User',
        'bio': 'Test user bio'
    }


@pytest.fixture
def sample_language_data():
    """Sample language data for testing"""
    return {
        'phone_number': '+15551234567',
        'language_name': 'English',
        'proficiency': 'Native'
    }


@pytest.fixture
def sample_voice_message_data():
    """Sample voice message data for testing"""
    from datetime import datetime
    return {
        'phone_number': '+15551234567',
        'transcription': 'This is a test voice message transcription.',
        'url': 'https://example.com/test_voice.m4a',
        'primary_language': 'en',
        'metadata': {
            'file_size': 12345,
            'duration': 2.5,
            'mime_type': 'audio/m4a',
            'filename': 'test_voice.m4a'
        },
        'other_languages': 'es,fr',
        'timestamp': datetime.utcnow()
    }

