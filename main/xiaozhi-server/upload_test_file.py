"""
Upload Test File to S3
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def upload_test_file():
    # AWS credentials from environment
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_DEFAULT_REGION")
    bucket_name = os.getenv("S3_BUCKET_NAME")
    
    print(f"Bucket: {bucket_name}")
    print(f"Region: {aws_region}")
    
    # Create S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region
    )
    
    # Create a simple test audio file (just text content for testing)
    test_content = b"This is a test audio file content for CDN testing"
    
    try:
        # Upload test file
        s3_client.put_object(
            Bucket=bucket_name,
            Key='test.mp3',
            Body=test_content,
            ContentType='audio/mpeg',
            CacheControl='public, max-age=86400'
        )
        print("✅ Uploaded test.mp3")
        
        # Upload another test file in uploads folder
        s3_client.put_object(
            Bucket=bucket_name,
            Key='uploads/sample.mp3',
            Body=test_content,
            ContentType='audio/mpeg',
            CacheControl='public, max-age=86400'
        )
        print("✅ Uploaded uploads/sample.mp3")
        
        # List files to confirm
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        print("\nFiles in bucket:")
        if 'Contents' in response:
            for obj in response['Contents']:
                print(f"  - {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("  No files found")
            
    except Exception as e:
        print(f"❌ Error uploading: {e}")

if __name__ == "__main__":
    upload_test_file()