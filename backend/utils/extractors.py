from typing import List, Dict, Optional, Set, Tuple, Any
import re
import base64
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup, Tag
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from playwright.async_api import async_playwright
import cssutils
from PIL import Image
import io
import webcolors
from collections import Counter
import logging
import json
from dataclasses import dataclass
from collections import defaultdict
import random
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom exceptions
class ScrapingError(Exception):
    """Base exception for scraping errors"""
    pass

class ProxyError(ScrapingError):
    """Raised when there are issues with proxy servers"""
    pass

class RateLimitError(ScrapingError):
    """Raised when rate limits are hit"""
    pass

# Proxy configuration
class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.last_rotation = datetime.now()
        self.rotation_interval = timedelta(minutes=10)
        self.current_index = 0
        
    def add_proxy(self, proxy: str):
        """Add a proxy to the pool"""
        self.proxies.append({
            "server": proxy,
            "failures": 0,
            "last_used": datetime.now() - timedelta(minutes=5)
        })
    
    def get_next_proxy(self) -> Optional[Dict[str, Any]]:
        """Get the next available proxy with basic load balancing"""
        if not self.proxies:
            return None
            
        now = datetime.now()
        if now - self.last_rotation > self.rotation_interval:
            random.shuffle(self.proxies)
            self.last_rotation = now
            
        # Find a proxy that hasn't failed too much
        for _ in range(len(self.proxies)):
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            
            if proxy["failures"] < 3 and now - proxy["last_used"] > timedelta(seconds=2):
                proxy["last_used"] = now
                return {"server": proxy["server"]}
                
        return None
    
    def mark_proxy_failure(self, proxy_server: str):
        """Mark a proxy as failed"""
        for proxy in self.proxies:
            if proxy["server"] == proxy_server:
                proxy["failures"] += 1
                break

# Initialize proxy manager with some example proxies (replace with your actual proxies)
proxy_manager = ProxyManager()
# Add your proxy servers here
# proxy_manager.add_proxy("http://proxy1:8080")
# proxy_manager.add_proxy("http://proxy2:8080")

# Browser configuration
BROWSER_CONFIG = {
    "viewport": {"width": 1280, "height": 800},
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    }
}

async def setup_browser() -> Tuple[Browser, BrowserContext]:
    """Setup a browser with anti-bot detection measures."""
    playwright = async_playwright()
    playwright_instance = await playwright.start()
    
    browser = await playwright_instance.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-site-isolation-trials"
        ]
    )
    
    # Get proxy configuration
    proxy_config = proxy_manager.get_next_proxy()
    context_options = {
        "viewport": BROWSER_CONFIG["viewport"],
        "user_agent": BROWSER_CONFIG["user_agent"],
        "extra_http_headers": BROWSER_CONFIG["headers"],
    }
    
    if proxy_config:
        context_options["proxy"] = proxy_config
    
    context = await browser.new_context(**context_options)
    
    # Additional anti-bot measures
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Hide automation flags
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
    """)
    
    return browser, context

async def get_page_content(url: str) -> Optional[Dict[str, str]]:
    """
    Fetch page content using Playwright with anti-bot measures.
    Returns HTML content, computed styles, and full page screenshot.
    """
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-site-isolation-trials"
                ]
            )
            
            context = await browser.new_context(
                viewport=BROWSER_CONFIG["viewport"],
                user_agent=BROWSER_CONFIG["user_agent"],
                extra_http_headers=BROWSER_CONFIG["headers"]
            )
            
            # Additional anti-bot measures
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            try:
                page = await context.new_page()
                
                # Set additional page properties
                await page.set_extra_http_headers(BROWSER_CONFIG["headers"])
                
                # Navigate with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = await page.goto(
                            url,
                            wait_until="networkidle",
                            timeout=30000
                        )
                        
                        if not response:
                            logger.error("No response received from page")
                            if attempt < max_retries - 1:
                                await page.wait_for_timeout(2000 * (attempt + 1))
                                continue
                            break
                            
                        status = response.status
                        if status == 200:
                            break
                            
                        if status == 403:
                            logger.warning(f"Received 403 status code (attempt {attempt + 1})")
                            if attempt < max_retries - 1:
                                await page.wait_for_timeout(2000 * (attempt + 1))
                                continue
                            break
                            
                        if status >= 400:
                            logger.error(f"Received error status code: {status}")
                            if attempt < max_retries - 1:
                                await page.wait_for_timeout(2000 * (attempt + 1))
                                continue
                            break
                            
                    except Exception as e:
                        logger.warning(f"Navigation failed (attempt {attempt + 1}): {str(e)}")
                        if attempt < max_retries - 1:
                            await page.wait_for_timeout(2000 * (attempt + 1))
                            continue
                        raise
                
                # Check if we got a successful response
                if not response or response.status != 200:
                    logger.error(f"Failed to load page: Status {response.status if response else 'No response'}")
                    return None
                
                # Wait for content to load
                await page.wait_for_load_state("networkidle")
                
                # Take full page screenshot
                screenshot = await page.screenshot(
                    full_page=True,
                    type='png'
                )
                
                # Get HTML content
                html_content = await page.content()
                
                # Get computed styles
                css_content = await page.evaluate("""() => {
                    const styleSheets = Array.from(document.styleSheets);
                    return styleSheets
                        .filter(sheet => {
                            try {
                                return sheet.cssRules !== null;
                            } catch (e) {
                                return false;
                            }
                        })
                        .map(sheet => {
                            return Array.from(sheet.cssRules)
                                .map(rule => rule.cssText)
                                .join('\\n');
                        })
                        .join('\\n');
                }""")
                
                result = {
                    "html": html_content,
                    "css": css_content,
                    "screenshot": base64.b64encode(screenshot).decode('utf-8')
                }
                return result
                
            finally:
                await context.close()
                await browser.close()
                
    except Exception as e:
        logger.error(f"Failed to fetch page content: {str(e)}")
        return None

def is_valid_url(url: str) -> bool:
    """Validate if the given URL is properly formatted."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def extract_title(soup: BeautifulSoup) -> str:
    """Extract page title."""
    title = soup.title.string if soup.title else ""
    return title.strip() if title else ""

def extract_css_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    """Extract all CSS stylesheet links."""
    css_links = []
    for link in soup.find_all('link', rel='stylesheet'):
        href = link.get('href')
        if href:
            absolute_url = urljoin(base_url, href)
            css_links.append(absolute_url)
    return css_links

def extract_css_content(soup: BeautifulSoup, base_url: str) -> str:
    """Extract and combine all CSS content for analysis."""
    css_content = []
    
    # Get inline styles
    for style in soup.find_all('style'):
        if style.string:
            css_content.append(style.string)
    
    # Get external stylesheets
    for link in soup.find_all('link', rel='stylesheet'):
        href = link.get('href')
        if href:
            absolute_url = urljoin(base_url, href)
            try:
                response = requests.get(absolute_url, timeout=10)
                if response.status_code == 200:
                    css_content.append(response.text)
            except:
                continue
    
    return "\n".join(css_content)

def extract_color_palette(css_content: str) -> List[str]:
    """Extract color codes from CSS content."""
    # Match hex colors and rgb/rgba values
    color_pattern = r'#[0-9a-fA-F]{3,6}|rgb\([^)]+\)|rgba\([^)]+\)'
    colors = re.findall(color_pattern, css_content)
    
    # Convert colors to hex format for consistency
    hex_colors = set()
    for color in colors:
        try:
            if color.startswith('#'):
                hex_colors.add(color.lower())
            elif color.startswith('rgb'):
                # Convert rgb/rgba to hex
                values = re.findall(r'\d+', color)[:3]
                hex_color = '#{:02x}{:02x}{:02x}'.format(*map(int, values))
                hex_colors.add(hex_color)
        except:
            continue
    
    # Return top colors (limit to reasonable number)
    return list(hex_colors)[:10]

def extract_fonts_from_css(css_content: str) -> Set[str]:
    """Extract font families from CSS content."""
    fonts = set()
    # Match font-family declarations, including those with multiple fonts
    font_pattern = r'font-family\s*:\s*([^;}]+)[;}]'
    matches = re.findall(font_pattern, css_content, re.IGNORECASE)
    
    for match in matches:
        # Split font list and clean each font name
        for font in match.split(','):
            font = font.strip().strip("'").strip('"')
            # Filter out generic families and CSS keywords
            if font.lower() not in {'inherit', 'initial', 'unset', 'serif', 'sans-serif', 'monospace', 'cursive', 'fantasy', 'system-ui'}:
                fonts.add(font)
    
    return fonts

def extract_fonts_from_inline_styles(soup: BeautifulSoup) -> Set[str]:
    """Extract fonts from inline style attributes."""
    fonts = set()
    
    # Find all elements with style attribute
    for element in soup.find_all(style=True):
        style = element['style']
        if 'font-family' in style.lower():
            # Extract fonts from inline style
            matches = re.findall(r'font-family\s*:\s*([^;]+)', style, re.IGNORECASE)
            for match in matches:
                for font in match.split(','):
                    font = font.strip().strip("'").strip('"')
                    if font.lower() not in {'inherit', 'initial', 'unset', 'serif', 'sans-serif', 'monospace', 'cursive', 'fantasy', 'system-ui'}:
                        fonts.add(font)
    
    return fonts

def extract_colors_from_css(css_content: str) -> List[str]:
    """Extract color values from CSS content."""
    colors = set()
    
    # Match various color formats
    color_patterns = [
        (r'#[0-9a-fA-F]{3}\b', lambda x: x),  # #RGB
        (r'#[0-9a-fA-F]{6}\b', lambda x: x),  # #RRGGBB
        (r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', 
         lambda x: '#{:02x}{:02x}{:02x}'.format(*map(int, x.groups()))),  # rgb()
        (r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*[\d.]+\s*\)',
         lambda x: '#{:02x}{:02x}{:02x}'.format(*map(int, x.groups())))  # rgba()
    ]
    
    # CSS properties that commonly contain colors
    color_properties = [
        'color:', 'background-color:', 'border-color:', 
        'box-shadow:', 'text-shadow:', 'outline-color:',
        'border:', 'background:', 'border-top-color:',
        'border-right-color:', 'border-bottom-color:',
        'border-left-color:'
    ]
    
    # Extract colors from each property
    for prop in color_properties:
        prop_pattern = f'{prop}[^;}}]+'
        matches = re.finditer(prop_pattern, css_content, re.IGNORECASE)
        for match in matches:
            value = match.group()
            for pattern, converter in color_patterns:
                color_matches = re.finditer(pattern, value)
                for color_match in color_matches:
                    try:
                        color = converter(color_match)
                        colors.add(color.lower())
                    except:
                        continue
    
    # Sort colors by frequency and return top 8
    return sorted(list(colors))[:8]

def extract_images(soup: BeautifulSoup, base_url: str) -> List[str]:
    """Extract image URLs from img tags."""
    images = set()
    
    for img in soup.find_all('img'):
        src = img.get('src')
        if src:
            absolute_url = urljoin(base_url, src)
            images.add(absolute_url)
    
    # Return top 10 images
    return list(images)[:10]

def extract_text_snippets(soup: BeautifulSoup) -> Dict[str, List[str]]:
    """Extract organized text content."""
    # Extract headings (h1-h3)
    headings = [h.get_text().strip() 
               for h in soup.find_all(['h1', 'h2', 'h3']) 
               if h.get_text().strip()]
    
    # Extract first 10 meaningful paragraphs
    paragraphs = [p.get_text().strip() 
                 for p in soup.find_all('p', limit=10) 
                 if len(p.get_text().strip()) > 20]  # Filter out tiny paragraphs
    
    # Extract button text
    buttons = []
    for btn in soup.find_all(['button', 'a']):
        if (btn.name == 'a' and 
            any(c for c in btn.get('class', []) if 'btn' in c.lower())):
            text = btn.get_text().strip()
            if text:
                buttons.append(text)
        elif btn.name == 'button':
            text = btn.get_text().strip()
            if text:
                buttons.append(text)
    
    return {
        "headings": headings,
        "paragraphs": paragraphs,
        "buttons": buttons
    }

def extract_layout_hints(soup: BeautifulSoup) -> List[str]:
    """Infer layout components from semantic tags and class names."""
    layout = []
    
    # Check semantic tags
    if soup.find('nav'):
        layout.append('navbar')
    if soup.find('header'):
        layout.append('header')
    if soup.find('footer'):
        layout.append('footer')
    
    # Check common class names
    common_components = {
        'hero': ['hero', 'banner', 'jumbotron'],
        'product-grid': ['products', 'grid', 'cards'],
        'features': ['features', 'services'],
        'testimonials': ['testimonials', 'reviews'],
        'contact': ['contact', 'get-in-touch'],
        'blog': ['blog', 'posts', 'articles']
    }
    
    for component, classes in common_components.items():
        for cls in classes:
            if soup.find(class_=lambda x: x and cls.lower() in x.lower()):
                layout.append(component)
                break
    
    return layout

def extract_raw_html_snippet(soup: BeautifulSoup) -> str:
    """Extract main semantic layout tags with truncated content."""
    # Find all semantic layout tags
    semantic_tags = soup.find_all(['header', 'main', 'footer', 'nav', 'section'])
    
    # Create a new soup with just these tags
    layout_soup = BeautifulSoup('<div></div>', 'html.parser')
    layout_div = layout_soup.div
    
    for tag in semantic_tags:
        # Create a new tag with the same name and attributes
        new_tag = layout_soup.new_tag(tag.name)
        new_tag.attrs = tag.attrs
        
        # Add truncated content placeholder
        new_tag.string = '...'
        layout_div.append(new_tag)
    
    return str(layout_div)

def capture_screenshot(url: str) -> Optional[str]:
    """Capture full page screenshot using Playwright."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, wait_until='networkidle')
            screenshot = page.screenshot(full_page=True)
            browser.close()
            return base64.b64encode(screenshot).decode('utf-8')
    except:
        return None

def get_rendered_html(url: str) -> Optional[str]:
    """Get JavaScript-rendered HTML content using Playwright."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, wait_until='networkidle')
            content = page.content()
            browser.close()
            return content
    except:
        return None 

@dataclass
class Component:
    type: str
    description: str
    confidence: float

def analyze_component(element: Tag) -> Optional[Component]:
    """Analyze a DOM element to determine if it's a recognized component."""
    
    def get_element_stats(el: Tag) -> Dict:
        """Get statistics about an element's contents."""
        return {
            'links': len(el.find_all('a')),
            'buttons': len(el.find_all(['button', 'a'], class_=lambda x: x and 'btn' in x.lower())),
            'images': len(el.find_all('img')),
            'headings': len(el.find_all(['h1', 'h2', 'h3'])),
            'text': len(el.get_text().strip()),
            'classes': el.get('class', [])
        }
    
    stats = get_element_stats(element)
    tag_name = element.name
    classes = ' '.join(element.get('class', [])).lower()
    
    # Navbar detection
    if (tag_name == 'nav' or 
        'nav' in classes or 
        'header' in classes or 
        'navbar' in classes):
        links = len(element.find_all('a'))
        has_logo = bool(element.find('img'))
        return Component(
            type='navbar',
            description=f"Navbar with {links} navigation links" + (" and logo" if has_logo else ""),
            confidence=0.9 if tag_name == 'nav' else 0.7
        )
    
    # Hero section detection
    if ('hero' in classes or 
        'banner' in classes or 
        'jumbotron' in classes or
        (tag_name == 'header' and stats['headings'] > 0)):
        cta_count = stats['buttons']
        has_image = bool(element.find('img'))
        return Component(
            type='hero',
            description=f"Hero section with {stats['headings']} heading(s)" + 
                       (f" and {cta_count} call-to-action button(s)" if cta_count else "") +
                       (" featuring hero image" if has_image else ""),
            confidence=0.8
        )
    
    # Product/Card grid detection
    repeated_elements = element.find_all(class_=lambda x: x and any(term in str(x).lower() for term in ['card', 'product', 'item', 'grid-item']))
    if len(repeated_elements) >= 3:
        return Component(
            type='product-grid',
            description=f"Grid of {len(repeated_elements)} product/content cards" +
                       (" with images" if any(el.find('img') for el in repeated_elements) else ""),
            confidence=0.7
        )
    
    # Footer detection
    if (tag_name == 'footer' or 'footer' in classes):
        social_links = len(element.find_all('a', class_=lambda x: x and 'social' in str(x).lower()))
        return Component(
            type='footer',
            description=f"Footer with {stats['links']} links" +
                       (f" including {social_links} social media links" if social_links else ""),
            confidence=0.9 if tag_name == 'footer' else 0.7
        )
    
    # Feature section detection
    if ('features' in classes or 
        'services' in classes or
        (tag_name == 'section' and stats['headings'] > 0)):
        return Component(
            type='features',
            description=f"Feature section with {stats['headings']} headings and {stats['images']} images",
            confidence=0.6
        )
    
    return None

def extract_component_descriptions(soup: BeautifulSoup) -> Tuple[List[str], List[str]]:
    """
    Extract component descriptions and layout structure.
    Returns (component_descriptions, layout)
    """
    components = []
    layout = []
    seen_types = set()
    
    # Look for main semantic sections
    for element in soup.find_all(['nav', 'header', 'main', 'section', 'footer', 'div']):
        component = analyze_component(element)
        if component and component.confidence >= 0.6:
            # Add to descriptions if we have meaningful info
            if component.description and component.type not in seen_types:
                components.append(component.description)
                seen_types.add(component.type)
            
            # Add to layout if not already included
            if component.type not in layout:
                layout.append(component.type)
    
    return components, layout 

def process_screenshot_for_llm(screenshot_base64: str) -> Dict[str, Any]:
    """
    Process screenshot for LLM consumption, extracting relevant visual information.
    """
    try:
        # Decode base64 image
        image_data = base64.b64decode(screenshot_base64)
        image = Image.open(io.BytesIO(image_data))
        
        # Get image dimensions
        width, height = image.size
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Get dominant colors
        colors = image.getcolors(maxcolors=256)
        if colors:
            colors.sort(reverse=True)
            dominant_colors = [webcolors.rgb_to_hex(color[1]) for color in colors[:5]]
        else:
            dominant_colors = []
        
        return {
            "dimensions": {
                "width": width,
                "height": height
            },
            "dominant_colors": dominant_colors,
            "base64_image": screenshot_base64
        }
    except Exception as e:
        logger.error(f"Failed to process screenshot: {str(e)}")
        return None