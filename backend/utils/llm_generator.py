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
    return f"""You are an expert front-end web developer tasked with recreating a static HTML and CSS version of a web page, using a structured design context provided to you.

Your output must:
- Reproduce the layout and visual style described as closely as possible.
- Use only **vanilla HTML and CSS** (no JS, React, or Tailwind).
- Prioritize semantic HTML5 tags (e.g., <nav>, <header>, <section>, <footer>, etc.).
- Use clean, maintainable class names and include embedded styles in a <style> block inside <head>.
- Include the provided images and headings in the correct layout blocks (hero, grid, footer, etc.).
- Match the font families and color palette closely.

Only output the complete HTML file — do not include comments, explanations, or markdown formatting.

Below is the structured design context for a webpage. Use this data to generate a full static HTML + CSS clone.

Design Context:
{json.dumps(design_context, indent=2)}"""

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
            
            # Try to extract HTML content
            html_match = re.search(r'```html\n(.*?)\n```', generated_text, re.DOTALL)
            if html_match:
                html_content = html_match.group(1).strip()
                
                # Extract CSS from the HTML (for preview purposes)
                css_match = re.search(r'<style>(.*?)</style>', html_content, re.DOTALL)
                css_content = css_match.group(1).strip() if css_match else ""
                
                return WebsiteCode(
                    html=html_content,
                    css=css_content
                )
            else:
                # If no code block, the entire response might be HTML
                if generated_text.strip().startswith('<!DOCTYPE html>') or generated_text.strip().startswith('<html>'):
                    html_content = generated_text.strip()
                    css_match = re.search(r'<style>(.*?)</style>', html_content, re.DOTALL)
                    css_content = css_match.group(1).strip() if css_match else ""
                    
                    return WebsiteCode(
                        html=html_content,
                        css=css_content
                    )
                else:
                    return WebsiteCode(
                        html="",
                        css="",
                        error="No valid HTML found in response"
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