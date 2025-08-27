import requests

# Test direct S3 access
s3_url = 'https://cheeko-audio-files.s3.us-east-1.amazonaws.com/stories/Fantasy/mary had a little lamb.mp3'
cloudfront_url = 'https://dbtnllz9fcr1z.cloudfront.net/stories/Fantasy/mary had a little lamb.mp3'

print('Testing Direct S3 Access:')
print(f'S3 URL: {s3_url}')

try:
    response = requests.head(s3_url, timeout=10)
    print(f'S3 Status: {response.status_code}')
    
    if response.status_code == 200:
        print('✅ S3 Direct access works!')
    else:
        print(f'❌ S3 Status: {response.status_code}')
        
except Exception as e:
    print(f'❌ S3 Error: {e}')

print('\nTesting CloudFront Access:')
print(f'CloudFront URL: {cloudfront_url}')

try:
    response = requests.head(cloudfront_url, timeout=10)
    print(f'CloudFront Status: {response.status_code}')
    
    if response.status_code == 200:
        print('✅ CloudFront access works!')
    else:
        print(f'❌ CloudFront Status: {response.status_code}')
        
except Exception as e:
    print(f'❌ CloudFront Error: {e}')

print('\n' + '='*50)
print('DIAGNOSIS:')
if response.status_code == 403:
    print('403 Forbidden usually means:')
    print('1. ❌ Origin Access Control (OAC) not configured properly')
    print('2. ❌ S3 bucket policy missing or incorrect')
    print('3. ❌ CloudFront distribution not fully deployed')
    print('\nSOLUTION: Configure OAC and update S3 bucket policy')