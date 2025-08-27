"""
Script to help fix S3 permissions for audio streaming
"""

import json

def generate_iam_policy():
    """Generate the required IAM policy for S3 audio streaming"""
    
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "CheekoAudioStreamingPolicy",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::cheeko-audio-files",
                    "arn:aws:s3:::cheeko-audio-files/*"
                ]
            }
        ]
    }
    
    return json.dumps(policy, indent=2)

def generate_bucket_policy():
    """Generate bucket policy to allow access"""
    
    # You'll need to replace YOUR_IAM_USER_ARN with your actual IAM user ARN
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowCheekoAudioAccess",
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:user/YOUR_IAM_USERNAME"
                },
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::cheeko-audio-files",
                    "arn:aws:s3:::cheeko-audio-files/*"
                ]
            }
        ]
    }
    
    return json.dumps(bucket_policy, indent=2)

def print_instructions():
    """Print step-by-step instructions to fix permissions"""
    
    print("🔧 S3 Permissions Fix Guide")
    print("=" * 60)
    
    print("\n📋 OPTION 1: Fix IAM User Permissions (Recommended)")
    print("-" * 50)
    print("1. Go to AWS IAM Console: https://console.aws.amazon.com/iam/")
    print("2. Click 'Users' in the left sidebar")
    print("3. Find and click on your IAM user")
    print("4. Click 'Add permissions' → 'Attach policies directly'")
    print("5. Click 'Create policy'")
    print("6. Click 'JSON' tab and paste this policy:")
    print()
    print(generate_iam_policy())
    print()
    print("7. Click 'Next' → 'Next' → Name it 'CheekoAudioStreamingPolicy'")
    print("8. Click 'Create policy'")
    print("9. Go back and attach this policy to your user")
    
    print("\n📋 OPTION 2: Fix Bucket Policy (Alternative)")
    print("-" * 50)
    print("1. Go to S3 Console: https://console.aws.amazon.com/s3/")
    print("2. Click on 'cheeko-audio-files' bucket")
    print("3. Go to 'Permissions' tab")
    print("4. Scroll down to 'Bucket policy'")
    print("5. Click 'Edit' and paste this policy:")
    print("   (Replace YOUR_ACCOUNT_ID and YOUR_IAM_USERNAME)")
    print()
    print(generate_bucket_policy())
    
    print("\n🚨 SECURITY REMINDER:")
    print("-" * 50)
    print("❌ Your AWS credentials are COMPROMISED (shared publicly)")
    print("✅ Create NEW access keys after fixing permissions")
    print("✅ Delete the old compromised keys")
    print("✅ Update your .env file with new credentials")
    
    print("\n🧪 After fixing permissions, test with:")
    print("-" * 50)
    print("python test_aws_credentials.py")
    print("python test_s3_audio.py")

def test_current_permissions():
    """Test what permissions the current user has"""
    import boto3
    import os
    from dotenv import load_dotenv
    from botocore.exceptions import ClientError
    
    load_dotenv()
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    
    bucket_name = 'cheeko-audio-files'
    test_key = 'music/English/Baa Baa Black Sheep.mp3'
    
    print("\n🔍 Testing Current Permissions:")
    print("-" * 40)
    
    # Test ListBucket
    try:
        s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        print("✅ s3:ListBucket - ALLOWED")
    except ClientError as e:
        print(f"❌ s3:ListBucket - DENIED ({e.response['Error']['Code']})")
    
    # Test GetObject
    try:
        s3_client.head_object(Bucket=bucket_name, Key=test_key)
        print("✅ s3:HeadObject - ALLOWED")
    except ClientError as e:
        print(f"❌ s3:HeadObject - DENIED ({e.response['Error']['Code']})")
    
    # Test actual GetObject
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=test_key, Range='bytes=0-1023')
        print("✅ s3:GetObject - ALLOWED")
    except ClientError as e:
        print(f"❌ s3:GetObject - DENIED ({e.response['Error']['Code']})")
        if e.response['Error']['Code'] == 'AccessDenied':
            print("   → This is the main issue! Need s3:GetObject permission")

if __name__ == "__main__":
    test_current_permissions()
    print_instructions()