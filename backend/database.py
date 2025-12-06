"""
Database models and operations for storing language profiles
"""
import logging
import os
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

logger = logging.getLogger(__name__)

Base = declarative_base()


class Language(Base):
    """
    Languages table to store user language profiles
    """
    __tablename__ = 'languages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    language_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Language(id={self.id}, language_name='{self.language_name}', phone_number='{self.phone_number}')>"


class Proficiency(Base):
    """
    Optional proficiency table for future implementation
    """
    __tablename__ = 'proficiencies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)
    proficiency_level = Column(String(50))  # e.g., 'beginner', 'intermediate', 'advanced', 'native'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    language = relationship("Language", backref="proficiencies")
    
    def __repr__(self):
        return f"<Proficiency(id={self.id}, language_id={self.language_id}, proficiency_level='{self.proficiency_level}')>"


class UserProfile(Base):
    """
    User profiles with bio information
    """
    __tablename__ = 'user_profiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String(20), nullable=False, unique=True)
    bio = Column(String(500))
    display_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserProfile(id={self.id}, phone_number='{self.phone_number}', display_name='{self.display_name}')>"


class ConversationState(Base):
    """
    Track conversation states for the matching workflow
    """
    __tablename__ = 'conversation_states'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String(20), nullable=False)
    state = Column(String(50))  # e.g., 'new_language_detected', 'asking_add_language', 'asking_matching', 'matching_users', 'showing_profile', 'asking_group_chat'
    language_name = Column(String(100))  # Language being discussed
    matched_user_phone = Column(String(20))  # Currently shown matched user
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ConversationState(id={self.id}, phone_number='{self.phone_number}', state='{self.state}')>"


class MatchingPreference(Base):
    """
    Track user preferences for language matching
    """
    __tablename__ = 'matching_preferences'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String(20), nullable=False)
    language_name = Column(String(100), nullable=False)
    wants_matching = Column(String(10), default='yes')  # 'yes' or 'no'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MatchingPreference(id={self.id}, phone_number='{self.phone_number}', language_name='{self.language_name}', wants_matching='{self.wants_matching}')>"


# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///languages.db')
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def get_db_session():
    """Get a database session"""
    return SessionLocal()


def add_user_language(phone_number: str, language_name: str):
    """
    Add or update user language profile
    
    Args:
        phone_number: User's phone number
        language_name: Name of the language detected
    
    Returns:
        Language object if successful, None otherwise
    """
    session = get_db_session()
    try:
        # Check if user already has this language
        existing = session.query(Language).filter_by(
            phone_number=phone_number,
            language_name=language_name
        ).first()
        
        if existing:
            logger.info(f"Language {language_name} already exists for {phone_number}")
            return existing
        
        # Create new language entry
        language = Language(
            phone_number=phone_number,
            language_name=language_name
        )
        session.add(language)
        session.commit()
        logger.info(f"Added language {language_name} for {phone_number}")
        return language
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding user language: {e}")
        return None
    finally:
        session.close()


def get_user_languages(phone_number: str):
    """
    Get all languages for a user
    
    Args:
        phone_number: User's phone number
    
    Returns:
        List of Language objects
    """
    session = get_db_session()
    try:
        languages = session.query(Language).filter_by(phone_number=phone_number).all()
        return languages
    except Exception as e:
        logger.error(f"Error getting user languages: {e}")
        return []
    finally:
        session.close()


def is_new_language_for_user(phone_number: str, language_name: str):
    """Check if a language is new for a user"""
    languages = get_user_languages(phone_number)
    return not any(lang.language_name == language_name for lang in languages)


def get_conversation_state(phone_number: str):
    """Get current conversation state for a user"""
    session = get_db_session()
    try:
        state = session.query(ConversationState).filter_by(phone_number=phone_number).order_by(ConversationState.updated_at.desc()).first()
        return state
    except Exception as e:
        logger.error(f"Error getting conversation state: {e}")
        return None
    finally:
        session.close()


def set_conversation_state(phone_number: str, state: str, language_name: str = None, matched_user_phone: str = None):
    """Set conversation state for a user"""
    session = get_db_session()
    try:
        existing = session.query(ConversationState).filter_by(phone_number=phone_number).first()
        if existing:
            existing.state = state
            if language_name:
                existing.language_name = language_name
            if matched_user_phone:
                existing.matched_user_phone = matched_user_phone
            existing.updated_at = datetime.utcnow()
        else:
            existing = ConversationState(
                phone_number=phone_number,
                state=state,
                language_name=language_name,
                matched_user_phone=matched_user_phone
            )
            session.add(existing)
        session.commit()
        return existing
    except Exception as e:
        session.rollback()
        logger.error(f"Error setting conversation state: {e}")
        return None
    finally:
        session.close()


def clear_conversation_state(phone_number: str):
    """Clear conversation state for a user"""
    session = get_db_session()
    try:
        session.query(ConversationState).filter_by(phone_number=phone_number).delete()
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error clearing conversation state: {e}")
        return False
    finally:
        session.close()


def set_matching_preference(phone_number: str, language_name: str, wants_matching: str):
    """Set matching preference for a user and language"""
    session = get_db_session()
    try:
        existing = session.query(MatchingPreference).filter_by(
            phone_number=phone_number,
            language_name=language_name
        ).first()
        
        if existing:
            existing.wants_matching = wants_matching
        else:
            existing = MatchingPreference(
                phone_number=phone_number,
                language_name=language_name,
                wants_matching=wants_matching
            )
            session.add(existing)
        session.commit()
        return existing
    except Exception as e:
        session.rollback()
        logger.error(f"Error setting matching preference: {e}")
        return None
    finally:
        session.close()


def find_matching_users(phone_number: str, language_name: str):
    """Find users who know the same language and want matching"""
    session = get_db_session()
    try:
        # Get users who have this language and want matching
        matching_prefs = session.query(MatchingPreference).filter_by(
            language_name=language_name,
            wants_matching='yes'
        ).all()
        
        # Get users who have this language
        languages = session.query(Language).filter_by(language_name=language_name).all()
        
        # Combine and exclude the requesting user
        matching_phones = set()
        for pref in matching_prefs:
            if pref.phone_number != phone_number:
                matching_phones.add(pref.phone_number)
        
        for lang in languages:
            if lang.phone_number != phone_number:
                matching_phones.add(lang.phone_number)
        
        # Get user profiles for matched phones
        profiles = []
        for phone in matching_phones:
            profile = session.query(UserProfile).filter_by(phone_number=phone).first()
            if profile:
                profiles.append(profile)
            else:
                # Create a basic profile if none exists
                profile = UserProfile(phone_number=phone, display_name=phone)
                profiles.append(profile)
        
        return profiles
    except Exception as e:
        logger.error(f"Error finding matching users: {e}")
        return []
    finally:
        session.close()


def get_or_create_user_profile(phone_number: str, bio: str = None, display_name: str = None):
    """Get or create a user profile"""
    session = get_db_session()
    try:
        profile = session.query(UserProfile).filter_by(phone_number=phone_number).first()
        if not profile:
            profile = UserProfile(
                phone_number=phone_number,
                bio=bio or f"User speaking {phone_number}",
                display_name=display_name or phone_number
            )
            session.add(profile)
            session.commit()
        return profile
    except Exception as e:
        session.rollback()
        logger.error(f"Error getting/creating user profile: {e}")
        return None
    finally:
        session.close()

