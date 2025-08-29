"""
Detailed 403 error diagnostic for S3 presigned URLs
"""

import os
import boto3
import requests
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

def debug_403_detailed():
    """Detailed debugging for 403 errors"""
    
    print("🔍 Detailed 403 Error Analysis")
    print("=" * 50)
    
    # Initialize S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    
    bucket_name = 'cheeko-audio-files'
    test_key = 'music/English/Baa Baa Black Sheep.mp3'
    
    print(f"Testing file: {test_key}")
    print(f"Bucket: {bucket_name}")
    
    # Step 1: Check if file exists
    print("\n1️⃣ Checking if file exists...")
    try:
        response = s3_client.head_object(Bucket=bucket_name, Key=test_key)
        print("✅ File exists in S3")
        print(f"   Size: {response.get('ContentLength', 'Unknown')} bytes")
        print(f"   Last Modified: {response.get('LastModified', 'Unknown')}")
        print(f"   Content-Type: {response.get('ContentType', 'Unknown')}")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print("❌ File does not exist in S3!")
            print("   Check if the file path is correct")
            return False
        else:
            print(f"❌ Error checking file: {error_code} - {e.response['Error']['Message']}")
            return False
    
    # Step 2: Test direct GetObject
    print("\n2️⃣ Testing direct GetObject...")
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=test_key, Range='bytes=0-1023')
        print("✅ Direct GetObject works!")
        print(f"   Downloaded {len(response['Body'].read())} bytes")
    except ClientError as e:
        print(f"❌ Direct GetObject failed: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        print("   This indicates a permissions issue")
    
    # Step 3: Test different presigned URL configurations
    print("\n3️⃣ Testing different presigned URL configurations...")
    
    # Test 1: Standard presigned URL
    try:
        url1 = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': test_key},
            ExpiresIn=3600
        )
        print("✅ Standard presigned URL generated")
        
        response = requests.head(url1, timeout=10)
        print(f"   HTTP Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response headers: {dict(response.headers)}")
            
    except Exception as e:
        print(f"❌ Standard presigned URL failed: {e}")
    
    # Test 2: Presigned URL with different method
    try:
        url2 = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': test_key},
            ExpiresIn=7200,
            HttpMethod='GET'
        )
        print("✅ Explicit GET method presigned URL generated")
        
        response = requests.head(url2, timeout=10)
        print(f"   HTTP Status: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Explicit GET method failed: {e}")
    
    # Step 4: Check bucket policy vs IAM policy conflict
    print("\n4️⃣ Checking for policy conflicts...")
    
    # Check current user identity
    try:
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        )
        identity = sts_client.get_caller_identity()
        print(f"✅ Current user ARN: {identity.get('Arn')}")
        print(f"   Account ID: {identity.get('Account')}")
        print(f"   User ID: {identity.get('UserId')}")
        
    except Exception as e:
        print(f"❌ Could not get caller identity: {e}")
    
    # Step 5: Test with different file
    print("\n5️⃣ Testing with different file...")
    
    # List files in the music/English folder
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='music/English/',
            MaxKeys=5
        )
        
        if 'Contents' in response:
            print("✅ Files found in music/English/:")
            for obj in response['Contents']:
                print(f"   - {obj['Key']} ({obj['Size']} bytes)")
                
                # Test the first file
                if obj['Key'] != test_key:
                    test_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': bucket_name, 'Key': obj['Key']},
                        ExpiresIn=3600
                    )
                    
                    test_response = requests.head(test_url, timeout=5)
                    print(f"   Test URL for {obj['Key']}: HTTP {test_response.status_code}")
                    break
        else:
            print("❌ No files found in music/English/ folder")
            
    except Exception as e:
        print(f"❌ Error listing files: {e}")
    
    # Step 6: Recommendations
    print("\n6️⃣ Recommendations:")
    print("-" * 30)
    
    print("1. Verify the exact file path in S3 matches your metadata.json")
    print("2. Check if there are any bucket-level restrictions")
    print("3. Ensure the IAM policy and bucket policy don't conflict")
    print("4. Try waiting 5-10 minutes for policy propagation")
    print("5. Consider using a different test file to isolate the issue")

if __name__ == "__main__":
    debug_403_detailed()