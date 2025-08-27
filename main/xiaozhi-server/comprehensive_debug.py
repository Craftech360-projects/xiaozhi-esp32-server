"""
Comprehensive CloudFront Debug - Check ALL potential issues
"""
import requests
import urllib.parse
import time

def comprehensive_debug():
    print("🔍 COMPREHENSIVE CLOUDFRONT DEBUG")
    print("="*60)
    
    # Configuration
    cloudfront_domain = "dbtnllz9fcr1z.cloudfront.net"
    distribution_id = "E2SE5I55XYE7OL"
    bucket_name = "cheeko-audio-files"
    
    print(f"CloudFront Domain: {cloudfront_domain}")
    print(f"Distribution ID: {distribution_id}")
    print(f"S3 Bucket: {bucket_name}")
    
    # Test different file paths and encodings
    test_cases = [
        {
            "name": "Original file with spaces",
            "path": "stories/Fantasy/mary had a little lamb.mp3",
            "encoded_path": "stories/Fantasy/mary%20had%20a%20little%20lamb.mp3"
        },
        {
            "name": "File without spaces",
            "path": "stories/Fantasy/twinkle twinkle little star.mp3",
            "encoded_path": "stories/Fantasy/twinkle%20twinkle%20little%20star.mp3"
        },
        {
            "name": "Simple file name",
            "path": "stories/Fantasy/goldilocks and the three bears.mp3",
            "encoded_path": "stories/Fantasy/goldilocks%20and%20the%20three%20bears.mp3"
        }
    ]
    
    print(f"\n🧪 TESTING DIFFERENT FILE PATHS:")
    print("-" * 60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ {test['name']}:")
        
        # Test 1: Original path
        cf_url_original = f"https://{cloudfront_domain}/{test['path']}"
        print(f"   Original URL: {cf_url_original}")
        
        try:
            response = requests.head(cf_url_original, timeout=10)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ SUCCESS!")
                return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 2: URL encoded path
        cf_url_encoded = f"https://{cloudfront_domain}/{test['encoded_path']}"
        print(f"   Encoded URL: {cf_url_encoded}")
        
        try:
            response = requests.head(cf_url_encoded, timeout=10)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ SUCCESS with URL encoding!")
                return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 3: Direct S3 check (should be 403)
        s3_url = f"https://{bucket_name}.s3.us-east-1.amazonaws.com/{test['path']}"
        try:
            s3_response = requests.head(s3_url, timeout=10)
            s3_status = "✅ Secure" if s3_response.status_code == 403 else f"⚠️ {s3_response.status_code}"
            print(f"   S3 Direct: {s3_status}")
        except:
            print(f"   S3 Direct: ❌ Error")
    
    print(f"\n" + "="*60)
    print("🔍 DETAILED ANALYSIS:")
    
    # Check CloudFront distribution status
    print(f"\n1️⃣ DISTRIBUTION STATUS CHECK:")
    try:
        root_response = requests.head(f"https://{cloudfront_domain}/", timeout=10)
        print(f"   Root access status: {root_response.status_code}")
        print(f"   Server header: {root_response.headers.get('server', 'Unknown')}")
        print(f"   CloudFront headers present: {'x-amz-cf-id' in root_response.headers}")
        
        if root_response.status_code == 403:
            print("   ✅ Distribution is active (403 expected for root)")
        else:
            print(f"   ⚠️ Unexpected root status: {root_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Distribution check failed: {e}")
    
    # Check for common issues
    print(f"\n2️⃣ COMMON ISSUE CHECKS:")
    
    # Issue 1: File path encoding
    print(f"   📁 File Path Issues:")
    problematic_chars = [' ', '(', ')', '[', ']', '&', '+']
    test_path = "stories/Fantasy/mary had a little lamb.mp3"
    
    for char in problematic_chars:
        if char in test_path:
            print(f"     ⚠️ Found '{char}' in path - may need URL encoding")
    
    # Issue 2: S3 bucket configuration
    print(f"   🪣 S3 Bucket Configuration:")
    try:
        # Check bucket region
        s3_response = requests.head(f"https://{bucket_name}.s3.amazonaws.com/", timeout=10)
        if 'x-amz-bucket-region' in s3_response.headers:
            region = s3_response.headers['x-amz-bucket-region']
            print(f"     Bucket region: {region}")
            if region != 'us-east-1':
                print(f"     ⚠️ Region mismatch - check CloudFront origin domain")
        else:
            print(f"     ✅ Bucket accessible")
    except Exception as e:
        print(f"     ❌ Bucket check failed: {e}")
    
    # Issue 3: CloudFront cache behavior
    print(f"   🔄 Cache Behavior Check:")
    test_url = f"https://{cloudfront_domain}/stories/Fantasy/mary%20had%20a%20little%20lamb.mp3"
    
    try:
        response = requests.head(test_url, timeout=15)
        cache_status = response.headers.get('x-cache', 'Unknown')
        print(f"     Cache status: {cache_status}")
        
        if 'Error from cloudfront' in cache_status:
            print(f"     ❌ CloudFront error - origin access issue")
        elif 'Miss from cloudfront' in cache_status:
            print(f"     ✅ CloudFront working - first request")
        elif 'Hit from cloudfront' in cache_status:
            print(f"     ✅ CloudFront working - cached response")
        else:
            print(f"     ⚠️ Unexpected cache status")
            
    except Exception as e:
        print(f"     ❌ Cache check failed: {e}")
    
    print(f"\n3️⃣ POTENTIAL SOLUTIONS:")
    print(f"   1. 🕐 Wait 15-20 minutes after OAC changes")
    print(f"   2. 🔄 Try URL-encoded file paths")
    print(f"   3. 📝 Check S3 bucket policy ARN matches distribution")
    print(f"   4. 🔍 Verify OAC is actually assigned to origin")
    print(f"   5. 🚫 Create CloudFront invalidation for test files")
    
    return False

def test_url_encoding():
    """Test if URL encoding fixes the issue"""
    print(f"\n🔤 URL ENCODING TEST:")
    print("-" * 40)
    
    original = "stories/Fantasy/mary had a little lamb.mp3"
    encoded = urllib.parse.quote(original)
    
    print(f"Original: {original}")
    print(f"Encoded:  {encoded}")
    
    url_encoded = f"https://dbtnllz9fcr1z.cloudfront.net/{encoded}"
    
    try:
        response = requests.head(url_encoded, timeout=15)
        print(f"Status with encoding: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS! URL encoding solved the issue!")
            return True
        else:
            print(f"❌ Still {response.status_code} with encoding")
            
    except Exception as e:
        print(f"❌ Error with encoding: {e}")
    
    return False

if __name__ == "__main__":
    print("Starting comprehensive CloudFront debugging...")
    
    success = comprehensive_debug()
    
    if not success:
        print(f"\n" + "="*60)
        print("🔤 TRYING URL ENCODING SOLUTION:")
        encoding_success = test_url_encoding()
        
        if encoding_success:
            print(f"\n🎯 SOLUTION FOUND: Use URL encoding for file paths!")
        else:
            print(f"\n⏳ Issue persists - may need more time for OAC deployment")
    
    print(f"\n📊 DEBUG COMPLETE")