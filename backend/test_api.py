import requests
import json
import os
from pathlib import Path

def test_api():
    """Test both endpoints of the website cloning API."""
    
    # Base URL for the API
    base_url = "http://localhost:8000"
    
    # Test website to clone
    test_url = "https://example.com"
    
    try:
        # 1. Test the root endpoint
        print("\nTesting API connection...")
        response = requests.get(base_url)
        response.raise_for_status()
        print("✅ API is running")
        
        # 2. Test the extract endpoint
        print("\nTesting design context extraction...")
        extract_response = requests.get(f"{base_url}/api/extract", params={"url": test_url})
        extract_response.raise_for_status()
        design_context = extract_response.json()
        print("✅ Successfully extracted design context:")
        print(f"  - Title: {design_context['title']}")
        print(f"  - Components: {len(design_context['component_descriptions'])} components detected")
        print(f"  - Colors: {len(design_context['color_palette'])} colors extracted")
        
        # 3. Test the generate endpoint
        print("\nTesting website generation...")
        generate_response = requests.post(
            f"{base_url}/api/generate",
            json={"url": test_url}
        )
        generate_response.raise_for_status()
        generated_code = generate_response.json()
        
        # 4. Save the generated files
        output_dir = Path("generated")
        output_dir.mkdir(exist_ok=True)
        
        # Save HTML
        with open(output_dir / "index.html", "w") as f:
            f.write(generated_code["html"])
            
        # Save CSS
        with open(output_dir / "styles.css", "w") as f:
            f.write(generated_code["css"])
            
        # Save full response for reference
        with open(output_dir / "response.json", "w") as f:
            json.dump(generated_code, f, indent=2)
            
        print("✅ Successfully generated website clone:")
        print(f"  - Files saved in: {output_dir.absolute()}")
        print("  - Generated files:")
        print("    - index.html")
        print("    - styles.css")
        print("    - response.json")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API. Make sure the server is running.")
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error: API request failed with status {e.response.status_code}")
        print(f"   Message: {e.response.json().get('detail', 'No detail provided')}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_api() 