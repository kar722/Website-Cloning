# Website Design Context API

A FastAPI-based API that extracts structured design context from websites to assist with LLM-based cloning.

## Features

- Extracts semantic layout structure
- Identifies color palette from CSS
- Lists all fonts used
- Collects image URLs
- Extracts meaningful text content (headings, paragraphs, buttons)
- Provides CSS stylesheet links
- Returns simplified HTML layout structure
- Infers layout components from semantic tags and class names

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Running the API

Start the FastAPI server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### GET /api/extract

Extracts structured design context from a given URL.

**Query Parameters:**
- `url` (required): The website URL to analyze

**Example Request:**
```bash
curl "http://localhost:8000/api/extract?url=https://example.com"
```

**Example Response:**
```json
{
  "title": "Example Website",
  "layout": ["navbar", "hero", "product-grid", "footer"],
  "color_palette": ["#ffffff", "#000000", "#ff0000"],
  "fonts": ["Inter", "Helvetica", "sans-serif"],
  "images": [
    "https://example.com/logo.png",
    "https://example.com/hero.jpg"
  ],
  "text_snippets": {
    "headings": ["Welcome", "Features", "Contact"],
    "paragraphs": ["Lorem ipsum..."],
    "buttons": ["Learn More", "Contact Us"]
  },
  "css_links": [
    "https://example.com/styles/main.css",
    "https://fonts.googleapis.com/css?family=Inter"
  ],
  "raw_html_snippet": "<header>...</header><main>...</main>"
}
```

## Error Handling

The API returns appropriate HTTP status codes:
- `400`: Invalid URL or failed to fetch URL
- `500`: Internal server error

## CORS

CORS is enabled for all origins to allow calls from any frontend application, particularly useful for localhost development.

## Implementation Details

1. **URL Fetching**: Uses `requests` library with a 15-second timeout
2. **HTML Parsing**: Uses `BeautifulSoup4` for robust HTML parsing
3. **CSS Processing**: 
   - Extracts both inline styles and external stylesheets
   - Processes color codes and font declarations
4. **Content Limits**:
   - Images: Limited to top 10 unique URLs
   - Paragraphs: First 10 meaningful paragraphs
   - Colors: Up to 10 unique colors
5. **Layout Detection**:
   - Uses semantic HTML5 tags
   - Scans common class names for component hints
   - Provides simplified HTML structure 