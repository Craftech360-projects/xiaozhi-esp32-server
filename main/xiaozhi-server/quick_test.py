"""
Quick OAC Test - Run this after configuring OAC
"""
import requests
import time

def quick_oac_test():
    print("🚀 QUICK OAC TEST")
    print("="*40)
    
    url = "https://dbtnllz9fcr1z.cloudfront.net/stories/Fantasy/mary had a little lamb.mp3"
    
    print(f"Testing: {url}")
    
    try:
        response = requests.head(url, timeout=15)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("🎉 SUCCESS! OAC is working!")
            print(f"Cache Status: {response.headers.get('x-cache', 'Unknown')}")
            print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
            print(f"Content-Length: {response.headers.get('content-length', 'Unknown')} bytes")
            
            # Test CDN helper
            print(f"\n✅ CDN Helper Test:")
            from utils.cdn_helper import get_audio_url
            test_url = get_audio_url("stories/Fantasy/mary had a little lamb.mp3")
            print(f"Generated URL: {test_url}")
            
            return True
            
        elif response.status_code == 403:
            print("❌ Still 403 - OAC not configured yet or still deploying")
            print("⏰ Wait 5-10 more minutes and try again")
            
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    success = quick_oac_test()
    
    if success:
        print(f"\n🎯 CDN SETUP COMPLETE!")
        print(f"Your audio streaming CDN is ready to use!")
    else:
        print(f"\n⏳ Complete OAC configuration in CloudFront console")
        print(f"Then wait 10 minutes and run: python quick_test.py")