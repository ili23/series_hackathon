"""
Language code to language name mapping
"""
# Mapping of ISO 639-1 language codes to full language names
LANGUAGE_CODE_TO_NAME = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'tr': 'Turkish',
    'pl': 'Polish',
    'nl': 'Dutch',
    'sv': 'Swedish',
    'da': 'Danish',
    'no': 'Norwegian',
    'fi': 'Finnish',
    'cs': 'Czech',
    'hu': 'Hungarian',
    'ro': 'Romanian',
    'el': 'Greek',
    'he': 'Hebrew',
    'th': 'Thai',
    'vi': 'Vietnamese',
    'id': 'Indonesian',
    'ms': 'Malay',
    'uk': 'Ukrainian',
    'bg': 'Bulgarian',
    'hr': 'Croatian',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'et': 'Estonian',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
    'ga': 'Irish',
    'mt': 'Maltese',
    'cy': 'Welsh',
    'is': 'Icelandic',
    'mk': 'Macedonian',
    'sq': 'Albanian',
    'sr': 'Serbian',
    'bs': 'Bosnian',
    'ca': 'Catalan',
    'eu': 'Basque',
    'gl': 'Galician',
    'fa': 'Persian',
    'ur': 'Urdu',
    'bn': 'Bengali',
    'ta': 'Tamil',
    'te': 'Telugu',
    'ml': 'Malayalam',
    'kn': 'Kannada',
    'gu': 'Gujarati',
    'pa': 'Punjabi',
    'mr': 'Marathi',
    'ne': 'Nepali',
    'si': 'Sinhala',
    'my': 'Myanmar',
    'km': 'Khmer',
    'lo': 'Lao',
    'ka': 'Georgian',
    'am': 'Amharic',
    'sw': 'Swahili',
    'zu': 'Zulu',
    'af': 'Afrikaans',
    'az': 'Azerbaijani',
    'be': 'Belarusian',
    'hy': 'Armenian',
    'kk': 'Kazakh',
    'ky': 'Kyrgyz',
    'mn': 'Mongolian',
    'uz': 'Uzbek',
    'tg': 'Tajik',
    'tk': 'Turkmen',
}


def get_language_name(language_code: str) -> str:
    """
    Convert language code to full language name
    
    Args:
        language_code: ISO 639-1 language code (e.g., 'en', 'es', 'fr')
    
    Returns:
        Full language name or the code itself if not found
    """
    if not language_code:
        return 'Unknown'
    
    # Handle language codes with region (e.g., 'en-US' -> 'en')
    code = language_code.lower().split('-')[0].split('_')[0]
    
    return LANGUAGE_CODE_TO_NAME.get(code, language_code.capitalize())
