"""
Test AWS credentials and S3 bucket access
"""

import os
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError

load_dotenv()

def test_aws_credentials():
    """Test AWS credentials and S3 access"""
    
    print("🔐 Testing AWS Credentials...")
    
    # Check environment variables
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    bucket_name = os.getenv('S3_BUCKET_NAME', 'cheeko-audio-files')
    
    if not access_key:
        print("❌ AWS_ACCESS_KEY_ID not found in environment")
        return False
    
    if not secret_key:
        print("❌ AWS_SECRET_ACCESS_KEY not found in environment")
        return False
    
    print(f"✅ Access Key: {access_key[:10]}...")
    print(f"✅ Region: {region}")
    print(f"✅ Bucket: {bucket_name}")
    
    # Test S3 client creation
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        print("✅ S3 client created successfully")
    except Exception as e:
        print(f"❌ Failed to create S3 client: {e}")
        return False
    
    # Test credentials by listing buckets
    print("\n🪣 Testing bucket access...")
    try:
        response = s3_client.list_buckets()
        print("✅ Successfully authenticated with AWS")
        
        bucket_names = [bucket['Name'] for bucket in response['Buckets']]
        print(f"Available buckets: {bucket_names}")
        
        if bucket_name in bucket_names:
            print(f"✅ Target bucket '{bucket_name}' found")
        else:
            print(f"❌ Target bucket '{bucket_name}' not found")
            print("Available buckets:", bucket_names)
            return False
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"❌ AWS Error ({error_code}): {e.response['Error']['Message']}")
        return False
    except NoCredentialsError:
        print("❌ No valid AWS credentials found")
        return False
    
    # Test bucket contents
    print(f"\n📁 Testing bucket contents...")
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='music/',
            MaxKeys=10
        )
        
        if 'Contents' in response:
            print(f"✅ Found {len(response['Contents'])} objects in music/ folder")
            for obj in response['Contents'][:5]:
                print(f"  - {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("❌ No objects found in music/ folder")
            
    except ClientError as e:
        print(f"❌ Error listing bucket contents: {e}")
        return False
    
    # Test specific file access
    print(f"\n🎵 Testing specific file access...")
    test_key = "music/English/Baa Baa Black Sheep.mp3"
    
    try:
        # Check if object exists
        s3_client.head_object(Bucket=bucket_name, Key=test_key)
        print(f"✅ File exists: {test_key}")
        
        # Generate presigned URL
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': test_key},
            ExpiresIn=3600
        )
        print(f"✅ Generated presigned URL successfully")
        print(f"URL: {url[:100]}...")
        
        # Test the presigned URL
        import requests
        response = requests.head(url, timeout=10)
        print(f"✅ Presigned URL test: HTTP {response.status_code}")
        
        if response.status_code == 200:
            print("🎉 S3 access is working correctly!")
            return True
        else:
            print(f"❌ Presigned URL returned {response.status_code}")
            return False
            
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"❌ File not found: {test_key}")
        else:
            print(f"❌ Error accessing file: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def suggest_fixes():
    """Suggest fixes for common S3 issues"""
    print("\n🔧 Troubleshooting Suggestions:")
    print("=" * 50)
    
    print("1. 🔐 SECURITY ISSUE:")
    print("   - The AWS credentials you shared are COMPROMISED")
    print("   - Go to AWS IAM Console immediately")
    print("   - Delete/revoke the current access keys")
    print("   - Create new access keys")
    print("   - Update your .env file with new credentials")
    
    print("\n2. 📁 Bucket Permissions:")
    print("   - Ensure your IAM user has S3 permissions:")
    print("     * s3:GetObject")
    print("     * s3:ListBucket")
    print("   - Check bucket policy allows your IAM user")
    
    print("\n3. 🌍 Bucket Region:")
    print("   - Verify bucket is in the correct region (us-east-1)")
    print("   - Update AWS_DEFAULT_REGION if needed")
    
    print("\n4. 📂 File Structure:")
    print("   - Ensure files are uploaded to correct paths:")
    print("     * music/English/Baa Baa Black Sheep.mp3")
    print("     * stories/Fantasy/a portrait of a cat.mp3")

if __name__ == "__main__":
    print("🧪 AWS S3 Credentials Test")
    print("=" * 50)
    
    success = test_aws_credentials()
    
    if not success:
        suggest_fixes()
    else:
        print("\n🎉 All tests passed! S3 streaming should work now.")