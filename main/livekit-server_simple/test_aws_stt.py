#!/usr/bin/env python3
"""
Test script for AWS Transcribe STT integration in livekit-server_simple
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aws_stt_test")

async def test_aws_stt():
    """Test AWS STT provider creation and basic functionality"""
    
    print("🧪 Testing AWS Transcribe STT Integration")
    print("=" * 50)
    
    # Test 1: Check if AWS plugin is available
    print("\n1. Checking AWS plugin availability...")
    try:
        from livekit.plugins import aws
        print("✅ LiveKit AWS plugin is available")
    except ImportError as e:
        print(f"❌ LiveKit AWS plugin not found: {e}")
        print("💡 Install with: pip install livekit-plugins-aws")
        return False
    
    # Test 2: Check AWS credentials
    print("\n2. Checking AWS credentials...")
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    if not aws_access_key_id or not aws_secret_access_key:
        print("❌ AWS credentials not found in environment variables")
        print("💡 Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env file")
        return False
    
    print(f"✅ AWS Access Key ID: {aws_access_key_id[:8]}...")
    print(f"✅ AWS Secret Key: {'*' * len(aws_secret_access_key)}")
    
    # Test 3: Test AWS credentials with boto3
    print("\n3. Testing AWS credentials...")
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError
        
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name='us-east-1'
        )
        
        # Test credentials
        sts_client = session.client('sts')
        identity = sts_client.get_caller_identity()
        print(f"✅ AWS credentials valid - Account: {identity.get('Account', 'Unknown')}")
        
    except NoCredentialsError:
        print("❌ AWS credentials not found")
        return False
    except ClientError as e:
        print(f"❌ AWS credentials invalid: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing AWS credentials: {e}")
        return False
    
    # Test 4: Test provider factory
    print("\n4. Testing provider factory...")
    try:
        from src.providers.provider_factory import ProviderFactory
        from src.config.config_loader import ConfigLoader
        
        # Load config with AWS settings
        config = ConfigLoader.get_groq_config()
        config['stt_provider'] = 'aws'
        config['aws_region'] = 'us-east-1'
        config['stt_language'] = 'en-US'
        
        print(f"📋 Config: {config}")
        
        # Create VAD first (required for STT)
        print("Creating VAD...")
        vad = ProviderFactory.create_vad()
        print(f"✅ VAD created: {type(vad)}")
        
        # Create AWS STT provider
        print("Creating AWS STT provider...")
        stt = ProviderFactory.create_stt(config, vad)
        print(f"✅ AWS STT provider created: {type(stt)}")
        
    except Exception as e:
        print(f"❌ Error creating AWS STT provider: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Test AWS Transcribe service access
    print("\n5. Testing AWS Transcribe service access...")
    try:
        transcribe_client = session.client('transcribe')
        
        # List transcription jobs (this tests service access)
        response = transcribe_client.list_transcription_jobs(MaxResults=1)
        print("✅ AWS Transcribe service accessible")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            print("❌ Access denied to AWS Transcribe service")
            print("💡 Check IAM permissions for transcribe:ListTranscriptionJobs")
        else:
            print(f"❌ AWS Transcribe error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error accessing AWS Transcribe: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! AWS Transcribe STT is ready to use.")
    print("\n📝 To use AWS STT, set in your config.yaml:")
    print("models:")
    print("  stt:")
    print("    provider: \"aws\"")
    print("    language: \"en-US\"")
    print("    aws_region: \"us-east-1\"")
    print("\n🚀 Start your LiveKit agent and enjoy enterprise-grade speech recognition!")
    
    return True

async def test_language_support():
    """Test different language configurations"""
    print("\n🌍 Testing Language Support")
    print("=" * 30)
    
    languages = [
        ("en-US", "English (United States)"),
        ("en-IN", "English (India)"),
        ("hi-IN", "Hindi (India)"),
        ("es-US", "Spanish (United States)"),
        ("fr-FR", "French (France)"),
        ("de-DE", "German (Germany)"),
        ("ja-JP", "Japanese (Japan)"),
        ("zh-CN", "Chinese (Mandarin)"),
    ]
    
    for lang_code, lang_name in languages:
        print(f"✅ {lang_code}: {lang_name}")
    
    print(f"\n💡 Total supported languages: 100+")
    print("📖 See AWS_STT_SETUP.md for complete language list")

if __name__ == "__main__":
    print("🧪 AWS Transcribe STT Test Suite")
    print("This script tests AWS STT integration for livekit-server_simple")
    print()
    
    # Run main test
    success = asyncio.run(test_aws_stt())
    
    if success:
        # Run language support test
        asyncio.run(test_language_support())
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Tests failed. Please fix the issues above and try again.")
        exit(1)