"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface Bbox {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

interface Block {
  id: number;
  page_id: number;
  page_number: number;
  type: string;
  bbox: Bbox;
  text_raw: string;
  ocr_used: boolean;
}

interface Page {
  id: number;
  page_number: number;
  width: number;
  height: number;
  blocks: Block[];
}

interface Document {
  id: number;
  filename: string;
  storage_path: string;
  checksum: string;
  status: string;
  created_at: string;
  pages: Page[];
}

export default function DocumentDetailPage() {
  const params = useParams();
  const [doc, setDoc] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`http://localhost:8000/documents/${params.id}`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        return res.json();
      })
      .then((data) => setDoc(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-4 text-slate-600">Loading document...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="max-w-md w-full bg-white rounded-lg shadow p-8 text-center">
          <div className="text-red-600 text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold mb-2">Error Loading Document</h2>
          <p className="text-sm text-slate-600 mb-6">{error}</p>
          <Link
            href="/"
            className="inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            ← Back to Upload
          </Link>
        </div>
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <p className="text-slate-600">Document not found</p>
          <Link
            href="/"
            className="inline-block mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            ← Back to Upload
          </Link>
        </div>
      </div>
    );
  }

  const totalBlocks = doc.pages.reduce((sum, page) => sum + page.blocks.length, 0);

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header with back button */}
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center text-sm text-blue-600 hover:text-blue-700 mb-4"
          >
            ← Back to Upload
          </Link>
        </div>

        {/* Document metadata card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h1 className="text-2xl font-bold text-slate-900 mb-4">{doc.filename}</h1>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <span className="text-sm text-slate-500">Status:</span>
              <span
                className={`ml-2 px-3 py-1 rounded-full text-sm font-medium ${
                  doc.status === "SUCCESS"
                    ? "bg-green-100 text-green-800"
                    : doc.status === "FAILED"
                    ? "bg-red-100 text-red-800"
                    : doc.status === "RUNNING"
                    ? "bg-yellow-100 text-yellow-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {doc.status}
              </span>
            </div>

            <div>
              <span className="text-sm text-slate-500">Document ID:</span>
              <span className="ml-2 font-mono text-sm text-slate-700">{doc.id}</span>
            </div>

            <div>
              <span className="text-sm text-slate-500">Pages:</span>
              <span className="ml-2 font-semibold text-slate-900">{doc.pages.length}</span>
            </div>

            <div>
              <span className="text-sm text-slate-500">Total Blocks:</span>
              <span className="ml-2 font-semibold text-slate-900">{totalBlocks}</span>
            </div>

            <div>
              <span className="text-sm text-slate-500">Uploaded:</span>
              <span className="ml-2 text-sm text-slate-700">
                {new Date(doc.created_at).toLocaleString()}
              </span>
            </div>

            <div>
              <span className="text-sm text-slate-500">Checksum:</span>
              <span className="ml-2 font-mono text-xs text-slate-600">{doc.checksum}</span>
            </div>
          </div>
        </div>

        {/* Pages list */}
        {doc.status === "SUCCESS" && doc.pages.length > 0 ? (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Extracted Content</h2>
            {doc.pages.map((page) => (
              <PageSection key={page.id} page={page} />
            ))}
          </div>
        ) : doc.status === "RUNNING" ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <p className="text-yellow-800">Document is currently being processed...</p>
            <p className="text-sm text-yellow-600 mt-2">Refresh the page in a few moments.</p>
          </div>
        ) : doc.status === "FAILED" ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-800">Processing failed for this document.</p>
            <p className="text-sm text-red-600 mt-2">Please try uploading again.</p>
          </div>
        ) : (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
            <p className="text-gray-600">No content extracted yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function PageSection({ page }: { page: Page }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 text-left font-semibold text-slate-900 hover:bg-slate-50 transition flex justify-between items-center"
      >
        <span>
          Page {page.page_number} - {page.blocks.length} block{page.blocks.length !== 1 ? "s" : ""}
        </span>
        <span className="text-slate-400">{expanded ? "▼" : "▶"}</span>
      </button>

      {expanded && (
        <div className="p-4 border-t border-slate-200 bg-slate-50">
          <div className="text-xs text-slate-500 mb-4">
            Dimensions: {page.width.toFixed(1)} × {page.height.toFixed(1)} pts
          </div>

          {page.blocks.length > 0 ? (
            <div className="space-y-3">
              {page.blocks.map((block) => (
                <BlockItem key={block.id} block={block} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500 italic">No blocks extracted from this page.</p>
          )}
        </div>
      )}
    </div>
  );
}

function BlockItem({ block }: { block: Block }) {
  const [showFull, setShowFull] = useState(false);
  const isTruncated = block.text_raw.length > 200;
  const displayText = showFull || !isTruncated ? block.text_raw : block.text_raw.substring(0, 200) + "...";

  return (
    <div className="border-l-4 border-blue-500 pl-4 py-2 bg-white rounded-r">
      <div className="text-xs text-slate-500 mb-2 flex flex-wrap gap-x-4 gap-y-1">
        <span>
          <strong>Block #{block.id}</strong>
        </span>
        <span>Type: {block.type}</span>
        <span>
          BBox: ({block.bbox.x0.toFixed(3)}, {block.bbox.y0.toFixed(3)}) → (
          {block.bbox.x1.toFixed(3)}, {block.bbox.y1.toFixed(3)})
        </span>
        {block.ocr_used && (
          <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium">
            OCR
          </span>
        )}
      </div>

      <p className="text-sm text-slate-800 whitespace-pre-wrap">{displayText}</p>

      {isTruncated && (
        <button
          onClick={() => setShowFull(!showFull)}
          className="text-xs text-blue-600 hover:text-blue-700 mt-2 font-medium"
        >
          {showFull ? "Show less" : "Show more"}
        </button>
      )}
    </div>
  );
}
