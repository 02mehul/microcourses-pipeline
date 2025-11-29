import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface TableData {
  headers: string[];
  rows: string[][];
  caption?: string;
}

interface Slide {
  id: number;
  slide_number: number;
  title: string;
  subheading: string;
  summary: string;
  content_chunk: string;
  chapter_title?: string;
  subchapter_title?: string;
  subchapter_id?: string;
  table_data?: TableData | null;
  has_table?: boolean;
}

interface SlideViewerProps {
  slides: Slide[];
}

export default function SlideViewer({ slides }: SlideViewerProps) {
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);

  if (!slides || slides.length === 0) {
    return <div className="text-gray-500 italic">No slides generated yet.</div>;
  }

  const currentSlide = slides[currentSlideIndex];

  const nextSlide = () => {
    setCurrentSlideIndex((prev) => (prev + 1) % slides.length);
  };

  const prevSlide = () => {
    setCurrentSlideIndex((prev) => (prev - 1 + slides.length) % slides.length);
  };

  // Parse summary - handle both JSON array strings and plain text
  const parseSummary = (summary: string): string[] => {
    try {
      // Try to parse as JSON first
      const parsed = JSON.parse(summary);
      if (Array.isArray(parsed)) {
        return parsed.filter(item => typeof item === 'string' && item.trim());
      }
    } catch (e) {
      // Not JSON, treat as plain text
    }

    // Fall back to splitting by newlines
    return summary
      .split('\n')
      .map(line => line.replace(/^[-*]\s*/, '').trim())
      .filter(line => line.length > 0);
  };

  const summaryPoints = parseSummary(currentSlide.summary);

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
      {/* Slide Content */}
      <div className="p-6 sm:p-10 bg-gradient-to-br from-white to-indigo-50/30 min-h-[750px] flex flex-col">
        <div className="w-full flex-1 flex flex-col justify-center px-4 sm:px-8">
          {/* Chapter/Subchapter Context */}
          {(currentSlide.chapter_title || currentSlide.subchapter_title) && (
            <div className="mb-3 pb-2 border-b border-indigo-200">
              {currentSlide.chapter_title && (
                <div className="text-xs text-indigo-700 font-medium">
                  {currentSlide.chapter_title}
                </div>
              )}
              {currentSlide.subchapter_title && (
                <div className="text-xs text-indigo-500 mt-0.5">
                  {currentSlide.subchapter_title}
                </div>
              )}
            </div>
          )}

          {/* Title and Subheading */}
          <div className="mb-6">
            <h2 className="text-2xl sm:text-3xl font-bold text-indigo-900 mb-2 leading-tight">
              {currentSlide.title}
            </h2>
            {currentSlide.subheading && (
              <h3 className="text-base sm:text-lg text-indigo-600 font-medium">
                {currentSlide.subheading}
              </h3>
            )}
          </div>

          {/* Content: Key Points + Optional Table */}
          <div className={`grid gap-5 ${currentSlide.has_table && currentSlide.table_data ? 'lg:grid-cols-2' : 'grid-cols-1'}`}>
            {/* Key Points */}
            <div className="bg-white p-5 sm:p-6 rounded-lg shadow-sm border border-gray-100">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                Key Points
              </h4>
              <div className="prose prose-sm prose-indigo max-w-none">
                <ul className="space-y-2 text-gray-700">
                  {summaryPoints.map((point, idx) => (
                    <li key={idx} className="leading-relaxed text-sm">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {point}
                      </ReactMarkdown>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Table (if present) */}
            {currentSlide.has_table && currentSlide.table_data && (
              <div className="bg-white p-5 sm:p-6 rounded-lg shadow-sm border border-gray-100">
                {currentSlide.table_data.caption && (
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                    {currentSlide.table_data.caption}
                  </h4>
                )}
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg text-sm">
                    <thead className="bg-indigo-50">
                      <tr>
                        {currentSlide.table_data.headers.map((header, idx) => (
                          <th
                            key={idx}
                            className="px-3 py-2 text-left text-xs font-semibold text-indigo-900 uppercase tracking-wider"
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {currentSlide.table_data.rows.map((row, rowIdx) => (
                        <tr key={rowIdx} className={rowIdx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                          {row.map((cell, cellIdx) => (
                            <td
                              key={cellIdx}
                              className="px-3 py-2 text-xs text-gray-700"
                            >
                              {cell}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Navigation Controls */}
      <div className="bg-gray-50 border-t border-gray-200 px-6 py-4 flex items-center justify-between">
        <button
          onClick={prevSlide}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
            slides.length <= 1 || currentSlideIndex === 0
              ? "text-gray-300 cursor-not-allowed"
              : "text-gray-700 hover:bg-gray-200 hover:shadow-sm"
          }`}
          disabled={slides.length <= 1}
        >
          <ChevronLeft className="w-5 h-5" />
          <span className="hidden sm:inline text-sm font-medium">Previous</span>
        </button>

        <div className="flex flex-col items-center gap-1">
          <span className="text-sm font-medium text-gray-600">
            Slide {currentSlideIndex + 1} of {slides.length}
          </span>
          {/* Progress dots */}
          <div className="flex gap-1.5">
            {slides.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentSlideIndex(idx)}
                className={`h-2 rounded-full transition-all ${
                  idx === currentSlideIndex
                    ? "w-8 bg-indigo-600"
                    : "w-2 bg-gray-300 hover:bg-gray-400"
                }`}
                aria-label={`Go to slide ${idx + 1}`}
              />
            ))}
          </div>
        </div>

        <button
          onClick={nextSlide}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
            slides.length <= 1 || currentSlideIndex === slides.length - 1
              ? "text-gray-300 cursor-not-allowed"
              : "text-gray-700 hover:bg-gray-200 hover:shadow-sm"
          }`}
          disabled={slides.length <= 1}
        >
          <span className="hidden sm:inline text-sm font-medium">Next</span>
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
