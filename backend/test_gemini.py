import requests
import os
from dotenv import load_dotenv
import json

def test_gemini():
    # Load API key
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    # Test URL and request
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "key": api_key
    }
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Generate a simple HTML page with a blue heading that says 'Hello World'"
                    }
                ]
            }
        ]
    }
    
    try:
        print("Making request to Gemini API...")
        response = requests.post(url, headers=headers, params=params, json=data)
        response.raise_for_status()
        
        result = response.json()
        print("\nAPI Response:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    test_gemini() 