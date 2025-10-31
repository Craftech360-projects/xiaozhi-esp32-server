#!/usr/bin/env python3
"""
Quick test script to verify AWS credentials
"""

import os
import boto3
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError, ClientError

# Load environment variables
load_dotenv(".env")

def test_aws_credentials():
    """Test AWS credentials"""
    print("🔑 Testing AWS Credentials")
    print("=" * 30)
    
    # Get credentials from environment
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    print(f"Access Key ID: {aws_access_key_id[:8]}..." if aws_access_key_id else "❌ Not found")
    print(f"Secret Key: {'*' * len(aws_secret_access_key)}" if aws_secret_access_key else "❌ Not found")
    print(f"Region: {aws_region}")
    
    if not aws_access_key_id or not aws_secret_access_key:
        print("\n❌ AWS credentials not found in .env file")
        print("💡 Please update your .env file with valid AWS credentials")
        return False
    
    try:
        # Create session
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        
        # Test credentials with STS
        sts_client = session.client('sts')
        identity = sts_client.get_caller_identity()
        
        print(f"\n✅ AWS credentials are VALID!")
        print(f"Account ID: {identity.get('Account')}")
        print(f"User ARN: {identity.get('Arn')}")
        
        # Test Transcribe access
        transcribe_client = session.client('transcribe')
        response = transcribe_client.list_transcription_jobs(MaxResults=1)
        print(f"✅ AWS Transcribe service is accessible!")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidClientTokenId':
            print(f"\n❌ Invalid AWS Access Key ID")
            print("💡 Please check your AWS_ACCESS_KEY_ID in .env file")
        elif error_code == 'SignatureDoesNotMatch':
            print(f"\n❌ Invalid AWS Secret Access Key")
            print("💡 Please check your AWS_SECRET_ACCESS_KEY in .env file")
        elif error_code == 'AccessDenied':
            print(f"\n❌ Access denied to AWS services")
            print("💡 Please check IAM permissions for your AWS user")
        else:
            print(f"\n❌ AWS Error: {e}")
        return False
        
    except NoCredentialsError:
        print(f"\n❌ No AWS credentials found")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_aws_credentials()
    
    if success:
        print(f"\n🎉 AWS credentials are working perfectly!")
        print(f"🚀 You can now use AWS Transcribe STT!")
    else:
        print(f"\n🔧 Please fix the AWS credentials and try again.")
        print(f"\n📝 Steps to fix:")
        print(f"1. Go to AWS Console → IAM → Users")
        print(f"2. Select your user → Security credentials")
        print(f"3. Create new access key")
        print(f"4. Update .env file with new credentials")