"use client";

import { useState } from "react";
import Link from "next/link";

export default function UploadPage() {
  const [docId, setDocId] = useState<number | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleSubmit: React.FormEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    setError(null);
    setStatus(null);
    setDocId(null);

    const form = e.currentTarget;
    const fileInput = form.elements.namedItem("file") as HTMLInputElement;
    if (!fileInput.files?.length) {
      setError("Please choose a PDF file.");
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
      const res = await fetch("http://localhost:8000/documents", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      setDocId(data.document_id);
      setStatus(data.status);
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-start p-10 bg-gradient-to-br from-slate-100 to-slate-200">
      <div className="w-full max-w-xl bg-white rounded-2xl shadow-lg p-8 space-y-6 border border-slate-200">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-slate-900">Upload Article PDF</h1>
          <p className="text-base text-slate-600">
            Upload a PDF to automatically extract page-wise text blocks with coordinates.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-3">
            <label htmlFor="file-upload" className="block text-sm font-semibold text-slate-800">
              Select PDF File
            </label>
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
              <label
                htmlFor="file-upload"
                className="cursor-pointer px-6 py-3 bg-slate-700 text-white border-2 border-slate-700 rounded-lg text-sm font-semibold hover:bg-slate-800 hover:border-slate-800 transition shadow-sm"
              >
                📁 Choose File
              </label>
              <input
                id="file-upload"
                type="file"
                name="file"
                accept="application/pdf"
                onChange={handleFileChange}
                className="hidden"
              />
              <div className="flex-1 min-w-0">
                <span className="text-sm text-slate-700 font-medium block truncate">
                  {selectedFile ? selectedFile.name : "No file selected"}
                </span>
                {selectedFile && (
                  <p className="text-xs text-slate-500 mt-1">
                    Size: {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                )}
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !selectedFile}
            className="w-full px-6 py-4 rounded-lg bg-blue-600 text-white text-base font-semibold hover:bg-blue-700 active:bg-blue-800 transition shadow-md disabled:bg-slate-300 disabled:text-slate-500 disabled:cursor-not-allowed disabled:shadow-none"
          >
            {loading ? "⏳ Uploading & processing..." : "🚀 Upload & Process"}
          </button>
        </form>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {docId && (
          <div className="mt-6 p-6 bg-green-50 border border-green-200 rounded-lg space-y-4">
            <div className="flex items-start">
              <div className="flex-shrink-0 text-green-600 text-2xl mr-3">✓</div>
              <div className="flex-1">
                <p className="text-green-800 font-semibold text-lg mb-1">
                  Upload successful!
                </p>
                <div className="text-sm text-green-700 space-y-1">
                  <p>Document ID: <span className="font-mono">{docId}</span></p>
                  <p>Status: <span className="font-medium">{status}</span></p>
                </div>
              </div>
            </div>
            <Link
              href={`/documents/${docId}`}
              className="inline-block w-full text-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition shadow-sm"
            >
              View Extracted Content →
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
