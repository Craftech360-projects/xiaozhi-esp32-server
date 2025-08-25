#!/usr/bin/env python3
"""
Test script to verify story functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from plugins_func.utils.multilingual_matcher import MultilingualMatcher

def test_story_system():
    """Test the story system functionality"""
    print("=== Testing Story System ===")
    
    story_dir = "./stories"
    story_ext = [".mp3", ".wav", ".m4a"]
    
    try:
        # Test multilingual matcher for stories
        matcher = MultilingualMatcher(story_dir, story_ext)
        print(f"✓ Story matcher initialized")
        
        if matcher.language_folders:
            print(f"✓ Found story categories with metadata: {matcher.language_folders}")
            
            # Test specific story requests
            test_requests = [
                "tell me a story",
                "play The Boy Who Cried Wolf",
                "bedtime story please",
                "fantasy story",
                "educational story"
            ]
            
            print("\n--- Testing Story Requests ---")
            for request in test_requests:
                print(f"\nRequest: '{request}'")
                
                # Test story matching
                match_result = matcher.find_content_match(request)
                if match_result:
                    file_path, category, metadata = match_result
                    print(f"  ✓ Match found: {file_path} ({category})")
                    print(f"    Title: {metadata.get('romanized', 'Unknown')}")
                else:
                    print(f"  ✗ No specific match found")
        else:
            print("ℹ No metadata.json found, using filesystem fallback")
            
        # Test filesystem fallback
        files = matcher.fallback_to_filesystem()
        print(f"\n✓ Total story files available: {len(files)}")
        
        if files:
            print("Sample stories:")
            for i, file in enumerate(files[:5]):  # Show first 5
                print(f"  {i+1}. {file}")
                
            # Test by category
            categories = {}
            for file in files:
                category = file.split(os.sep)[0] if os.sep in file else 'root'
                if category not in categories:
                    categories[category] = []
                categories[category].append(file)
            
            print(f"\n✓ Story categories found: {list(categories.keys())}")
            for category, story_files in categories.items():
                print(f"  {category}: {len(story_files)} stories")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

def test_story_function_description():
    """Test that the story function description is clear"""
    print("\n=== Testing Story Function Description ===")
    
    try:
        from plugins_func.functions.play_story import play_story_function_desc
        
        description = play_story_function_desc["function"]["description"]
        print("Function Description:")
        print(description)
        
        # Check for key phrases
        key_phrases = [
            "ALWAYS use this function",
            "NEVER generate",
            "pre-recorded",
            "audio files"
        ]
        
        print("\n--- Checking Key Phrases ---")
        for phrase in key_phrases:
            if phrase in description:
                print(f"  ✓ Contains: '{phrase}'")
            else:
                print(f"  ✗ Missing: '{phrase}'")
                
    except Exception as e:
        print(f"✗ Error loading function description: {e}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    test_story_system()
    test_story_function_description()
    
    print("\n" + "=" * 50)
    print("Story functionality test completed!")
    print("If you see story files listed above, the system should work correctly.")
    print("Make sure to restart your server to apply the configuration changes.")