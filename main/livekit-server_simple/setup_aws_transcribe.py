#!/usr/bin/env python3
"""
Automated AWS Transcribe Setup Script
This script helps you set up AWS Transcribe with proper permissions
"""

import boto3
import json
import os
from botocore.exceptions import ClientError, NoCredentialsError

def create_transcribe_policy():
    """Create IAM policy for Transcribe access"""
    
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "transcribe:StartStreamTranscription",
                    "transcribe:StartTranscriptionJob",
                    "transcribe:GetTranscriptionJob",
                    "transcribe:ListTranscriptionJobs",
                    "transcribe:DeleteTranscriptionJob"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject"
                ],
                "Resource": "arn:aws:s3:::*transcribe*/*"
            }
        ]
    }
    
    return json.dumps(policy_document, indent=2)

def setup_aws_transcribe():
    """Main setup function"""
    print("🚀 AWS Transcribe Setup Assistant")
    print("=" * 50)
    
    # Check if user has AWS CLI configured
    try:
        session = boto3.Session()
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS CLI configured for account: {identity['Account']}")
        print(f"✅ Current user: {identity['Arn']}")
    except NoCredentialsError:
        print("❌ AWS CLI not configured")
        print("📝 Please configure AWS CLI first:")
        print("   1. Install AWS CLI: https://aws.amazon.com/cli/")
        print("   2. Run: aws configure")
        print("   3. Enter your Access Key, Secret Key, and region")
        return False
    except Exception as e:
        print(f"❌ AWS CLI error: {e}")
        return False
    
    print("\n🔧 Setup Options:")
    print("1. 📋 Show IAM policy (copy-paste to AWS Console)")
    print("2. 🧪 Test current permissions")
    print("3. 🌍 Check service availability in regions")
    print("4. 📖 Show manual setup instructions")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        print("\n📋 IAM Policy for AWS Transcribe:")
        print("=" * 40)
        print("Copy this policy and paste it in AWS Console:")
        print("(IAM → Policies → Create Policy → JSON)")
        print()
        print(create_transcribe_policy())
        print()
        print("💡 Policy name suggestion: 'TranscribeSTTPolicy'")
        
    elif choice == "2":
        test_permissions()
        
    elif choice == "3":
        check_regions()
        
    elif choice == "4":
        show_manual_instructions()
        
    else:
        print("❌ Invalid choice")
        return False
    
    return True

def test_permissions():
    """Test current AWS permissions"""
    print("\n🧪 Testing AWS Permissions:")
    print("=" * 30)
    
    try:
        session = boto3.Session()
        
        # Test STS (basic AWS access)
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ Basic AWS access: OK")
        
        # Test Transcribe access
        regions_to_test = ['us-east-1', 'ap-south-1', 'us-west-2']
        
        for region in regions_to_test:
            try:
                transcribe = session.client('transcribe', region_name=region)
                response = transcribe.list_transcription_jobs(MaxResults=1)
                print(f"✅ Transcribe access in {region}: OK")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'SubscriptionRequiredException':
                    print(f"⚠️ Transcribe in {region}: Service not enabled")
                elif error_code == 'AccessDenied':
                    print(f"❌ Transcribe in {region}: Access denied")
                else:
                    print(f"❌ Transcribe in {region}: {error_code}")
            except Exception as e:
                print(f"❌ Transcribe in {region}: {e}")
                
    except Exception as e:
        print(f"❌ Permission test failed: {e}")

def check_regions():
    """Check Transcribe availability in different regions"""
    print("\n🌍 Amazon Transcribe Regional Availability:")
    print("=" * 45)
    
    regions = [
        ('us-east-1', 'US East (N. Virginia)', '🇺🇸'),
        ('us-west-2', 'US West (Oregon)', '🇺🇸'),
        ('ap-south-1', 'Asia Pacific (Mumbai)', '🇮🇳'),
        ('ap-southeast-1', 'Asia Pacific (Singapore)', '🇸🇬'),
        ('eu-west-1', 'Europe (Ireland)', '🇪🇺'),
        ('ap-northeast-1', 'Asia Pacific (Tokyo)', '🇯🇵'),
    ]
    
    session = boto3.Session()
    
    for region_code, region_name, flag in regions:
        try:
            transcribe = session.client('transcribe', region_name=region_code)
            response = transcribe.list_transcription_jobs(MaxResults=1)
            print(f"✅ {flag} {region_name} ({region_code}): Available")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'SubscriptionRequiredException':
                print(f"⚠️ {flag} {region_name} ({region_code}): Available (needs enabling)")
            else:
                print(f"❌ {flag} {region_name} ({region_code}): {error_code}")
        except Exception as e:
            print(f"❌ {flag} {region_name} ({region_code}): Not available")
    
    print(f"\n💡 Recommended for India: ap-south-1 (Mumbai)")
    print(f"💡 Most reliable: us-east-1 (N. Virginia)")

def show_manual_instructions():
    """Show manual setup instructions"""
    print("\n📖 Manual Setup Instructions:")
    print("=" * 35)
    print()
    print("🔧 Step 1: Enable Amazon Transcribe")
    print("   1. Go to: https://console.aws.amazon.com/transcribe/")
    print("   2. Select region: us-east-1")
    print("   3. Click 'Get Started' to enable service")
    print()
    print("👤 Step 2: Create IAM User")
    print("   1. Go to: https://console.aws.amazon.com/iam/")
    print("   2. Users → Create user")
    print("   3. Username: transcribe-user")
    print("   4. Attach policy: AmazonTranscribeFullAccess")
    print("   5. Create access key for CLI")
    print()
    print("📝 Step 3: Update .env file")
    print("   AWS_ACCESS_KEY_ID=your-access-key")
    print("   AWS_SECRET_ACCESS_KEY=your-secret-key")
    print("   AWS_DEFAULT_REGION=us-east-1")
    print()
    print("🧪 Step 4: Test setup")
    print("   python test_aws_credentials.py")

if __name__ == "__main__":
    try:
        setup_aws_transcribe()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("💡 Try the manual setup instructions instead")