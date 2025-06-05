"use client";

import { useState } from "react";
import Image from "next/image";

interface ScrapedData {
  html: string;
  styles: string[];
  images: Array<{
    src: string;
    alt: string;
    width?: string;
    height?: string;
  }>;
  fonts: string[];
  colors: string[];
  layout_structure: any;
  metadata: {
    title: string;
    url: string;
    screenshot: string;
    viewport: {
      width: number;
      height: number;
    };
  };
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scrapedData, setScrapedData] = useState<ScrapedData | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8002/api/scrape", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setScrapedData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      console.error("Error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const renderPreview = () => {
    if (error) {
      return (
        <div className="text-red-500 text-center">
          <p>Error: {error}</p>
        </div>
      );
    }

    if (!scrapedData) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
          Enter a URL above to see the cloned website preview
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">Website Screenshot</h3>
            {scrapedData.metadata.screenshot && (
              <img
                src={`data:image/png;base64,${scrapedData.metadata.screenshot}`}
                alt="Website screenshot"
                className="w-full rounded-lg shadow-lg"
              />
            )}
          </div>
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">Design Elements</h3>
            <div className="space-y-2">
              <h4 className="font-medium">Colors</h4>
              <div className="flex flex-wrap gap-2">
                {scrapedData.colors.map((color, index) => (
                  <div
                    key={index}
                    className="w-8 h-8 rounded-full shadow-md"
                    style={{ backgroundColor: color }}
                    title={color}
                  />
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <h4 className="font-medium">Fonts</h4>
              <ul className="list-disc list-inside">
                {scrapedData.fonts.map((font, index) => (
                  <li key={index}>{font}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
        <div className="space-y-4">
          <h3 className="font-semibold text-lg">HTML Preview</h3>
          <div className="bg-gray-100 dark:bg-gray-900 p-4 rounded-lg">
            <pre className="text-sm overflow-x-auto">
              {scrapedData.html.slice(0, 500)}...
            </pre>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Website Cloner
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            Enter any public website URL and get an AI-generated clone with similar
            aesthetics
          </p>
        </div>

        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto mb-12">
          <div className="flex gap-4">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Enter website URL (e.g., https://example.com)"
              className="flex-1 px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              required
            />
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Processing...
                </>
              ) : (
                "Clone Website"
              )}
            </button>
          </div>
        </form>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Preview
            </h2>
            {scrapedData && (
              <button
                className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-medium text-sm"
                onClick={() => {
                  const blob = new Blob([scrapedData.html], {
                    type: "text/html",
                  });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = "cloned-website.html";
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                  URL.revokeObjectURL(url);
                }}
              >
                Download HTML
              </button>
            )}
          </div>
          <div className="border rounded-lg p-4 min-h-[400px] bg-gray-50 dark:bg-gray-900">
            {renderPreview()}
          </div>
        </div>
      </div>
    </div>
  );
}
