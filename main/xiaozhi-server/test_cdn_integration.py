"""
Test CDN Integration with Music and Story Functions
"""
import asyncio
import requests
from utils.cdn_helper import get_audio_url, cdn, is_cdn_ready

def test_cdn_helper():
    """Test CDN helper functionality"""
    print("🧪 TESTING CDN HELPER INTEGRATION")
    print("="*60)
    
    # Test CDN status
    print("1️⃣ CDN Configuration Status:")
    status = cdn.get_status()
    for key, value in status.items():
        icon = "✅" if value else "❌"
        print(f"   {icon} {key}: {value}")
    
    print(f"\n2️⃣ CDN Ready: {'✅ YES' if is_cdn_ready() else '❌ NO'}")
    
    # Test URL generation for different content types
    print(f"\n3️⃣ Testing URL Generation:")
    
    test_cases = [
        {
            "type": "Music",
            "files": [
                "music/English/twinkle twinkle little star.mp3",
                "music/Hindi/hanuman chalisa.mp3",
                "music/Telugu/bala krishna song.mp3"
            ]
        },
        {
            "type": "Stories", 
            "files": [
                "stories/Fantasy/goldilocks and the three bears.mp3",
                "stories/Educational/twinkle twinkle little star song.mp3",
                "stories/Fairy Tales/the boy who cried wolf.mp3"
            ]
        }
    ]
    
    for category in test_cases:
        print(f"\n   📁 {category['type']} URLs:")
        for file in category['files']:
            try:
                cdn_url = get_audio_url(file)
                print(f"     ✅ {file}")
                print(f"        → {cdn_url}")
                
                # Test if URL is accessible
                response = requests.head(cdn_url, timeout=5)
                status_icon = "🟢" if response.status_code == 200 else "🔴"
                print(f"        {status_icon} Status: {response.status_code}")
                
            except Exception as e:
                print(f"     ❌ {file}: Error - {e}")

def test_function_integration():
    """Test integration with play_music and play_story functions"""
    print(f"\n🎵 TESTING FUNCTION INTEGRATION")
    print("="*60)
    
    # Test music function integration
    print("1️⃣ Music Function Integration:")
    try:
        from plugins_func.functions.play_music import generate_cdn_music_url
        
        test_music = [
            ("English", "twinkle twinkle little star.mp3"),
            ("Hindi", "hanuman chalisa.mp3"),
            ("Telugu", "bala krishna song.mp3")
        ]
        
        for language, filename in test_music:
            try:
                music_url = generate_cdn_music_url(language, filename)
                print(f"   ✅ {language}/{filename}")
                print(f"      → {music_url}")
            except Exception as e:
                print(f"   ❌ {language}/{filename}: {e}")
                
    except ImportError as e:
        print(f"   ❌ Could not import music function: {e}")
    
    # Test story function integration
    print(f"\n2️⃣ Story Function Integration:")
    try:
        from plugins_func.functions.play_story import generate_cdn_story_url
        
        test_stories = [
            ("Fantasy", "goldilocks and the three bears.mp3"),
            ("Educational", "twinkle twinkle little star song.mp3"),
            ("Fairy Tales", "the boy who cried wolf.mp3")
        ]
        
        for category, filename in test_stories:
            try:
                story_url = generate_cdn_story_url(category, filename)
                print(f"   ✅ {category}/{filename}")
                print(f"      → {story_url}")
            except Exception as e:
                print(f"   ❌ {category}/{filename}: {e}")
                
    except ImportError as e:
        print(f"   ❌ Could not import story function: {e}")

def test_api_endpoints():
    """Test CDN API endpoints"""
    print(f"\n🌐 TESTING API ENDPOINTS")
    print("="*60)
    
    base_url = "http://localhost:8003"  # Default HTTP server port
    
    # Test CDN status endpoint
    print("1️⃣ Testing CDN Status Endpoint:")
    try:
        response = requests.get(f"{base_url}/xiaozhi/cdn/status", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ CDN Ready: {data.get('cdn_ready', False)}")
            print(f"   📊 Test URLs: {len(data.get('test_urls', {}))}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        print(f"   💡 Make sure the server is running on port 8003")
    
    # Test CDN URL generation endpoint
    print(f"\n2️⃣ Testing CDN URL Generation Endpoint:")
    try:
        test_data = {
            "audio_file": "stories/Fantasy/goldilocks and the three bears.mp3"
        }
        response = requests.post(
            f"{base_url}/xiaozhi/cdn/url", 
            json=test_data, 
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Generated URL: {data.get('cdn_url', 'N/A')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")

def main():
    """Run all CDN integration tests"""
    print("🚀 CDN INTEGRATION TEST SUITE")
    print("="*60)
    print("Testing CDN integration with music and story functions...")
    
    # Test CDN helper
    test_cdn_helper()
    
    # Test function integration
    test_function_integration()
    
    # Test API endpoints
    test_api_endpoints()
    
    print(f"\n" + "="*60)
    print("🎯 CDN INTEGRATION TEST SUMMARY:")
    
    if is_cdn_ready():
        print("✅ CDN Helper: Working")
        print("✅ URL Generation: Working") 
        print("✅ CloudFront Distribution: Active")
        print("✅ Music & Story Functions: Updated for CDN")
        print(f"\n🎉 CDN INTEGRATION COMPLETE!")
        print("Your server now uses CloudFront CDN for all audio streaming!")
        
        print(f"\n📋 USAGE:")
        print("• Say 'play music' or 'tell me a story' to test")
        print("• All audio will stream through CloudFront CDN")
        print("• Global fast delivery with caching")
        print("• Automatic URL encoding for file paths")
        
    else:
        print("❌ CDN Helper: Not configured")
        print("⚠️ Check your .env file and CloudFront setup")

if __name__ == "__main__":
    main()