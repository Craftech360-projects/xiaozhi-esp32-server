"""
Check S3 Files
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def check_s3_files():
    # AWS credentials from environment
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_DEFAULT_REGION")
    bucket_name = os.getenv("S3_BUCKET_NAME")
    
    print(f"Checking bucket: {bucket_name}")
    
    # Create S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region
    )
    
    try:
        # List all files
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' in response:
            print(f"\nFound {len(response['Contents'])} files:")
            for obj in response['Contents']:
                print(f"  📁 {obj['Key']}")
                print(f"     Size: {obj['Size']} bytes")
                print(f"     Modified: {obj['LastModified']}")
                print()
        else:
            print("❌ No files found in bucket")
            
    except Exception as e:
        print(f"❌ Error checking bucket: {e}")

if __name__ == "__main__":
    check_s3_files()