# ⚡ Quick AWS Transcribe Setup (5 Minutes)

Follow these exact steps to get AWS Transcribe working:

## 🎯 **Step 1: Enable Amazon Transcribe (2 minutes)**

1. **Open this link**: https://console.aws.amazon.com/transcribe/
2. **Sign in** to your AWS account
3. **Select region**: Choose `us-east-1` from top-right dropdown
4. **Click "Get Started"** (you'll see a welcome page)
5. **Accept terms** and click through
6. ✅ **Service is now enabled!**

## 👤 **Step 2: Create User with Permissions (2 minutes)**

1. **Open this link**: https://console.aws.amazon.com/iam/home#/users
2. **Click "Create user"**
3. **Username**: `transcribe-user`
4. **Click "Next"**
5. **Select "Attach policies directly"**
6. **Search for**: `AmazonTranscribeFullAccess`
7. **Check the box** next to it
8. **Click "Next"** → **"Create user"**

## 🔑 **Step 3: Get Access Keys (1 minute)**

1. **Click on your new user** (`transcribe-user`)
2. **Click "Security credentials" tab**
3. **Click "Create access key"**
4. **Select "Command Line Interface (CLI)"**
5. **Check confirmation box** → **"Next"**
6. **Click "Create access key"**
7. **📝 COPY THESE VALUES IMMEDIATELY:**
   - **Access Key ID**: `AKIA...`
   - **Secret Access Key**: `...`

## 📝 **Step 4: Update Your .env File**

Replace these lines in your `.env` file:

```bash
# Replace with your actual values from Step 3
AWS_ACCESS_KEY_ID=AKIA... # Your actual Access Key ID
AWS_SECRET_ACCESS_KEY=... # Your actual Secret Access Key
```

## 🧪 **Step 5: Test It Works**

Run this command:

```bash
python test_aws_credentials.py
```

**Expected output:**
```
✅ AWS credentials are VALID!
✅ AWS Transcribe service is accessible!
🎉 AWS credentials are working perfectly!
```

## 🚀 **Step 6: Start Your Agent**

```bash
python simple_main.py
```

**You should see:**
```
🎤 Creating custom AWS Transcribe STT provider
✅ Custom AWS Transcribe STT created successfully
```

---

## 🆘 **If You Get Errors:**

### Error: "SubscriptionRequiredException"
- **Fix**: Go back to Step 1 and enable the service

### Error: "InvalidClientTokenId" 
- **Fix**: Check your Access Key ID in .env file

### Error: "AccessDenied"
- **Fix**: Make sure you attached `AmazonTranscribeFullAccess` policy

---

## 💰 **Don't Worry About Costs**

- **Free Tier**: 60 minutes per month for FREE
- **After free tier**: Only $0.024 per minute (~₹2/minute)
- **You only pay for what you use**

---

**That's it! Your AWS Transcribe STT with Indian English support is ready!** 🇮🇳✨