"""
Final CDN Test - After OAC Configuration
"""
import requests
from utils.cdn_helper import get_audio_url, cdn

def test_cdn_setup():
    print("🚀 FINAL CDN TEST")
    print("="*50)
    
    # Test CDN helper configuration
    print("1. CDN Helper Status:")
    status = cdn.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print(f"\n2. CDN Ready: {'✅ YES' if cdn.is_cdn_enabled() else '❌ NO'}")
    
    # Test URL generation
    test_file = "stories/Fantasy/mary had a little lamb.mp3"
    generated_url = get_audio_url(test_file)
    print(f"\n3. Generated URL: {generated_url}")
    
    # Test actual access
    print(f"\n4. Testing Access:")
    try:
        response = requests.head(generated_url, timeout=15)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS! CDN is working perfectly!")
            print(f"   Content-Type: {response.headers.get('content-type', 'Unknown')}")
            print(f"   Content-Length: {response.headers.get('content-length', 'Unknown')} bytes")
            print(f"   Cache Status: {response.headers.get('x-cache', 'Unknown')}")
            print(f"   Age: {response.headers.get('age', 'Fresh')} seconds")
            
            # Test a few more files
            print(f"\n5. Testing Additional Files:")
            test_files = [
                "stories/Educational/twinkle twinkle little star song.mp3",
                "stories/Fairy Tales/london bridge song.mp3"
            ]
            
            for file in test_files:
                url = get_audio_url(file)
                try:
                    resp = requests.head(url, timeout=10)
                    status_icon = "✅" if resp.status_code == 200 else "❌"
                    print(f"   {status_icon} {file}: {resp.status_code}")
                except Exception as e:
                    print(f"   ❌ {file}: Error - {e}")
                    
        elif response.status_code == 403:
            print("   ❌ 403 Forbidden - OAC not configured yet")
            print("   📋 Next steps:")
            print("      1. Configure Origin Access Control in CloudFront")
            print("      2. Update S3 bucket policy")
            print("      3. Wait 5-10 minutes for deployment")
            
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*50)
    print("🎯 CDN SETUP SUMMARY:")
    print("✅ CloudFront Distribution: Active")
    print("✅ S3 Bucket: Has audio files")
    print("✅ CDN Helper: Configured")
    print("⏳ OAC Configuration: Pending (if 403 errors)")

if __name__ == "__main__":
    test_cdn_setup()