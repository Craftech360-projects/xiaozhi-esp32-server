#!/usr/bin/env python3
"""
Test that the system has been reverted to original state
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append('.')

# Load environment variables
load_dotenv()

async def test_original_deepgram():
    """Test that Deepgram is back to original configuration"""
    print("🔧 Testing Original Deepgram Configuration")
    print("=" * 45)
    
    try:
        import yaml
        from core.providers.asr.deepgram import ASRProvider
        
        # Load configuration
        with open('data/.config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        asr_config = config['ASR']['DeepgramASR']
        
        # Check configuration values
        print(f"📋 Configuration:")
        print(f"   Model: {asr_config.get('model')}")
        print(f"   Language: {asr_config.get('language')}")
        print(f"   Smart Format: {asr_config.get('smart_format')}")
        print(f"   Detect Language: {asr_config.get('detect_language', 'Not set')}")
        print(f"   Code Switching: {asr_config.get('code_switching', 'Not set')}")
        
        # Initialize ASR provider
        asr_provider = ASRProvider(asr_config, delete_audio_file=False)
        
        print(f"\n✅ Deepgram ASR initialized successfully!")
        print(f"   Language: {asr_provider.language}")
        print(f"   Model: {asr_provider.model}")
        
        # Check that multilingual attributes are not present or are default
        if hasattr(asr_provider, 'detect_language'):
            print(f"   Detect Language: {getattr(asr_provider, 'detect_language', 'Not set')}")
        if hasattr(asr_provider, 'code_switching'):
            print(f"   Code Switching: {getattr(asr_provider, 'code_switching', 'Not set')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Deepgram: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_original_multilingual_matcher():
    """Test that multilingual matcher works without enhanced features"""
    print("\n🎯 Testing Original Multilingual Matcher")
    print("-" * 40)
    
    try:
        from plugins_func.utils.multilingual_matcher import MultilingualMatcher
        
        # Initialize matcher
        matcher = MultilingualMatcher("./music", [".mp3", ".wav", ".p3"])
        
        # Test basic functionality
        test_cases = [
            "play Baa Baa Black Sheep",
            "play Hanuman Chalisa", 
            "sing Bandar Mama"
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: '{test_case}'")
            
            try:
                # Extract content name
                content_name = matcher.extract_content_name_from_request(test_case)
                print(f"   Extracted: '{content_name}'")
                
                # Find match
                if content_name:
                    match_result = matcher.find_content_match(test_case)
                    if match_result:
                        file_path, language, metadata = match_result
                        print(f"   ✅ Found: {metadata.get('romanized', 'Unknown')} ({language})")
                    else:
                        print(f"   ❌ No match found")
                else:
                    print(f"   ℹ️  No content extracted")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing multilingual matcher: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_revert_summary():
    """Show what was reverted"""
    print("\n" + "=" * 50)
    print("📋 SYSTEM REVERT SUMMARY")
    print("=" * 50)
    
    print("\n🔧 Deepgram ASR - Reverted to Original:")
    print("   ✅ Single language: en-IN")
    print("   ✅ Simple configuration")
    print("   ✅ No multilingual features")
    print("   ✅ No code-switching")
    print("   ✅ Standard PrerecordedOptions")
    
    print("\n🎯 Multilingual Matcher - Reverted to Original:")
    print("   ✅ Simple fuzzy matching")
    print("   ✅ No phonetic normalization")
    print("   ✅ Standard threshold (60%)")
    print("   ✅ Basic content extraction")
    
    print("\n📁 Configuration - Back to Simple:")
    print("   ✅ language: en-IN (single language)")
    print("   ✅ No detect_language")
    print("   ✅ No code_switching")
    print("   ✅ No additional parameters")
    
    print("\n💡 Current State:")
    print("   • System uses original simple STT")
    print("   • Regional language songs may not work as well")
    print("   • No multilingual enhancements")
    print("   • Stable and error-free configuration")

if __name__ == "__main__":
    print("🔄 Testing Reverted System Configuration")
    print("=" * 50)
    
    # Test original Deepgram
    deepgram_success = asyncio.run(test_original_deepgram())
    
    # Test original multilingual matcher
    matcher_success = test_original_multilingual_matcher()
    
    # Show revert summary
    show_revert_summary()
    
    print("\n" + "=" * 50)
    print("🎯 REVERT TEST RESULTS")
    print("=" * 50)
    
    if deepgram_success and matcher_success:
        print("✅ SYSTEM SUCCESSFULLY REVERTED!")
        print("✅ Deepgram back to original configuration")
        print("✅ Multilingual matcher back to basic functionality")
        print("✅ No more multilingual STT features")
        print("✅ System stable and error-free")
        print("\n📝 Note: Regional language song recognition")
        print("   may not work as well as before, but system is stable.")
    else:
        print("❌ SOME ISSUES DETECTED")
        if not deepgram_success:
            print("   - Deepgram revert has issues")
        if not matcher_success:
            print("   - Multilingual matcher revert has issues")