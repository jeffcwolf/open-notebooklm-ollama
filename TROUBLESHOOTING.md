# Troubleshooting Guide

This guide covers common issues and their solutions when using Open NotebookLM Ollama.

## 🚨 Installation Issues

### Python/pip Issues

**Error: `python: command not found`**
```bash
# On macOS/Linux
brew install python3
# or
sudo apt install python3 python3-pip

# On Windows
# Download from https://python.org
```

**Error: `pip: command not found`**
```bash
# Install pip
python3 -m ensurepip --upgrade
```

**Error: `Permission denied` when installing packages**
```bash
# Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate.bat  # Windows

# Then install
pip install -r requirements.txt
```

### Ollama Issues

**Error: `ollama: command not found`**
- **Solution**: Install Ollama from [https://ollama.ai](https://ollama.ai)
- **macOS**: `brew install ollama`
- **Linux**: `curl -fsSL https://ollama.ai/install.sh | sh`
- **Windows**: Download installer from website

**Error: `Cannot connect to Ollama`**
```bash
# Start Ollama service
ollama serve

# Check if running
curl http://localhost:11434/api/tags

# Check process
ps aux | grep ollama  # Linux/macOS
tasklist | findstr ollama  # Windows
```

**Error: `No models installed`**
```bash
# Install a model
ollama pull qwen2.5:32b

# List installed models
ollama list

# Check model size before downloading
ollama show qwen2.5:32b
```

## 🔧 Runtime Issues

### LLM Generation Errors

**Error: `Error with Ollama model`**
1. **Check model is installed**: `ollama list`
2. **Check model name in .env**: Ensure `OLLAMA_MODEL` matches installed model
3. **Check Ollama is running**: `ollama serve`
4. **Test with curl**:
   ```bash
   curl http://localhost:11434/api/generate -d '{
     "model": "qwen2.5:32b",
     "prompt": "Hello",
     "stream": false
   }'
   ```

**Error: `Context window exceeded`**
- **Reduce input size**: Split large documents into smaller parts
- **Use larger context model**: Switch to model with larger context window
- **Adjust settings**: Reduce `OLLAMA_MAX_TOKENS` in .env

**Error: `JSON parsing errors`**
- **Try different model**: Some models handle structured output better
- **Adjust temperature**: Lower temperature (0.1) for more consistent output
- **Check model compatibility**: Ensure model supports instruction following

### Memory Issues

**Error: `Out of memory` / System hanging**
```bash
# Check memory usage
htop  # Linux
top   # macOS
taskmgr  # Windows

# Solutions:
# 1. Use smaller model
OLLAMA_MODEL=llama3.1:8b

# 2. Reduce context window
OLLAMA_CONTEXT_WINDOW=32768

# 3. Close other applications
# 4. Add swap space (Linux)
sudo fallocate -l 8G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Audio Generation Issues

**Error: `MeloTTS service unavailable`**
- **Solution**: Use transcript-only mode (recommended)
- **Alternative**: Enable "Advanced Audio Generation" (requires more setup)

**Error: `Bark audio generation failed`**
- **Solution**: Audio generation is optional - use transcript-only mode
- **Fix**: Install audio dependencies:
  ```bash
  pip install torch torchaudio bark
  ```

## 🌐 Network Issues

**Error: `Connection refused` to Ollama**
```bash
# Check if port 11434 is in use
netstat -an | grep 11434  # Linux/macOS
netstat -an | findstr 11434  # Windows

# Check firewall settings
sudo ufw allow 11434  # Linux
# Windows: Add firewall exception for port 11434

# Try different port
OLLAMA_BASE_URL=http://localhost:11435/v1
```

**Error: `Cannot parse URL`**
- **Check URL format**: Ensure URL starts with `http://` or `https://`
- **Test URL manually**: Open in browser first
- **Check internet connection**: Some sites may be blocked

## 📱 Browser/Interface Issues

**Error: `Gradio interface not loading`**
- **Check port**: Default is http://localhost:7860
- **Try different browser**: Chrome, Firefox, Safari
- **Disable ad blockers**: May interfere with Gradio
- **Check browser console**: Press F12, look for errors

**Error: `File upload not working`**
- **Check file size**: Large files may timeout
- **Check file type**: Only PDF files supported
- **Try different file**: Test with simple PDF

## 🔧 Performance Issues

### Slow Generation
```bash
# Use faster model
OLLAMA_MODEL=llama3.1:8b

# Reduce output length
# Choose "Short" or "Medium" instead of "Extended"

# Reduce max tokens
OLLAMA_MAX_TOKENS=20000

# Use GPU acceleration (if available)
# Install CUDA drivers and run on GPU-enabled system
```

### High Memory Usage
```bash
# Monitor memory
watch -n 1 'free -h'  # Linux
top  # macOS

# Reduce context window
OLLAMA_CONTEXT_WINDOW=16384

# Use quantized models (automatically used by Ollama)

# Clear gradio cache
rm -rf gradio_cached_examples/tmp/*
```

## 🐳 Docker Issues

**Docker build fails**
```bash
# Clear Docker cache
docker system prune -a

# Rebuild with no cache
docker build --no-cache -t open-notebooklm-ollama .
```

**Cannot connect to host Ollama from Docker**
```bash
# For Linux
docker run --network host ...

# For macOS/Windows (use host.docker.internal)
# This is already configured in docker-compose.yml
```

## 📋 Environment Issues

**Error: `Environment variables not loaded`**
```bash
# Check .env file exists and is readable
ls -la .env
cat .env

# Check format (no quotes around values)
USE_OLLAMA=true  # ✅ Correct
USE_OLLAMA="true"  # ❌ Wrong

# Load manually for testing
export $(cat .env | xargs)
```

## 🔍 Debugging

### Enable Debug Mode
```bash
# Add to .env
LOG_LEVEL=debug

# Or run with verbose output
python -u app.py

# Check logs
tail -f logs/app.log  # if logging to file
```

### Test Components Individually

**Test Ollama directly**:
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:32b",
  "prompt": "Hello world",
  "stream": false
}'
```

**Test PDF processing**:
```python
from pypdf import PdfReader
reader = PdfReader("test.pdf")
text = reader.pages[0].extract_text()
print(text[:100])
```

**Test URL parsing**:
```python
import requests
response = requests.get("https://r.jina.ai/https://example.com")
print(response.text[:100])
```

## 🆘 Getting Help

If you're still having issues:

1. **Check the logs** for specific error messages
2. **Try with a minimal example** (simple PDF, short text)
3. **Update dependencies**: `pip install -r requirements.txt --upgrade`
4. **Restart everything**:
   ```bash
   # Stop Ollama
   pkill ollama
   
   # Restart Ollama
   ollama serve
   
   # Restart app
   python app.py
   ```

5. **Open a GitHub issue** with:
   - Your operating system
   - Python version (`python --version`)
   - Ollama version (`ollama --version`)
   - Full error message
   - Steps to reproduce

## 📊 System Requirements

### Minimum Requirements
- **RAM**: 8GB (for 7B models)
- **Storage**: 10GB free space
- **CPU**: 4 cores recommended
- **Python**: 3.8+

### Recommended Requirements
- **RAM**: 16GB+ (for 32B+ models)
- **Storage**: 50GB+ (for multiple large models)
- **GPU**: NVIDIA GPU with 8GB+ VRAM (optional but faster)
- **CPU**: 8+ cores for good performance

### Model Size Guide
| Model | RAM Usage | Quality | Speed | Use Case |
|-------|-----------|---------|--------|----------|
| llama3.1:8b | ~6GB | Good | Fast | Testing, quick tasks |
| qwen2.5:14b | ~10GB | Very Good | Medium | Balanced choice |
| qwen2.5:32b | ~20GB | Excellent | Slower | Production, quality |
| llama3.3:70b | ~40GB | Best | Slowest | Maximum quality |
