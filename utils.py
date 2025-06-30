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
from schema import ShortDialogue, MediumDialogue

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


def generate_script(
    system_prompt: str,
    input_text: str,
    output_model: Union[ShortDialogue, MediumDialogue],
) -> Union[ShortDialogue, MediumDialogue]:
    """
    Get the dialogue from the LLM.

    Args:
        system_prompt (str): The system prompt to guide the LLM.
        input_text (str): The input text to process.
        output_model (Union[ShortDialogue, MediumDialogue]): The desired output model.

    Returns:
        Union[ShortDialogue, MediumDialogue]: The generated dialogue.
    """

    # Call the LLM for the first time
    first_draft_dialogue = call_llm(system_prompt, input_text, output_model)

    # Call the LLM a second time to improve the dialogue
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
    Fallback method for Ollama when structured output fails.
    Uses manual JSON parsing with schema instructions.
    """
    
    # Get the schema as a string for the prompt
    schema_example = get_schema_example(dialogue_format)
    
    # Much more forceful prompt that demands JSON
    enhanced_system_prompt = f"""{system_prompt}

🚨 CRITICAL INSTRUCTIONS - YOU MUST FOLLOW THESE EXACTLY 🚨

1. DO NOT write explanatory text, summaries, or helpful responses
2. DO NOT preserve the input format or create metadata structures
3. DO NOT ask questions or offer to help
4. You MUST create a podcast dialogue between Host (Jane) and Guest
5. You MUST respond with ONLY this exact JSON format:

{{
  "scratchpad": "Brief notes about transforming this content into an engaging podcast",
  "name_of_guest": "Dr. [Guest Name]",
  "dialogue": [
    {{"speaker": "Host (Jane)", "text": "Welcome to our podcast! [intro about the topic]"}},
    {{"speaker": "Guest", "text": "[guest response about the topic]"}},
    {{"speaker": "Host (Jane)", "text": "[follow-up question]"}},
    {{"speaker": "Guest", "text": "[detailed response]"}}
  ]
}}

CRITICAL SPEAKER RULES:
- Use EXACTLY "Host (Jane)" for the host speaker
- Use EXACTLY "Guest" for the guest speaker (never use the guest's actual name as speaker)
- The guest's actual name goes in the "name_of_guest" field only

FORMAT REQUIREMENT:
- Your response must start with {{ and end with }}
- No markdown, no explanations, no additional text, no metadata preservation
- ONLY the JSON object with scratchpad, name_of_guest, and dialogue fields

TASK: Transform the provided content into a podcast dialogue format. Ignore the input format completely and create a fresh conversation."""

    # Make regular completion call
    client = OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama",
    )
    
    # Try multiple approaches if needed
    for attempt in range(2):
        try:
            if attempt == 0:
                # First attempt with clear JSON instruction and content emphasis
                messages = [
                    {"role": "system", "content": enhanced_system_prompt},
                    {"role": "user", "content": f"""Create a detailed podcast dialogue using the specific facts and information from this content.

IMPORTANT: Use actual details, names, dates, and facts from the content below. Don't be generic.

Content: {text[:5000]}

Create a podcast dialogue that discusses the specific details from this content. Make the guest knowledgeable about the actual facts presented."""}
                ]
            else:
                # Second attempt with even more explicit instruction  
                messages = [
                    {"role": "system", "content": "You are a JSON-only response bot. You ONLY output valid JSON. Never write explanatory text."},
                    {"role": "user", "content": f"""Create a detailed podcast dialogue in JSON format using specific facts from the content.

JSON Format:
{{
  "scratchpad": "Notes about key facts to discuss from the content",
  "name_of_guest": "Dr. [Expert Name]",
  "dialogue": [
    {{"speaker": "Host (Jane)", "text": "Welcome! Today we're discussing [specific topic from content]"}},
    {{"speaker": "Guest", "text": "Thanks! Let me share some fascinating details about [specific facts from content]"}},
    {{"speaker": "Host (Jane)", "text": "That's interesting! Can you tell us about [specific detail from content]?"}},
    {{"speaker": "Guest", "text": "[Detailed response using actual facts from content]"}}
  ]
}}

Content to use: {text[:3000]}

Use specific details, not generic responses. Respond with ONLY the JSON object."""}
                ]
            
            response = client.chat.completions.create(
                messages=messages,
                model=OLLAMA_MODEL_ID,
                max_tokens=OLLAMA_MAX_TOKENS,
                temperature=OLLAMA_TEMPERATURE,
            )
            
            # Parse the JSON response
            json_text = response.choices[0].message.content.strip()
            
            # Remove any markdown formatting if present
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            
            # Remove any leading/trailing text that isn't JSON
            if '{' in json_text and '}' in json_text:
                start = json_text.find('{')
                end = json_text.rfind('}') + 1
                json_text = json_text[start:end]
            
            json_data = json.loads(json_text)
            
            # Handle nested podcast dialogue structure
            if "podcast_dialogue" in json_data:
                # Model created nested structure, extract the dialogue part
                podcast_part = json_data["podcast_dialogue"]
                if isinstance(podcast_part, dict):
                    # If it's already in the right format
                    json_data = podcast_part
                elif isinstance(podcast_part, list):
                    # If it's just a dialogue array, create the full structure
                    json_data = {
                        "scratchpad": f"Podcast about {json_data.get('title', 'the provided content')}",
                        "name_of_guest": "Expert Guest",
                        "dialogue": podcast_part
                    }
            
            # Ensure all required fields exist
            if "scratchpad" not in json_data:
                json_data["scratchpad"] = "Brainstorming notes about the content"
            if "name_of_guest" not in json_data:
                json_data["name_of_guest"] = "Expert Guest"
            if "dialogue" not in json_data:
                # Try to find dialogue in various possible locations
                if "podcast_dialogue" in json_data and isinstance(json_data["podcast_dialogue"], list):
                    json_data["dialogue"] = json_data["podcast_dialogue"]
                else:
                    # Create minimal dialogue if none found
                    json_data["dialogue"] = [
                        {"speaker": "Host (Jane)", "text": "Welcome to today's podcast!"},
                        {"speaker": "Guest", "text": "Thank you for having me."}
                    ]
            
            # Fix speaker names if they're incorrect
            if "dialogue" in json_data:
                for item in json_data["dialogue"]:
                    if item["speaker"] not in ["Host (Jane)", "Guest"]:
                        # If it's not the host, it must be the guest
                        if "Jane" not in item["speaker"] and "Host" not in item["speaker"]:
                            item["speaker"] = "Guest"
                        elif "Host" in item["speaker"] or "Jane" in item["speaker"]:
                            item["speaker"] = "Host (Jane)"
            
            return dialogue_format.parse_obj(json_data)
            
        except json.JSONDecodeError as e:
            if attempt == 0:
                print(f"JSON parsing failed on attempt {attempt + 1}, trying more explicit approach...")
                continue
            else:
                print(f"All JSON parsing attempts failed. Raw response: {response.choices[0].message.content}")
                raise Exception(f"Failed to get valid JSON after multiple attempts. Last error: {e}")
        except Exception as e:
            if attempt == 0:
                print(f"Attempt {attempt + 1} failed: {e}, trying again...")
                continue
            else:
                raise Exception(f"Failed to parse LLM response as JSON: {e}\nResponse: {response.choices[0].message.content}")


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