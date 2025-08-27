import requests

# Test with an existing file
cloudfront_url = 'https://dbtnllz9fcr1z.cloudfront.net/stories/Fantasy/mary had a little lamb.mp3'
print('Testing CloudFront with existing file:')
print(f'URL: {cloudfront_url}')

try:
    response = requests.head(cloudfront_url, timeout=10)
    print(f'Status: {response.status_code}')
    
    if response.status_code == 200:
        print('✅ SUCCESS! CloudFront is working!')
        print(f'Content-Type: {response.headers.get("content-type", "Unknown")}')
        print(f'Content-Length: {response.headers.get("content-length", "Unknown")}')
        print(f'Cache Status: {response.headers.get("x-cache", "Unknown")}')
        print(f'Age: {response.headers.get("age", "Unknown")}')
    else:
        print(f'❌ Status: {response.status_code}')
        
except Exception as e:
    print(f'❌ Error: {e}')