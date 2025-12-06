"""
Event handlers for processing Kafka events
"""
import json
import logging
from datetime import datetime
from backend.services.voice_processor import process_voice_attachments, is_audio_attachment
from backend.services.language_mapper import get_language_name
from backend.db.accessors import add_voice_message, add_to_user_table
from backend.services.conversation_flow import handle_new_language_detected, process_conversation, reset_conversation
from backend.api.series_api_client import send_message

logger = logging.getLogger(__name__)


def handle_message_received(event_data):
    """Handle message.received events"""
    # Extract relevant information
    message_id = event_data.get('id')
    chat_id = event_data.get('chat_id')
    from_phone = event_data.get('from_phone')
    text = event_data.get('text')
    is_read = event_data.get('is_read')
    attachments = event_data.get('attachments', [])
    
    logger.info(f"Message from {from_phone} (chat:{chat_id}): {text[:50] if text else 'no text'}")
    
    # Check for voice message attachments
    if attachments:
        # Check if any are voice/audio messages
        voice_attachments = [att for att in attachments if is_audio_attachment(att)]
        
        if voice_attachments:
            logger.info(f"Transcribing {len(voice_attachments)} voice message(s)...")
            
            # Reset conversation state on new voice messages to restart workflows
            if from_phone:
                reset_conversation(from_phone)
            
            # Process voice attachments (transcribe to English using local Whisper)
            transcriptions = process_voice_attachments(voice_attachments, translate_to_english=True)
            
            for i, transcription in enumerate(transcriptions):
                if transcription.get('success'):
                    english_text = transcription.get('text', '')
                    original_text = transcription.get('original_text', '')
                    language_code = transcription.get('language', 'unknown')
                    language_name = get_language_name(language_code)
                    
                    # Log transcription results
                    if original_text and original_text != english_text:
                        logger.info(f"Transcribed [{language_name}]: {original_text[:100]} → EN: {english_text[:100]}")
                    else:
                        logger.info(f"Transcribed [{language_name}]: {english_text[:100]}")
                    
                    # Get attachment URL or use a placeholder
                    attachment_url = voice_attachments[i].get('url', f'voice_message_{message_id}_{i}')
                    attachment_filename = voice_attachments[i].get('filename', 'voice.m4a')
                    attachment_mime_type = voice_attachments[i].get('mime_type', 'audio/m4a')
                    
                    # Store voice message in database
                    if from_phone:
                        # Ensure user exists in database
                        try:
                            add_to_user_table(from_phone, "", "")  # Will create or update user
                        except Exception as e:
                            logger.error(f"Error ensuring user in database: {e}", exc_info=True)
                        
                        # Add voice message
                        try:
                            voice_msg_id = add_voice_message(
                                phone_number=from_phone,
                                transcription=original_text,  # Store original language transcription
                                url=attachment_url,
                                primary_language=language_code,
                                metadata={
                                    'filename': attachment_filename,
                                    'mime_type': attachment_mime_type
                                },
                                timestamp=datetime.utcnow()
                            )
                            
                            if voice_msg_id:
                                logger.info(f"Saved voice message (ID: {voice_msg_id}) for {from_phone}")
                                
                                # Send transcribed message back to user as confirmation
                                try:
                                    response_message = f"📝 Transcribed: {original_text}"
                                    if english_text and english_text != original_text:
                                        response_message += f"\n🇬🇧 English: {english_text}"
                                    response_message += f"\n🌐 Language: {language_name}"
                                    
                                    send_message(from_phone, response_message, chat_id)
                                except Exception as e:
                                    logger.error(f"Error sending transcription confirmation: {e}", exc_info=True)
                                
                                # Check if this is a new language and trigger conversation flow
                                try:
                                    from backend.services.conversation_flow import is_new_language_for_user, handle_existing_language_detected
                                    if is_new_language_for_user(from_phone, language_name):
                                        logger.info(f"New language {language_name} detected for {from_phone}")
                                        handle_new_language_detected(from_phone, language_name, chat_id)
                                    else:
                                        logger.info(f"Existing language {language_name} detected for {from_phone}")
                                        handle_existing_language_detected(from_phone, language_name, chat_id)
                                except Exception as e:
                                    logger.error(f"Error processing language workflow: {e}", exc_info=True)
                            else:
                                logger.error(f"Failed to save voice message (add_voice_message returned None)")
                        except Exception as e:
                            logger.error(f"Error saving voice message: {e}", exc_info=True)
                    else:
                        logger.warning(f"Cannot save voice message: from_phone missing")
                else:
                    error = transcription.get('error', 'Unknown error')
                    logger.error(f"Transcription failed for {from_phone} (msg:{message_id}): {error}")
    
    # Process text messages for conversation flow
    if text and from_phone:
        # Check if there's an active conversation state
        process_conversation(from_phone, text, chat_id)


def handle_typing_indicator_received(event_data):
    """Handle typing_indicator.received events"""
    chat_id = event_data.get('chat_id')
    logger.debug(f"Typing indicator received for chat {chat_id}")
    
    # TODO: Add your business logic here
    # - Update UI with typing indicator
    # - Store typing state
    # etc.


def handle_typing_indicator_removed(event_data):
    """Handle typing_indicator.removed events"""
    chat_id = event_data.get('chat_id')
    logger.debug(f"Typing indicator removed for chat {chat_id}")
    
    # TODO: Add your business logic here
    # - Remove typing indicator from UI
    # - Update typing state
    # etc.


def process_kafka_event(event):
    """Process incoming Kafka events"""
    try:
        event_type = event.get('event_type')
        data = event.get('data', {})
        
        if event_type == 'message.received':
            handle_message_received(data)
        elif event_type == 'typing_indicator.received':
            handle_typing_indicator_received(data)
        elif event_type == 'typing_indicator.removed':
            handle_typing_indicator_removed(data)
        else:
            logger.warning(f"Unknown event type: {event_type}")
            
    except Exception as e:
        logger.error(f"Error processing {event_type}: {e}", exc_info=True)
        raise

