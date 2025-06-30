#!/usr/bin/env python3
"""
Simple test to see if llama3.1:8b can generate JSON at all
"""

import os
from openai import OpenAI

# Set up client
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

def test_simple_json():
    """Test if the model can generate simple JSON"""
    
    print("🔍 Testing simple JSON generation...")
    
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system", 
                "content": "You are a JSON-only response bot. You ONLY output valid JSON. Never write explanatory text."
            },
            {
                "role": "user", 
                "content": '''Generate JSON for a simple podcast dialogue with 2 items:
{
  "host": "Jane",
  "guest": "Dr. Smith", 
  "dialogue": [
    {"speaker": "Host", "text": "Welcome!"},
    {"speaker": "Guest", "text": "Thanks!"}
  ]
}

Output ONLY this JSON format, no other text.'''
            }
        ],
        model="llama3.1:8b",
        max_tokens=200,
        temperature=0.1,
    )
    
    result = response.choices[0].message.content
    print("Raw response:")
    print("=" * 40)
    print(result)
    print("=" * 40)
    
    # Try to parse it
    try:
        import json
        # Try to extract JSON if it's mixed with other text
        if '{' in result and '}' in result:
            start = result.find('{')
            end = result.rfind('}') + 1
            json_part = result[start:end]
            print(f"\nExtracted JSON: {json_part}")
            
            parsed = json.loads(json_part)
            print("✅ Successfully parsed JSON!")
            return True
        else:
            print("❌ No JSON found in response")
            return False
    except Exception as e:
        print(f"❌ Failed to parse JSON: {e}")
        return False

def test_forced_json():
    """Test with very aggressive JSON-only prompt"""
    
    print("\n🔍 Testing forced JSON generation...")
    
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user", 
                "content": '''You MUST respond with ONLY this JSON object, nothing else:

{"name": "test", "items": ["a", "b"]}

Do NOT add any explanations. Output ONLY the JSON.'''
            }
        ],
        model="llama3.1:8b",
        max_tokens=100,
        temperature=0.0,
    )
    
    result = response.choices[0].message.content.strip()
    print(f"Response: '{result}'")
    
    try:
        import json
        json.loads(result)
        print("✅ Perfect JSON response!")
        return True
    except:
        print("❌ Not valid JSON")
        return False

if __name__ == "__main__":
    print("🧪 Testing JSON capabilities of llama3.1:8b\n")
    
    test1 = test_simple_json()
    test2 = test_forced_json()
    
    print(f"\n📊 Results:")
    print(f"  Simple JSON test: {'✅' if test1 else '❌'}")
    print(f"  Forced JSON test: {'✅' if test2 else '❌'}")
    
    if not test1 and not test2:
        print("\n💡 Your model seems to be too 'helpful' for JSON-only responses.")
        print("   Consider trying a different model like:")
        print("   - granite3.2:8b (designed for structured output)")
        print("   - qwen2.5:7b (good at following format instructions)")
        print("   - Or enable the simple app version for basic functionality")