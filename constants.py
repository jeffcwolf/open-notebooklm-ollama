"""
constants.py
"""

import os
from pathlib import Path

# Key constants
APP_TITLE = "Open NotebookLM 🎙️"
CHARACTER_LIMIT = 100_000

# Gradio-related constants
GRADIO_CACHE_DIR = "./gradio_cached_examples/tmp/"
GRADIO_CLEAR_CACHE_OLDER_THAN = 1 * 24 * 60 * 60  # 1 day

# Error messages-related constants
ERROR_MESSAGE_NO_INPUT = "Please provide at least one PDF file or a URL."
ERROR_MESSAGE_NOT_PDF = "The provided file is not a PDF. Please upload only PDF files."
ERROR_MESSAGE_NOT_SUPPORTED_IN_MELO_TTS = "The selected language is not supported without advanced audio generation. Please enable advanced audio generation or choose a supported language."
ERROR_MESSAGE_READING_PDF = "Error reading the PDF file"
ERROR_MESSAGE_TOO_LONG = f"The total content is too long. Please ensure it's under {CHARACTER_LIMIT} characters."

# LLM Configuration - Ollama vs Fireworks
USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"

# Ollama API-related constants
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL_ID = os.getenv("OLLAMA_MODEL", "llama3.1:8b")  # Default model, user can change this
OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "32768"))  # INCREASED from 16384 to 32768
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))

# Fireworks API-related constants (kept as fallback) 
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
FIREWORKS_MAX_TOKENS = 32_768  # INCREASED from 16_384 to 32_768
FIREWORKS_MODEL_ID = "accounts/fireworks/models/llama-v3p3-70b-instruct"
FIREWORKS_TEMPERATURE = 0.1

# Jina Reader-related constants
JINA_READER_URL = "https://r.jina.ai/"
JINA_RETRY_ATTEMPTS = 3
JINA_RETRY_DELAY = 5  # in seconds

# MeloTTS
MELO_API_NAME = "/synthesize"
MELO_TTS_SPACES_ID = "mrfakename/MeloTTS"
MELO_RETRY_ATTEMPTS = 3
MELO_RETRY_DELAY = 5  # in seconds

MELO_TTS_LANGUAGE_MAPPING = {
    "en": "EN",
    "es": "ES",
    "fr": "FR",
    "zh": "ZJ",
    "ja": "JP",
    "ko": "KR",
}

# Suno related constants
SUNO_LANGUAGE_MAPPING = {
    "English": "en",
    "Chinese": "zh",
    "French": "fr",
    "German": "de",
    "Hindi": "hi",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Polish": "pl",
    "Portuguese": "pt",
    "Russian": "ru",
    "Spanish": "es",
    "Turkish": "tr",
}

# General audio-related constants
NOT_SUPPORTED_IN_MELO_TTS = list(
    set(SUNO_LANGUAGE_MAPPING.values()) - set(MELO_TTS_LANGUAGE_MAPPING.keys())
)
NOT_SUPPORTED_IN_MELO_TTS = [
    k for k, v in SUNO_LANGUAGE_MAPPING.items() if v in NOT_SUPPORTED_IN_MELO_TTS
]

# Import focus areas
try:
    from focus_areas import get_focus_names
    FOCUS_AREA_CHOICES = get_focus_names()
except ImportError:
    print("Warning: focus_areas.py not found. Focus selection will not be available.")
    FOCUS_AREA_CHOICES = ["No Specific Focus"]

# UI-related constants
UI_DESCRIPTION = """
Upload PDF files or enter a URL to convert the content into an engaging podcast dialogue. 
You can also generate just the transcript without audio if you prefer.

**New Features**: 
- 🎯 **Focus Areas**: Anchor conversations around specific themes and perspectives
- 🧠 **Deep Discussion**: Enable rigorous, intellectually challenging expert conversations

**Note:** This app now supports local LLMs via Ollama! Set USE_OLLAMA=true and configure your model.
"""

UI_INPUTS = {
    "file_upload": {
        "label": "📁 Upload PDF(s)",
        "file_count": "multiple",
        "file_types": [".pdf"],
    },
    "url": {
        "label": "🌐 Or Enter URL",
        "placeholder": "https://example.com/article",
    },
    "question": {
        "label": "❓ Custom Question (Optional)",
        "placeholder": "What specific aspect would you like the podcast to focus on?",
    },
    "focus_area": {
        "label": "🎯 Focus Area (Optional)",
        "choices": FOCUS_AREA_CHOICES,
        "value": FOCUS_AREA_CHOICES[0] if FOCUS_AREA_CHOICES else "No Specific Focus",
        "info": "Select a thematic focus to anchor the conversation around specific perspectives or applications."
    },
    "tone": {
        "label": "🎭 Tone",
        "choices": ["Informative", "Casual", "Humorous", "Deep Discussion"],
        "value": "Informative",
    },
    "length": {
        "label": "⏱️ Length",
        "choices": ["Short (1-2 min)", "Medium (3-5 min)", "Long (8-12 min)", "Extended (15+ min)"],
        "value": "Medium (3-5 min)",
    },
    "language": {
        "label": "🌍 Language",
        "choices": list(SUNO_LANGUAGE_MAPPING.keys()),
        "value": "English",
    },
    "use_advanced_audio": {
        "label": "🔊 Advanced Audio Generation (Experimental)",
        "value": False,
    },
    "transcript_only": {
        "label": "📝 Generate Transcript Only (No Audio)",
        "value": True,
    },
}

UI_OUTPUTS = {
    "audio": {
        "label": "🎧 Generated Podcast Audio",
    },
    "transcript": {
        "label": "📄 Transcript",
    },
}

# Updated examples to include focus area
UI_EXAMPLES = [
    [
        None,  # No file upload
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "What are the key milestones in AI development?",
        "AI Ethics and Policy Implications",  # Focus area
        "Casual",  # Valid choice from tone dropdown
        "Long (8-12 min)",  # Valid choice from length dropdown
        "English",  # Valid choice from language dropdown
        False,  # Valid boolean for advanced audio
        True,  # Valid boolean for transcript only
        False,  # Valid boolean for multi-pass
    ],
    [
        None,  # No file upload
        "https://www.python.org/about/",
        None,  # No custom question
        "Practical Implementation and Applications",  # Focus area
        "Informative",  # Valid choice from tone dropdown
        "Extended (15+ min)",  # Valid choice from length dropdown
        "English",  # Valid choice from language dropdown
        False,  # Valid boolean for advanced audio
        True,  # Valid boolean for transcript only
        True,   # Valid boolean for multi-pass
    ],
]

UI_API_NAME = "generate_podcast"
UI_ALLOW_FLAGGING = "never"
UI_CONCURRENCY_LIMIT = 3
UI_SHOW_API = False
UI_CACHE_EXAMPLES = True

# Recommended Ollama Models for this use case
RECOMMENDED_OLLAMA_MODELS = [
    "llama3.3:70b",      # Best quality if you have enough VRAM
    "llama3.1:8b",       # Good balance of speed and quality
    "llama3.2:3b",       # Fastest, lower quality
    "qwen2.5:14b",       # Alternative high-quality option
    "mistral:7b",        # Another good alternative
    "gemma2:9b",         # Google's model
]

def get_model_recommendations():
    """Return formatted model recommendations for the user."""
    return f"""
Recommended Ollama models for this application:
{chr(10).join([f"- {model}" for model in RECOMMENDED_OLLAMA_MODELS])}

To install a model: ollama pull <model_name>
To list your models: ollama list
"""