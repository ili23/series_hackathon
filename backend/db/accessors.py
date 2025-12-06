"""
Public database accessor functions
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError
from .database import get_db_session
from .models import User, Language, VoiceMessage

logger = logging.getLogger(__name__)


def add_to_user_table(phone_number: str, f_name: str, l_name: str, bio: Optional[str] = None) -> bool:
    """
    Add a user to the user table (might just prefill this)
    
    Args:
        phone_number: User's phone number (primary key)
        f_name: First name
        l_name: Last name
        bio: Optional bio
    
    Returns:
        True if successful, False otherwise
    """
    session = get_db_session()
    try:
        # Check if user already exists
        existing_user = session.query(User).filter_by(phone_number=phone_number).first()
        if existing_user:
            logger.info(f"User {phone_number} already exists, updating...")
            existing_user.f_name = f_name
            existing_user.l_name = l_name
            if bio is not None:
                existing_user.bio = bio
            session.commit()
            return True
        
        # Create new user
        user = User(
            phone_number=phone_number,
            f_name=f_name,
            l_name=l_name,
            bio=bio
        )
        session.add(user)
        session.commit()
        logger.info(f"Added user: {phone_number}")
        return True
        
    except IntegrityError as e:
        session.rollback()
        logger.error(f"Error adding user {phone_number}: {e}")
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error adding user {phone_number}: {e}", exc_info=True)
        return False
    finally:
        session.close()


def add_language_for_user(language_name: str, phone_number: str, proficiency: Optional[str] = None) -> bool:
    """
    Add a language for a user
    
    Args:
        language_name: Name of the language
        phone_number: User's phone number
        proficiency: Optional proficiency level
    
    Returns:
        True if successful, False otherwise
    """
    session = get_db_session()
    try:
        # Check if user exists
        user = session.query(User).filter_by(phone_number=phone_number).first()
        if not user:
            logger.warning(f"User {phone_number} not found. Creating user first...")
            # Create a basic user entry
            user = User(
                phone_number=phone_number,
                f_name="",
                l_name=""
            )
            session.add(user)
            session.flush()
        
        # Check if language already exists for this user
        existing_lang = session.query(Language).filter_by(
            phone_number=phone_number,
            language_name=language_name
        ).first()
        
        if existing_lang:
            logger.info(f"Language {language_name} already exists for {phone_number}, updating proficiency...")
            if proficiency is not None:
                existing_lang.proficiency = proficiency
            session.commit()
            return True
        
        # Create new language entry
        language = Language(
            phone_number=phone_number,
            language_name=language_name,
            proficiency=proficiency
        )
        session.add(language)
        session.commit()
        logger.info(f"Added language {language_name} for user {phone_number}")
        return True
        
    except IntegrityError as e:
        session.rollback()
        logger.error(f"Error adding language {language_name} for {phone_number}: {e}")
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error adding language: {e}", exc_info=True)
        return False
    finally:
        session.close()


def add_voice_message(
    phone_number: str,
    transcription: str,
    url: str,
    primary_language: str,
    metadata: Optional[Dict[str, Any]] = None,
    other_languages: Optional[str] = None,
    timestamp: Optional[Any] = None
) -> Optional[int]:
    """
    Add a voice message to the database
    
    Args:
        phone_number: User's phone number
        transcription: Transcription text in primary language
        url: File storage URL/path
        primary_language: Primary language code
        metadata: Optional dict with file_size, duration, mime_type, filename
        other_languages: Optional other languages (JSON string or comma-separated)
        timestamp: Optional timestamp (datetime object), defaults to now
    
    Returns:
        Voice message ID if successful, None otherwise
    """
    from datetime import datetime
    
    session = get_db_session()
    try:
        # Check if user exists, create if not
        user = session.query(User).filter_by(phone_number=phone_number).first()
        if not user:
            logger.warning(f"User {phone_number} not found. Creating user first...")
            user = User(
                phone_number=phone_number,
                f_name="",
                l_name=""
            )
            session.add(user)
            session.flush()
        
        # Extract metadata
        file_size = metadata.get('file_size') if metadata else None
        duration = metadata.get('duration') if metadata else None
        mime_type = metadata.get('mime_type') if metadata else None
        filename = metadata.get('filename') if metadata else None
        
        # Use provided timestamp or current time
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Create voice message
        voice_message = VoiceMessage(
            phone_number=phone_number,
            transcription_primary_language=transcription,
            url=url,
            primary_language=primary_language,
            other_languages=other_languages,
            timestamp=timestamp,
            file_size=file_size,
            duration=duration,
            mime_type=mime_type,
            filename=filename
        )
        
        session.add(voice_message)
        session.commit()
        
        message_id = voice_message.id
        logger.info(f"Added voice message {message_id} for user {phone_number}")
        return message_id
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding voice message: {e}", exc_info=True)
        return None
    finally:
        session.close()


def get_user_given_language(primary_language: str) -> List[Dict[str, Any]]:
    """
    Get all users who have a given language as their primary language
    
    Args:
        primary_language: Language code to search for
    
    Returns:
        List of user dictionaries with phone_number, f_name, l_name, bio
    """
    session = get_db_session()
    try:
        # Query users who have voice messages in the given primary language
        results = session.query(User).join(VoiceMessage).filter(
            VoiceMessage.primary_language == primary_language
        ).distinct().all()
        
        users = []
        for user in results:
            users.append({
                'phone_number': user.phone_number,
                'f_name': user.f_name,
                'l_name': user.l_name,
                'bio': user.bio
            })
        
        logger.info(f"Found {len(users)} users with primary language {primary_language}")
        return users
        
    except Exception as e:
        logger.error(f"Error getting users for language {primary_language}: {e}", exc_info=True)
        return []
    finally:
        session.close()

