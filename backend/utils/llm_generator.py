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
model = None  # Will be set by configure_gemini

@dataclass
class WebsiteCode:
    html: str
    css: str
    error: Optional[str] = None

def configure_gemini(api_key: str):
    """Configure Gemini with API key."""
    global GEMINI_API_KEY, model
    GEMINI_API_KEY = api_key
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-exp")

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

async def generate_website_code(design_context: Dict[str, Any], model_name: str = "gemini-2.0-flash-exp") -> WebsiteCode:
    """
    Generate website code using Gemini Pro based on design context.
    """
    try:
        if not model:
            return WebsiteCode(
                html="",
                css="",
                error="Gemini model not initialized"
            )

        # Extract screenshot information
        screenshot_info = design_context.get("screenshot", {})
        screenshot_prompt = ""
        if screenshot_info:
            screenshot_prompt = f"""
            Visual Reference:
            - Page dimensions: {screenshot_info.get('dimensions', {}).get('width')}x{screenshot_info.get('dimensions', {}).get('height')} pixels
            - Dominant colors: {', '.join(screenshot_info.get('dominant_colors', []))}
            - Full page screenshot is available for reference
            """

        # Construct the prompt
        prompt = f"""
        Create a modern, responsive website clone based on the following design context:

        {screenshot_prompt}

        Design Elements:
        - Title: {design_context.get('title', '')}
        - Color Palette: {', '.join(design_context.get('color_palette', []))}
        - Fonts: {', '.join(design_context.get('fonts', []))}
        
        Layout Structure:
        {json.dumps(design_context.get('layout', []), indent=2)}
        
        Component Descriptions:
        {json.dumps(design_context.get('component_descriptions', []), indent=2)}
        
        Text Content:
        {json.dumps(design_context.get('text_snippets', {}), indent=2)}
        
        Original HTML Structure:
        {design_context.get('raw_html_snippet', '')}
        
        Requirements:
        1. Generate clean, semantic HTML5 markup
        2. Use modern CSS3 features for styling
        3. Ensure responsive design that works on all devices
        4. Match the original layout and design as closely as possible
        5. Use the provided color palette and fonts
        6. Implement proper accessibility features
        7. Optimize for performance
        
        Please provide the complete HTML and CSS code for the cloned website.
        """

        # Generate code using Gemini
        try:
            response = await model.generate_content_async(prompt)
            
            if not response or not response.text:
                return WebsiteCode(
                    html="",
                    css="",
                    error="Failed to generate website code"
                )
            
            # Parse the response to extract HTML and CSS
            try:
                html_start = response.text.find("<html")
                html_end = response.text.find("</html>") + 7
                html = response.text[html_start:html_end]
                
                css_start = response.text.find("<style>") + 7
                css_end = response.text.find("</style>")
                css = response.text[css_start:css_end]
                
                return WebsiteCode(
                    html=html,
                    css=css,
                    error=None
                )
            except Exception as e:
                return WebsiteCode(
                    html="",
                    css="",
                    error=f"Failed to parse generated code: {str(e)}"
                )
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            return WebsiteCode(
                html="",
                css="",
                error=f"Failed to call Gemini API: {str(e)}"
            )
            
    except Exception as e:
        logger.error(f"Error generating website code: {str(e)}")
        return WebsiteCode(
            html="",
            css="",
            error=f"Failed to generate website code: {str(e)}"
        )