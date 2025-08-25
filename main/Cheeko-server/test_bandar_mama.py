#!/usr/bin/env python3
"""
Quick test for the Bandar Mama song matching issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from plugins_func.utils.multilingual_matcher import MultilingualMatcher

def test_bandar_mama():
    """Test the specific Bandar Mama song matching"""
    print("=== Testing Bandar Mama Song Matching ===")
    
    music_dir = "./music"
    music_ext = [".mp3", ".wav", ".m4a"]
    
    try:
        matcher = MultilingualMatcher(music_dir, music_ext)
        
        # Test the problematic request
        request = "play bandar mama or kele song"
        print(f"Request: '{request}'")
        
        # Test language detection
        detected_lang = matcher.detect_language_from_request(request)
        print(f"Detected language: {detected_lang}")
        
        # Test content matching without language hint (this should find the Hindi song)
        match_result = matcher.find_content_match(request, None)
        if match_result:
            file_path, language, metadata = match_result
            print(f"✓ Match found: {file_path} ({language})")
            print(f"  Title: {metadata.get('romanized', 'Unknown')}")
            print(f"  Alternatives: {metadata.get('alternatives', [])}")
        else:
            print("✗ No match found")
        
        # Test with wrong language hint (simulating LLM error)
        print(f"\n--- Testing with wrong language hint (kannada) ---")
        match_result_wrong = matcher.find_content_match(request, "kannada")
        if match_result_wrong:
            file_path, language, metadata = match_result_wrong
            print(f"✓ Match found despite wrong hint: {file_path} ({language})")
        else:
            print("✗ No match found with wrong language hint")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    test_bandar_mama()