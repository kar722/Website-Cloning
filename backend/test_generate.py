import requests
import json
import os
from dotenv import load_dotenv

def test_generate():
    # Load and verify API key
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env file")
        print("Please create a .env file with your Gemini API key:")
        print('GEMINI_API_KEY=your_api_key_here')
        return
    elif api_key == 'your_api_key_here':
        print("❌ Error: Please replace the placeholder with your actual Gemini API key")
        print("Get your API key from: https://makersuite.google.com/app/apikey")
        return
    
    print(f"✅ Found API key: {api_key[:4]}...{api_key[-4:]}")
    
    url = "http://localhost:8000/api/generate"
    payload = {
        "url": "https://mkbhd.com"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        
        # Create generated directory if it doesn't exist
        os.makedirs("generated", exist_ok=True)
        
        # Save the generated files
        with open("generated/index.html", "w") as f:
            f.write(result["html"])
            
        with open("generated/styles.css", "w") as f:
            f.write(result["css"])
            
        print("✅ Successfully generated website clone!")
        print("Files saved in the 'generated' directory:")
        print("- index.html")
        print("- styles.css")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    test_generate() 