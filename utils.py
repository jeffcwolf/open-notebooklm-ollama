"""
utils.py

Functions:
- generate_script: Get the dialogue from the LLM.
- call_llm: Call the LLM with the given prompt and dialogue format.
- parse_url: Parse the given URL and return the text content.
- generate_podcast_audio: Generate audio for podcast using TTS or advanced audio models.
- _use_suno_model: Generate advanced audio using Bark.
- _use_melotts_api: Generate audio using TTS model.
- _get_melo_tts_params: Get TTS parameters based on speaker and language.

"""

# Standard library imports
import json
import time
from typing import Any, Union

# Third-party imports
import instructor
import requests
from bark import SAMPLE_RATE, generate_audio, preload_models
from gradio_client import Client
from scipy.io.wavfile import write as write_wav
from openai import OpenAI

# Local imports
from constants import (
    # Remove Fireworks constants, add Ollama constants
    OLLAMA_BASE_URL,
    OLLAMA_MODEL_ID,
    OLLAMA_MAX_TOKENS,
    OLLAMA_TEMPERATURE,
    USE_OLLAMA,
    FIREWORKS_API_KEY,
    FIREWORKS_MODEL_ID,
    FIREWORKS_MAX_TOKENS,
    FIREWORKS_TEMPERATURE,
    MELO_API_NAME,
    MELO_TTS_SPACES_ID,
    MELO_RETRY_ATTEMPTS,
    MELO_RETRY_DELAY,
    JINA_READER_URL,
    JINA_RETRY_ATTEMPTS,
    JINA_RETRY_DELAY,
)
# UPDATED IMPORT - Added LongDialogue and ExtendedDialogue
from schema import ShortDialogue, MediumDialogue, LongDialogue, ExtendedDialogue

# Initialize clients based on configuration
if USE_OLLAMA:
    # Initialize Ollama client with OpenAI-compatible API
    ollama_client = OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama",  # Ollama doesn't need a real API key
    )
    # Patch with instructor for structured outputs
    ollama_client = instructor.from_openai(ollama_client)
    llm_client = ollama_client
else:
    # Fallback to Fireworks
    from fireworks.client import Fireworks
    fw_client = Fireworks(api_key=FIREWORKS_API_KEY)
    fw_client = instructor.from_fireworks(fw_client)
    llm_client = fw_client

# Initialize Hugging Face client lazily (only when needed)
hf_client = None

# Bark models will be loaded lazily too
bark_models_loaded = False


# def generate_script(
#     system_prompt: str,
#     input_text: str,
#     output_model: Union[ShortDialogue, MediumDialogue, LongDialogue, ExtendedDialogue],
# ) -> Union[ShortDialogue, MediumDialogue, LongDialogue, ExtendedDialogue]:
#     """
#     Get the dialogue from the LLM.

#     Args:
#         system_prompt (str): The system prompt to guide the LLM.
#         input_text (str): The input text to process.
#         output_model (Union[ShortDialogue, MediumDialogue, LongDialogue, ExtendedDialogue]): The desired output model.

#     Returns:
#         Union[ShortDialogue, MediumDialogue, LongDialogue, ExtendedDialogue]: The generated dialogue.
#     """

#     # Call the LLM for the first time
#     first_draft_dialogue = call_llm(system_prompt, input_text, output_model)

#     # Call the LLM a second time to improve the dialogue
#     system_prompt_with_dialogue = f"{system_prompt}\n\nHere is the first draft of the dialogue you provided:\n\n{first_draft_dialogue.model_dump_json()}."
#     final_dialogue = call_llm(system_prompt_with_dialogue, "Please improve the dialogue. Make it more natural and engaging.", output_model)

#     return final_dialogue

def generate_script(
    system_prompt: str,
    input_text: str,
    output_model: Union[ShortDialogue, MediumDialogue, LongDialogue, ExtendedDialogue],
) -> Union[ShortDialogue, MediumDialogue, LongDialogue, ExtendedDialogue]:
    """
    Get the dialogue from the LLM.
    For long content, skip the second improvement pass to avoid context overflow.
    """

    # Call the LLM for the first time
    first_draft_dialogue = call_llm(system_prompt, input_text, output_model)
    
    # Skip second pass for long content to avoid context overflow
    if output_model in [LongDialogue, ExtendedDialogue]:
        print(f"✅ Skipping second pass for {output_model.__name__} to avoid context overflow")
        print(f"✅ Generated {len(first_draft_dialogue.dialogue)} exchanges in first pass")
        return first_draft_dialogue

    # Call the LLM a second time to improve the dialogue (only for short/medium)
    print("Doing second improvement pass for short/medium content...")
    system_prompt_with_dialogue = f"{system_prompt}\n\nHere is the first draft of the dialogue you provided:\n\n{first_draft_dialogue.model_dump_json()}."
    final_dialogue = call_llm(system_prompt_with_dialogue, "Please improve the dialogue. Make it more natural and engaging.", output_model)

    return final_dialogue


def call_llm(system_prompt: str, text: str, dialogue_format: Any) -> Any:
    """Call the LLM with the given prompt and dialogue format."""
    
    if USE_OLLAMA:
        # Use Ollama with structured output
        try:
            # Try with instructor first (for models that support it well)
            response = llm_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                model=OLLAMA_MODEL_ID,
                max_tokens=OLLAMA_MAX_TOKENS,
                temperature=OLLAMA_TEMPERATURE,
                response_model=dialogue_format,
            )
            return response
        except Exception as e:
            print(f"Error with Ollama structured output: {e}")
            # Check if it's the multiple tool calls issue
            if "multiple tool calls" in str(e) or "List[Model]" in str(e):
                print("Detected multiple tool calls issue, trying alternative approach...")
                try:
                    return call_llm_alternative(system_prompt, text, dialogue_format)
                except Exception as alt_error:
                    print(f"Alternative method also failed: {alt_error}")
                    print("Falling back to JSON parsing method...")
                    return call_llm_fallback(system_prompt, text, dialogue_format)
            else:
                # Other errors, use fallback
                return call_llm_fallback(system_prompt, text, dialogue_format)
    else:
        # Use Fireworks API
        response = llm_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            model=FIREWORKS_MODEL_ID,
            max_tokens=FIREWORKS_MAX_TOKENS,
            temperature=FIREWORKS_TEMPERATURE,
            response_model=dialogue_format,
        )
        return response


def call_llm_alternative(system_prompt: str, text: str, dialogue_format: Any) -> Any:
    """
    Alternative method for models that support tools but have issues with Instructor.
    Uses raw OpenAI client with explicit tool calling.
    """
    
    # Create a tool definition from our Pydantic model
    tool_definition = {
        "type": "function",
        "function": {
            "name": "create_podcast_dialogue",
            "description": "Create a structured podcast dialogue",
            "parameters": {
                "type": "object",
                "properties": {
                    "scratchpad": {
                        "type": "string",
                        "description": "Brainstorming notes about the content"
                    },
                    "name_of_guest": {
                        "type": "string", 
                        "description": "Full name of the guest"
                    },
                    "dialogue": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "speaker": {
                                    "type": "string",
                                    "enum": ["Host (Jane)", "Guest"],
                                    "description": "Must be exactly 'Host (Jane)' or 'Guest'"
                                },
                                "text": {
                                    "type": "string",
                                    "description": "The dialogue text"
                                }
                            },
                            "required": ["speaker", "text"]
                        }
                    }
                },
                "required": ["scratchpad", "name_of_guest", "dialogue"]
            }
        }
    }
    
    client = OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama",
    )
    
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        model=OLLAMA_MODEL_ID,
        max_tokens=OLLAMA_MAX_TOKENS,
        temperature=OLLAMA_TEMPERATURE,
        tools=[tool_definition],
        tool_choice={"type": "function", "function": {"name": "create_podcast_dialogue"}}
    )
    
    # Extract the tool call result
    try:
        # Check if tool_calls exists and has content
        if not response.choices[0].message.tool_calls:
            # No tool calls - model responded with regular text, use fallback
            print("Model didn't use tools, falling back to JSON parsing method...")
            return call_llm_fallback(system_prompt, text, dialogue_format)
            
        tool_call = response.choices[0].message.tool_calls[0]
        function_args = tool_call.function.arguments
        
        # Parse the JSON arguments
        if isinstance(function_args, str):
            import json
            json_data = json.loads(function_args)
        else:
            json_data = function_args
            
        # Fix dialogue field if it's a stringified JSON array
        if "dialogue" in json_data and isinstance(json_data["dialogue"], str):
            try:
                import json
                json_data["dialogue"] = json.loads(json_data["dialogue"])
            except json.JSONDecodeError:
                # If it fails to parse, leave it as is and let validation catch it
                pass
            
        # Fix speaker names if needed
        if "dialogue" in json_data and isinstance(json_data["dialogue"], list):
            for item in json_data["dialogue"]:
                if isinstance(item, dict) and "speaker" in item:
                    if item["speaker"] not in ["Host (Jane)", "Guest"]:
                        if "Jane" not in item["speaker"] and "Host" not in item["speaker"]:
                            item["speaker"] = "Guest"
                        elif "Host" in item["speaker"] or "Jane" in item["speaker"]:
                            item["speaker"] = "Host (Jane)"
        
        return dialogue_format.parse_obj(json_data)
        
    except Exception as e:
        print(f"Tool calling failed: {e}, falling back to JSON parsing...")
        return call_llm_fallback(system_prompt, text, dialogue_format)


def call_llm_fallback(system_prompt: str, text: str, dialogue_format: Any) -> Any:
    """
    Enhanced fallback method for Ollama when structured output fails.
    Uses manual JSON parsing with strong length emphasis and better JSON handling.
    """
    
    # Determine expected length based on dialogue format
    expected_exchanges = "18-28"  # default for Medium
    length_emphasis = ""
    
    if dialogue_format == ShortDialogue:
        expected_exchanges = "11-17"
        length_emphasis = "SHORT FORMAT: Create a concise dialogue with 11-17 total exchanges."
    elif dialogue_format == MediumDialogue:
        expected_exchanges = "18-28"
        length_emphasis = "MEDIUM FORMAT: Create a dialogue with 18-28 total exchanges."
    elif dialogue_format == LongDialogue:
        expected_exchanges = "35-50"
        length_emphasis = "LONG FORMAT: Create an extensive dialogue with 35-50 total exchanges. This should be a comprehensive, in-depth discussion with detailed explanations, follow-up questions, and exploration of subtopics."
    elif dialogue_format == ExtendedDialogue:
        expected_exchanges = "50-70"
        length_emphasis = "EXTENDED FORMAT: Create a very long, thorough dialogue with 50-70 total exchanges. Include multiple subtopics, detailed explanations, examples, analogies, and comprehensive coverage."
    
    # Get the schema example for the format
    schema_example = get_enhanced_schema_example(dialogue_format, expected_exchanges)
    
    # Make regular completion call
    client = OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama",
    )
    
    # Try multiple approaches if needed
    for attempt in range(3):  # 3 attempts
        try:
            # Adjust max_tokens based on expected length to avoid truncation
            if dialogue_format == LongDialogue:
                max_tokens = min(OLLAMA_MAX_TOKENS, 20000)  # Increase for long content
            elif dialogue_format == ExtendedDialogue:
                max_tokens = min(OLLAMA_MAX_TOKENS, 25000)  # Even more for extended
            else:
                max_tokens = OLLAMA_MAX_TOKENS
            
            if attempt == 0:
                # First attempt: Very explicit structure with step-by-step guidance
                enhanced_system_prompt = f"""{system_prompt}

🚨 CRITICAL LENGTH REQUIREMENT 🚨
{length_emphasis}

STEP-BY-STEP INSTRUCTIONS:
1. Read the provided content carefully
2. Create a {expected_exchanges}-exchange dialogue about the content
3. Format it as valid JSON with the exact structure shown below
4. Count exchanges as you write - each speaker turn = 1 exchange
5. Do not stop until you reach {expected_exchanges} exchanges

REQUIRED JSON FORMAT (respond with ONLY this structure):
{{
  "scratchpad": "Brief notes about the content and how to make it engaging",
  "name_of_guest": "Dr. [Expert Name based on content]",
  "dialogue": [
    {{"speaker": "Host (Jane)", "text": "Welcome to our podcast! Today we're exploring [topic from content]..."}},
    {{"speaker": "Guest", "text": "Thank you for having me. [Initial response based on content]..."}},
    {{"speaker": "Host (Jane)", "text": "[Follow-up question based on content]..."}},
    {{"speaker": "Guest", "text": "[Detailed response using content facts]..."}}
    // CONTINUE THIS PATTERN until you have exactly {expected_exchanges} total exchanges
    // Keep going! Don't stop early!
  ]
}}

CRITICAL: Use EXACTLY "Host (Jane)" and "Guest" as speakers."""

                messages = [
                    {"role": "system", "content": enhanced_system_prompt},
                    {"role": "user", "content": f"""Create a {expected_exchanges}-exchange podcast dialogue using specific facts from this content.

CONTENT TO DISCUSS: {text[:6000]}

REMINDER: Generate exactly {expected_exchanges} exchanges. Count them as you create the dialogue array!"""}
                ]
                
            elif attempt == 1:
                # Second attempt: More structured approach with explicit counting
                messages = [
                    {"role": "system", "content": f"""You are a podcast dialogue generator. You MUST create exactly {expected_exchanges} exchanges.

CRITICAL RULES:
1. Only output valid JSON
2. Use exactly {expected_exchanges} dialogue exchanges
3. Each speaker turn counts as 1 exchange
4. Use "Host (Jane)" and "Guest" as speakers
5. Base content on the provided text

{length_emphasis}"""},
                    {"role": "user", "content": f"""Generate a {expected_exchanges}-exchange podcast dialogue in this JSON format:

{{
  "scratchpad": "Notes about key points to cover",
  "name_of_guest": "Expert Name",
  "dialogue": [
    // Create exactly {expected_exchanges} exchanges here
    // Example: {{"speaker": "Host (Jane)", "text": "question"}}, 
    // Example: {{"speaker": "Guest", "text": "answer"}},
    // Continue until {expected_exchanges} total
  ]
}}

Content: {text[:4000]}

CRITICAL: Generate ALL {expected_exchanges} exchanges. Do not truncate!"""}
                ]
                
            else:
                # Third attempt: Simplified structure focusing on completion
                messages = [
                    {"role": "system", "content": f"Generate {expected_exchanges} podcast exchanges. Output only JSON. Never stop early."},
                    {"role": "user", "content": f"""Create {expected_exchanges} exchanges about: {text[:3000]}

JSON format:
{{
  "scratchpad": "notes",
  "name_of_guest": "expert name", 
  "dialogue": [
    // {expected_exchanges} total exchanges here
  ]
}}"""}
                ]
            
            print(f"Attempt {attempt + 1}: Requesting {expected_exchanges} exchanges with max_tokens={max_tokens}")
            
            response = client.chat.completions.create(
                messages=messages,
                model=OLLAMA_MODEL_ID,
                max_tokens=max_tokens,  # Use adjusted token limit
                temperature=OLLAMA_TEMPERATURE,
            )
            
            # Get the full response content
            json_text = response.choices[0].message.content.strip()
            print(f"Raw response length: {len(json_text)} characters")
            
            # More robust JSON extraction
            json_text = extract_json_from_response(json_text)
            
            if not json_text:
                print(f"No valid JSON found in response on attempt {attempt + 1}")
                continue
            
            try:
                json_data = json.loads(json_text)
            except json.JSONDecodeError as json_error:
                print(f"JSON decode error on attempt {attempt + 1}: {json_error}")
                print(f"Problematic JSON (first 500 chars): {json_text[:500]}")
                
                # Try to fix common JSON issues
                json_text = fix_common_json_issues(json_text)
                try:
                    json_data = json.loads(json_text)
                    print("Fixed JSON issues successfully")
                except json.JSONDecodeError:
                    print("Could not fix JSON issues")
                    if attempt == 2:
                        raise
                    continue
            
            # Validate and fix the parsed data
            json_data = validate_and_fix_dialogue_data(json_data)
            
            # Check if we got the expected length
            dialogue_length = len(json_data.get("dialogue", []))
            print(f"Parsed {dialogue_length} exchanges on attempt {attempt + 1}")
            
            # For longer formats, be more strict about length
            expected_min = int(expected_exchanges.split('-')[0])
            if dialogue_format in [LongDialogue, ExtendedDialogue]:
                acceptance_threshold = 0.8  # 80% of minimum for long formats
            else:
                acceptance_threshold = 0.7  # 70% for shorter formats
            
            if dialogue_length >= expected_min * acceptance_threshold or attempt == 2:
                try:
                    return dialogue_format.parse_obj(json_data)
                except Exception as parse_error:
                    print(f"Pydantic parsing error: {parse_error}")
                    if attempt == 2:
                        raise
                    continue
            else:
                print(f"Length {dialogue_length} too short (need ≥{expected_min * acceptance_threshold:.0f}), trying again...")
                continue
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            if attempt == 2:
                raise Exception(f"All attempts failed. Last error: {e}")
            continue


def extract_json_from_response(response_text: str) -> str:
    """Extract JSON from response text, handling various formats."""
    
    # Remove markdown formatting
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    
    # Find JSON boundaries
    start_idx = response_text.find('{')
    if start_idx == -1:
        return ""
    
    # Find the matching closing brace
    brace_count = 0
    end_idx = -1
    for i in range(start_idx, len(response_text)):
        if response_text[i] == '{':
            brace_count += 1
        elif response_text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break
    
    if end_idx == -1:
        # If we can't find matching braces, try rfind
        end_idx = response_text.rfind('}') + 1
        if end_idx == 0:
            return ""
    
    return response_text[start_idx:end_idx].strip()


def fix_common_json_issues(json_text: str) -> str:
    """Fix common JSON formatting issues."""
    
    # Remove trailing commas before closing brackets/braces
    import re
    json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
    
    # Fix unescaped quotes in text
    # This is a simple fix - for production, you'd want more sophisticated handling
    lines = json_text.split('\n')
    fixed_lines = []
    for line in lines:
        if '"text":' in line and line.count('"') > 2:
            # Try to fix unescaped quotes in dialogue text
            if line.strip().endswith(','):
                # Extract the text part and escape internal quotes
                start = line.find('"text": "') + 9
                end = line.rfind('"')
                if start < end:
                    text_part = line[start:end]
                    escaped_text = text_part.replace('"', '\\"')
                    line = line[:start] + escaped_text + line[end:]
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def validate_and_fix_dialogue_data(json_data: dict) -> dict:
    """Validate and fix dialogue data structure."""
    
    # Ensure required fields exist
    if "scratchpad" not in json_data:
        json_data["scratchpad"] = "Brainstorming notes about the content"
    if "name_of_guest" not in json_data:
        json_data["name_of_guest"] = "Expert Guest"
    if "dialogue" not in json_data:
        json_data["dialogue"] = [
            {"speaker": "Host (Jane)", "text": "Welcome to today's podcast!"},
            {"speaker": "Guest", "text": "Thank you for having me."}
        ]
    
    # Fix speaker names if they're incorrect
    if "dialogue" in json_data and isinstance(json_data["dialogue"], list):
        for item in json_data["dialogue"]:
            if isinstance(item, dict) and "speaker" in item:
                if item["speaker"] not in ["Host (Jane)", "Guest"]:
                    if "Jane" in item["speaker"] or "Host" in item["speaker"]:
                        item["speaker"] = "Host (Jane)"
                    else:
                        item["speaker"] = "Guest"
                
                # Ensure text field exists and is a string
                if "text" not in item or not isinstance(item["text"], str):
                    item["text"] = "..."
    
    return json_data


def get_enhanced_schema_example(dialogue_format: Any, expected_exchanges: str) -> str:
    """Generate an enhanced schema example showing the expected length."""
    
    if dialogue_format == LongDialogue:
        return """{
  "scratchpad": "Detailed brainstorming notes about transforming this content into a comprehensive 35-50 exchange podcast discussion",
  "name_of_guest": "Dr. Expert Name",
  "dialogue": [
    {"speaker": "Host (Jane)", "text": "Welcome to our podcast! Today we're diving deep into..."},
    {"speaker": "Guest", "text": "Thank you for having me. I'm excited to explore..."},
    {"speaker": "Host (Jane)", "text": "Let's start with the fundamentals..."},
    {"speaker": "Guest", "text": "Absolutely. To understand this topic..."},
    // Continue with detailed back-and-forth until you reach 35-50 total exchanges
    // Include follow-up questions, examples, and deeper exploration
  ]
}"""
    elif dialogue_format == ExtendedDialogue:
        return """{
  "scratchpad": "Comprehensive brainstorming notes for a thorough 50-70 exchange podcast covering all aspects",
  "name_of_guest": "Dr. Expert Name", 
  "dialogue": [
    {"speaker": "Host (Jane)", "text": "Welcome to our extended podcast episode..."},
    {"speaker": "Guest", "text": "Thank you. This is such a rich topic..."},
    {"speaker": "Host (Jane)", "text": "Let's begin with the historical context..."},
    {"speaker": "Guest", "text": "Great starting point. Historically..."},
    // Continue with very detailed discussion until 50-70 total exchanges
    // Include multiple subtopics, examples, analogies, comprehensive coverage
  ]
}"""
    else:
        return get_schema_example(dialogue_format)


def get_length_example_structure(dialogue_format: Any) -> str:
    """Get an example structure showing the expected length pattern."""
    
    if dialogue_format == LongDialogue:
        return """Expected structure (35-50 exchanges):
1. Host (Jane): Introduction and topic overview
2. Guest: Initial response and expertise
3. Host (Jane): First detailed question
4. Guest: Comprehensive answer
5. Host (Jane): Follow-up question
6. Guest: Detailed explanation
... continue this pattern with:
- Multiple subtopics
- Follow-up questions  
- Examples and analogies
- Deeper exploration
... until you reach 35-50 total exchanges"""
    elif dialogue_format == ExtendedDialogue:
        return """Expected structure (50-70 exchanges):
1. Host (Jane): Extended introduction
2. Guest: Detailed opening
3. Host (Jane): First major topic
4. Guest: Comprehensive explanation
5. Host (Jane): Clarifying question
6. Guest: Further detail
... continue with extensive coverage:
- Historical background
- Current developments  
- Multiple subtopics
- Detailed examples
- Comparative analysis
- Future implications
... until you reach 50-70 total exchanges"""
    else:
        return "Standard dialogue structure"


def get_schema_example(dialogue_format: Any) -> str:
    """Generate a schema example for the given dialogue format."""
    
    if dialogue_format == ShortDialogue:
        return """{
  "scratchpad": "Brief brainstorming notes about the content...",
  "name_of_guest": "Dr. Example Name",
  "dialogue": [
    {
      "speaker": "Host (Jane)",
      "text": "Welcome to our podcast! Today we're discussing..."
    },
    {
      "speaker": "Guest", 
      "text": "Thank you for having me. I'm excited to share..."
    }
  ]
}"""
    elif dialogue_format == MediumDialogue:
        return """{
  "scratchpad": "Detailed brainstorming notes about the content...",
  "name_of_guest": "Dr. Example Name",
  "dialogue": [
    {
      "speaker": "Host (Jane)",
      "text": "Welcome to our podcast! Today we're discussing..."
    },
    {
      "speaker": "Guest",
      "text": "Thank you for having me. I'm excited to share..."
    }
  ]
}"""
    
    return "{}"


def parse_url(url: str) -> str:
    """
    Parse the given URL and return the text content using Jina Reader.

    Args:
        url (str): The URL to parse.

    Returns:
        str: The text content of the URL.
    """

    for attempt in range(JINA_RETRY_ATTEMPTS):
        try:
            full_url = f"{JINA_READER_URL}{url}"
            response = requests.get(full_url, timeout=60)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            if attempt < JINA_RETRY_ATTEMPTS - 1:
                time.sleep(JINA_RETRY_DELAY)
            else:
                raise Exception(f"Failed to fetch URL after {JINA_RETRY_ATTEMPTS} attempts: {e}")


def _ensure_bark_models_loaded():
    """Ensure Bark models are loaded."""
    global bark_models_loaded
    if not bark_models_loaded:
        try:
            preload_models()
            bark_models_loaded = True
        except Exception as e:
            raise Exception(f"Failed to load Bark models: {e}")


def _ensure_hf_client():
    """Ensure HuggingFace client is initialized."""
    global hf_client
    if hf_client is None:
        try:
            hf_client = Client(MELO_TTS_SPACES_ID)
        except Exception as e:
            raise Exception(f"Failed to connect to MeloTTS service. The service may be temporarily unavailable. Error: {e}")
    return hf_client


def generate_podcast_audio(
    text: str, speaker: str, language: str, use_advanced_audio: bool, random_voice_number: int = 0
) -> str:
    """
    Generate audio for podcast using TTS or advanced audio models.

    Args:
        text (str): The text to convert to audio.
        speaker (str): The speaker name.
        language (str): The language code.
        use_advanced_audio (bool): Whether to use advanced audio generation.
        random_voice_number (int): Random voice number for TTS.

    Returns:
        str: The path to the generated audio file.
    """

    if use_advanced_audio:
        return _use_suno_model(text, speaker, language, random_voice_number)
    else:
        return _use_melotts_api(text, speaker, language)


def _use_suno_model(text: str, speaker: str, language: str, random_voice_number: int) -> str:
    """
    Generate advanced audio using Bark.

    Args:
        text (str): The text to convert to audio.
        speaker (str): The speaker name.
        language (str): The language code.
        random_voice_number (int): Random voice number.

    Returns:
        str: The path to the generated audio file.
    """

    # Ensure Bark models are loaded
    _ensure_bark_models_loaded()

    # Determine voice preset based on speaker and language
    if speaker == "Host (Jane)":
        voice_preset = f"v2/{language}_speaker_{random_voice_number}"
    else:
        voice_preset = f"v2/{language}_speaker_{random_voice_number + 1}"

    # Generate audio using Bark
    audio_array = generate_audio(text, history_prompt=voice_preset)

    # Save audio to a temporary file
    audio_file_path = f"audio_{int(time.time())}_{speaker.replace(' ', '_')}.wav"
    write_wav(audio_file_path, SAMPLE_RATE, audio_array)

    return audio_file_path


def _use_melotts_api(text: str, speaker: str, language: str) -> str:
    """
    Generate audio using TTS model.

    Args:
        text (str): The text to convert to audio.
        speaker (str): The speaker name.
        language (str): The language code.

    Returns:
        str: The path to the generated audio file.
    """

    # Ensure HuggingFace client is available
    client = _ensure_hf_client()

    # Get TTS parameters
    params = _get_melo_tts_params(speaker, language)

    # Make the API call
    for attempt in range(MELO_RETRY_ATTEMPTS):
        try:
            result = client.predict(
                text=text,
                language=params["language"],
                speaker=params["speaker"],
                speed=1.0,
                api_name=MELO_API_NAME,
            )
            return result
        except Exception as e:
            if attempt < MELO_RETRY_ATTEMPTS - 1:
                time.sleep(MELO_RETRY_DELAY)
            else:
                raise Exception(f"Failed to generate audio after {MELO_RETRY_ATTEMPTS} attempts: {e}")


def _get_melo_tts_params(speaker: str, language: str) -> dict:
    """
    Get TTS parameters based on speaker and language.

    Args:
        speaker (str): The speaker name.
        language (str): The language code.

    Returns:
        dict: TTS parameters.
    """

    # Define speaker mapping
    speaker_mapping = {
        "Host (Jane)": "EN-US",
        "Guest": "EN-Default",
    }

    return {
        "language": language,
        "speaker": speaker_mapping.get(speaker, "EN-Default"),
    }