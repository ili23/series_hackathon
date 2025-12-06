"""
Voice message processing using local OpenAI Whisper for transcription
"""
import logging
import os
import requests
import tempfile
import whisper
import subprocess
import shutil

logger = logging.getLogger(__name__)

# Load Whisper model (lazy loading - only load when needed)
_whisper_model = None


def get_whisper_model():
    """Get or load Whisper model (lazy loading)"""
    global _whisper_model
    if _whisper_model is None:
        logger.info("Loading Whisper model...")
        _whisper_model = whisper.load_model("base")
        logger.debug("Whisper model loaded")
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


def check_ffmpeg():
    """Check if ffmpeg is available in PATH"""
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        logger.info(f"Found ffmpeg at: {ffmpeg_path}")
        return True
    else:
        logger.warning("ffmpeg not found in PATH. Whisper requires ffmpeg to process audio files.")
        logger.warning("Please install ffmpeg: https://ffmpeg.org/download.html")
        logger.warning("Or use: choco install ffmpeg (if Chocolatey is installed)")
        return False


def convert_audio_to_wav(input_path: str, output_path: str = None):
    """
    Convert audio file to WAV format using ffmpeg if available
    
    Args:
        input_path: Path to input audio file
        output_path: Path to output WAV file (optional, creates temp file if not provided)
    
    Returns:
        Path to converted WAV file, or original path if conversion not needed/failed
    """
    if not output_path:
        output_path = input_path.rsplit('.', 1)[0] + '.wav'
    
    ffmpeg_path = shutil.which('ffmpeg')
    if not ffmpeg_path:
        logger.warning("ffmpeg not found, trying to use original file")
        return input_path
    
    try:
        # Convert to WAV format (16kHz, mono, 16-bit PCM)
        cmd = [
            ffmpeg_path,
            '-i', input_path,
            '-ar', '16000',  # Sample rate 16kHz (Whisper's requirement)
            '-ac', '1',      # Mono channel
            '-acodec', 'pcm_s16le',  # 16-bit PCM
            '-y',            # Overwrite output file
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            logger.info(f"Converted audio to WAV: {output_path}")
            return output_path
        else:
            logger.warning(f"ffmpeg conversion failed: {result.stderr}")
            return input_path
    except Exception as e:
        logger.warning(f"Error converting audio: {e}, using original file")
        return input_path


def transcribe_voice_message_from_url(url: str):
    """
    Transcribe a voice message from a URL using local Whisper model
    
    Args:
        url: URL to the audio file (mp4a, mp3, or other audio format)
    
    Returns:
        dict with 'text', 'language', 'original_text', and 'success' keys
    """
    temp_path = None
    converted_path = None
    
    try:
        logger.debug(f"Transcribing from URL: {url}")
        
        # Check for ffmpeg
        check_ffmpeg()
        
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
        
        # Create a temporary file with appropriate extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name
        logger.info(f"Saved audio to temporary file: {temp_path}")
        
        # Try to convert to WAV if not already WAV (helps with compatibility)
        if file_extension != '.wav':
            converted_path = convert_audio_to_wav(temp_path)
            audio_path = converted_path if converted_path != temp_path else temp_path
        else:
            audio_path = temp_path
        try:
            # Load Whisper model
            model = get_whisper_model()
            
            # First, transcribe in original language

            logger.info("Transcribing in original language...")
            result_original = model.transcribe(audio_path, task="transcribe")
            original_text = result_original.get('text', '').strip()
            detected_language = result_original.get('language', 'unknown')
            
            # Then, translate to English
            logger.info("Translating to English...")
            result_english = model.transcribe(audio_path, task="translate")
            english_text = result_english.get('text', '').strip()
            
            logger.debug(f"Transcribed [{detected_language}]: {len(original_text)} chars → EN: {len(english_text)} chars")
            
            return {
                'success': True,
                'text': english_text,  # English translation
                'original_text': original_text,  # Original language text
                'language': detected_language,
            }
            
        finally:
            # Clean up temporary files
            for path in [temp_path, converted_path]:
                if path and path != temp_path and os.path.exists(path):
                    try:
                        os.unlink(path)
                        logger.debug(f"Deleted temp file: {path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete temp file {path}: {e}")
            
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_path}: {e}")
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading audio from URL: {e}")
        return {'success': False, 'error': f'Failed to download audio: {e}'}
    except FileNotFoundError as e:
        error_msg = str(e)
        if 'ffmpeg' in error_msg.lower() or 'The system cannot find the file specified' in error_msg:
            logger.error("ffmpeg is required but not found. Please install ffmpeg:")
            logger.error("  Windows: choco install ffmpeg (or download from https://ffmpeg.org/download.html)")
            logger.error("  Or add ffmpeg to your system PATH")
            return {'success': False, 'error': 'ffmpeg not found. Please install ffmpeg to process audio files.'}
        else:
            logger.error(f"Error transcribing voice message: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
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
        
        converted_path = None
        
        try:
            # Check for ffmpeg
            check_ffmpeg()
            
            # Try to convert to WAV if not already WAV (helps with compatibility)
            file_ext = os.path.splitext(temp_path)[1].lower()
            if file_ext != '.wav':
                converted_path = convert_audio_to_wav(temp_path)
                audio_path = converted_path if converted_path != temp_path else temp_path
            else:
                audio_path = temp_path
            
            # Load Whisper model
            model = get_whisper_model()
            
            # First, transcribe in original language
            logger.info("Transcribing in original language...")
            result_original = model.transcribe(audio_path, task="transcribe")
            original_text = result_original.get('text', '').strip()
            detected_language = result_original.get('language', 'unknown')
            
            # Then, translate to English
            if translate_to_english:
                logger.info("Translating to English...")
                result_english = model.transcribe(audio_path, task="translate")
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
            
        except FileNotFoundError as e:
            error_msg = str(e)
            if 'ffmpeg' in error_msg.lower() or 'The system cannot find the file specified' in error_msg:
                logger.error("ffmpeg is required but not found. Please install ffmpeg:")
                logger.error("  Windows: choco install ffmpeg (or download from https://ffmpeg.org/download.html)")
                logger.error("  Or add ffmpeg to your system PATH")
                return {'success': False, 'error': 'ffmpeg not found. Please install ffmpeg to process audio files.'}
            else:
                raise
        finally:
            # Clean up temporary files
            for path in [temp_path, converted_path]:
                if path and path != temp_path and os.path.exists(path):
                    try:
                        os.unlink(path)
                        logger.debug(f"Deleted temp file: {path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete temp file {path}: {e}")
            
            if temp_path and os.path.exists(temp_path):
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
