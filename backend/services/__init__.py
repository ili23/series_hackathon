"""
Service modules for processing events, voice, and conversations
"""
from .event_handlers import process_kafka_event, handle_message_received
from .voice_processor import process_voice_attachments, is_audio_attachment
from .conversation_flow import handle_new_language_detected, process_conversation
from .language_mapper import get_language_name

__all__ = [
    'process_kafka_event',
    'handle_message_received',
    'process_voice_attachments',
    'is_audio_attachment',
    'handle_new_language_detected',
    'process_conversation',
    'get_language_name',
]

