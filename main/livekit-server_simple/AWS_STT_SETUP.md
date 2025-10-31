# AWS Transcribe STT Setup Guide for LiveKit Server Simple

This guide explains how to set up Amazon Transcribe as the Speech-to-Text provider in the livekit-server_simple using the official LiveKit AWS plugin.

## Prerequisites

1. **AWS Account**: You need an active AWS account with billing enabled
2. **AWS Transcribe Access**: Ensure your account has access to Amazon Transcribe service
3. **LiveKit AWS Plugin**: Install the official LiveKit AWS plugin

## Installation

### 1. Install LiveKit AWS Plugin

```bash
pip install livekit-plugins-aws
```

### 2. Install AWS SDK Dependencies

```bash
pip install boto3 botocore
```

## AWS Configuration

### 1. Create AWS IAM User

1. Go to AWS Console → IAM → Users
2. Create a new user for your application
3. Attach the following policy (or create a custom policy):

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
                "transcribe:ListTranscriptionJobs"
            ],
            "Resource": "*"
        }
    ]
}
```

4. Generate Access Key ID and Secret Access Key
5. Save these credentials securely

### 2. Configure Credentials

You can configure AWS credentials in two ways:

#### Option A: Environment Variables (.env file)

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
```

#### Option B: Config File (config.yaml)

```yaml
api_keys:
  aws:
    access_key_id: "your-aws-access-key-id"
    secret_access_key: "your-aws-secret-access-key"
```

### 3. Configure STT Provider

Update your `config.yaml` to use AWS Transcribe:

```yaml
models:
  stt:
    provider: "aws"  # Change from "groq" to "aws"
    model: "whisper-large-v3-turbo"  # This is ignored for AWS
    language: "en"  # Language code for transcription
    aws_region: "us-east-1"  # AWS region for Transcribe service
```

## Supported Languages

AWS Transcribe supports 100+ languages. Here are some common language codes:

### English Variants
- `en-US` - English (United States)
- `en-GB` - English (United Kingdom)
- `en-AU` - English (Australia)
- `en-IN` - English (India)
- `en-IE` - English (Ireland)

### Indian Languages
- `hi-IN` - Hindi (India)
- `bn-IN` - Bengali (India)
- `ta-IN` - Tamil (India)
- `te-IN` - Telugu (India)
- `gu-IN` - Gujarati (India)
- `kn-IN` - Kannada (India)
- `ml-IN` - Malayalam (India)
- `mr-IN` - Marathi (India)
- `pa-IN` - Punjabi (India)

### Other Major Languages
- `es-US` - Spanish (United States)
- `fr-FR` - French (France)
- `de-DE` - German (Germany)
- `ja-JP` - Japanese (Japan)
- `ko-KR` - Korean (South Korea)
- `zh-CN` - Chinese (Mandarin, Simplified)
- `pt-BR` - Portuguese (Brazil)
- `it-IT` - Italian (Italy)
- `ru-RU` - Russian (Russia)
- `ar-SA` - Arabic (Saudi Arabia)

## Configuration Examples

### Basic English Setup

```yaml
models:
  stt:
    provider: "aws"
    language: "en-US"
    aws_region: "us-east-1"

api_keys:
  aws:
    access_key_id: "AKIA..."
    secret_access_key: "your-secret-key"
```

### Indian English Setup (Recommended for India)

```yaml
models:
  stt:
    provider: "aws"
    language: "en-IN"  # English (India) - Optimized for Indian accents
    aws_region: "us-east-1"

api_keys:
  aws:
    access_key_id: "AKIA..."
    secret_access_key: "your-secret-key"
```

**Why en-IN is better for Indian users:**
- 🎯 Specifically trained on Indian English speech patterns
- 🗣️ Better recognition of Indian accents and pronunciation
- 📚 Understands Indian context and expressions
- ⚡ Higher accuracy for Indian speakers compared to en-US

### With Fallback to Groq

```yaml
models:
  stt:
    provider: "aws"
    language: "en-US"
    aws_region: "us-east-1"
    fallback_enabled: true  # Enable fallback to Groq if AWS fails

api_keys:
  groq: "gsk_..."  # Groq API key for fallback
  aws:
    access_key_id: "AKIA..."
    secret_access_key: "your-secret-key"
```

## AWS Regions

Choose the AWS region closest to your users for best performance:

- **US East (N. Virginia)**: `us-east-1`
- **US West (Oregon)**: `us-west-2`
- **Europe (Ireland)**: `eu-west-1`
- **Asia Pacific (Singapore)**: `ap-southeast-1`
- **Asia Pacific (Sydney)**: `ap-southeast-2`
- **Asia Pacific (Tokyo)**: `ap-northeast-1`

## Pricing

AWS Transcribe pricing (as of 2024):
- **Standard**: $0.024 per minute
- **Medical**: $0.048 per minute
- **Call Analytics**: $0.048 per minute

For real-time streaming:
- **Streaming**: $0.024 per minute

## Testing

1. Start your LiveKit server
2. Update your configuration with AWS credentials
3. Set `STT_PROVIDER=aws` in your environment or config
4. Test with a client connection

You should see logs like:
```
🎤 Creating single AWS Transcribe STT provider
🎤 AWS credentials found, creating STT with region: us-east-1
✅ AWS Transcribe STT created successfully
```

## Troubleshooting

### Common Issues

1. **"AWS plugin not available"**
   ```bash
   pip install livekit-plugins-aws
   ```

2. **"AWS credentials not found"**
   - Check your `.env` file or `config.yaml`
   - Ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set

3. **"Access denied"**
   - Verify your IAM user has Transcribe permissions
   - Check if your AWS account has Transcribe enabled

4. **"Region not supported"**
   - Use a supported AWS region (us-east-1, us-west-2, etc.)
   - Check AWS Transcribe availability in your region

### Debug Logging

Enable debug logging to see detailed AWS STT operations:

```python
import logging
logging.getLogger("provider_factory").setLevel(logging.DEBUG)
```

## Performance Comparison

| Provider | Latency | Accuracy | Languages | Cost |
|----------|---------|----------|-----------|------|
| Groq | ~200ms | High | 50+ | Free tier |
| Deepgram | ~150ms | High | 30+ | $0.0043/min |
| AWS Transcribe | ~300ms | Very High | 100+ | $0.024/min |

## Benefits of AWS Transcribe

1. **Enterprise Grade**: Highly reliable and scalable
2. **100+ Languages**: Extensive language support
3. **High Accuracy**: Excellent transcription quality
4. **Real-time Streaming**: Low-latency streaming support
5. **Custom Vocabularies**: Support for domain-specific terms
6. **Speaker Identification**: Multi-speaker recognition
7. **Compliance**: HIPAA, SOC, and other compliance certifications

## Next Steps

1. Set up your AWS credentials
2. Install the LiveKit AWS plugin
3. Update your configuration
4. Test with your application
5. Monitor usage and costs in AWS Console

For more advanced features like custom vocabularies and speaker identification, refer to the [AWS Transcribe documentation](https://docs.aws.amazon.com/transcribe/).