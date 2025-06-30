"""
Simple working version of Open NotebookLM with Ollama
"""

import gradio as gr
import random
from loguru import logger
from pypdf import PdfReader
from pathlib import Path
from constants import USE_OLLAMA, get_model_recommendations
from prompts import SYSTEM_PROMPT, TONE_MODIFIER, LENGTH_MODIFIERS
from schema import MediumDialogue, ShortDialogue
from utils import generate_script, parse_url


def generate_podcast_simple(
    files,
    url,
    question,
    tone,
    length,
    language,
    transcript_only=True,
):
    """Simplified podcast generation - transcript only by default."""
    
    try:
        text = ""
        
        # Process PDFs if any
        if files:
            for file in files:
                if not file.name.lower().endswith(".pdf"):
                    return None, "❌ Please upload only PDF files."
                
                try:
                    with open(file.name, "rb") as f:
                        reader = PdfReader(f)
                        text += "\n\n".join(
                            page.extract_text() for page in reader.pages if page.extract_text()
                        )
                except Exception as e:
                    return None, f"❌ Error reading PDF: {e}"
        
        # Process URL if provided
        if url:
            try:
                url_text = parse_url(url)
                text += f"\n\n{url_text}"
            except Exception as e:
                return None, f"❌ Error parsing URL: {e}"
        
        # Check if we have content
        if not text.strip():
            return None, "❌ Please provide at least one PDF file or a URL."
        
        # Limit text length
        if len(text) > 100000:
            text = text[:100000]
            logger.warning("Text truncated to 100,000 characters")
        
        # Build the system prompt
        modified_system_prompt = SYSTEM_PROMPT
        
        if question:
            modified_system_prompt += f"\n\nThe user has asked: {question}"
        
        if tone and tone in TONE_MODIFIER:
            modified_system_prompt += f"\n\n{TONE_MODIFIER[tone]}"
        
        if length and length in LENGTH_MODIFIERS:
            modified_system_prompt += f"\n\n{LENGTH_MODIFIERS[length]}"
        
        if language != "English":
            modified_system_prompt += f"\n\nGenerate the entire dialogue in {language}."
        
        # Choose output model
        output_model = ShortDialogue if length == "Short (1-2 min)" else MediumDialogue
        
        logger.info(f"Generating podcast with {USE_OLLAMA and 'Ollama' or 'Fireworks'}")
        
        # Generate the dialogue
        llm_output = generate_script(
            system_prompt=modified_system_prompt,
            input_text=text,
            output_model=output_model,
        )
        
        # Create transcript
        transcript = ""
        for line in llm_output.dialogue:
            if line.speaker == "Host (Jane)":
                speaker = f"**Host**: {line.text}"
            else:
                speaker = f"**{llm_output.name_of_guest}**: {line.text}"
            transcript += speaker + "\n\n"
        
        # Add generation info
        transcript += f"\n---\n*Generated using {'Ollama' if USE_OLLAMA else 'Fireworks API'}*"
        
        logger.info(f"Generated transcript with {len(llm_output.dialogue)} dialogue items")
        
        return None, transcript
        
    except Exception as e:
        logger.error(f"Error generating podcast: {e}")
        return None, f"❌ Error: {e}"


# Create the interface
with gr.Blocks(title="Open NotebookLM 🎙️", theme=gr.themes.Soft()) as demo:
    
    gr.Markdown("# Open NotebookLM 🎙️")
    
    if USE_OLLAMA:
        gr.Markdown("### 🦙 **Using Local Ollama Model**")
        gr.Markdown(get_model_recommendations())
    else:
        gr.Markdown("### 🎆 **Using Fireworks API**")
    
    gr.Markdown("""
    Upload PDF files or enter a URL to convert the content into an engaging podcast transcript.
    
    **Note:** This simplified version generates transcripts only for faster testing.
    """)
    
    with gr.Row():
        with gr.Column():
            # Inputs
            file_upload = gr.File(label="📁 Upload PDF(s)", file_count="multiple", file_types=[".pdf"])
            url_input = gr.Textbox(label="🌐 Or Enter URL", placeholder="https://example.com/article")
            question_input = gr.Textbox(label="❓ Custom Question (Optional)", 
                                      placeholder="What specific aspect would you like the podcast to focus on?")
            
            with gr.Row():
                tone_dropdown = gr.Dropdown(
                    label="🎭 Tone",
                    choices=["Informative", "Casual", "Humorous"],
                    value="Informative"
                )
                length_dropdown = gr.Dropdown(
                    label="⏱️ Length", 
                    choices=["Short (1-2 min)", "Medium (3-5 min)"],
                    value="Short (1-2 min)"
                )
            
            language_dropdown = gr.Dropdown(
                label="🌍 Language",
                choices=["English", "Spanish", "French", "German", "Chinese"],
                value="English"
            )
            
            generate_button = gr.Button("🎙️ Generate Podcast Transcript", variant="primary", size="lg")
        
        with gr.Column():
            # Outputs
            audio_output = gr.Audio(label="🎧 Audio (Not generated in simple mode)", visible=False)
            transcript_output = gr.Markdown(label="📄 Generated Transcript")
    
    # Examples
    gr.Examples(
        examples=[
            [None, "https://en.wikipedia.org/wiki/Artificial_intelligence", "What are the key milestones in AI development?", "Casual", "Short (1-2 min)", "English"],
            [None, "https://www.python.org/about/", None, "Informative", "Medium (3-5 min)", "English"],
        ],
        inputs=[file_upload, url_input, question_input, tone_dropdown, length_dropdown, language_dropdown],
    )
    
    # Event handler
    generate_button.click(
        fn=generate_podcast_simple,
        inputs=[file_upload, url_input, question_input, tone_dropdown, length_dropdown, language_dropdown],
        outputs=[audio_output, transcript_output],
    )

if __name__ == "__main__":
    demo.launch(inbrowser=True)