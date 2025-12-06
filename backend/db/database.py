"""
Database connection and initialization
"""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

# Base class for models
Base = declarative_base()

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'parsing.db')
DB_URL = f'sqlite:///{DB_PATH}'

# Engine and session
engine = None
SessionLocal = None


def init_db():
    """Initialize database connection and create tables"""
    global engine, SessionLocal
    
    try:
        # Create engine
        engine = create_engine(
            DB_URL,
            connect_args={'check_same_thread': False},  # SQLite specific
            echo=False  # Set to True for SQL query logging
        )
        
        # Create session factory
        SessionLocal = scoped_session(sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        ))
        
        # Import models to register them with Base
        from .models import User, Language, VoiceMessage
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info(f"Database initialized at {DB_PATH}")
        
        # Seed database with sample data (only if empty)
        # from .seed_data import seed_database
        # seed_database()
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        return False


def get_db_session():
    """Get a database session"""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return SessionLocal()


def close_db_session():
    """Close database session"""
    if SessionLocal:
        SessionLocal.remove()

