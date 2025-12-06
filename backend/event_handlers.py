"""
Event handlers for processing Kafka events
"""
import json
import logging
from datetime import datetime
from voice_processor import process_voice_attachments, is_audio_attachment
from language_mapper import get_language_name
from db.accessors import add_voice_message, add_to_user_table
from conversation_flow import (
    handle_new_language_detected, 
    handle_existing_language_detected, 
    process_conversation,
    is_yes_response
)

logger = logging.getLogger(__name__)


def handle_message_received(event_data):
    """Handle message.received events"""
    logger.info(f"Message received event: {json.dumps(event_data, indent=2)}")
    
    # Extract relevant information
    message_id = event_data.get('id')
    chat_id = event_data.get('chat_id')
    from_phone = event_data.get('from_phone')  # User who sent the message (will receive agent responses)
    text = event_data.get('text')
    is_read = event_data.get('is_read')
    attachments = event_data.get('attachments', [])
    
    logger.info(f"📨 INCOMING MESSAGE: From user {from_phone} in chat {chat_id}: {text}")
    logger.info(f"   Agent number (+16463230991) will respond to user: {from_phone}")
    
    # Check for voice message attachments
    if attachments:
        logger.info(f"Message has {len(attachments)} attachment(s)")
        
        # Log all attachment types for debugging
        for i, att in enumerate(attachments):
            logger.info(f"  Attachment {i+1}: mime_type={att.get('mime_type')}, filename={att.get('filename')}, is_audio={is_audio_attachment(att)}")
        
        # Check if any are voice/audio messages
        voice_attachments = [att for att in attachments if is_audio_attachment(att)]
        
        if voice_attachments:
            logger.info(f"🎤 VOICE MESSAGE DETECTED: Found {len(voice_attachments)} voice message(s) from user {from_phone}")
            logger.info(f"   Transcribing with local Whisper...")
            logger.info(f"   Agent (+16463230991) will automatically respond after transcription if new language detected")
            
            # Log URLs for debugging
            for i, att in enumerate(voice_attachments):
                url = att.get('url')
                if url:
                    logger.info(f"  Voice attachment {i+1} URL: {url}")
                else:
                    logger.warning(f"  Voice attachment {i+1} has no URL, will try data_base64 if available")
            
            # Process voice attachments (transcribe to English using local Whisper)
            # This will use URLs if available, or fall back to data_base64
            transcriptions = process_voice_attachments(voice_attachments, translate_to_english=True)
            
            for i, transcription in enumerate(transcriptions):
                if transcription.get('success'):
                    english_text = transcription.get('text', '')
                    original_text = transcription.get('original_text', '')
                    language_code = transcription.get('language', 'unknown')
                    language_name = get_language_name(language_code)
                    
                    # Print detailed transcription results
                    print("\n" + "="*80)
                    print("VOICE MESSAGE TRANSCRIPTION SUCCESSFUL")
                    print("="*80)
                    print(f"Message ID: {message_id}")
                    print(f"From Phone: {from_phone}")
                    print(f"Chat ID: {chat_id}")
                    print(f"\n📝 Transcription (English):")
                    print(f"   {english_text}")
                    if original_text and original_text != english_text:
                        print(f"\n🌍 Original Language ({language_name}):")
                        print(f"   {original_text}")
                    print(f"\n🌐 Language Information:")
                    print(f"   Language Code: {language_code}")
                    print(f"   Language Name: {language_name}")
                    print("="*80 + "\n")
                    
                    logger.info(f"Voice message {i+1} transcription (English): {english_text}")
                    if original_text and original_text != english_text:
                        logger.info(f"Voice message {i+1} transcription (Original): {original_text}")
                    logger.info(f"  Detected language code: {language_code}")
                    logger.info(f"  Language name: {language_name}")
                    
                    # Log specifically for Chinese and Spanish detection
                    if language_code.lower().startswith('zh') or language_name.lower() == 'chinese':
                        logger.info(f"🇨🇳 CHINESE DETECTED: Language code '{language_code}' mapped to '{language_name}'")
                    elif language_code.lower().startswith('es') or language_name.lower() == 'spanish':
                        logger.info(f"🇪🇸 SPANISH DETECTED: Language code '{language_code}' mapped to '{language_name}'")
                    
                    # Get attachment URL or use a placeholder
                    attachment_url = voice_attachments[i].get('url', f'voice_message_{message_id}_{i}')
                    attachment_filename = voice_attachments[i].get('filename', 'voice.m4a')
                    attachment_mime_type = voice_attachments[i].get('mime_type', 'audio/m4a')
                    
                    # Store voice message in database
                    if from_phone:
                        logger.info(f"Storing voice message in database for {from_phone}...")
                        # Ensure user exists in database
                        try:
                            add_to_user_table(from_phone, "", "")  # Will create or update user
                            logger.info(f"User {from_phone} ensured in database")
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
                                print(f"✅ Successfully saved voice message to database (ID: {voice_msg_id})")
                                logger.info(f"Successfully saved voice message {voice_msg_id} to database for {from_phone}")
                                
                                # Check if this is a new language and trigger conversation flow
                                try:
                                    from conversation_flow import is_new_language_for_user
                                    if is_new_language_for_user(from_phone, language_name):
                                        print(f"🆕 New language detected: {language_name} for {from_phone}")
                                        logger.info(f"New language {language_name} detected for {from_phone}, starting conversation flow")
                                        logger.info(f"🤖 AGENT AUTO-RESPONSE: Agent number (+16463230991) will automatically send message to user {from_phone} about new language {language_name}")
                                        handle_new_language_detected(from_phone, language_name, chat_id)
                                    else:
                                        print(f"✅ Language {language_name} already exists for {from_phone}")
                                        logger.info(f"Language {language_name} already exists for {from_phone}")
                                        # Trigger workflow for existing language - ask if they want to be matched
                                        logger.info(f"🤖 AGENT AUTO-RESPONSE: Agent number (+16463230991) will automatically send message to user {from_phone} about existing language {language_name}")
                                        handle_existing_language_detected(from_phone, language_name, chat_id)
                                except Exception as e:
                                    logger.error(f"Error checking/processing new language: {e}", exc_info=True)
                            else:
                                print(f"⚠️  Failed to save voice message to database (add_voice_message returned None)")
                                logger.error(f"Failed to save voice message to database for {from_phone} - add_voice_message returned None")
                        except Exception as e:
                            print(f"⚠️  Exception while saving voice message to database: {e}")
                            logger.error(f"Exception while saving voice message to database for {from_phone}: {e}", exc_info=True)
                    else:
                        logger.warning(f"Cannot save voice message: from_phone is missing or None")
                else:
                    error = transcription.get('error', 'Unknown error')
                    print("\n" + "="*80)
                    print("VOICE MESSAGE TRANSCRIPTION FAILED")
                    print("="*80)
                    print(f"Message ID: {message_id}")
                    print(f"From Phone: {from_phone}")
                    print(f"Error: {error}")
                    print("="*80 + "\n")
                    logger.error(f"Failed to transcribe voice message {i+1}: {error}")
    
    # Process text messages for conversation flow
    # Parse text attribute and from_phone number to continue workflow
    if text and from_phone:
        text_cleaned = text.strip() if text else ""
        logger.info(f"📨 TEXT MESSAGE RECEIVED: From {from_phone}, text: '{text_cleaned[:100]}{'...' if len(text_cleaned) > 100 else ''}'")
        logger.info(f"   Parsing response: text='{text_cleaned}', from_phone='{from_phone}'")
        
        # Check if response contains "yes" to continue workflow
        is_yes = is_yes_response(text_cleaned)
        logger.info(f"   Response analysis: is_yes={is_yes}, will continue workflow if in active state")
        
        logger.info(f"   Agent (+16463230991) will process this response and continue workflow")
        logger.info(f"   Processing conversation flow for user {from_phone}")
        
        # Process conversation - this will parse "yes" responses and continue workflow:
        # - If "yes" to add language → adds user to language database, continues workflow
        # - If "yes" to matching → sends random user profile from database, continues workflow
        # - If "yes" to group chat → creates group chat via iMessage API, exits workflow
        # - If "no" at any point → exits workflow
        # Workflow continues through states until completion or exit
        process_conversation(from_phone, text_cleaned, chat_id)


def handle_typing_indicator_received(event_data):
    """Handle typing_indicator.received events"""
    logger.info(f"Typing indicator received: {json.dumps(event_data, indent=2)}")
    
    chat_id = event_data.get('chat_id')
    display = event_data.get('display')
    
    logger.info(f"User started typing in chat {chat_id}")
    
    # TODO: Add your business logic here
    # - Update UI with typing indicator
    # - Store typing state
    # etc.


def handle_typing_indicator_removed(event_data):
    """Handle typing_indicator.removed events"""
    logger.info(f"Typing indicator removed: {json.dumps(event_data, indent=2)}")
    
    chat_id = event_data.get('chat_id')
    
    logger.info(f"User stopped typing in chat {chat_id}")
    
    # TODO: Add your business logic here
    # - Remove typing indicator from UI
    # - Update typing state
    # etc.


def process_kafka_event(event):
    """Process incoming Kafka events"""
    try:
        event_type = event.get('event_type')
        data = event.get('data', {})
        
        logger.info(f"Processing event: {event_type}")
        
        if event_type == 'message.received':
            handle_message_received(data)
        elif event_type == 'typing_indicator.received':
            handle_typing_indicator_received(data)
        elif event_type == 'typing_indicator.removed':
            handle_typing_indicator_removed(data)
        else:
            logger.warning(f"Unknown event type: {event_type} - event will be logged but not processed")
            logger.debug(f"Full event data: {json.dumps(event, indent=2)}")
            
    except Exception as e:
        logger.error(f"Error processing event: {e}", exc_info=True)
        # Re-raise to ensure the error is logged at the Kafka consumer level too
        raise

