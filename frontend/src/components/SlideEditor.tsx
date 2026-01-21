import { useState, useEffect } from "react";
import { ChevronLeft, ChevronRight, Save, Edit2, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChartRenderer } from "./ChartRenderer";

interface TableData {
  headers: string[];
  rows: string[][];
  caption?: string;
}

interface VisualizationData {
  type: 'chart' | 'table';
  chart_type?: 'line' | 'bar' | 'pie';
  data: any;
  title?: string;
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
  visualization_data?: VisualizationData | null;
}

interface SlideEditorProps {
  slides: Slide[];
  onSaveSlide: (slideId: number, updatedSlide: Partial<Slide>) => Promise<void>;
}

export default function SlideEditor({ slides, onSaveSlide }: SlideEditorProps) {
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [isEditing, setIsEditing] = useState(false);
  const [editedSlide, setEditedSlide] = useState<Slide | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  if (!slides || slides.length === 0) {
    return <div className="text-gray-500 italic">No slides generated yet.</div>;
  }

  const currentSlide = slides[currentSlideIndex];

  useEffect(() => {
    setEditedSlide(currentSlide);
    setIsEditing(false);
  }, [currentSlideIndex, slides]);

  const nextSlide = () => {
    if (isEditing) {
        if (!confirm("You have unsaved changes. Discard them?")) return;
    }
    setCurrentSlideIndex((prev) => (prev + 1) % slides.length);
  };

  const prevSlide = () => {
    if (isEditing) {
        if (!confirm("You have unsaved changes. Discard them?")) return;
    }
    setCurrentSlideIndex((prev) => (prev - 1 + slides.length) % slides.length);
  };

  const handleSave = async () => {
    if (!editedSlide) return;
    setIsSaving(true);
    try {
      await onSaveSlide(editedSlide.id, {
        title: editedSlide.title,
        subheading: editedSlide.subheading,
        summary: editedSlide.summary,
      });
      setIsEditing(false);
    } catch (error) {
      console.error("Failed to save slide:", error);
      alert("Failed to save changes.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditedSlide(currentSlide);
    setIsEditing(false);
  };

  // Parse summary for display
  const parseSummary = (summary: string): string[] => {
    try {
      const parsed = JSON.parse(summary);
      if (Array.isArray(parsed)) {
        return parsed.filter(item => typeof item === 'string' && item.trim());
      }
    } catch (e) {
      // Not JSON
    }
    return summary
      .split('\n')
      .map(line => line.replace(/^[-*]\s*/, '').trim())
      .filter(line => line.length > 0);
  };

  const summaryPoints = parseSummary(currentSlide.summary);

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
      {/* Toolbar */}
      <div className="bg-gray-50 px-6 py-3 border-b border-gray-200 flex justify-between items-center">
        <div className="text-sm text-gray-500 font-medium">
          Slide {currentSlideIndex + 1} of {slides.length}
        </div>
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <button
                onClick={handleCancel}
                disabled={isSaving}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <X className="w-4 h-4" />
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                {isSaving ? "Saving..." : "Save Changes"}
              </button>
            </>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-indigo-600 bg-indigo-50 border border-indigo-100 rounded-lg hover:bg-indigo-100"
            >
              <Edit2 className="w-4 h-4" />
              Edit Slide
            </button>
          )}
        </div>
      </div>

      {/* Slide Content */}
      <div className="p-4 sm:py-2 sm:px-4 bg-linear-to-br from-white to-indigo-50/30 min-h-[500px] flex flex-col">
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
          <div className="mb-6 space-y-3">
            {isEditing ? (
              <>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Title</label>
                  <input
                    type="text"
                    value={editedSlide?.title || ""}
                    onChange={(e) => setEditedSlide(prev => prev ? ({ ...prev, title: e.target.value }) : null)}
                    className="w-full text-2xl font-bold text-indigo-900 border-b-2 border-indigo-200 focus:border-indigo-600 outline-none bg-transparent px-1 py-0.5"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Subheading</label>
                  <input
                    type="text"
                    value={editedSlide?.subheading || ""}
                    onChange={(e) => setEditedSlide(prev => prev ? ({ ...prev, subheading: e.target.value }) : null)}
                    className="w-full text-lg text-indigo-600 font-medium border-b-2 border-indigo-200 focus:border-indigo-600 outline-none bg-transparent px-1 py-0.5"
                  />
                </div>
              </>
            ) : (
              <>
                <h2 className="text-2xl sm:text-3xl font-bold text-indigo-900 mb-2 leading-tight">
                  {currentSlide.title}
                </h2>
                {currentSlide.subheading && (
                  <h3 className="text-base sm:text-lg text-indigo-600 font-medium">
                    {currentSlide.subheading}
                  </h3>
                )}
              </>
            )}
          </div>

          {/* Content: Key Points + Optional Visualization (Chart or Table) */}
          <div className={`grid gap-5 ${currentSlide.visualization_data ? 'lg:grid-cols-2' : 'grid-cols-1'}`}>
            {/* Key Points */}
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                Key Points
              </h4>

              {isEditing ? (
                <div className="space-y-2">
                  <label className="block text-xs text-gray-400">Edit content (Markdown supported)</label>
                  <textarea
                    value={editedSlide?.summary || ""}
                    onChange={(e) => setEditedSlide(prev => prev ? ({ ...prev, summary: e.target.value }) : null)}
                    className="w-full h-64 p-3 text-sm text-gray-700 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                  />
                </div>
              ) : (
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
              )}
            </div>

            {/* Visualization: Chart or Table (if present) */}
            {currentSlide.visualization_data && (
              <div>
                {currentSlide.visualization_data.type === 'chart' && currentSlide.visualization_data.chart_type ? (
                  <ChartRenderer
                    data={currentSlide.visualization_data.data}
                    type={currentSlide.visualization_data.chart_type}
                    title={currentSlide.visualization_data.title}
                  />
                ) : currentSlide.visualization_data.type === 'table' ? (
                  <div>
                    {currentSlide.visualization_data.title && (
                      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                        {currentSlide.visualization_data.title}
                      </h4>
                    )}
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg text-sm">
                        <thead className="bg-indigo-50">
                          <tr>
                            {currentSlide.visualization_data.data.headers?.map((header: string, idx: number) => (
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
                          {currentSlide.visualization_data.data.rows?.map((row: string[], rowIdx: number) => (
                            <tr key={rowIdx} className={rowIdx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                              {row.map((cell: string, cellIdx: number) => (
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
                ) : null}
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
          {/* Progress dots */}
          <div className="flex gap-1.5">
            {slides.map((_, idx) => (
              <button
                key={idx}
                onClick={() => {
                    if (isEditing) {
                        if (!confirm("You have unsaved changes. Discard them?")) return;
                    }
                    setCurrentSlideIndex(idx);
                }}
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
