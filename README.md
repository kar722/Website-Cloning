# Website Cloner

An AI-powered website cloning tool that uses Playwright for web scraping and Google's Gemini Pro for generating static clones of websites.

## Project Overview

This tool allows you to clone any public website by:
1. Extracting design elements using Playwright's headless browser
2. Analyzing the website's structure and styling
3. Generating a static clone using Gemini Pro LLM
4. Providing downloadable HTML/CSS output

### Key Features
- **Smart Web Scraping**: Uses Playwright for JavaScript-rendered content and anti-bot measures
- **Design Analysis**: Extracts colors, fonts, layout structure, and component descriptions
- **AI Generation**: Leverages Gemini Pro to generate semantic HTML and CSS
- **Modern UI**: Built with Next.js and styled with TailwindCSS

## Tech Stack

### Backend
- FastAPI for the API server
- Playwright for web scraping and screenshot capture
- Google Gemini Pro for code generation
- BeautifulSoup4 for HTML parsing
- Python 3.11+

### Frontend
- Next.js with TypeScript
- React 19
- TailwindCSS for styling
- Modern, responsive UI with dark mode support

## Getting Started

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   # Create .env file with:
   GEMINI_API_KEY=your_api_key_here
   ```

4. Run the development server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

The application will be available at `http://localhost:3000`
