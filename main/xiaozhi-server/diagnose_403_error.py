"""
Advanced diagnostic for 403 errors with full S3 permissions
"""

import os
import boto3
import requests
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import urllib.parse

load_dotenv()

def test_direct_s3_access():
    """Test direct S3 access with different methods"""
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    
    bucket_name = 'cheeko-audio-files'
    test_key = 'music/English/Baa Baa Black Sheep.mp3'
    
    print("🔍 Advanced 403 Error Diagnosis")
    print("=" * 50)
    
    # Test 1: Direct boto3 GetObject
    print("\n1️⃣ Testing direct boto3 GetObject...")
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=test_key, Range='bytes=0-1023')
        print("✅ Direct boto3 GetObject works!")
        print(f"   Content-Type: {response.get('ContentType', 'Unknown')}")
        print(f"   Content-Length: {response.get('ContentLength', 'Unknown')}")
    except ClientError as e:
        print(f"❌ Direct boto3 GetObject failed: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        return False
    
    # Test 2: Presigned URL generation
    print("\n2️⃣ Testing presigned URL generation...")
    try:
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': test_key},
            ExpiresIn=3600
        )
        print("✅ Presigned URL generated successfully")
        print(f"   URL length: {len(presigned_url)} characters")
    except Exception as e:
        print(f"❌ Presigned URL generation failed: {e}")
        return False
    
    # Test 3: Test presigned URL with requests
    print("\n3️⃣ Testing presigned URL with requests...")
    try:
        response = requests.get(presigned_url, stream=True, timeout=10)
        print(f"   HTTP Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Presigned URL works with requests!")
            # Try to read some content
            content = response.content[:100]
            print(f"   Downloaded {len(content)} bytes successfully")
        else:
            print(f"❌ Presigned URL returned {response.status_code}")
            print(f"   Response text: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Requests failed: {e}")
    
    # Test 4: Test different URL formats
    print("\n4️⃣ Testing different URL formats...")
    
    # Public URL (URL encoded)
    encoded_key = urllib.parse.quote(test_key)
    public_url = f"https://{bucket_name}.s3.amazonaws.com/{encoded_key}"
    print(f"   Public URL: {public_url}")
    
    try:
        response = requests.head(public_url, timeout=5)
        print(f"   Public URL status: {response.status_code}")
    except Exception as e:
        print(f"   Public URL failed: {e}")
    
    # Test 5: Check bucket region and endpoint
    print("\n5️⃣ Testing bucket region and endpoint...")
    try:
        bucket_location = s3_client.get_bucket_location(Bucket=bucket_name)
        region = bucket_location.get('LocationConstraint') or 'us-east-1'
        print(f"   Bucket region: {region}")
        
        if region != os.getenv('AWS_DEFAULT_REGION', 'us-east-1'):
            print(f"   ⚠️  Region mismatch! Bucket is in {region}, client uses {os.getenv('AWS_DEFAULT_REGION', 'us-east-1')}")
            
            # Try with correct region
            print("   🔄 Retrying with correct region...")
            regional_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=region
            )
            
            regional_url = regional_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': test_key},
                ExpiresIn=3600
            )
            
            response = requests.head(regional_url, timeout=5)
            print(f"   Regional URL status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Region was the issue! Update AWS_DEFAULT_REGION in .env")
                return True
                
    except Exception as e:
        print(f"   Region check failed: {e}")
    
    # Test 6: Check for bucket encryption/policies
    print("\n6️⃣ Checking bucket configuration...")
    try:
        # Check bucket policy
        try:
            policy = s3_client.get_bucket_policy(Bucket=bucket_name)
            print("   ℹ️  Bucket has a policy (might be blocking access)")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                print("   ✅ No bucket policy (good)")
            else:
                print(f"   ⚠️  Policy check failed: {e.response['Error']['Code']}")
        
        # Check bucket ACL
        try:
            acl = s3_client.get_bucket_acl(Bucket=bucket_name)
            print(f"   ℹ️  Bucket owner: {acl['Owner']['DisplayName']}")
        except Exception as e:
            print(f"   ⚠️  ACL check failed: {e}")
            
    except Exception as e:
        print(f"   Configuration check failed: {e}")
    
    return False

def test_pydub_compatibility():
    """Test if the issue is with pydub URL handling"""
    print("\n🎵 Testing pydub compatibility...")
    
    # Test with a simple HTTP URL first
    test_urls = [
        "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",  # Simple test URL
        "https://cheeko-audio-files.s3.amazonaws.com/music/English/Baa%20Baa%20Black%20Sheep.mp3"  # Your file
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n   Test {i}: {url[:60]}...")
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(url)
            print(f"   ✅ pydub loaded audio: {len(audio)}ms duration")
        except Exception as e:
            print(f"   ❌ pydub failed: {e}")

if __name__ == "__main__":
    success = test_direct_s3_access()
    
    if not success:
        test_pydub_compatibility()
        
        print("\n🔧 Possible Solutions:")
        print("=" * 30)
        print("1. Check if bucket region matches AWS_DEFAULT_REGION in .env")
        print("2. Verify no bucket policy is blocking access")
        print("3. Try using temporary file download method (already implemented)")
        print("4. Check if bucket has public read access blocked")
        print("5. Verify the exact filename in S3 matches metadata.json")