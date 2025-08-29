"""
Diagnose OAC Configuration Issues
"""
import requests
import time

def diagnose_cloudfront_oac():
    print("🔍 DIAGNOSING CLOUDFRONT OAC CONFIGURATION")
    print("="*60)
    
    # Your CloudFront details
    cloudfront_domain = "dbtnllz9fcr1z.cloudfront.net"
    distribution_id = "E2SE5I55XYE7OL"
    
    print(f"CloudFront Domain: {cloudfront_domain}")
    print(f"Distribution ID: {distribution_id}")
    print(f"S3 Bucket Policy: ✅ Configured correctly")
    
    # Test file
    test_file = "stories/Fantasy/mary had a little lamb.mp3"
    cloudfront_url = f"https://{cloudfront_domain}/{test_file}"
    s3_url = f"https://cheeko-audio-files.s3.us-east-1.amazonaws.com/{test_file}"
    
    print(f"\n📁 Test File: {test_file}")
    
    # Test 1: Direct S3 access (should be 403 - good!)
    print(f"\n1️⃣ Testing Direct S3 Access (should be 403):")
    try:
        s3_response = requests.head(s3_url, timeout=10)
        if s3_response.status_code == 403:
            print("   ✅ S3 Direct Access: 403 Forbidden (GOOD - bucket is secure)")
        else:
            print(f"   ⚠️ S3 Direct Access: {s3_response.status_code} (unexpected)")
    except Exception as e:
        print(f"   ❌ S3 Error: {e}")
    
    # Test 2: CloudFront access
    print(f"\n2️⃣ Testing CloudFront Access:")
    try:
        cf_response = requests.head(cloudfront_url, timeout=15)
        print(f"   Status: {cf_response.status_code}")
        
        if cf_response.status_code == 200:
            print("   ✅ SUCCESS! OAC is working!")
            print(f"   Cache Status: {cf_response.headers.get('x-cache', 'Unknown')}")
            return True
            
        elif cf_response.status_code == 403:
            print("   ❌ 403 Forbidden from CloudFront")
            print("   🔍 This means OAC is NOT properly configured")
            
        elif cf_response.status_code == 404:
            print("   ❌ 404 Not Found - File doesn't exist or path issue")
            
        else:
            print(f"   ❌ Unexpected status: {cf_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ CloudFront Error: {e}")
    
    # Test 3: Check CloudFront headers for clues
    print(f"\n3️⃣ Analyzing CloudFront Response Headers:")
    try:
        cf_response = requests.head(cloudfront_url, timeout=15)
        important_headers = [
            'x-cache', 'x-amz-cf-pop', 'x-amz-cf-id', 
            'server', 'x-amzn-errortype', 'x-amzn-requestid'
        ]
        
        print("   Headers:")
        for header in important_headers:
            value = cf_response.headers.get(header, 'Not present')
            print(f"     {header}: {value}")
            
    except Exception as e:
        print(f"   ❌ Header analysis failed: {e}")
    
    print(f"\n" + "="*60)
    print("🎯 DIAGNOSIS RESULTS:")
    
    if cf_response.status_code == 403:
        print("❌ ISSUE IDENTIFIED: OAC Configuration Problem")
        print("\n📋 SOLUTION STEPS:")
        print("1. Go to CloudFront Console")
        print("2. Click your distribution (E2SE5I55XYE7OL)")
        print("3. Go to 'Origins' tab")
        print("4. Edit the S3 origin")
        print("5. Under 'Origin access':")
        print("   - Select 'Origin access control settings (recommended)'")
        print("   - Create new OAC or select existing one")
        print("6. Save changes")
        print("7. Wait 5-10 minutes for deployment")
        print("8. Test again")
        
        print(f"\n⏰ If you just made changes, wait 10 minutes and test again")
        
    return False

def test_multiple_files():
    """Test multiple files to confirm OAC is working"""
    print(f"\n🧪 TESTING MULTIPLE FILES:")
    
    test_files = [
        "stories/Fantasy/mary had a little lamb.mp3",
        "stories/Educational/twinkle twinkle little star song.mp3",
        "stories/Fairy Tales/london bridge song.mp3"
    ]
    
    success_count = 0
    
    for file in test_files:
        url = f"https://dbtnllz9fcr1z.cloudfront.net/{file}"
        try:
            response = requests.head(url, timeout=10)
            status_icon = "✅" if response.status_code == 200 else "❌"
            print(f"   {status_icon} {response.status_code}: {file}")
            if response.status_code == 200:
                success_count += 1
        except Exception as e:
            print(f"   ❌ Error: {file} - {e}")
    
    print(f"\n📊 Results: {success_count}/{len(test_files)} files accessible")
    return success_count == len(test_files)

if __name__ == "__main__":
    oac_working = diagnose_cloudfront_oac()
    
    if oac_working:
        test_multiple_files()
        print(f"\n🎉 CDN SETUP COMPLETE! Your audio streaming CDN is ready!")
    else:
        print(f"\n⏳ Complete OAC configuration and test again in 10 minutes")