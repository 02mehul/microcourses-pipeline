"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import SlideViewer from "@/components/SlideViewer";
import QuizViewer from "@/components/QuizViewer";

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

interface Question {
  id: number;
  question_text: string;
  answer_text: string;
  subchapter_id?: string;
  subchapter_title?: string;
}

interface DocumentDetail {
  id: number;
  filename: string;
  status: string;
  slides?: Slide[];
  questions?: Question[];
}

export default function DocumentDetails() {
  const params = useParams();
  const id = params.id;
  
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'slides' | 'quiz'>('slides');
  const pollInterval = useRef<NodeJS.Timeout | null>(null);

  const fetchDocument = async () => {
    try {
      const docRes = await fetch(`http://localhost:8000/documents/${id}`);
      if (docRes.ok) {
        const docData = await docRes.json();
        setDocument(docData);
        return docData;
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    return null;
  };

  useEffect(() => {
    if (!id) return;

    const initFetch = async () => {
      const doc = await fetchDocument();
      setLoading(false);

      // Start polling if status is not final
      if (doc && (doc.status === 'PENDING' || doc.status === 'RUNNING')) {
        pollInterval.current = setInterval(async () => {
          const updatedDoc = await fetchDocument();
          if (updatedDoc && (updatedDoc.status === 'SUCCESS' || updatedDoc.status === 'FAILED')) {
            if (pollInterval.current) clearInterval(pollInterval.current);
          }
        }, 2000);
      }
    };

    initFetch();

    return () => {
      if (pollInterval.current) clearInterval(pollInterval.current);
    };
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Document not found</h2>
        <Link href="/" className="text-indigo-600 hover:text-indigo-800">Return to Dashboard</Link>
      </div>
    );
  }

  // Processing State
  if (document.status === 'PENDING' || document.status === 'RUNNING') {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <div className="bg-white p-8 rounded-xl shadow-lg border border-gray-100 max-w-md w-full text-center">
          <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Generating Microcourse</h2>
          <p className="text-gray-500 mb-6">
            We are processing <strong>{document.filename}</strong>. This involves extracting content, generating slides, and creating review questions.
          </p>
          <div className="w-full bg-gray-100 rounded-full h-2 mb-2">
            <div className="bg-indigo-600 h-2 rounded-full animate-pulse w-2/3 mx-auto"></div>
          </div>
          <p className="text-xs text-gray-400">This may take a minute...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="flex items-center space-x-2 text-sm text-gray-500 mb-1">
                <Link href="/" className="hover:text-gray-900">Dashboard</Link>
                <span>/</span>
                <span>Documents</span>
              </div>
              <h1 className="text-2xl font-bold text-gray-900">{document.filename}</h1>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              document.status === 'SUCCESS' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
            }`}>
              {document.status}
            </span>
          </div>

          {/* Tabs */}
          <div className="flex space-x-8 border-b border-gray-200 -mb-px">
            <button
              onClick={() => setActiveTab('slides')}
              className={`pb-4 text-sm font-medium transition-colors border-b-2 ${
                activeTab === 'slides'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Generated Slides
            </button>
            <button
              onClick={() => setActiveTab('quiz')}
              className={`pb-4 text-sm font-medium transition-colors border-b-2 ${
                activeTab === 'quiz'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Review Quiz
            </button>
          </div>
        </div>
      </div>

      <div className="w-full px-4 sm:px-6 lg:px-8 py-8">

        {/* Tab Content */}
        {activeTab === 'slides' && (
          <div className="w-full">
            <SlideViewer slides={document.slides || []} />
          </div>
        )}

        {activeTab === 'quiz' && (
          <div className="max-w-3xl mx-auto">
            <QuizViewer questions={document.questions || []} />
          </div>
        )}

      </div>
    </div>
  );
}
