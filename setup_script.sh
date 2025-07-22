#!/bin/bash

# Open NotebookLM Ollama Setup Script
# This script helps set up the environment for running Open NotebookLM with Ollama

set -e  # Exit on any error

echo "🎙️ Open NotebookLM Ollama Setup"
echo "================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed."
    echo "📥 Please install Ollama first:"
    echo "   • Visit: https://ollama.ai"
    echo "   • Or run: curl -fsSL https://ollama.ai/install.sh | sh"
    echo ""
    read -p "Do you want to continue setup anyway? (y/n): " continue_setup
    if [[ $continue_setup != "y" && $continue_setup != "Y" ]]; then
        exit 1
    fi
else
    echo "✅ Ollama found: $(ollama --version 2>/dev/null || echo 'installed')"
fi

# Create virtual environment
echo ""
echo "📦 Setting up Python virtual environment..."
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
echo "✅ Virtual environment activated"

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "📦 Installing Python dependencies..."
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "❌ requirements.txt not found. Please ensure it exists in the current directory."
    exit 1
fi

# Create .env file if it doesn't exist
echo ""
if [[ ! -f ".env" ]]; then
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
        echo "📝 Please edit .env file to configure your settings"
    else
        echo "📝 Creating basic .env file..."
        cat > .env << EOL
USE_OLLAMA=true
OLLAMA_MODEL=qwen2.5:32b
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MAX_TOKENS=40000
OLLAMA_CONTEXT_WINDOW=65536
OLLAMA_TEMPERATURE=0.1
EOL
        echo "✅ Basic .env file created"
    fi
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p extended_dialogues
mkdir -p gradio_cached_examples/tmp
echo "✅ Directories created"

# Check if Ollama is running and suggest models
if command -v ollama &> /dev/null; then
    echo ""
    echo "🦙 Ollama Model Setup"
    echo "===================="
    
    # Check if Ollama is running
    if pgrep -x "ollama" > /dev/null; then
        echo "✅ Ollama service is running"
    else
        echo "⚠️  Ollama service not running. Starting it..."
        echo "💡 Run: ollama serve"
        echo ""
    fi
    
    # List installed models
    echo "📋 Checking installed models..."
    if ollama list 2>/dev/null | grep -q "NAME"; then
        echo "✅ Currently installed models:"
        ollama list 2>/dev/null
    else
        echo "⚠️  No models installed yet"
    fi
    
    echo ""
    echo "🎯 Recommended models to install:"
    echo "   • qwen2.5:32b     - Best balance (default) - ~19GB"
    echo "   • llama3.3:70b    - Highest quality - ~40GB" 
    echo "   • llama3.1:8b     - Fast and good - ~4.7GB"
    echo "   • mistral:7b      - Very fast - ~4.1GB"
    echo ""
    echo "📥 To install a model:"
    echo "   ollama pull qwen2.5:32b"
    echo ""
    
    read -p "Do you want to install the default model (qwen2.5:32b) now? This will download ~19GB. (y/n): " install_model
    if [[ $install_model == "y" || $install_model == "Y" ]]; then
        echo "📥 Installing qwen2.5:32b model..."
        ollama pull qwen2.5:32b
        echo "✅ Model installed"
    fi
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "🚀 To start the application:"
echo "   1. Activate virtual environment: source venv/bin/activate"
echo "   2. Make sure Ollama is running: ollama serve"
echo "   3. Start the app: python app.py"
echo "   4. Open your browser to: http://localhost:7860"
echo ""
echo "📚 Next steps:"
echo "   • Review/edit .env file for your preferences"
echo "   • Install additional Ollama models if desired"
echo "   • Check the README.md for usage instructions"
echo ""
echo "💡 Need help? Check the README.md or open an issue on GitHub"
