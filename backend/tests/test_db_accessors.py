"""
Pytest tests for database accessor functions
"""
import pytest
from datetime import datetime
import sys
import os
from unittest.mock import patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.db.models import User, Language, VoiceMessage
from backend.db.accessors import (
    add_to_user_table,
    add_language_for_user,
    add_voice_message,
    get_user_given_language
)


class TestAddToUserTable:
    """Tests for add_to_user_table function"""
    
    def test_add_new_user(self, test_db, sample_user_data):
        """Test adding a new user"""
        with patch('backend.db.accessors.get_db_session', return_value=test_db()):
            result = add_to_user_table(
                phone_number=sample_user_data['phone_number'],
                f_name=sample_user_data['f_name'],
                l_name=sample_user_data['l_name'],
                bio=sample_user_data['bio']
            )
            assert result is True
            
            # Verify user was added
            session = test_db()
            user = session.query(User).filter_by(
                phone_number=sample_user_data['phone_number']
            ).first()
            assert user is not None
            assert user.f_name == sample_user_data['f_name']
            assert user.l_name == sample_user_data['l_name']
            assert user.bio == sample_user_data['bio']
            session.close()
    
    def test_update_existing_user(self, test_db, sample_user_data):
        """Test updating an existing user"""
        # First, create a user
        session = test_db()
        user = User(
            phone_number=sample_user_data['phone_number'],
            f_name='Old',
            l_name='Name',
            bio='Old bio'
        )
        session.add(user)
        session.commit()
        session.close()
        
        # Now update it
        with patch('backend.db.accessors.get_db_session', return_value=test_db()):
            result = add_to_user_table(
                phone_number=sample_user_data['phone_number'],
                f_name=sample_user_data['f_name'],
                l_name=sample_user_data['l_name'],
                bio=sample_user_data['bio']
            )
            assert result is True
            
            # Verify user was updated
            session = test_db()
            user = session.query(User).filter_by(
                phone_number=sample_user_data['phone_number']
            ).first()
            assert user.f_name == sample_user_data['f_name']
            assert user.l_name == sample_user_data['l_name']
            session.close()


class TestAddLanguageForUser:
    """Tests for add_language_for_user function"""
    
    def test_add_language_new_user(self, test_db, sample_language_data):
        """Test adding language for a new user (should create user)"""
        with patch('backend.db.accessors.get_db_session', return_value=test_db()):
            result = add_language_for_user(
                language_name=sample_language_data['language_name'],
                phone_number=sample_language_data['phone_number'],
            )
            assert result is True
            
            # Verify language was added and user was created
            session = test_db()
            user = session.query(User).filter_by(
                phone_number=sample_language_data['phone_number']
            ).first()
            assert user is not None
            
            language = session.query(Language).filter_by(
                phone_number=sample_language_data['phone_number'],
                language_name=sample_language_data['language_name']
            ).first()
            assert language is not None
            session.close()
    
    def test_add_multiple_languages(self, test_db, sample_language_data):
        """Test adding multiple languages for same user"""
        with patch('backend.db.accessors.get_db_session', return_value=test_db()):
            # Add first language
            result1 = add_language_for_user(
                language_name='English',
                phone_number=sample_language_data['phone_number'],
            )
            assert result1 is True
            
            # Add second language
            result2 = add_language_for_user(
                language_name='Spanish',
                phone_number=sample_language_data['phone_number'],
            )
            assert result2 is True
            
            # Verify both languages exist
            session = test_db()
            languages = session.query(Language).filter_by(
                phone_number=sample_language_data['phone_number']
            ).all()
            assert len(languages) == 2
            session.close()


class TestAddVoiceMessage:
    """Tests for add_voice_message function"""
    
    def test_add_voice_message(self, test_db, sample_voice_message_data):
        """Test adding a voice message"""
        with patch('backend.db.accessors.get_db_session', return_value=test_db()):
            message_id = add_voice_message(
                phone_number=sample_voice_message_data['phone_number'],
                transcription=sample_voice_message_data['transcription'],
                url=sample_voice_message_data['url'],
                primary_language=sample_voice_message_data['primary_language'],
                metadata=sample_voice_message_data['metadata'],
                other_languages=sample_voice_message_data['other_languages'],
                timestamp=sample_voice_message_data['timestamp']
            )
            assert message_id is not None
            assert isinstance(message_id, int)
            
            # Verify message was added
            session = test_db()
            message = session.query(VoiceMessage).filter_by(id=message_id).first()
            assert message is not None
            assert message.transcription_primary_language == sample_voice_message_data['transcription']
            assert message.url == sample_voice_message_data['url']
            assert message.primary_language == sample_voice_message_data['primary_language']
            assert message.file_size == sample_voice_message_data['metadata']['file_size']
            assert message.duration == sample_voice_message_data['metadata']['duration']
            session.close()
    
    def test_add_voice_message_creates_user(self, test_db, sample_voice_message_data):
        """Test that adding voice message creates user if doesn't exist"""
        with patch('backend.db.accessors.get_db_session', return_value=test_db()):
            # Add voice message for non-existent user
            message_id = add_voice_message(
                phone_number='+19999999999',
                transcription='Test',
                url='https://example.com/test.m4a',
                primary_language='en'
            )
            assert message_id is not None
            
            # Verify user was created
            session = test_db()
            user = session.query(User).filter_by(phone_number='+19999999999').first()
            assert user is not None
            session.close()


class TestGetUserGivenLanguage:
    """Tests for get_user_given_language function"""
    
    def test_get_users_by_language(self, test_db):
        """Test getting users by primary language"""
        # Create users with voice messages
        session = test_db()
        
        # User 1 with English voice message
        user1 = User(phone_number='+11111111111', f_name='John', l_name='Doe')
        session.add(user1)
        msg1 = VoiceMessage(
            phone_number='+11111111111',
            transcription_primary_language='Hello',
            url='https://example.com/1.m4a',
            primary_language='en',
            timestamp=datetime.utcnow()
        )
        session.add(msg1)
        
        # User 2 with Spanish voice message
        user2 = User(phone_number='+22222222222', f_name='Jane', l_name='Smith')
        session.add(user2)
        msg2 = VoiceMessage(
            phone_number='+22222222222',
            transcription_primary_language='Hola',
            url='https://example.com/2.m4a',
            primary_language='es',
            timestamp=datetime.utcnow()
        )
        session.add(msg2)
        
        # User 3 with English voice message
        user3 = User(phone_number='+33333333333', f_name='Bob', l_name='Johnson')
        session.add(user3)
        msg3 = VoiceMessage(
            phone_number='+33333333333',
            transcription_primary_language='Hi there',
            url='https://example.com/3.m4a',
            primary_language='en',
            timestamp=datetime.utcnow()
        )
        session.add(msg3)
        
        session.commit()
        session.close()
        
        # Test query
        with patch('backend.db.accessors.get_db_session', return_value=test_db()):
            users = get_user_given_language('en')
            assert len(users) == 2
            phone_numbers = [u['phone_number'] for u in users]
            assert '+11111111111' in phone_numbers
            assert '+33333333333' in phone_numbers
            assert '+22222222222' not in phone_numbers
            
            # Test with non-existent language
            users = get_user_given_language('fr')
            assert len(users) == 0


class TestDatabaseRelationships:
    """Tests for database relationships"""
    
    def test_user_languages_relationship(self, test_db):
        """Test user-languages relationship"""
        session = test_db()
        
        # Create user with languages
        user = User(phone_number='+15555555555', f_name='Test', l_name='User')
        session.add(user)
        session.flush()
        
        lang1 = Language(phone_number='+15555555555', language_name='English')
        lang2 = Language(phone_number='+15555555555', language_name='Spanish')
        session.add(lang1)
        session.add(lang2)
        session.commit()
        
        # Test relationship
        user = session.query(User).filter_by(phone_number='+15555555555').first()
        assert len(user.languages) == 2
        assert user.languages[0].language_name in ['English', 'Spanish']
        
        session.close()
    
    def test_user_voice_messages_relationship(self, test_db):
        """Test user-voice_messages relationship"""
        session = test_db()
        
        # Create user with voice messages
        user = User(phone_number='+16666666666', f_name='Test', l_name='User')
        session.add(user)
        session.flush()
        
        msg1 = VoiceMessage(
            phone_number='+16666666666',
            transcription_primary_language='Message 1',
            url='https://example.com/1.m4a',
            primary_language='en',
            timestamp=datetime.utcnow()
        )
        msg2 = VoiceMessage(
            phone_number='+16666666666',
            transcription_primary_language='Message 2',
            url='https://example.com/2.m4a',
            primary_language='en',
            timestamp=datetime.utcnow()
        )
        session.add(msg1)
        session.add(msg2)
        session.commit()
        
        # Test relationship
        user = session.query(User).filter_by(phone_number='+16666666666').first()
        assert len(user.voice_messages) == 2
        
        session.close()

