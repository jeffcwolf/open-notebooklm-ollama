"""
main.py - Modified to support Ollama and transcript-only generation
"""

# Standard library imports
import glob
import os
import time
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Tuple, Optional, Union

# Third-party imports
import gradio as gr
import random
from loguru import logger
from pypdf import PdfReader
from pydub import AudioSegment

# Local imports
from constants import (
    APP_TITLE,
    CHARACTER_LIMIT,
    ERROR_MESSAGE_NOT_PDF,
    ERROR_MESSAGE_NO_INPUT,
    ERROR_MESSAGE_NOT_SUPPORTED_IN_MELO_TTS,
    ERROR_MESSAGE_READING_PDF,
    ERROR_MESSAGE_TOO_LONG,
    GRADIO_CACHE_DIR,
    GRADIO_CLEAR_CACHE_OLDER_THAN,
    MELO_TTS_LANGUAGE_MAPPING,
    NOT_SUPPORTED_IN_MELO_TTS,
    SUNO_LANGUAGE_MAPPING,
    UI_ALLOW_FLAGGING,
    UI_API_NAME,
    UI_CACHE_EXAMPLES,
    UI_CONCURRENCY_LIMIT,
    UI_DESCRIPTION,
    UI_EXAMPLES,
    UI_INPUTS,
    UI_OUTPUTS,
    UI_SHOW_API,
    USE_OLLAMA,
    get_model_recommendations,
)
from prompts import (
    LANGUAGE_MODIFIER,
    LENGTH_MODIFIERS,
    QUESTION_MODIFIER,
    SYSTEM_PROMPT,
    TONE_MODIFIER,
)
from schema import MediumDialogue, ShortDialogue
from utils import generate_podcast_audio, generate_script, parse_url


def generate_podcast(
    files: List[str],
    url: Optional[str],
    question: Optional[str],
    tone: Optional[str],
    length: Optional[str],
    language: str,
    use_advanced_audio: bool,
    transcript_only: bool = False,
) -> Tuple[Union[str, None], str]:
    """Generate the audio and transcript from the PDFs and/or URL."""

    text = ""

    # Choose random number from 0 to 8
    random_voice_number = random.randint(0, 8)  # this is for suno model

    # Check if advanced audio is needed but not enabled for unsupported languages
    if not transcript_only and not use_advanced_audio and language in NOT_SUPPORTED_IN_MELO_TTS:
        raise gr.Error(ERROR_MESSAGE_NOT_SUPPORTED_IN_MELO_TTS)

    # Check if at least one input is provided
    if not files and not url:
        raise gr.Error(ERROR_MESSAGE_NO_INPUT)

    # Process PDFs if any
    if files:
        for file in files:
            if not file.lower().endswith(".pdf"):
                raise gr.Error(ERROR_MESSAGE_NOT_PDF)

            try:
                with Path(file).open("rb") as f:
                    reader = PdfReader(f)
                    text += "\n\n".join(
                        page.extract_text() for page in reader.pages if page.extract_text()
                    )
            except Exception as e:
                logger.error(f"Error reading PDF: {e}")
                raise gr.Error(f"{ERROR_MESSAGE_READING_PDF}: {e}")

    # Process URL if provided
    if url:
        try:
            url_text = parse_url(url)
            text += f"\n\n{url_text}"
        except Exception as e:
            logger.error(f"Error parsing URL: {e}")
            raise gr.Error(f"Error parsing URL: {e}")

    # Check total character limit
    if len(text) > CHARACTER_LIMIT:
        raise gr.Error(ERROR_MESSAGE_TOO_LONG)

    # Modify the prompt based on the user inputs
    modified_system_prompt = SYSTEM_PROMPT

    if question:
        modified_system_prompt += f"\n\n{QUESTION_MODIFIER} {question}"

    if tone:
        modified_system_prompt += f"\n\n{TONE_MODIFIER[tone]}"

    if language != "English":
        modified_system_prompt += f"\n\n{LANGUAGE_MODIFIER} {language}."

    # Choose the output model based on the length
    if length == "Short (1-2 min)":
        output_model = ShortDialogue
        modified_system_prompt += f"\n\n{LENGTH_MODIFIERS['Short (1-2 min)']}"
    else:
        output_model = MediumDialogue
        modified_system_prompt += f"\n\n{LENGTH_MODIFIERS['Medium (3-5 min)']}"

    logger.info(f"Generating podcast with {USE_OLLAMA and 'Ollama' or 'Fireworks'}")
    logger.info(f"Modified system prompt: {modified_system_prompt}")

    # Generate the dialogue
    try:
        llm_output = generate_script(
            system_prompt=modified_system_prompt,
            input_text=text,
            output_model=output_model,
        )
        logger.info(f"Generated dialogue: {llm_output}")
    except Exception as e:
        logger.error(f"Error generating script: {e}")
        if USE_OLLAMA:
            error_msg = f"Error with Ollama model. Please check that your model is running and accessible. Error: {e}"
        else:
            error_msg = f"Error generating script: {e}"
        raise gr.Error(error_msg)

    # Process the dialogue for transcript
    transcript = ""
    total_characters = 0

    for line in llm_output.dialogue:
        if line.speaker == "Host (Jane)":
            speaker = f"**Host**: {line.text}"
        else:
            speaker = f"**{llm_output.name_of_guest}**: {line.text}"
        transcript += speaker + "\n\n"
        total_characters += len(line.text)

    # Add model info to transcript
    model_info = f"\n---\n*Generated using {'Ollama' if USE_OLLAMA else 'Fireworks API'}*"
    transcript += model_info

    # If transcript only, return early
    if transcript_only:
        logger.info(f"Generated transcript-only with {total_characters} characters")
        return None, transcript

    # Generate audio if not transcript-only
    audio_segments = []
    language_for_tts = SUNO_LANGUAGE_MAPPING[language]

    if not use_advanced_audio:
        language_for_tts = MELO_TTS_LANGUAGE_MAPPING[language_for_tts]

    try:
        for line in llm_output.dialogue:
            logger.info(f"Generating audio for {line.speaker}: {line.text}")

            # Get audio file path
            audio_file_path = generate_podcast_audio(
                line.text, line.speaker, language_for_tts, use_advanced_audio, random_voice_number
            )
            # Read the audio file into an AudioSegment
            audio_segment = AudioSegment.from_file(audio_file_path)
            audio_segments.append(audio_segment)

        # Concatenate all audio segments
        combined_audio = sum(audio_segments)

        # Export the combined audio to a temporary file
        temporary_directory = GRADIO_CACHE_DIR
        os.makedirs(temporary_directory, exist_ok=True)

        temporary_file = NamedTemporaryFile(
            dir=temporary_directory,
            delete=False,
            suffix=".mp3",
        )
        combined_audio.export(temporary_file.name, format="mp3")

        # Delete any files in the temp directory that end with .mp3 and are over a day old
        for file in glob.glob(f"{temporary_directory}*.mp3"):
            if (
                os.path.isfile(file)
                and time.time() - os.path.getmtime(file) > GRADIO_CLEAR_CACHE_OLDER_THAN
            ):
                os.remove(file)

        logger.info(f"Generated {total_characters} characters of audio")

        return temporary_file.name, transcript

    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        # If audio generation fails, still return the transcript
        logger.info("Audio generation failed, returning transcript only")
        audio_error_msg = ""
        if "MeloTTS" in str(e):
            audio_error_msg = "\n\n*Note: MeloTTS service is currently unavailable. Try enabling 'Generate Transcript Only' or 'Advanced Audio Generation'.*"
        elif "Bark" in str(e):
            audio_error_msg = "\n\n*Note: Bark audio generation failed. You may need to install additional dependencies or try 'Generate Transcript Only'.*"
        else:
            audio_error_msg = f"\n\n*Note: Audio generation failed: {e}*"
        
        return None, transcript + audio_error_msg


# Create the Gradio interface
with gr.Blocks(title=APP_TITLE, theme=gr.themes.Soft()) as demo:
    
    gr.Markdown(f"# {APP_TITLE}")
    
    # Show configuration status
    if USE_OLLAMA:
        gr.Markdown("### 🦙 **Using Local Ollama Model**")
        gr.Markdown(get_model_recommendations())
    else:
        gr.Markdown("### 🎆 **Using Fireworks API**")
        
    gr.Markdown(UI_DESCRIPTION)
    
    with gr.Row():
        with gr.Column(scale=1):
            # Input components
            file_upload = gr.File(**UI_INPUTS["file_upload"])
            url_input = gr.Textbox(**UI_INPUTS["url"])
            question_input = gr.Textbox(**UI_INPUTS["question"])
            
            with gr.Row():
                tone_dropdown = gr.Dropdown(**UI_INPUTS["tone"])
                length_dropdown = gr.Dropdown(**UI_INPUTS["length"])
            
            with gr.Row():
                language_dropdown = gr.Dropdown(**UI_INPUTS["language"])
                advanced_audio_checkbox = gr.Checkbox(**UI_INPUTS["use_advanced_audio"])
            
            transcript_only_checkbox = gr.Checkbox(**UI_INPUTS["transcript_only"])
            
            generate_button = gr.Button("🎙️ Generate Podcast", variant="primary", size="lg")
        
        with gr.Column(scale=1):
            # Output components
            audio_output = gr.Audio(**UI_OUTPUTS["audio"])
            transcript_output = gr.Markdown(**UI_OUTPUTS["transcript"])
    
    # Examples
    gr.Examples(
        examples=UI_EXAMPLES,
        inputs=[
            file_upload,
            url_input,
            question_input,
            tone_dropdown,
            length_dropdown,
            language_dropdown,
            advanced_audio_checkbox,
            transcript_only_checkbox,
        ],
        outputs=[audio_output, transcript_output],
        fn=generate_podcast,
        cache_examples=False,  # Disable caching to avoid file issues
    )
    
    # Event handler
    generate_button.click(
        fn=generate_podcast,
        inputs=[
            file_upload,
            url_input,
            question_input,
            tone_dropdown,
            length_dropdown,
            language_dropdown,
            advanced_audio_checkbox,
            transcript_only_checkbox,
        ],
        outputs=[audio_output, transcript_output],
    )

if __name__ == "__main__":
    demo.launch(
        show_api=UI_SHOW_API,
        share=False,
        inbrowser=True,
    )