"""
Voice message processing using OpenAI Whisper API for transcription
"""
import logging
import os
import requests
import tempfile
from openai import OpenAI
from config import OPENAI_CONFIG

logger = logging.getLogger(__name__)

# Initialize OpenAI client
_openai_client = None


def get_openai_client():
    """Get or initialize OpenAI client"""
    global _openai_client
    if _openai_client is None:
        api_key = OPENAI_CONFIG.get('api_key')
        if not api_key:
            logger.warning("OPENAI_API_KEY not set")
        _openai_client = OpenAI(api_key=api_key) if api_key else None
    return _openai_client


def is_audio_attachment(attachment):
    """Check if attachment is an audio/voice message"""
    mime_type = attachment.get('mime_type', '').lower()
    audio_types = ['audio/m4a', 'audio/aac', 'audio/mp4', 'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4a']
    return any(mime_type.startswith(audio_type) for audio_type in audio_types)


def transcribe_voice_message_from_url(url: str):
    """
    Transcribe a voice message from a URL using OpenAI Whisper API
    
    Args:
        url: URL to the audio file (mp4a or other audio format)
    
    Returns:
        dict with 'text', 'language', 'original_text', and 'success' keys
    """
    try:
        client = get_openai_client()
        if not client:
            return {'success': False, 'error': 'OpenAI client not initialized. Please set OPENAI_API_KEY.'}
        
        logger.info(f"Transcribing voice message from URL: {url}")
        
        # Download the audio file temporarily for OpenAI API
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.m4a') as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name
        
        try:
            # First, transcribe in original language to get original text
            with open(temp_path, 'rb') as audio_file:
                transcript_original = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
            
            original_text = transcript_original.text.strip()
            detected_language = transcript_original.language if hasattr(transcript_original, 'language') else 'unknown'
            
            # Then, translate to English
            with open(temp_path, 'rb') as audio_file:
                transcript_english = client.audio.translations.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
            
            english_text = transcript_english.text.strip()
            
            logger.info("Transcription successful")
            logger.info(f"  Original language: {detected_language}")
            logger.info(f"  Original text length: {len(original_text)} characters")
            logger.info(f"  English text length: {len(english_text)} characters")
            
            return {
                'success': True,
                'text': english_text,  # English translation
                'original_text': original_text,  # Original language text
                'language': detected_language,
            }
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_path}: {e}")
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading audio from URL: {e}")
        return {'success': False, 'error': f'Failed to download audio: {e}'}
    except Exception as e:
        logger.error(f"Error transcribing voice message: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


def transcribe_voice_message(attachment, translate_to_english=True):
    """
    Transcribe a voice message attachment to text using OpenAI Whisper API
    
    Args:
        attachment: Attachment dict with filename, mime_type, url (or data_base64)
        translate_to_english: If True, translate to English; if False, keep original language
    
    Returns:
        dict with 'text', 'original_text', 'language', and 'success' keys
    """
    try:
        # Check if it's an audio file
        if not is_audio_attachment(attachment):
            logger.warning(f"Attachment is not audio: {attachment.get('mime_type')}")
            return {'success': False, 'error': 'Not an audio attachment'}
        
        # Prefer URL if available
        url = attachment.get('url')
        if url:
            logger.info("Using URL for transcription")
            return transcribe_voice_message_from_url(url)
        
        # Fallback to base64 if URL not available
        import base64
        
        data_base64 = attachment.get('data_base64')
        if not data_base64:
            return {'success': False, 'error': 'No URL or data_base64 found in attachment'}
        
        # Decode base64 data
        try:
            audio_data = base64.b64decode(data_base64)
        except Exception as e:
            logger.error(f"Error decoding base64 audio: {e}")
            return {'success': False, 'error': f'Failed to decode audio: {e}'}
        
        if not audio_data:
            return {'success': False, 'error': 'No audio data found'}
        
        # Determine file extension from filename
        filename = attachment.get('filename', 'voice.m4a')
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1] or '.m4a') as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        try:
            client = get_openai_client()
            if not client:
                return {'success': False, 'error': 'OpenAI client not initialized. Please set OPENAI_API_KEY.'}
            
            # First, transcribe in original language
            with open(temp_path, 'rb') as audio_file:
                transcript_original = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
            
            original_text = transcript_original.text.strip()
            detected_language = transcript_original.language if hasattr(transcript_original, 'language') else 'unknown'
            
            # Then, translate to English
            with open(temp_path, 'rb') as audio_file:
                transcript_english = client.audio.translations.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
            
            english_text = transcript_english.text.strip()
            
            logger.info("Transcription successful")
            logger.info(f"  Original language: {detected_language}")
            
            return {
                'success': True,
                'text': english_text,  # English translation
                'original_text': original_text,  # Original language text
                'language': detected_language,
            }
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_path}: {e}")
                
    except Exception as e:
        logger.error(f"Error transcribing voice message: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


def process_voice_attachments(attachments, translate_to_english=True):
    """
    Process multiple voice attachments and return transcriptions
    
    Args:
        attachments: List of attachment dicts
        translate_to_english: If True, translate to English
    
    Returns:
        List of transcription results
    """
    if not attachments:
        return []
    
    results = []
    for i, attachment in enumerate(attachments):
        if is_audio_attachment(attachment):
            logger.info(f"Processing voice attachment {i+1}/{len(attachments)}")
            result = transcribe_voice_message(attachment, translate_to_english)
            results.append(result)
        else:
            logger.debug(f"Skipping non-audio attachment: {attachment.get('mime_type')}")
    
    return results
