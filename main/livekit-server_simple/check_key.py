import os
from dotenv import load_dotenv

# Import the main Gemini SDK client
try:
    from google import genai
    from google.genai.errors import APIError
except ImportError:
    print("Error: The 'google-genai' package is required.")
    print("Please install it: pip install google-genai")
    exit(1)


# Load environment variables from the .env.local file
# This mirrors what your LiveKit Agent script does
load_dotenv(".env.local")

# The LiveKit Agent uses GEMINI_API_KEY
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ FAILURE: GEMINI_API_KEY not found in .env.local or environment.")
    print("Please ensure your .env.local file has the line: GEMINI_API_KEY=\"Your-Key-Here\"")
    exit(1)


def check_api_key():
    print("Attempting to connect to Gemini API...")
    
    try:
        # Initialize the client. It automatically picks up the API_KEY from the environment/dotenv.
        client = genai.Client(api_key=API_KEY)
        
        # Test the key by making a simple request to a general model
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say 'API Key is valid' and nothing else.",
        )
        
        if response.text.strip().lower() == "api key is valid":
            print("\n✅ SUCCESS: The Gemini API Key is valid and working!")
            print("The issue is likely with the LiveKit Agent's specific connection (e.g., Live API access, model access, or a security restriction).")
        else:
             # This block is for success, but unexpected response content
            print("\n⚠️ WARNING: Key is valid, but received an unexpected response.")
            print(f"Response: {response.text}")
            print("The API is reachable, but double-check your model or key restrictions.")

    except APIError as e:
        print("\n❌ FAILURE: An API Error occurred.")
        print(f"Error details: {e}")
        # The expired key error will usually fall here
        if "invalid API key" in str(e) or "API key expired" in str(e):
            print("\nACTION REQUIRED: Your key is confirmed to be invalid/expired/restricted by the Gemini service.")
            print("Please generate a new key on the Google AI Studio website and update your .env.local file.")
        else:
            print("\nACTION REQUIRED: The key is likely restricted (e.g., to the wrong service/IP) or linked to an account with no access.")
            print("Check key restrictions on Google AI Studio.")
            
    except Exception as e:
        print(f"\n❌ FAILURE: An unexpected error occurred: {type(e).__name__}")
        print(f"Details: {e}")
        print("This may be a network or environment issue.")

 
if __name__ == "__main__":
    check_api_key()