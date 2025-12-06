"""
Voice message processing using local OpenAI Whisper for transcription
"""
import logging
import os
import requests
import tempfile
import whisper

logger = logging.getLogger(__name__)

# Load Whisper model (lazy loading - only load when needed)
_whisper_model = None


def get_whisper_model():
    """Get or load Whisper model (lazy loading)"""
    global _whisper_model
    if _whisper_model is None:
        logger.info("Loading Whisper model (this may take a moment on first use)...")
        # Using 'base' model - good balance of speed and accuracy
        # Options: tiny, base, small, medium, large
        _whisper_model = whisper.load_model("base")
        logger.info("Whisper model loaded successfully")
    return _whisper_model


def is_audio_attachment(attachment):
    """Check if attachment is an audio/voice message"""
    mime_type = attachment.get('mime_type', '').lower()
    # Check if it starts with 'audio/' to catch all audio formats including audio/mp3, audio/mpeg, etc.
    if mime_type.startswith('audio/'):
        return True
    # Also check for specific known audio types for backward compatibility
    audio_types = ['audio/m4a', 'audio/aac', 'audio/mp4', 'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg', 'audio/mp4a']
    return any(mime_type.startswith(audio_type) for audio_type in audio_types)


def transcribe_voice_message_from_url(url: str):
    """
    Transcribe a voice message from a URL using local Whisper model
    
    Args:
        url: URL to the audio file (mp4a, mp3, or other audio format)
    
    Returns:
        dict with 'text', 'language', 'original_text', and 'success' keys
    """
    try:
        logger.info(f"Transcribing voice message from URL: {url}")
        
        # Download the audio file temporarily
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Determine file extension from Content-Type header or URL
        content_type = response.headers.get('Content-Type', '').lower()
        file_extension = '.m4a'  # default
        if 'mp3' in content_type or url.endswith('.mp3'):
            file_extension = '.mp3'
        elif 'mp4' in content_type or url.endswith('.mp4'):
            file_extension = '.mp4'
        elif 'wav' in content_type or url.endswith('.wav'):
            file_extension = '.wav'
        elif 'ogg' in content_type or url.endswith('.ogg'):
            file_extension = '.ogg'
        
        logger.info(f"Downloaded audio file, Content-Type: {content_type}, using extension: {file_extension}")
        
        # Create a temporary file with appropriate extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name
        
        logger.info(f"Saved audio to temporary file: {temp_path}")
        
        try:
            # Load Whisper model
            model = get_whisper_model()
            
            # First, transcribe in original language
            logger.info("Transcribing in original language...")
            result_original = model.transcribe(temp_path, task="transcribe")
            original_text = result_original.get('text', '').strip()
            detected_language = result_original.get('language', 'unknown')
            
            # Then, translate to English
            logger.info("Translating to English...")
            result_english = model.transcribe(temp_path, task="translate")
            english_text = result_english.get('text', '').strip()
            
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
    Transcribe a voice message attachment to text using local Whisper model
    
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
            # Load Whisper model
            model = get_whisper_model()
            
            # First, transcribe in original language
            logger.info("Transcribing in original language...")
            result_original = model.transcribe(temp_path, task="transcribe")
            original_text = result_original.get('text', '').strip()
            detected_language = result_original.get('language', 'unknown')
            
            # Then, translate to English
            if translate_to_english:
                logger.info("Translating to English...")
                result_english = model.transcribe(temp_path, task="translate")
                english_text = result_english.get('text', '').strip()
            else:
                english_text = original_text
            
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
