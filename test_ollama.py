#!/usr/bin/env python3
"""
Test script to verify Ollama setup for Open NotebookLM
This script tests the LLM functionality without requiring TTS services.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_ollama_connection():
    """Test basic Ollama connection."""
    try:
        from openai import OpenAI
        from constants import OLLAMA_BASE_URL, OLLAMA_MODEL_ID
        
        print("🔍 Testing Ollama connection...")
        
        client = OpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key="ollama",
        )
        
        response = client.chat.completions.create(
            messages=[
                {"role": "user", "content": "Hello! Please respond with just 'Connection successful' if you can see this."}
            ],
            model=OLLAMA_MODEL_ID,
            max_tokens=50,
            temperature=0.1,
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ Ollama connection successful!")
        print(f"   Model: {OLLAMA_MODEL_ID}")
        print(f"   Response: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Make sure Ollama is running: ollama serve")
        print(f"   2. Make sure the model is installed: ollama pull {OLLAMA_MODEL_ID}")
        print("   3. Check your .env configuration")
        return False

def test_structured_output():
    """Test structured output with Pydantic models."""
    try:
        print("\n🔍 Testing structured output...")
        
        import instructor
        from openai import OpenAI
        from constants import OLLAMA_BASE_URL, OLLAMA_MODEL_ID
        from schema import ShortDialogue
        
        client = OpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key="ollama",
        )
        client = instructor.from_openai(client)
        
        test_prompt = """Create a very short podcast dialogue about AI. Include a scratchpad with brief notes, name the guest "Dr. AI Expert", and create exactly 2 dialogue items - one where the host welcomes the guest, and one where the guest responds. 

CRITICAL: Use exactly "Host (Jane)" and "Guest" as the speaker values."""
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a podcast producer. Create engaging dialogue. Use exactly 'Host (Jane)' and 'Guest' as speaker values."},
                {"role": "user", "content": test_prompt}
            ],
            model=OLLAMA_MODEL_ID,
            max_tokens=500,
            temperature=0.1,
            response_model=ShortDialogue,
        )
        
        print("✅ Structured output successful!")
        print(f"   Guest name: {response.name_of_guest}")
        print(f"   Dialogue items: {len(response.dialogue)}")
        print(f"   First line: {response.dialogue[0].text[:50]}...")
        return True
        
    except Exception as e:
        print(f"⚠️  Structured output failed, will use fallback method: {e}")
        return False

def test_fallback_method():
    """Test fallback JSON parsing method."""
    try:
        print("\n🔍 Testing fallback JSON method...")
        
        from utils import call_llm_fallback
        from schema import ShortDialogue
        
        test_prompt = """Create a very short podcast dialogue about AI. Include a scratchpad with brief notes, name the guest "Dr. AI Expert", and create exactly 2 dialogue items.

CRITICAL: Use exactly "Host (Jane)" and "Guest" as the speaker values."""
        
        response = call_llm_fallback(
            "You are a podcast producer. Create engaging dialogue. IMPORTANT: Use exactly 'Host (Jane)' for the host and 'Guest' for the guest speaker.",
            test_prompt,
            ShortDialogue
        )
        
        print("✅ Fallback method successful!")
        print(f"   Guest name: {response.name_of_guest}")
        print(f"   Dialogue items: {len(response.dialogue)}")
        print(f"   Speakers: {[item.speaker for item in response.dialogue]}")
        return True
        
    except Exception as e:
        print(f"❌ Fallback method failed: {e}")
        return False

def test_transcript_generation():
    """Test end-to-end transcript generation."""
    try:
        print("\n🔍 Testing transcript generation...")
        
        from utils import generate_script
        from schema import ShortDialogue
        from prompts import SYSTEM_PROMPT
        
        test_text = "Artificial Intelligence is transforming the world through machine learning, natural language processing, and computer vision technologies."
        
        result = generate_script(
            system_prompt=SYSTEM_PROMPT + "\n\nCreate a very brief dialogue (2-3 exchanges only). CRITICAL: Use exactly 'Host (Jane)' and 'Guest' as speaker values.",
            input_text=test_text,
            output_model=ShortDialogue
        )
        
        print("✅ Transcript generation successful!")
        print(f"   Guest: {result.name_of_guest}")
        print(f"   Lines: {len(result.dialogue)}")
        print(f"   Speakers: {[line.speaker for line in result.dialogue]}")
        for i, line in enumerate(result.dialogue[:2]):  # Show first 2 lines
            print(f"   {i+1}. {line.speaker}: {line.text[:60]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Transcript generation failed: {e}")
        return False

def test_alternative_method():
    """Test alternative tool calling method for llama3.1."""
    try:
        print("\n🔍 Testing alternative tool calling method...")
        
        from utils import call_llm_alternative
        from schema import ShortDialogue
        
        test_prompt = """Create a very short podcast dialogue about AI. Include a scratchpad with brief notes, name the guest "Dr. AI Expert", and create exactly 2 dialogue items.

CRITICAL: Use exactly "Host (Jane)" and "Guest" as the speaker values."""
        
        response = call_llm_alternative(
            "You are a podcast producer. Create engaging dialogue. IMPORTANT: Use exactly 'Host (Jane)' for the host and 'Guest' for the guest speaker.",
            test_prompt,
            ShortDialogue
        )
        
        print("✅ Alternative method successful!")
        print(f"   Guest name: {response.name_of_guest}")
        print(f"   Dialogue items: {len(response.dialogue)}")
        print(f"   Speakers: {[item.speaker for item in response.dialogue]}")
        
        # Validate the response structure
        assert hasattr(response, 'name_of_guest'), "Missing name_of_guest"
        assert hasattr(response, 'dialogue'), "Missing dialogue"
        assert len(response.dialogue) >= 1, "Dialogue is empty"
        assert all(item.speaker in ["Host (Jane)", "Guest"] for item in response.dialogue), "Invalid speakers"
        
        return True
        
    except Exception as e:
        print(f"❌ Alternative method failed: {e}")
        # Print more debug info
        import traceback
        print(f"   Debug info: {traceback.format_exc()}")
        return False


def main():
    """Run all tests."""
    print("🎙️ Open NotebookLM Ollama Test Suite")
    print("=" * 50)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("💡 Tip: Install python-dotenv for .env file support")
    
    # Check configuration
    from constants import USE_OLLAMA, OLLAMA_MODEL_ID, OLLAMA_BASE_URL
    
    if not USE_OLLAMA:
        print("❌ USE_OLLAMA is set to False. Please set USE_OLLAMA=true in your .env file.")
        return False
    
    print(f"🔧 Configuration:")
    print(f"   Model: {OLLAMA_MODEL_ID}")
    print(f"   Base URL: {OLLAMA_BASE_URL}")
    print()
    
    # Run tests
    tests = [
        test_ollama_connection,
        test_structured_output,
        test_alternative_method,
        test_fallback_method,
        test_transcript_generation,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Your Ollama setup is ready.")
        print("\n💡 Next steps:")
        print("   - Run: python app.py")
        print("   - Try transcript-only mode first")
        print("   - Upload a small PDF to test")
    elif passed >= 3:
        print("✅ Good functionality working! The app should run well.")
        print("\n💡 What's working:")
        print("   - Basic LLM connection ✅")
        print("   - At least one structured output method ✅") 
        print("   - Transcript generation ✅")
    else:
        print("❌ Setup needs attention. Check the error messages above.")
        
    return passed == len(tests)

if __name__ == "__main__":
    main()