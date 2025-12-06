"""
Database models for Series iMessage Backend
"""
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    """User table"""
    __tablename__ = 'users'
    
    phone_number = Column(String, primary_key=True)
    f_name = Column(String, nullable=False)
    l_name = Column(String, nullable=False)
    bio = Column(Text, nullable=True)
    # Last outbound agent message text for conversation continuity
    last_agent_sent_message = Column(Text, nullable=True)
    # Persist minimal conversation context so we can rebuild state across events
    last_agent_state = Column(String, nullable=True)
    last_agent_language = Column(String, nullable=True)
    last_agent_matched_phone = Column(String, nullable=True)
    # Comma-separated list of phones that have been shown to the user
    last_agent_shown_phones = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    languages = relationship('Language', back_populates='user', cascade='all, delete-orphan')
    voice_messages = relationship('VoiceMessage', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<User(phone_number='{self.phone_number}', name='{self.f_name} {self.l_name}')>"


class Language(Base):
    """Languages table - tracks languages for each user"""
    __tablename__ = 'languages'
    
    phone_number = Column(String, ForeignKey('users.phone_number', ondelete='CASCADE'), primary_key=True)
    language_name = Column(String, primary_key=True)
    proficiency = Column(String, nullable=True)  # Optional proficiency level
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship('User', back_populates='languages')
    
    def __repr__(self):
        return f"<Language(phone_number='{self.phone_number}', language='{self.language_name}')>"


class VoiceMessage(Base):
    """All Voice Messages table"""
    __tablename__ = 'voice_messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String, ForeignKey('users.phone_number', ondelete='CASCADE'), nullable=False)
    transcription_primary_language = Column(Text, nullable=False)
    url = Column(String, nullable=False)  # File storage URL/path
    primary_language = Column(String, nullable=False)
    other_languages = Column(Text, nullable=True)  # JSON string or comma-separated
    timestamp = Column(DateTime, nullable=False)
    
    # Additional file metadata
    file_size = Column(Integer, nullable=True)  # Size in bytes
    duration = Column(Float, nullable=True)  # Duration in seconds
    mime_type = Column(String, nullable=True)
    filename = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship('User', back_populates='voice_messages')
    
    def __repr__(self):
        return f"<VoiceMessage(id={self.id}, phone_number='{self.phone_number}', language='{self.primary_language}')>"

