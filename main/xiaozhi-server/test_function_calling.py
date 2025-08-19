#!/usr/bin/env python3
"""
Test if function calling is working with the current LLM configuration
"""

import os
import sys
import asyncio

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import load_config
from core.providers.llm.openai.openai import LLMProvider
from config.logger import setup_logging

logger = setup_logging()


async def test_function_calling():
    """Test if the LLM supports and uses function calling"""
    
    print("=== Testing Function Calling with Current LLM ===\n")
    
    # Load configuration
    config = load_config()
    selected_llm = config['selected_module']['LLM']
    llm_config = config['LLM'][selected_llm]
    
    print(f"1. Using LLM: {selected_llm}")
    print(f"   Model: {llm_config.get('model_name', 'default')}")
    print(f"   Base URL: {llm_config.get('base_url', 'default')}\n")
    
    # Initialize LLM
    try:
        llm = LLMProvider(llm_config)
        print("✓ LLM initialized successfully\n")
    except Exception as e:
        print(f"✗ Failed to initialize LLM: {str(e)}")
        return
    
    # Test messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant that uses functions when appropriate."},
        {"role": "user", "content": "What is an extrinsic semiconductor? Please search the textbook for information."}
    ]
    
    # Define the search_textbook function
    functions = [{
        "type": "function",
        "function": {
            "name": "search_textbook",
            "description": "Search textbook content to answer study questions",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Question or keywords to search"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Subject (optional): Physics, Math, etc."
                    }
                },
                "required": ["query"]
            }
        }
    }]
    
    print("2. Testing function calling...")
    print("   User message: 'What is an extrinsic semiconductor?'")
    print("   Available function: search_textbook\n")
    
    try:
        # Test with functions
        response = await llm.response_with_functions(messages, functions)
        
        print("3. Response from LLM:")
        print(f"   Type: {type(response)}")
        
        if isinstance(response, str):
            print(f"   Content: {response[:200]}...")
            print("\n   ⚠️  LLM returned text instead of function call")
            print("   This suggests the LLM might not be properly recognizing function calls\n")
        elif isinstance(response, dict):
            if 'function' in response:
                print(f"   ✓ Function call detected!")
                print(f"   Function: {response['function']['name']}")
                print(f"   Arguments: {response['function']['arguments']}")
            else:
                print(f"   Response structure: {response}")
        else:
            print(f"   Unexpected response type: {response}")
            
    except Exception as e:
        print(f"✗ Error during function call test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test without functions for comparison
    print("\n4. Testing regular response (without functions)...")
    try:
        regular_response = await llm.response(messages[1:])  # Skip system message
        print(f"   Regular response: {regular_response[:200]}...")
    except Exception as e:
        print(f"✗ Error during regular response: {str(e)}")


async def main():
    await test_function_calling()


if __name__ == "__main__":
    print("Starting function calling test...\n")
    asyncio.run(main())
    print("\n✅ Test complete!")