# Open NotebookLM Ollama 🎙️

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18662009.svg)](https://doi.org/10.5281/zenodo.18662009)

A **local, privacy-focused** fork of [Open NotebookLM](https://github.com/gabrielchua/open-notebooklm) that generates engaging podcast-style conversations from your documents using **Ollama** instead of paid APIs.

> **Why this fork?** The original project requires Fireworks API (paid service). This version runs entirely on your local machine using Ollama, giving you complete privacy and no API costs.

## ✨ Key Features

### 🆕 **New in This Fork**
- **🦙 Local LLM Support**: Uses Ollama instead of paid Fireworks API
- **🎯 Focus Areas**: Anchor conversations around specific themes (AI Ethics, Research Methods, etc.)
- **🧠 Deep Discussion Mode**: Generate rigorous, academic-level conversations
- **📝 Extended Dialogues**: Support for 50-70 exchange conversations (15+ minutes)
- **📄 Markdown Export**: Save extended conversations as formatted markdown files
- **🔄 Multi-Stage Generation**: Sophisticated system for handling very long content
- **🔒 Complete Privacy**: Everything runs locally on your machine

### 📚 **Core Capabilities**
- Convert PDFs and web articles into engaging podcast conversations
- Multiple conversation lengths: Short (1-2 min) → Extended (15+ min)
- Support for 13+ languages
- Transcript-only mode (no audio generation required)
- Advanced audio generation (optional)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai) installed and running
- At least 8GB RAM (16GB+ recommended for larger models)

### 1. Install Ollama & Download Models

```bash
# Install Ollama (see https://ollama.ai for your platform)
# Then download a recommended model:
ollama pull qwen2.5:32b  # Default model (good balance of speed/quality)
# OR for better quality if you have more VRAM:
ollama pull llama3.3:70b
```

### 2. Clone & Setup

```bash
git clone https://github.com/yourusername/open-notebooklm-ollama.git
cd open-notebooklm-ollama
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file:

```bash
# Core Configuration
USE_OLLAMA=true
OLLAMA_MODEL=qwen2.5:32b  # or your preferred model
OLLAMA_BASE_URL=http://localhost:11434/v1

# Optional: For audio generation (if desired)
# FIREWORKS_API_KEY=your_key_here  # Only needed for fallback
```

### 4. Run the App

```bash
python app.py
```

Open your browser to `http://localhost:7860`

## 🎯 Usage Guide

### Basic Workflow
1. **Upload PDFs** or **enter a URL** of content to discuss
2. **Choose a focus area** (optional) to anchor the conversation theme
3. **Select tone**: Informative, Casual, Humorous, or **Deep Discussion**
4. **Pick length**: Short (1-2 min) through Extended (15+ min)
5. **Generate!** Choose transcript-only for fastest results

### 🧠 Deep Discussion Mode
Perfect for academic or professional content:
- Generates intellectually challenging conversations
- Host asks probing, incisive questions
- Guest provides sophisticated, evidence-based responses
- Explores contradictions, limitations, and complexities

### 🎯 Focus Areas
Anchor conversations around specific perspectives:
- **AI Ethics and Policy Implications**
- **Practical Implementation and Applications**
- **LLMs as Methodological Tools in HPSS Research**
- **Research Methods and Academic Standards**
- *(Easily extensible - see `focus_areas.py`)*

### 📊 Extended Dialogues (15+ min)
For comprehensive discussions:
- Automatically uses multi-stage generation for complex content
- Exports as markdown files in `extended_dialogues/` folder
- Can generate 50-70 exchanges covering multiple subtopics
- Includes statistics and metadata

## ⚙️ Configuration

### Recommended Ollama Models

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| `qwen2.5:32b` | ~19GB | Fast | High | Default choice |
| `llama3.3:70b` | ~40GB | Slower | Highest | Best quality |
| `llama3.1:8b` | ~4.7GB | Fastest | Good | Quick testing |
| `mistral:7b` | ~4.1GB | Very Fast | Good | Resource constrained |

### Environment Variables

```bash
# Ollama Configuration
USE_OLLAMA=true                    # Use Ollama instead of Fireworks
OLLAMA_MODEL=qwen2.5:32b          # Model to use
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MAX_TOKENS=40000           # Increased for extended dialogues
OLLAMA_CONTEXT_WINDOW=65536       # Context window size
OLLAMA_TEMPERATURE=0.1            # Creativity level (0-1)

# Optional Audio Generation
FIREWORKS_API_KEY=your_key        # Only if you want advanced audio
```

## 📁 Project Structure

```
open-notebooklm-ollama/
├── app.py                    # Main Gradio interface
├── constants.py             # Configuration constants
├── prompts.py               # System prompts and modifiers
├── schema.py                # Dialogue data structures
├── utils.py                 # Core LLM and audio generation
├── multi_stage_extended.py  # Multi-stage generation system
├── markdown_export.py       # Export extended dialogues
├── focus_areas.py           # Thematic focus definitions
├── extended_dialogues/      # Generated markdown files
└── requirements.txt         # Python dependencies
```

## 🔧 Advanced Features

### Multi-Stage Generation
For content that exceeds context windows:
- Stage 1: Foundational discussion
- Stage 2: Deep dive analysis  
- Stage 3: Implications & synthesis
- Seamlessly combines stages into single conversation

### Custom Focus Areas
Add your own themes in `focus_areas.py`:

```python
FOCUS_AREAS = {
    "custom_focus": {
        "name": "My Custom Focus",
        "prompt_modifier": "Focus the conversation on [your specific angle]..."
    }
}
```

### Transcript Export
Extended dialogues (50+ exchanges) are automatically saved as markdown:
- Formatted with speakers and exchange numbers
- Includes statistics (word count, reading time)
- Timestamp and metadata
- Searchable and archivable

## 🚨 Troubleshooting

### Common Issues

**"Error with Ollama model"**
- Ensure Ollama is running: `ollama serve`
- Check model is installed: `ollama list`
- Verify model name in environment variables

**"Context window exceeded"**
- Use smaller input documents (under 100k characters)
- Try a model with larger context window
- Enable multi-pass generation for very long content

**"Slow generation"**
- Use smaller models (qwen2.5:14b, llama3.1:8b)
- Reduce max_tokens in constants.py
- Choose shorter dialogue lengths

**"JSON parsing errors"**
- This can happen with some models - check logs
- Try different temperature settings
- Some models work better with the fallback parsing

### Performance Tips
- **RAM**: 16GB+ recommended for 32B+ models
- **GPU**: Optional but significantly faster with CUDA
- **Storage**: Models require 4-40GB depending on size
- **CPU**: More cores = faster inference for CPU-only setups

## 🔄 Comparison with Original

| Feature | Original OpenNotebookLM | This Fork |
|---------|------------------------|-----------|
| **LLM** | Fireworks API (paid) | Local Ollama (free) |
| **Privacy** | Data sent to API | Completely local |
| **Cost** | Pay per token | Free after setup |
| **Setup** | API key required | Local installation |
| **Max Length** | Standard dialogues | Extended (50-70 exchanges) |
| **Focus Areas** | Not available | Thematic conversation anchoring |
| **Deep Mode** | Basic tones | Academic-level discussions |
| **Export** | Audio/transcript only | Markdown export for long conversations |

## 🤝 Contributing

This is a working tool but has room for improvement:

### Known Limitations
- Can be repetitious (LLM limitation)
- May lack fine-grained technical details
- Context window constraints for very long documents
- Some Ollama models better than others for structured output

### Areas for Enhancement
- Better conversation flow algorithms
- More sophisticated focus area system
- Enhanced audio generation options
- Multi-modal support (images in PDFs)
- Conversation memory/continuity

Pull requests welcome! This is open source software.

## 📜 License

MIT License - same as original project. Use freely for personal or commercial projects.

## 🙏 Acknowledgments

- **Original Project**: [gabrielchua/open-notebooklm](https://github.com/gabrielchua/open-notebooklm)
- **Ollama Team**: For making local LLMs accessible
- **Community**: For model recommendations and testing

---

**Happy podcasting! 🎧** Generate engaging conversations from your documents, completely locally and privately.