"use client";

import { useState } from "react";
import DocumentList from "../components/DocumentList";
import DragDropUpload from "../components/DragDropUpload";

export default function Home() {
  // Key to force re-render of list after upload
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = () => {
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 text-gray-900">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl mb-4">
            Transform Your Documents
          </h1>
          <p className="max-w-2xl mx-auto text-xl text-gray-500">
            Upload PDFs or Word documents to extract structured content for micro-courses.
          </p>
        </div>

        <DragDropUpload onUploadSuccess={handleUploadSuccess} />
        
        {/* Pass key to force refresh when upload happens */}
        <div key={refreshKey}>
            <DocumentList />
        </div>
      </main>
    </div>
  );
}
