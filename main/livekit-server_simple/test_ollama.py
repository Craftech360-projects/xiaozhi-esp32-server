#!/usr/bin/env python3
"""
Test Ollama Connection and LLM Response
"""
import os
import sys
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))

print("=" * 60)
print("🧪 Ollama Connection Test")
print("=" * 60)
print(f"📍 URL: {OLLAMA_API_URL}")
print(f"🤖 Model: {OLLAMA_MODEL}")
print(f"⏱️  Timeout: {OLLAMA_TIMEOUT}s")
print("=" * 60)

async def test_ollama_connection():
    """Test basic Ollama API connection"""
    print("\n1️⃣ Testing API connection...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_API_URL}/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                print(f"   ✅ Connected successfully!")
                print(f"   📦 Available models: {len(models)}")
                for model in models:
                    name = model.get("name", "unknown")
                    size_mb = model.get("size", 0) / (1024 * 1024)
                    print(f"      - {name} ({size_mb:.1f}MB)")
                return True
            else:
                print(f"   ❌ Failed: HTTP {response.status_code}")
                return False
                
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

async def test_ollama_generation():
    """Test LLM text generation"""
    print("\n2️⃣ Testing text generation...")
    
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=OLLAMA_TIMEOUT, connect=10.0)) as client:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": "Say hello in one short sentence.",
                "stream": False
            }
            
            print(f"   📤 Sending request to {OLLAMA_MODEL}...")
            response = await client.post(
                f"{OLLAMA_API_URL}/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                text = data.get("response", "").strip()
                eval_count = data.get("eval_count", 0)
                eval_duration = data.get("eval_duration", 0) / 1e9  # Convert to seconds
                
                print(f"   ✅ Generation successful!")
                print(f"   💬 Response: {text}")
                print(f"   📊 Tokens: {eval_count}")
                print(f"   ⏱️  Duration: {eval_duration:.2f}s")
                print(f"   🚀 Speed: {eval_count/eval_duration:.1f} tokens/s")
                return True
            else:
                print(f"   ❌ Failed: HTTP {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"   ❌ Generation failed: {e}")
        return False

async def test_ollama_streaming():
    """Test streaming generation"""
    print("\n3️⃣ Testing streaming generation...")
    
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=OLLAMA_TIMEOUT, connect=10.0)) as client:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": "Count from 1 to 5.",
                "stream": True
            }
            
            print(f"   📤 Sending streaming request...")
            print(f"   💬 Response: ", end="", flush=True)
            
            async with client.stream(
                "POST",
                f"{OLLAMA_API_URL}/api/generate",
                json=payload
            ) as response:
                if response.status_code == 200:
                    async for line in response.aiter_lines():
                        if line:
                            import json
                            data = json.loads(line)
                            chunk = data.get("response", "")
                            print(chunk, end="", flush=True)
                    
                    print()  # New line
                    print(f"   ✅ Streaming successful!")
                    return True
                else:
                    print(f"\n   ❌ Failed: HTTP {response.status_code}")
                    return False
                    
    except Exception as e:
        print(f"\n   ❌ Streaming failed: {e}")
        return False

async def test_livekit_integration():
    """Test LiveKit OpenAI plugin with Ollama"""
    print("\n4️⃣ Testing LiveKit integration...")
    
    try:
        from livekit.plugins import openai
        import openai as openai_sdk
        
        print(f"   📦 Creating LLM instance with custom timeout...")
        
        # Create custom client with timeout
        custom_client = openai_sdk.AsyncOpenAI(
            base_url=f"{OLLAMA_API_URL}/v1",
            api_key="ollama",  # Ollama doesn't need real API key
            timeout=httpx.Timeout(timeout=OLLAMA_TIMEOUT, connect=10.0)
        )
        
        llm = openai.LLM(
            model=OLLAMA_MODEL,
            client=custom_client
        )
        
        print(f"   📤 Sending chat request...")
        from livekit.agents import llm as llm_module
        
        chat_ctx = llm_module.ChatContext()
        chat_ctx.append(role="user", text="Say hello in one sentence.")
        
        stream = llm.chat(chat_ctx=chat_ctx)
        
        response_text = ""
        async for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta.content:
                    response_text += delta.content
                    print(delta.content, end="", flush=True)
        
        print()  # New line
        print(f"   ✅ LiveKit integration successful!")
        print(f"   💬 Full response: {response_text}")
        return True
        
    except Exception as e:
        print(f"   ❌ LiveKit integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    results = []
    
    # Test 1: Connection
    results.append(await test_ollama_connection())
    
    if not results[0]:
        print("\n❌ Connection failed. Please check:")
        print(f"   1. Ollama is running at {OLLAMA_API_URL}")
        print(f"   2. Model '{OLLAMA_MODEL}' is installed")
        print(f"   3. Network connectivity")
        sys.exit(1)
    
    # Test 2: Generation
    results.append(await test_ollama_generation())
    
    # Test 3: Streaming
    results.append(await test_ollama_streaming())
    
    # Test 4: LiveKit Integration
    results.append(await test_livekit_integration())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    tests = [
        "API Connection",
        "Text Generation",
        "Streaming Generation",
        "LiveKit Integration"
    ]
    
    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i}. {test}: {status}")
    
    all_passed = all(results)
    print("=" * 60)
    
    if all_passed:
        print("🎉 All tests passed! Ollama is ready to use.")
        print(f"\n💡 Your agent will use:")
        print(f"   - Model: {OLLAMA_MODEL}")
        print(f"   - URL: {OLLAMA_API_URL}")
        print(f"   - Timeout: {OLLAMA_TIMEOUT}s")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
