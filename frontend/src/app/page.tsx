"use client";

import { useState } from "react";
import Image from "next/image";
import { CgWebsite } from "react-icons/cg";
import { HiArrowRight } from "react-icons/hi";
import { FiGithub } from "react-icons/fi";
import TypewriterInput from "./components/TypewriterInput";

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
  design_context?: {
    color_palette?: string[];
    fonts?: string[];
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
      const response = await fetch("http://localhost:8000/api/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url, options: {} }),
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
        <div className="grid grid-cols-1 gap-6">
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">Cloned Website Preview</h3>
            <div className="bg-white rounded-lg shadow-lg overflow-hidden" style={{ height: '600px' }}>
              <iframe
                srcDoc={scrapedData.html}
                className="w-full h-full border-0"
                sandbox="allow-same-origin"
                title="Cloned website preview"
              />
            </div>
          </div>
          
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">Design Elements</h3>
            <div className="space-y-2">
              <h4 className="font-medium">Colors</h4>
              <div className="flex flex-wrap gap-2">
                {scrapedData.design_context?.color_palette?.map((color, index) => (
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
                {scrapedData.design_context?.fonts?.map((font, index) => (
                  <li key={index}>{font}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        <div className="flex justify-between items-center">
          <h3 className="font-semibold text-lg">Generated Code</h3>
          <button
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
            className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-medium text-sm"
          >
            Download HTML
          </button>
        </div>
        <div className="bg-gray-100 dark:bg-gray-900 p-4 rounded-lg">
          <pre className="text-sm overflow-x-auto whitespace-pre-wrap">
            {scrapedData.html}
          </pre>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#000000] relative overflow-hidden">
      {/* Animated gradient orbs in background */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -inset-[10px] opacity-30">
          {/* Top left orb */}
          <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-[#c541e0] rounded-full mix-blend-screen filter blur-[80px] animate-blob" />
          {/* Bottom right orb */}
          <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-[#e041b6] rounded-full mix-blend-screen filter blur-[80px] animate-blob animation-delay-2000" />
          {/* Center orb */}
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-[#c541e0] rounded-full mix-blend-screen filter blur-[80px] animate-blob animation-delay-4000" />
        </div>
      </div>

      {/* Main content */}
      <div className="relative z-10">
        {/* Navbar */}
        <nav className="w-full border-b border-white/5 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center gap-2">
                <CgWebsite className="w-8 h-8 text-[#c541e0]" />
                <span className="text-white/80 font-space-grotesk text-lg">Website Cloner</span>
              </div>
              <a
                href="https://github.com/kar722/Website-Cloning"
                target="_blank"
                rel="noopener noreferrer"
                className="text-white/60 hover:text-white transition-colors p-2 rounded-full hover:bg-white/5"
              >
                <FiGithub className="w-6 h-6" />
              </a>
            </div>
          </div>
        </nav>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center mb-20">
            <div className="flex items-center justify-center gap-4 mb-6">
              <CgWebsite className="w-16 h-16 text-[#c541e0] animate-float drop-shadow-[0_0_8px_rgba(197,65,224,0.5)]" />
              <h1 className="text-7xl font-bold tracking-tight relative">
                <span className="absolute inset-0 text-[#c541e0] blur-[2px] select-none" aria-hidden="true">
                  Website Cloner
                </span>
                <span className="absolute inset-0 text-[#e041b6] blur-[4px] select-none opacity-70" aria-hidden="true">
                  Website Cloner
                </span>
                <span className="relative text-[#c541e0] font-space-grotesk drop-shadow-[0_0_10px_rgba(197,65,224,0.3)]">
                  Website Cloner
                </span>
              </h1>
            </div>
            <p className="text-xl text-[#FFFFFF] max-w-2xl mx-auto font-space-grotesk mb-16">
              Enter any public website URL and get an AI-generated clone with similar
              aesthetics
            </p>

            <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
              <div className="flex flex-col sm:flex-row items-center gap-6">
                <TypewriterInput
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="w-full sm:max-w-xl px-6 py-5 rounded-2xl border border-white/10 bg-black/20 
                    backdrop-blur-xl text-white placeholder-gray-400 focus:ring-2 focus:ring-[#e041b6] 
                    focus:border-transparent transition-all text-lg focus:shadow-[0_0_20px_rgba(224,65,182,0.3)] 
                    hover:border-[#e041b6] hover:shadow-[0_0_15px_rgba(224,65,182,0.2)]
                    shadow-[0_4px_15px_rgba(0,0,0,0.1)] hover:shadow-[0_4px_20px_rgba(0,0,0,0.2)]
                    text-left"
                />
                <button
                  type="submit"
                  disabled={isLoading}
                  className="group h-[60px] px-8 bg-transparent hover:bg-gradient-to-r hover:from-[#e041b6] hover:to-[#c541e0]
                    text-white font-medium rounded-2xl transition-all duration-300 
                    disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-lg 
                    relative overflow-hidden border-2 border-[#c541e0] hover:border-transparent
                    shadow-[0_0_20px_rgba(224,65,182,0.2)] hover:shadow-[0_0_30px_rgba(224,65,182,0.4)]
                    sm:w-auto w-full justify-center whitespace-nowrap font-space-grotesk"
                >
                  {isLoading ? (
                    <div className="flex items-center gap-3">
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
                      <span className="animate-pulse">Processing...</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      Clone Website
                      <HiArrowRight className="w-5 h-5 transform transition-transform duration-300 group-hover:translate-x-1" />
                    </div>
                  )}
                </button>
              </div>
            </form>
          </div>

          <div className="bg-black/30 backdrop-blur-xl rounded-xl border border-white/10 
            shadow-[0_8px_32px_rgba(0,0,0,0.4)] p-8 transition-all duration-300 
            hover:shadow-[0_12px_40px_rgba(0,0,0,0.5)] relative">
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/[0.03] to-transparent"></div>
            <div className="relative">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-semibold text-white">
                  Preview
                </h2>
                {scrapedData && (
                  <button
                    className="text-[#e041b6] hover:text-[#c541e0] font-medium text-base transition-colors 
                      flex items-center gap-2 group bg-black/20 px-4 py-2 rounded-lg backdrop-blur-sm 
                      border border-white/5 hover:border-white/10"
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
                    <HiArrowRight className="w-4 h-4 transform transition-transform duration-300 group-hover:translate-x-1" />
                  </button>
                )}
              </div>
              <div className="border border-white/[0.05] rounded-xl p-6 min-h-[500px] 
                bg-black/40 backdrop-blur-sm transition-all duration-300 
                shadow-[inset_0_2px_15px_rgba(0,0,0,0.4)]">
                {renderPreview()}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
