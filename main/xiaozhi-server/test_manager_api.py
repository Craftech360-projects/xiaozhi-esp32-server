import requests

# Test connection to manager-api
url = "http://localhost:8002/xiaozhi/config/server-base"
secret = "cheeko-secret-key-2025"

headers = {
    "Authorization": f"Bearer {secret}",
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("\nSuccess! Manager API is accessible with the secret.")
    else:
        print("\nFailed to access Manager API")
        
except Exception as e:
    print(f"Error: {e}")
    print("Make sure manager-api is running on http://localhost:8002/xiaozhi")