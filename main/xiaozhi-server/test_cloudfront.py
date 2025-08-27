"""
Simple CloudFront Test
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN")
S3_BASE_URL = os.getenv("S3_BASE_URL")

def test_cloudfront():
    print(f"Testing CloudFront: {CLOUDFRONT_DOMAIN}")
    print(f"S3 Base URL: {S3_BASE_URL}")
    print("-" * 50)
    
    # Test some common file paths
    test_files = [
        "test.mp3",
        "audio/test.mp3", 
        "uploads/test.mp3",
        "sample.wav"
    ]
    
    for file_path in test_files:
        cloudfront_url = f"https://{CLOUDFRONT_DOMAIN}/{file_path}"
        s3_url = f"{S3_BASE_URL}/{file_path}"
        
        print(f"\nTesting: {file_path}")
        print(f"CloudFront URL: {cloudfront_url}")
        
        try:
            # Test CloudFront
            cf_response = requests.head(cloudfront_url, timeout=10)
            print(f"CloudFront Status: {cf_response.status_code}")
            
            if cf_response.status_code == 200:
                print("✅ File accessible through CloudFront!")
                print(f"Content-Type: {cf_response.headers.get('content-type', 'Unknown')}")
                print(f"Cache Status: {cf_response.headers.get('x-cache', 'Unknown')}")
                break
            elif cf_response.status_code == 403:
                print("❌ 403 Forbidden - File doesn't exist or no access")
            else:
                print(f"❌ Status: {cf_response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*50)
    print("CloudFront Distribution Status:")
    
    # Test root access
    try:
        root_response = requests.head(f"https://{CLOUDFRONT_DOMAIN}/", timeout=10)
        print(f"Root access status: {root_response.status_code}")
        print("✅ CloudFront distribution is active!")
    except Exception as e:
        print(f"❌ CloudFront error: {e}")

if __name__ == "__main__":
    test_cloudfront()