"use client";

import { useState } from "react";

export default function UploadForm({ onUploadSuccess }: { onUploadSuccess: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/documents/", {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        setMessage("Upload successful!");
        setFile(null);
        // Reset file input
        const fileInput = document.getElementById("file-upload") as HTMLInputElement;
        if (fileInput) fileInput.value = "";
        
        onUploadSuccess();
      } else {
        const data = await res.json();
        setMessage(`Upload failed: ${data.detail}`);
      }
    } catch (error) {
      setMessage("Upload failed: Network error");
      console.error(error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white shadow sm:rounded-lg p-6">
      <h3 className="text-lg leading-6 font-medium text-gray-900">Upload Document</h3>
      <div className="mt-2 max-w-xl text-sm text-gray-500">
        <p>Upload a PDF or DOCX file to process.</p>
      </div>
      <form onSubmit={handleSubmit} className="mt-5 sm:flex sm:items-center">
        <div className="w-full sm:max-w-xs">
          <label htmlFor="file-upload" className="sr-only">
            Choose file
          </label>
          <input
            type="file"
            name="file-upload"
            id="file-upload"
            accept=".pdf,.docx"
            onChange={handleFileChange}
            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
          />
        </div>
        <button
          type="submit"
          disabled={!file || uploading}
          className={`mt-3 w-full inline-flex items-center justify-center px-4 py-2 border border-transparent shadow-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm ${
            (!file || uploading) ? "opacity-50 cursor-not-allowed" : ""
          }`}
        >
          {uploading ? "Uploading..." : "Upload"}
        </button>
      </form>
      {message && (
        <p className={`mt-2 text-sm ${message.includes("failed") ? "text-red-600" : "text-green-600"}`}>
          {message}
        </p>
      )}
    </div>
  );
}
