from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from bs4 import BeautifulSoup
import requests
from typing import Dict, Any, Optional
import validators
import logging
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import json

from utils.extractors import (
    is_valid_url,
    extract_title,
    extract_css_links,
    extract_css_content,
    extract_colors_from_css,
    extract_fonts_from_css,
    extract_fonts_from_inline_styles,
    extract_images,
    extract_text_snippets,
    extract_component_descriptions,
    extract_raw_html_snippet,
    get_page_content,
    process_screenshot_for_llm
)

from utils.llm_generator import (
    configure_gemini,
    generate_website_code,
    WebsiteCode
)

# Settings for API configuration
class Settings(BaseSettings):
    gemini_api_key: str
    
    class Config:
        env_file = ".env"

# Request/Response models
class GenerateWebsiteRequest(BaseModel):
    url: str
    options: Optional[Dict[str, Any]] = None

class GenerateWebsiteResponse(BaseModel):
    html: str
    css: str
    error: Optional[str] = None
    design_context: Optional[Dict[str, Any]] = None
    screenshot: Optional[Dict[str, Any]] = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Website Design Context and Generation API",
    description="API for extracting design context and generating cloned websites using Gemini Pro",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencies
async def get_settings():
    return Settings()

@app.on_event("startup")
async def startup_event():
    # Configure Gemini on startup
    settings = await get_settings()
    configure_gemini(settings.gemini_api_key)

@app.get("/")
async def root():
    return {"message": "Website Design Context and Generation API is running"}

@app.post("/api/generate", response_model=GenerateWebsiteResponse)
async def generate_website(
    request: GenerateWebsiteRequest,
    settings: Settings = Depends(get_settings)
) -> GenerateWebsiteResponse:
    """
    Generate a cloned website using Gemini Pro based on extracted design context.
    
    Parameters:
    - url: The website URL to clone
    - options: Optional configuration for generation
    
    Returns:
    - Generated HTML and CSS code
    """
    try:
        # Configure Gemini with API key
        configure_gemini(settings.gemini_api_key)
        
        # First, extract design context
        design_context = await extract_design_context(request.url)
        
        if not design_context:
            raise HTTPException(
                status_code=400,
                detail="Failed to extract design context from the provided URL"
            )
        
        # Generate website code using Gemini
        generated_code = await generate_website_code(
            design_context=design_context,
            model_name="gemini-2.0-flash"
        )
        
        # Check for generation errors
        if generated_code.error:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate website code: {generated_code.error}"
            )
        
        # Validate generated code
        if not generated_code.html or not generated_code.css:
            raise HTTPException(
                status_code=500,
                detail="Generated code is incomplete or invalid"
            )
        
        # Return response with both generated code and design context
        return GenerateWebsiteResponse(
            html=generated_code.html,
            css=generated_code.css,
            error=None,
            design_context=design_context
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating website: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate website: {str(e)}"
        )

@app.get("/api/extract")
async def extract_design_context(url: str) -> Dict[str, Any]:
    """
    Extract rich design context from a given URL using enhanced analysis.
    
    Parameters:
    - url: The website URL to analyze
    
    Returns:
    - Dictionary containing detailed design context for LLM consumption
    """
    # Validate URL
    if not is_valid_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    
    try:
        # Fetch page content using Playwright with anti-bot measures
        content = await get_page_content(url)
        
        if not content:
            # Fallback to regular requests if Playwright fails
            logger.warning("Playwright fetch failed, falling back to requests")
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                response = requests.get(url, timeout=15, headers=headers)
                response.raise_for_status()
                content = {
                    "html": response.text,
                    "css": "",  # No computed styles in fallback mode
                    "screenshot": None  # No screenshot in fallback mode
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
        
        # Parse HTML
        soup = BeautifulSoup(content["html"], 'html.parser')
        
        # Extract CSS links and fetch their content
        css_links = extract_css_links(soup, url)
        all_css = content["css"] or ""  # Start with computed/inline CSS
        
        # Fetch and combine external CSS
        for css_url in css_links:
            try:
                css_response = requests.get(css_url, timeout=10)
                if css_response.ok:
                    all_css += "\n" + css_response.text
            except:
                logger.warning(f"Failed to fetch CSS from {css_url}")
        
        # Extract fonts from both CSS and inline styles
        fonts_from_css = extract_fonts_from_css(all_css)
        fonts_from_inline = extract_fonts_from_inline_styles(soup)
        all_fonts = sorted(list(fonts_from_css.union(fonts_from_inline)))
        
        # Extract component descriptions and layout
        component_descriptions, layout = extract_component_descriptions(soup)
        
        # Process screenshot if available
        screenshot_data = None
        if content.get("screenshot"):
            screenshot_data = process_screenshot_for_llm(content["screenshot"])
        
        # Build enhanced response
        result = {
            "title": extract_title(soup),
            "layout": layout,
            "color_palette": extract_colors_from_css(all_css),
            "fonts": all_fonts,
            "images": extract_images(soup, url),
            "text_snippets": extract_text_snippets(soup),
            "css_links": css_links,
            "raw_html_snippet": extract_raw_html_snippet(soup),
            "component_descriptions": component_descriptions,
            "screenshot": screenshot_data
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing URL {url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 