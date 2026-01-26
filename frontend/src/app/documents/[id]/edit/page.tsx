"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

export default function EditRawDocument() {
  const params = useParams();
  const router = useRouter();
  const id = params.id;
  
  const [rawMarkdown, setRawMarkdown] = useState<string>("");
  const [originalMarkdown, setOriginalMarkdown] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filename, setFilename] = useState<string>("");

  useEffect(() => {
    if (!id) return;

    const fetchData = async () => {
      try {
        // Fetch document details
        const docRes = await fetch(`http://localhost:8000/documents/${id}`);
        if (!docRes.ok) throw new Error("Document not found");
        const docData = await docRes.json();
        setFilename(docData.filename);

        // Fetch raw markdown
        const rawRes = await fetch(`http://localhost:8000/documents/${id}/raw`);
        if (!rawRes.ok) throw new Error("Failed to fetch raw markdown");
        const rawData = await rawRes.json();
        setRawMarkdown(rawData.raw_markdown || "");
        setOriginalMarkdown(rawData.raw_markdown || "");
      } catch (err) {
        console.error("Error:", err);
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const handleSaveAndReprocess = async () => {
    if (!rawMarkdown.trim()) {
      setError("Markdown content cannot be empty");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const res = await fetch(`http://localhost:8000/documents/${id}/raw`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_markdown: rawMarkdown }),
      });

      if (!res.ok) {
        throw new Error("Failed to save and reprocess");
      }

      // Redirect to document view - it will show processing status
      router.push(`/documents/${id}`);
    } catch (err) {
      console.error("Save error:", err);
      setError(err instanceof Error ? err.message : "Failed to save");
      setSaving(false);
    }
  };

  const hasChanges = rawMarkdown !== originalMarkdown;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading document...</p>
        </div>
      </div>
    );
  }

  if (error && !rawMarkdown) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center text-red-600">
          <p className="text-xl font-semibold">Error</p>
          <p>{error}</p>
          <Link href="/" className="mt-4 inline-block text-blue-600 hover:underline">
            ← Back to Documents
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href={`/documents/${id}`} className="text-gray-500 hover:text-gray-700">
              ← Back
            </Link>
            <h1 className="text-xl font-semibold text-gray-900 truncate max-w-md">
              Edit: {filename}
            </h1>
            {hasChanges && (
              <span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                Unsaved changes
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <Link
              href={`/documents/${id}`}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </Link>
            <button
              onClick={handleSaveAndReprocess}
              disabled={saving || !hasChanges}
              className={`px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors flex items-center gap-2 ${
                saving || !hasChanges
                  ? "bg-gray-300 cursor-not-allowed"
                  : "bg-indigo-600 hover:bg-indigo-700"
              }`}
            >
              {saving ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Saving...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Save & Reprocess
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Editor */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200 bg-gray-50 rounded-t-lg">
            <h2 className="text-sm font-medium text-gray-700">Raw Markdown Content</h2>
            <p className="text-xs text-gray-500 mt-1">
              Edit the parsed markdown below. Saving will regenerate all slides and questions.
            </p>
          </div>
          <textarea
            value={rawMarkdown}
            onChange={(e) => setRawMarkdown(e.target.value)}
            className="w-full h-[calc(100vh-280px)] p-4 font-mono text-sm text-gray-800 bg-white border-0 focus:ring-0 focus:outline-none resize-none"
            placeholder="Markdown content will appear here..."
            spellCheck={false}
          />
        </div>

        <div className="mt-4 text-sm text-gray-500">
          <p>
            <strong>Note:</strong> Editing this content will trigger a full reprocessing of the document. 
            All existing slides and questions will be regenerated based on the new content.
          </p>
        </div>
      </main>
    </div>
  );
}
