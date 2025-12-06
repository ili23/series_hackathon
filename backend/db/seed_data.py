"""
Seed sample data into the database
"""
import logging
from datetime import datetime
from .database import get_db_session
from .models import User
from .accessors import add_to_user_table, add_language_for_user, add_voice_message

logger = logging.getLogger(__name__)


def seed_database():
    """Load sample data into the database if it's empty"""
    session = get_db_session()
    try:
        # Check if database already has data
        existing_users = session.query(User).count()
        if existing_users > 0:
            logger.info("Database already contains data, skipping seed")
            return True
        
        logger.info("Seeding database with sample data...")
        
        # Team members from info.md
        users = [
            {
                'phone_number': '+16469324962',
                'f_name': 'Iram',
                'l_name': 'Liu',
                'bio': 'Cornell student working on Series iMessage hackathon project'
            },
            {
                'phone_number': '+19172156679',
                'f_name': 'Crystal',
                'l_name': 'Liang',
                'bio': 'Team member working on Series iMessage hackathon project'
            },
            {
                'phone_number': '+16463230991',  # Sender number
                'f_name': 'System',
                'l_name': 'Bot',
                'bio': 'System sender number'
            }
        ]
        
        for user in users:
            success = add_to_user_table(
                phone_number=user['phone_number'],
                f_name=user['f_name'],
                l_name=user['l_name'],
                bio=user.get('bio')
            )
            if success:
                logger.info(f"  ✓ Added user: {user['f_name']} {user['l_name']} ({user['phone_number']})")
            else:
                logger.warning(f"  ✗ Failed to add user: {user['phone_number']}")
        
        # Add languages for users
        languages = [
            ('+16469324962', 'English'),
            ('+16469324962', 'Spanish'),
            ('+19172156679', 'English'),
            ('+19172156679', 'Mandarin'),
            ('+19172156679', 'French'),
        ]
        
        for phone_number, language_name in languages:
            success = add_language_for_user(
                language_name=language_name,
                phone_number=phone_number,
            )
            if success:
                logger.info(f"  ✓ Added {language_name} for {phone_number}")
            else:
                logger.warning(f"  ✗ Failed to add language {language_name} for {phone_number}")
        
        logger.info("Database seeding complete!")
        return True
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}", exc_info=True)
        return False
    finally:
        session.close()

