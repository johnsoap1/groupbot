"""
Translation Module
Translate text using DeepL API or a free translation service
Usage: Reply to a message with /translate [lang_code]
Example: /translate en
"""

import os
import requests
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from deep_translator import GoogleTranslator

try:
    from wbb import app, DEEPL_API, LOG_GROUP_ID
    from wbb.utils import capture_err
    
    # DeepL supported languages
    DEEPL_LANGS = [
        "BG", "CS", "DA", "DE", "EL", "EN", "ES", "ET", "FI", "FR",
        "HU", "ID", "IT", "JA", "LT", "LV", "NL", "PL", "PT", "RO",
        "RU", "SK", "SL", "SV", "TR", "ZH"
    ]
    
    # Google Translate supported languages
    GOOGLE_LANGS = [
        "af", "sq", "am", "ar", "hy", "az", "eu", "be", "bn", "bs", "bg", "ca",
        "ceb", "zh", "zh-TW", "co", "hr", "cs", "da", "nl", "en", "eo", "et",
        "fi", "fr", "fy", "gl", "ka", "de", "el", "gu", "ht", "ha", "haw", "he",
        "hi", "hmn", "hu", "is", "ig", "id", "ga", "it", "ja", "jv", "kn", "kk",
        "km", "rw", "ko", "ku", "ky", "lo", "la", "lv", "lt", "lb", "mk", "mg",
        "ms", "ml", "mt", "mi", "mr", "mn", "my", "ne", "no", "ny", "or", "ps",
        "fa", "pl", "pt", "pa", "ro", "ru", "sm", "gd", "sr", "st", "sn", "sd",
        "si", "sk", "sl", "so", "es", "su", "sw", "sv", "tl", "tg", "ta", "tt",
        "te", "th", "tr", "tk", "uk", "ur", "ug", "uz", "vi", "cy", "xh", "yi",
        "yo", "zu"
    ]
    
    # Language code to name mapping
    LANG_NAMES = {
        "af": "Afrikaans", "sq": "Albanian", "am": "Amharic", "ar": "Arabic",
        "hy": "Armenian", "az": "Azerbaijani", "eu": "Basque", "be": "Belarusian",
        "bn": "Bengali", "bs": "Bosnian", "bg": "Bulgarian", "ca": "Catalan",
        "ceb": "Cebuano", "zh": "Chinese", "zh-TW": "Chinese (Traditional)",
        "co": "Corsican", "hr": "Croatian", "cs": "Czech", "da": "Danish",
        "nl": "Dutch", "en": "English", "eo": "Esperanto", "et": "Estonian",
        "fi": "Finnish", "fr": "French", "fy": "Frisian", "gl": "Galician",
        "ka": "Georgian", "de": "German", "el": "Greek", "gu": "Gujarati",
        "ht": "Haitian Creole", "ha": "Hausa", "haw": "Hawaiian", "he": "Hebrew",
        "hi": "Hindi", "hmn": "Hmong", "hu": "Hungarian", "is": "Icelandic",
        "ig": "Igbo", "id": "Indonesian", "ga": "Irish", "it": "Italian",
        "ja": "Japanese", "jv": "Javanese", "kn": "Kannada", "kk": "Kazakh",
        "km": "Khmer", "rw": "Kinyarwanda", "ko": "Korean", "ku": "Kurdish",
        "ky": "Kyrgyz", "lo": "Lao", "la": "Latin", "lv": "Latvian",
        "lt": "Lithuanian", "lb": "Luxembourgish", "mk": "Macedonian",
        "mg": "Malagasy", "ms": "Malay", "ml": "Malayalam", "mt": "Maltese",
        "mi": "Maori", "mr": "Marathi", "mn": "Mongolian", "my": "Myanmar",
        "ne": "Nepali", "no": "Norwegian", "ny": "Nyanja", "or": "Odia",
        "ps": "Pashto", "fa": "Persian", "pl": "Polish", "pt": "Portuguese",
        "pa": "Punjabi", "ro": "Romanian", "ru": "Russian", "sm": "Samoan",
        "gd": "Scots Gaelic", "sr": "Serbian", "st": "Sesotho", "sn": "Shona",
        "sd": "Sindhi", "si": "Sinhala", "sk": "Slovak", "sl": "Slovenian",
        "so": "Somali", "es": "Spanish", "su": "Sundanese", "sw": "Swahili",
        "sv": "Swedish", "tl": "Tagalog", "tg": "Tajik", "ta": "Tamil",
        "tt": "Tatar", "te": "Telugu", "th": "Thai", "tr": "Turkish",
        "tk": "Turkmen", "uk": "Ukrainian", "ur": "Urdu", "ug": "Uyghur",
        "uz": "Uzbek", "vi": "Vietnamese", "cy": "Welsh", "xh": "Xhosa",
        "yi": "Yiddish", "yo": "Yoruba", "zu": "Zulu"
    }
    
    __MODULE__ = "Translate"
    __HELP__ = """
**Translate Module**

Translate text using DeepL API (if configured) or Google Translate.

**Commands:**
- `/translate [lang_code]` - Translate the replied message to the specified language.
- `/langs` - Show list of supported language codes.

**Examples:**
- Reply to a message with `/translate es` to translate to Spanish
- `/translate fr` - Translate to French
- `/translate zh` - Translate to Chinese

**Note:** If DeepL API key is configured, it will be used for higher quality translations. Otherwise, it will fall back to Google Translate.
"""
    
    def detect_language(text):
        """Detect language of the text"""
        try:
            # GoogleTranslator.detect() returns a string like 'en', 'fr', etc.
            return GoogleTranslator(source='auto', target='en').detect(text)
        except Exception as e:
            print(f"Language detection error: {e}")
            return None
    
    def translate_text(text, target_lang, source_lang='auto'):
        """Translate text using DeepL or fallback to Google Translate"""
        print(f"[DEBUG] translate_text - Source: {source_lang}, Target: {target_lang}")
        print(f"[DEBUG] Text length: {len(text)} chars")
        
        # Normalize language codes
        target_lang = target_lang.lower()
        if source_lang != 'auto':
            source_lang = source_lang.lower()
        
        # Handle Chinese variants
        if target_lang in ['zh-cn', 'zh_tw', 'zh-tw']:
            target_lang = 'zh-TW'
        
        # Try DeepL first if API key is available and target language is supported
        if DEEPL_API and target_lang.upper() in DEEPL_LANGS:
            try:
                import deepl
                translator = deepl.Translator(DEEPL_API)
                
                # Convert to DeepL format (uppercase, 2-letter code)
                deepl_target = target_lang[:2].upper()
                
                # For DeepL, source can be None for auto-detection
                deepl_source = source_lang[:2].upper() if source_lang != 'auto' else None
                
                print(f"[DEBUG] Using DeepL: {deepl_source} -> {deepl_target}")
                
                if deepl_source:
                    result = translator.translate_text(
                        text,
                        source_lang=deepl_source,
                        target_lang=deepl_target
                    )
                else:
                    result = translator.translate_text(
                        text,
                        target_lang=deepl_target
                    )
                
                print(f"[DEBUG] DeepL translation successful")
                return result.text, "DeepL"
                
            except Exception as e:
                print(f"[ERROR] DeepL translation failed: {str(e)}")
                # Fall through to Google Translate
        
        # Fallback to Google Translate
        try:
            print(f"[DEBUG] Using Google Translate: {source_lang} -> {target_lang}")
            
            # Google expects source='auto' for auto-detection
            google_source = 'auto' if source_lang == 'auto' else source_lang
            
            translator = GoogleTranslator(
                source=google_source,
                target=target_lang
            )
            
            # Split long text to avoid hitting API limits
            max_chunk_size = 5000
            if len(text) > max_chunk_size:
                chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
                translated_chunks = []
                for chunk in chunks:
                    translated = translator.translate(chunk)
                    if translated is None:
                        raise Exception("Translation returned None")
                    translated_chunks.append(translated)
                translated = ' '.join(translated_chunks)
            else:
                translated = translator.translate(text)
                if translated is None:
                    raise Exception("Translation returned None")
            
            print("[DEBUG] Google Translate successful")
            return translated, "Google"
            
        except Exception as e:
            print(f"[ERROR] Google Translate failed: {str(e)}")
            return None, None
    
    @app.on_message(filters.command("translate") & ~filters.private)
    @capture_err
    async def translate_command(client, message):
        """Handle the /translate command"""
        if not message.reply_to_message or not message.reply_to_message.text:
            await message.reply_text("Please reply to a message to translate it.")
            return
        
        if len(message.command) < 2:
            await message.reply_text(
                "Please specify a target language code.\n"
                "Example: `/translate es` for Spanish\n"
                "Use `/langs` to see available language codes."
            )
            return
        
        target_lang = message.command[1].lower()
        
        # Handle Chinese variants
        if target_lang in ['zh-cn', 'zh_tw', 'zh-tw']:
            target_lang = 'zh-TW'
        
        # Normalize target language for checking
        check_lang = target_lang.lower()
        # Check if language is supported by either service
        if (check_lang not in GOOGLE_LANGS and 
            check_lang.upper() not in DEEPL_LANGS):
            # Also check without region code
            base_lang = check_lang.split('-')[0]
            if base_lang not in GOOGLE_LANGS and base_lang.upper() not in DEEPL_LANGS:
            await message.reply_text(
                "Unsupported language code. Use /langs to see available languages."
            )
            return
        
        text = message.reply_to_message.text
        
        # Detect source language if not specified
        detected = detect_language(text)
        source_lang = detected if detected else 'auto'
        
        print(f"[DEBUG] Detected language: {source_lang}")
        print(f"[DEBUG] Target language: {target_lang}")
        print(f"[DEBUG] Text sample: {text[:100]}..." if len(text) > 100 else f"[DEBUG] Text: {text}")
        
        # Translate the text
        translated, service = translate_text(text, target_lang, source_lang)
        
        if not translated:
            await message.reply_text("Failed to translate the text. Please try again later.")
            return
        
        # Get language names
        source_name = LANG_NAMES.get(source_lang, source_lang.upper()) if source_lang != 'auto' else "Auto-detected"
        target_name = LANG_NAMES.get(target_lang, target_lang.upper())
        
        # Ensure the translated text is not too long for Telegram
        max_length = 4000  # Leave some room for the header
        if len(translated) > max_length:
            translated = translated[:max_length] + "... [truncated]"
        
        # Format the response
        response = (
            f"🌐 **Translated from {source_name} to {target_name}** ({service}):\n\n"
            f"{translated}"
        )
        
        await message.reply_text(response, reply_to_message_id=message.reply_to_message.id)
    
    @app.on_message(filters.command("langs") & ~filters.private)
    @capture_err
    async def list_languages(client, message):
        """List available language codes"""
        # Create a formatted list of supported languages
        deepl_langs = ", ".join(DEEPL_LANGS)
        google_langs = ", ".join(GOOGLE_LANGS)
        
        response = (
            "**Available Languages:**\n\n"
            "**DeepL Supported Languages (higher quality):**\n"
            f"{deepl_langs}\n\n"
            "**Google Translate Supported Languages:**\n"
            f"{google_langs}\n\n"
            "**Usage:** `/translate [lang_code]`\n"
            "Example: `/translate es` for Spanish"
        )
        
        await message.reply_text(response)
    
    # Add command help to the main help menu
    __HELP__ = __HELP__
    
except Exception as e:
    print(f"Error in translate module: {e}")
    __HELP__ = """
**Translate Module**

This module is not properly configured. Please check the logs for details.
"""
