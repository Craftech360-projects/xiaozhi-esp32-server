#!/usr/bin/env python3
"""
Simple connection test for remote services
Tests that the servers are reachable and responding
"""
import requests
import sys

def test_connection(name, url):
    """Test if a service is reachable"""
    print(f"\n🔍 Testing {name} at {url}")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {name} is ONLINE")
            print(f"   Response: {data}")
            return True
        else:
            print(f"❌ {name} returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name} is OFFLINE (connection refused)")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ {name} TIMEOUT (no response)")
        return False
    except Exception as e:
        print(f"❌ {name} ERROR: {e}")
        return False

def main():
    """Test both services"""
    print("=" * 60)
    print("🌐 Remote Services Connection Test")
    print("=" * 60)
    
    whisper_ok = test_connection(
        "Whisper Server",
        "http://192.168.1.114:8000/health"
    )
    
    piper_ok = test_connection(
        "Piper Server",
        "http://192.168.1.114:8001/health"
    )
    
    print("\n" + "=" * 60)
    print("📊 Connection Test Results")
    print("=" * 60)
    print(f"Whisper Server: {'✅ ONLINE' if whisper_ok else '❌ OFFLINE'}")
    print(f"Piper Server:   {'✅ ONLINE' if piper_ok else '❌ OFFLINE'}")
    print("=" * 60)
    
    if whisper_ok and piper_ok:
        print("\n✅ Both servers are reachable!")
        print("\n📝 Next steps:")
        print("   1. Update your .env file:")
        print("      STT_PROVIDER=remote_whisper")
        print("      REMOTE_WHISPER_URL=http://192.168.1.114:8000")
        print("      TTS_PROVIDER=remote_piper")
        print("      REMOTE_PIPER_URL=http://192.168.1.114:8001")
        print("\n   2. Start your LiveKit agent:")
        print("      python simple_main.py dev")
        return 0
    else:
        print("\n⚠️  Some servers are not reachable.")
        print("   Check that the servers are running on 192.168.1.114")
        return 1

if __name__ == "__main__":
    sys.exit(main())
