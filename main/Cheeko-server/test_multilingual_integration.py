#!/usr/bin/env python3
"""
Test script for multilingual music and story integration
"""

import sys
import os
import random
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from plugins_func.utils.multilingual_matcher import MultilingualMatcher

def test_music_matcher():
    """Test the multilingual music matcher"""
    print("=== Testing Multilingual Music Matcher ===")
    
    music_dir = "./music"
    music_ext = [".mp3", ".wav", ".m4a"]
    
    try:
        matcher = MultilingualMatcher(music_dir, music_ext)
        print(f"✓ Matcher initialized successfully")
        print(f"✓ Found language folders: {matcher.language_folders}")
        
        # Test various requests
        test_requests = [
            "play Baa Baa Black Sheep",
            "sing Hanuman Chalisa",
            "play bandar mama or kele song",  # Test the problematic case
            "play Hindi song",
            "Telugu music please", 
            "play phonics",
            "any English song",
            "play Baby Shark",
            "sing me Lakdi Ki Kathi",
            "play some Hindi music"
        ]
        
        print("\n--- Testing Music Requests ---")
        for request in test_requests:
            print(f"\nRequest: '{request}'")
            
            # Test language detection
            detected_lang = matcher.detect_language_from_request(request)
            print(f"  Detected language: {detected_lang}")
            
            # Check if language-only request
            is_lang_only = matcher.is_language_only_request(request)
            print(f"  Language-only request: {is_lang_only}")
            
            # Test content matching
            match_result = matcher.find_content_match(request, detected_lang)
            if match_result:
                file_path, language, metadata = match_result
                print(f"  ✓ Match found: {file_path} ({language})")
                print(f"    Title: {metadata.get('romanized', 'Unknown')}")
            else:
                if is_lang_only and detected_lang:
                    # Test language-specific content
                    lang_content = matcher.get_language_specific_content(detected_lang)
                    if lang_content:
                        print(f"  ✓ Language-specific content available: {len(lang_content)} songs")
                        sample = random.choice(lang_content)
                        print(f"    Sample: {sample[1].get('romanized', 'Unknown')}")
                    else:
                        print(f"  ✗ No {detected_lang} content found")
                else:
                    print(f"  ✗ No specific match found")
        
        # Test language-specific content
        print("\n--- Testing Language-Specific Content ---")
        for lang in matcher.language_folders:
            content = matcher.get_language_specific_content(lang)
            print(f"{lang.title()}: {len(content)} songs")
            if content:
                print(f"  Sample: {content[0][1].get('romanized', 'Unknown')}")
        
    except Exception as e:
        print(f"✗ Error testing music matcher: {e}")
        import traceback
        traceback.print_exc()

def test_story_matcher():
    """Test the multilingual story matcher"""
    print("\n=== Testing Multilingual Story Matcher ===")
    
    story_dir = "./stories"
    story_ext = [".mp3", ".wav", ".m4a"]
    
    try:
        matcher = MultilingualMatcher(story_dir, story_ext)
        print(f"✓ Story matcher initialized successfully")
        
        if matcher.language_folders:
            print(f"✓ Found language folders: {matcher.language_folders}")
        else:
            print("ℹ No metadata.json found, using filesystem fallback")
            # Test filesystem fallback
            files = matcher.fallback_to_filesystem()
            print(f"✓ Found {len(files)} story files via filesystem")
            if files:
                print(f"  Sample stories: {files[:3]}")
        
        # Test story requests
        test_requests = [
            "tell me The Boy Who Cried Wolf",
            "play a bedtime story",
            "fantasy story please",
            "educational story",
            "any story"
        ]
        
        print("\n--- Testing Story Requests ---")
        for request in test_requests:
            print(f"\nRequest: '{request}'")
            
            # Test content matching
            match_result = matcher.find_content_match(request)
            if match_result:
                file_path, language, metadata = match_result
                print(f"  ✓ Match found: {file_path} ({language})")
                print(f"    Title: {metadata.get('romanized', 'Unknown')}")
            else:
                print(f"  ✗ No match found")
        
    except Exception as e:
        print(f"✗ Error testing story matcher: {e}")
        import traceback
        traceback.print_exc()

def test_content_extraction():
    """Test content name extraction"""
    print("\n=== Testing Content Name Extraction ===")
    
    matcher = MultilingualMatcher("./music", [".mp3"])
    
    test_phrases = [
        "play Baa Baa Black Sheep",
        "sing me Hanuman Chalisa please",
        "I want to hear Baby Shark Dance",
        "put on some Hindi music",
        "play phonics songs for kids",
        "tell me The Boy Who Cried Wolf story",
        "I want a bedtime story please"
    ]
    
    for phrase in test_phrases:
        extracted = matcher.extract_content_name_from_request(phrase)
        print(f"'{phrase}' → '{extracted}'")

if __name__ == "__main__":
    print("Multilingual Integration Test")
    print("=" * 50)
    
    # Change to the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    test_content_extraction()
    test_music_matcher()
    test_story_matcher()
    
    print("\n" + "=" * 50)
    print("Test completed!")