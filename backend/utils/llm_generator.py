from typing import Dict, Any, Optional
import google.generativeai as genai
import json
import logging
from dataclasses import dataclass
import re
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
GEMINI_API_KEY = None  # Will be set by configure_gemini

@dataclass
class WebsiteCode:
    html: str
    css: str
    error: Optional[str] = None

def configure_gemini(api_key: str):
    """Configure Gemini with API key."""
    global GEMINI_API_KEY
    GEMINI_API_KEY = api_key

def create_generation_prompt(design_context: Dict[str, Any]) -> str:
    """Create a detailed prompt for Gemini to generate website code."""
    return f"""You are an expert web developer. Generate clean, modern HTML and CSS code to clone a website based on the following design specifications. Return ONLY the code blocks, no explanations.

DESIGN SPECIFICATIONS:
---------------------
Title: {design_context['title']}

Layout Structure:
{json.dumps(design_context['layout'], indent=2)}

Color Palette:
{json.dumps(design_context['color_palette'], indent=2)}

Fonts Used:
{json.dumps(design_context['fonts'], indent=2)}

Text Content:
{json.dumps(design_context['text_snippets'], indent=2)}

Images:
{json.dumps(design_context['images'], indent=2)}

Original HTML Structure:
{design_context['raw_html_snippet']}

REQUIREMENTS:
------------
1. Generate ONLY the HTML and CSS code - no explanations
2. Use semantic HTML5 elements
3. Make it responsive
4. Include all necessary font imports and image references
5. Match the color scheme and typography exactly
6. Follow the original layout structure

RESPONSE FORMAT:
--------------
Return ONLY two code blocks in this format:

```html
<!DOCTYPE html>
... your HTML code here ...
</html>
```

```css
/* Your CSS code here */
```

Do not include any other text or explanations - just the code blocks."""

async def generate_website_code(design_context: Dict[str, Any], model_name: str = "gemini-2.0-flash") -> WebsiteCode:
    """Generate website code using Gemini."""
    try:
        # Create the prompt
        prompt = create_generation_prompt(design_context)
        
        # Prepare request in the correct format
        request_body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        # Make direct HTTP request to Gemini API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        headers = {
            "Content-Type": "application/json"
        }
        params = {
            "key": GEMINI_API_KEY
        }
        
        logger.info(f"Making request to Gemini API: {url}")
        response = requests.post(
            url,
            headers=headers,
            params=params,
            json=request_body
        )
        
        # Check for errors
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        logger.info(f"Received response from Gemini API: {result}")
        
        try:
            # Extract the generated text
            generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
            logger.info(f"Extracted text from response: {generated_text[:100]}...")
            
            # Try to extract code blocks
            html_match = re.search(r'```html\n(.*?)\n```', generated_text, re.DOTALL)
            css_match = re.search(r'```css\n(.*?)\n```', generated_text, re.DOTALL)
            
            if html_match:
                html = html_match.group(1).strip()
                css = css_match.group(1).strip() if css_match else ""
                return WebsiteCode(
                    html=html,
                    css=css
                )
            else:
                return WebsiteCode(
                    html="",
                    css="",
                    error="No HTML code found in response"
                )
                
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected response format: {str(e)}")
            return WebsiteCode(
                html="",
                css="",
                error=f"Unexpected response format: {str(e)}"
            )
            
    except Exception as e:
        logger.error(f"Error generating website code: {str(e)}")
        return WebsiteCode(
            html="",
            css="",
            error=str(e)
        ) 