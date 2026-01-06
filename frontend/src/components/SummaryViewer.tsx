"use client";

import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import {
  FileText,
  Target,
  Lightbulb,
  RefreshCw,
  BookOpen,
} from "lucide-react";
import { toast } from "sonner";
import ConfirmDialog from "./ConfirmDialog";

interface DocumentStats {
  word_count: number;
  reading_time_minutes: number;
  page_count: number;
  complexity_score: number;
  block_count: number;
  table_count: number;
  image_count: number;
}

interface KeyConcept {
  name: string;
  importance: number;
  frequency: number;
  category?: string;
}

interface TopicDistribution {
  section: string;
  topic: string;
  weight: number;
}

interface DocumentSummary {
  id: number;
  document_id: number;
  executive_summary?: string;
  stats?: DocumentStats;
  key_concepts: KeyConcept[];
  topic_distribution: TopicDistribution[];
  main_takeaways: string[];
  learning_objectives: string[];
  created_at?: string;
}

interface SummaryViewerProps {
  summary?: DocumentSummary | null;
  documentId: number;
}

const CHART_COLORS = [
  "#6366f1", // Indigo
  "#8b5cf6", // Violet
  "#a855f7", // Purple
  "#d946ef", // Fuchsia
  "#ec4899", // Pink
  "#f43f5e", // Rose
  "#10b981", // Emerald
  "#14b8a6", // Teal
];

export default function SummaryViewer({
  summary,
  documentId,
}: SummaryViewerProps) {
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [regenerateDialogOpen, setRegenerateDialogOpen] = useState(false);

  const handleRegenerateClick = () => {
    setRegenerateDialogOpen(true);
  };

  const confirmRegenerate = async () => {
    setIsRegenerating(true);

    const regeneratePromise = fetch(
      `http://localhost:8000/documents/${documentId}/summary/regenerate`,
      {
        method: "POST",
      }
    ).then(async (res) => {
      if (!res.ok) throw new Error("Failed to regenerate");

      // Poll for updated summary without full page reload
      const pollForSummary = async (attempts = 0, maxAttempts = 15): Promise<void> => {
        if (attempts >= maxAttempts) {
          throw new Error("Summary regeneration timed out");
        }

        try {
          const response = await fetch(
            `http://localhost:8000/documents/${documentId}/summary`
          );
          if (response.ok) {
            // Summary is ready, reload the page to fetch fresh data
            window.location.reload();
          } else {
            // Not ready yet, try again
            await new Promise((resolve) => setTimeout(resolve, 2000));
            return pollForSummary(attempts + 1, maxAttempts);
          }
        } catch (err) {
          // Retry on error
          await new Promise((resolve) => setTimeout(resolve, 2000));
          return pollForSummary(attempts + 1, maxAttempts);
        }
      };

      // Start polling after a short delay
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await pollForSummary();
    });

    toast.promise(regeneratePromise, {
      loading: "Regenerating summary...",
      success: "Summary regenerated successfully",
      error: "Failed to regenerate summary",
    });
  };

  if (!summary) {
    return (
      <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8 text-center">
        <div className="max-w-md mx-auto">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No Summary Available
          </h3>
          <p className="text-gray-500 mb-6">
            The summary for this document hasn&apos;t been generated yet. Click
            below to generate it now.
          </p>
          <button
            onClick={handleRegenerateClick}
            disabled={isRegenerating}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isRegenerating ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                Generate Summary
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  const keyConcepts = summary.key_concepts || [];

  return (
    <div className="space-y-6">
      {/* Header with Regenerate Button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-indigo-600" />
            Document Summary
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            AI-generated overview and key insights
          </p>
        </div>
        <button
          onClick={handleRegenerateClick}
          disabled={isRegenerating}
          className="inline-flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw
            className={`w-4 h-4 ${isRegenerating ? "animate-spin" : ""}`}
          />
          {isRegenerating ? "Regenerating..." : "Regenerate"}
        </button>
      </div>

      {/* Executive Summary */}
      {summary.executive_summary && (
        <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl border border-indigo-100 p-6">
          <h3 className="text-sm font-semibold text-indigo-900 uppercase tracking-wider mb-3 flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Executive Summary
          </h3>
          <p className="text-gray-700 leading-relaxed text-lg">
            {summary.executive_summary}
          </p>
        </div>
      )}

      {/* Key Concepts Chart - Full Width */}
      {keyConcepts.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Target className="w-4 h-4 text-indigo-600" />
            Key Concepts by Importance
          </h3>
          <div className="h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={keyConcepts}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  type="number"
                  domain={[0, 100]}
                  tickFormatter={(v) => `${v}%`}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={95}
                  tick={{ fontSize: 13 }}
                />
                <Tooltip
                  formatter={(value: number | undefined) => [
                    `${value?.toFixed(0) ?? 0}%`,
                    "Importance",
                  ]}
                  contentStyle={{
                    backgroundColor: "white",
                    border: "1px solid #e5e7eb",
                    borderRadius: "8px",
                  }}
                />
                <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                  {keyConcepts.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Takeaways and Objectives */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Main Takeaways */}
        {summary.main_takeaways && summary.main_takeaways.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-amber-500" />
              Key Takeaways
            </h3>
            <ul className="space-y-3">
              {summary.main_takeaways.map((takeaway: string, index: number) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="shrink-0 w-6 h-6 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center text-xs font-bold">
                    {index + 1}
                  </span>
                  <p className="text-gray-700 leading-relaxed">{takeaway}</p>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Learning Objectives */}
        {summary.learning_objectives &&
          summary.learning_objectives.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4 flex items-center gap-2">
                <Target className="w-4 h-4 text-emerald-500" />
                Learning Objectives
              </h3>
              <ul className="space-y-3">
                {summary.learning_objectives.map(
                  (objective: string, index: number) => (
                    <li key={index} className="flex items-start gap-3">
                      <span className="shrink-0 w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center">
                        <svg
                          className="w-3.5 h-3.5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      </span>
                      <p className="text-gray-700 leading-relaxed">
                        {objective}
                      </p>
                    </li>
                  )
                )}
              </ul>
            </div>
          )}
      </div>

      <ConfirmDialog
        isOpen={regenerateDialogOpen}
        onClose={() => setRegenerateDialogOpen(false)}
        onConfirm={confirmRegenerate}
        title="Regenerate Summary"
        message="Are you sure you want to regenerate the summary? This will replace the current summary with a new AI-generated version."
        confirmText="Regenerate"
        cancelText="Cancel"
        variant="warning"
      />
    </div>
  );
}
