"""
Voice message processing using Whisper for transcription
"""
import base64
import logging
import os
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
    audio_types = ['audio/m4a', 'audio/aac', 'audio/mp4', 'audio/mpeg', 'audio/wav', 'audio/ogg']
    return any(mime_type.startswith(audio_type) for audio_type in audio_types)


def transcribe_voice_message(attachment, translate_to_english=True):
    """
    Transcribe a voice message attachment to text
    
    Args:
        attachment: Attachment dict with filename, mime_type, and data_base64
        translate_to_english: If True, translate to English; if False, keep original language
    
    Returns:
        dict with 'text', 'language', and 'success' keys
    """
    try:
        # Check if it's an audio file
        if not is_audio_attachment(attachment):
            logger.warning(f"Attachment is not audio: {attachment.get('mime_type')}")
            return {'success': False, 'error': 'Not an audio attachment'}
        
        # Decode base64 data
        try:
            audio_data = base64.b64decode(attachment.get('data_base64', ''))
        except Exception as e:
            logger.error(f"Error decoding base64 audio: {e}")
            return {'success': False, 'error': f'Failed to decode audio: {e}'}
        
        if not audio_data:
            return {'success': False, 'error': 'No audio data found'}
        
        # Determine file extension from mime_type
        mime_type = attachment.get('mime_type', '').lower()
        filename = attachment.get('filename', 'voice.m4a')
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1] or '.m4a') as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        try:
            # Load Whisper model
            model = get_whisper_model()
            
            # Transcribe (and optionally translate)
            task = "translate" if translate_to_english else "transcribe"
            logger.info(f"Transcribing voice message (task: {task})...")
            
            result = model.transcribe(temp_path, task=task)
            
            transcription = result.get('text', '').strip()
            detected_language = result.get('language', 'unknown')
            
            logger.info(f"Transcription successful: {len(transcription)} characters")
            logger.info(f"Detected language: {detected_language}")
            
            return {
                'success': True,
                'text': transcription,
                'language': detected_language,
                'original_language': detected_language if translate_to_english else None
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

