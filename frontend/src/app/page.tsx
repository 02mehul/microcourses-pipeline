"use client";

import { useState } from "react";

export default function UploadPage() {
  const [docId, setDocId] = useState<number | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit: React.FormEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    setError(null);
    setStatus(null);
    setDocId(null);
    setLoading(true);

    const form = e.currentTarget;
    const fileInput = form.elements.namedItem("file") as HTMLInputElement;
    if (!fileInput.files?.length) {
      setError("Please choose a PDF file.");
      setLoading(false);
      return;
    }

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
    <div className="min-h-screen flex flex-col items-center justify-start p-10 bg-slate-50">
      <div className="w-full max-w-xl bg-white rounded-2xl shadow p-8 space-y-6">
        <h1 className="text-2xl font-semibold">Upload Article PDF</h1>
        <p className="text-sm text-slate-600">
          Upload a PDF to automatically extract page-wise text blocks with coordinates.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="file"
            name="file"
            accept="application/pdf"
            className="block w-full text-sm"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 rounded-xl border border-slate-900 text-slate-900 text-sm hover:bg-slate-900 hover:text-white transition disabled:opacity-50"
          >
            {loading ? "Uploading & processing..." : "Upload & process"}
          </button>
        </form>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {docId && (
          <div className="mt-4 space-y-1 text-sm">
            <p className="font-medium">Document ID: {docId}</p>
            <p>Status: {status}</p>
            <p className="text-slate-600">
              Next: call <code>/documents/{docId}/blocks</code> from the UI to see extracted chunks.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
