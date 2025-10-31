# 🚀 Complete AWS Transcribe Setup Guide

This guide will walk you through setting up Amazon Transcribe from scratch, including policies, permissions, and service activation.

## 📋 **Prerequisites**
- AWS Account (free tier is fine)
- Admin access to AWS Console
- Credit card on file (for verification, free tier covers most usage)

---

## 🔧 **Step 1: Enable Amazon Transcribe Service**

### 1.1 Go to Amazon Transcribe Console
1. **Open AWS Console**: https://console.aws.amazon.com/
2. **Sign in** to your AWS account
3. **Search for "Transcribe"** in the services search box
4. **Click "Amazon Transcribe"**

### 1.2 Enable the Service
1. **Select Region**: Choose `us-east-1` (N. Virginia) from the top-right dropdown
2. **You'll see a welcome page** - Click **"Get Started"**
3. **Accept Terms**: Read and accept the service terms
4. **Service is now enabled!** ✅

---

## 👤 **Step 2: Create IAM User with Proper Permissions**

### 2.1 Go to IAM Console
1. **Search for "IAM"** in AWS Console
2. **Click "IAM"** (Identity and Access Management)

### 2.2 Create New User
1. **Click "Users"** in left sidebar
2. **Click "Create user"**
3. **User name**: `transcribe-user` (or any name you prefer)
4. **Click "Next"**

### 2.3 Set Permissions
1. **Select "Attach policies directly"**
2. **Search for and select these policies**:
   - ✅ `AmazonTranscribeFullAccess`
   - ✅ `AmazonS3ReadOnlyAccess` (needed for some Transcribe features)
3. **Click "Next"**
4. **Click "Create user"**

### 2.4 Create Access Keys
1. **Click on your new user** (`transcribe-user`)
2. **Go to "Security credentials" tab**
3. **Click "Create access key"**
4. **Select "Command Line Interface (CLI)"**
5. **Check the confirmation box**
6. **Click "Next"**
7. **Add description**: "LiveKit Transcribe STT"
8. **Click "Create access key"**
9. **📝 IMPORTANT: Copy both values immediately!**
   - **Access Key ID**: `AKIA...`
   - **Secret Access Key**: `...` (you can only see this once!)

---

## 🔐 **Step 3: Create Custom IAM Policy (More Secure)**

If you want more granular control, create a custom policy:

### 3.1 Create Custom Policy
1. **In IAM Console**, click **"Policies"** in left sidebar
2. **Click "Create policy"**
3. **Click "JSON" tab**
4. **Paste this policy**:

```json
{
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
```

5. **Click "Next"**
6. **Policy name**: `TranscribeSTTPolicy`
7. **Description**: "Policy for LiveKit Transcribe STT"
8. **Click "Create policy"**

### 3.2 Attach Custom Policy to User
1. **Go back to Users** → **Select your user**
2. **Click "Add permissions"** → **"Attach policies directly"**
3. **Search for `TranscribeSTTPolicy`**
4. **Select it and click "Next"**
5. **Click "Add permissions"**

---

## 🌍 **Step 4: Test Different Regions**

Amazon Transcribe availability by region:

| Region | Code | Transcribe Available | Recommended For |
|--------|------|---------------------|-----------------|
| 🇺🇸 US East (N. Virginia) | `us-east-1` | ✅ Yes | **Best for testing** |
| 🇺🇸 US West (Oregon) | `us-west-2` | ✅ Yes | US West Coast |
| 🇮🇳 Asia Pacific (Mumbai) | `ap-south-1` | ✅ Yes | **Best for India** |
| 🇸🇬 Asia Pacific (Singapore) | `ap-southeast-1` | ✅ Yes | Southeast Asia |
| 🇪🇺 Europe (Ireland) | `eu-west-1` | ✅ Yes | Europe |

---

## 📝 **Step 5: Update Your Configuration**

### 5.1 Update .env file
```bash
# AWS Credentials (from Step 2.4)
AWS_ACCESS_KEY_ID=AKIA... # Your actual Access Key ID
AWS_SECRET_ACCESS_KEY=... # Your actual Secret Access Key
AWS_DEFAULT_REGION=us-east-1

# STT Configuration
STT_PROVIDER=aws
STT_LANGUAGE=en-IN
AWS_STT_REGION=us-east-1
```

### 5.2 Update config.yaml
```yaml
models:
  stt:
    provider: "aws"
    language: "en-IN"
    aws_region: "us-east-1"
```

---

## 🧪 **Step 6: Test Your Setup**

### 6.1 Test AWS Credentials
```bash
python test_aws_credentials.py
```

**Expected output:**
```
✅ AWS credentials are VALID!
✅ AWS Transcribe service is accessible!
```

### 6.2 Test AWS STT Integration
```bash
python test_aws_stt.py
```

### 6.3 Test Indian English Configuration
```bash
python test_indian_english.py
```

---

## 💰 **Step 7: Understanding Costs**

### Free Tier (First 12 months)
- **60 minutes per month** of transcription for FREE
- Perfect for development and testing

### Pay-as-you-go Pricing
- **Standard**: $0.024 per minute (~₹2 per minute)
- **Medical**: $0.048 per minute
- **Call Analytics**: $0.048 per minute

### Cost Examples
- **1 hour of transcription**: $1.44 (~₹120)
- **10 hours per month**: $14.40 (~₹1,200)
- **Daily 30-minute sessions**: ~$21.60/month (~₹1,800)

---

## 🔧 **Troubleshooting**

### Error: "SubscriptionRequiredException"
- **Solution**: Enable Amazon Transcribe service (Step 1)

### Error: "InvalidClientTokenId"
- **Solution**: Check your Access Key ID in .env file

### Error: "SignatureDoesNotMatch"
- **Solution**: Check your Secret Access Key in .env file

### Error: "AccessDenied"
- **Solution**: Add proper IAM permissions (Step 2 or 3)

### Error: "Service not available in region"
- **Solution**: Switch to `us-east-1` region

---

## 🎯 **Quick Setup Checklist**

- [ ] Enable Amazon Transcribe service
- [ ] Create IAM user with Transcribe permissions
- [ ] Generate Access Keys
- [ ] Update .env file with real credentials
- [ ] Test credentials with `python test_aws_credentials.py`
- [ ] Test STT with `python test_aws_stt.py`
- [ ] Start your LiveKit agent!

---

## 🚀 **Final Step: Start Your Agent**

Once everything is working:

```bash
python simple_main.py
```

You should see:
```
🎤 Creating custom AWS Transcribe STT provider
🎤 AWS credentials found, creating custom STT with region: us-east-1
✅ Custom AWS Transcribe STT created successfully
```

**Congratulations! You now have enterprise-grade AWS Transcribe STT with Indian English support!** 🎉

---

## 📞 **Need Help?**

If you encounter any issues:
1. Check the troubleshooting section above
2. Run the test scripts to identify the specific problem
3. Verify your AWS Console settings match this guide

**Your AWS STT will provide much better accuracy for Indian English compared to other providers!** 🇮🇳