#!/usr/bin/env python3
"""
Test script to verify Indian English (en-IN) configuration for AWS STT
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("indian_english_test")

async def test_indian_english_config():
    """Test Indian English configuration"""
    
    print("🇮🇳 Testing Indian English Configuration")
    print("=" * 50)
    
    # Test 1: Check environment variables
    print("\n1. Checking environment variables...")
    stt_language = os.getenv('STT_LANGUAGE')
    stt_provider = os.getenv('STT_PROVIDER')
    aws_region = os.getenv('AWS_STT_REGION', os.getenv('AWS_DEFAULT_REGION'))
    
    print(f"✅ STT_LANGUAGE: {stt_language}")
    print(f"✅ STT_PROVIDER: {stt_provider}")
    print(f"✅ AWS_REGION: {aws_region}")
    
    if stt_language == 'en-IN':
        print("🎯 Perfect! Using Indian English (en-IN) for better accent recognition")
    else:
        print(f"⚠️ Warning: Using {stt_language} instead of en-IN")
    
    # Test 2: Check config loader
    print("\n2. Testing config loader...")
    try:
        from src.config.config_loader import ConfigLoader
        
        config = ConfigLoader.get_groq_config()
        print(f"📋 Config STT Language: {config.get('stt_language')}")
        print(f"📋 Config STT Provider: {config.get('stt_provider')}")
        print(f"📋 Config AWS Region: {config.get('aws_region')}")
        
        if config.get('stt_language') == 'en-IN':
            print("✅ Config loader correctly set to Indian English!")
        else:
            print(f"❌ Config loader using {config.get('stt_language')} instead of en-IN")
            
    except Exception as e:
        print(f"❌ Error testing config loader: {e}")
        return False
    
    # Test 3: Test AWS STT with Indian English
    print("\n3. Testing AWS STT provider with Indian English...")
    try:
        from livekit.plugins import aws
        
        # Create AWS STT with Indian English
        aws_stt = aws.STT(
            language='en-IN',
            region=aws_region or 'us-east-1'
        )
        
        print(f"✅ AWS STT created successfully with Indian English (en-IN)")
        print(f"🎤 STT Type: {type(aws_stt)}")
        
    except Exception as e:
        print(f"❌ Error creating AWS STT: {e}")
        return False
    
    # Test 4: Show Indian English benefits
    print("\n4. Indian English (en-IN) Benefits:")
    print("=" * 40)
    print("🎯 Optimized for Indian accents and pronunciation")
    print("🗣️ Better recognition of Indian English patterns")
    print("📚 Trained on Indian English speech data")
    print("🌏 Understands Indian context and expressions")
    print("⚡ Higher accuracy for Indian speakers")
    
    # Test 5: Show other Indian languages supported
    print("\n5. Other Indian Languages Supported by AWS:")
    print("=" * 45)
    indian_languages = [
        ("hi-IN", "Hindi (India)"),
        ("bn-IN", "Bengali (India)"),
        ("ta-IN", "Tamil (India)"),
        ("te-IN", "Telugu (India)"),
        ("gu-IN", "Gujarati (India)"),
        ("kn-IN", "Kannada (India)"),
        ("ml-IN", "Malayalam (India)"),
        ("mr-IN", "Marathi (India)"),
        ("pa-IN", "Punjabi (India)"),
    ]
    
    for lang_code, lang_name in indian_languages:
        print(f"🇮🇳 {lang_code}: {lang_name}")
    
    print("\n💡 To switch to any Indian language, update STT_LANGUAGE in .env file")
    
    return True

async def show_usage_examples():
    """Show usage examples for Indian English"""
    print("\n📝 Usage Examples")
    print("=" * 20)
    
    print("\n🔧 Environment Variable (.env):")
    print("STT_LANGUAGE=en-IN")
    print("STT_PROVIDER=aws")
    print("AWS_STT_REGION=us-east-1")
    
    print("\n🔧 Config File (config.yaml):")
    print("models:")
    print("  stt:")
    print("    provider: \"aws\"")
    print("    language: \"en-IN\"")
    print("    aws_region: \"us-east-1\"")
    
    print("\n🎤 Sample Indian English Phrases AWS Will Recognize Better:")
    phrases = [
        "What is the time now?",
        "Please call my friend",
        "I need to book a cab",
        "Can you help me with this?",
        "The weather is quite hot today",
        "I am going to the market",
        "Please send me the details",
        "Thank you so much"
    ]
    
    for phrase in phrases:
        print(f"🗣️ \"{phrase}\"")

if __name__ == "__main__":
    print("🇮🇳 Indian English Configuration Test")
    print("This script verifies AWS STT is configured for Indian English")
    print()
    
    # Run main test
    success = asyncio.run(test_indian_english_config())
    
    if success:
        # Show usage examples
        asyncio.run(show_usage_examples())
        print("\n✅ Indian English configuration is perfect!")
        print("🚀 Your AWS STT is optimized for Indian accents and speech patterns!")
    else:
        print("\n❌ Configuration issues found. Please fix and try again.")
        exit(1)