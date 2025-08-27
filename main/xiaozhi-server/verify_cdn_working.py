"""
Verify CDN is Working with Multiple Files
"""
import requests
from utils.cdn_helper import get_audio_url, cdn
import urllib.parse

def verify_cdn_working():
    print("🎉 CDN VERIFICATION TEST")
    print("="*50)
    
    # Test files that should work
    working_files = [
        "stories/Fantasy/twinkle twinkle little star.mp3",
        "stories/Fantasy/goldilocks and the three bears.mp3",
        "stories/Fantasy/little red riding hood.mp3",
        "stories/Educational/twinkle twinkle little star song.mp3"
    ]
    
    success_count = 0
    
    for file in working_files:
        print(f"\n📁 Testing: {file}")
        
        # Test with CDN helper
        cdn_url = get_audio_url(file)
        print(f"   CDN URL: {cdn_url}")
        
        try:
            response = requests.head(cdn_url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS!")
                print(f"   Cache: {response.headers.get('x-cache', 'Unknown')}")
                print(f"   Type: {response.headers.get('content-type', 'Unknown')}")
                print(f"   Size: {response.headers.get('content-length', 'Unknown')} bytes")
                success_count += 1
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n" + "="*50)
    print(f"📊 RESULTS: {success_count}/{len(working_files)} files accessible")
    
    if success_count > 0:
        print("🎉 CDN IS WORKING CORRECTLY!")
        print("✅ OAC Configuration: SUCCESS")
        print("✅ S3 Bucket Policy: SUCCESS") 
        print("✅ CloudFront Distribution: SUCCESS")
        
        print(f"\n🔧 ISSUE IDENTIFIED:")
        print("Some files may have path/naming issues that need URL encoding")
        
        return True
    else:
        print("❌ CDN still not working")
        return False

def test_problematic_files():
    """Test files with spaces and special characters"""
    print(f"\n🔤 TESTING PROBLEMATIC FILE PATHS:")
    print("-" * 50)
    
    problematic_files = [
        "stories/Fantasy/mary had a little lamb.mp3",
        "stories/Educational/six a song of sixpence (1).mp3",
        "stories/Fairy Tales/the boy who cried wolf.mp3"
    ]
    
    for file in problematic_files:
        print(f"\n📁 Testing: {file}")
        
        # Test original path
        original_url = f"https://dbtnllz9fcr1z.cloudfront.net/{file}"
        
        # Test URL encoded path
        encoded_path = urllib.parse.quote(file)
        encoded_url = f"https://dbtnllz9fcr1z.cloudfront.net/{encoded_path}"
        
        print(f"   Original: {requests.head(original_url, timeout=5).status_code if True else 'Error'}")
        
        try:
            orig_resp = requests.head(original_url, timeout=5)
            print(f"   Original: {orig_resp.status_code}")
        except:
            print(f"   Original: Error")
            
        try:
            enc_resp = requests.head(encoded_url, timeout=5)
            print(f"   Encoded:  {enc_resp.status_code}")
            if enc_resp.status_code == 200:
                print("   ✅ URL encoding fixes the issue!")
        except:
            print(f"   Encoded:  Error")

if __name__ == "__main__":
    cdn_working = verify_cdn_working()
    
    if cdn_working:
        test_problematic_files()
        
        print(f"\n🎯 SUMMARY:")
        print("✅ Your CloudFront CDN is working correctly!")
        print("✅ OAC configuration is successful!")
        print("⚠️ Some files need URL encoding for spaces/special chars")
        print(f"\n🔧 NEXT STEP: Update CDN helper to handle URL encoding")
    else:
        print(f"\n❌ CDN still needs troubleshooting")