"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import SlideEditor from "@/components/SlideEditor";
import QuizViewer from "@/components/QuizViewer";
import ChatAssistant from "@/components/ChatAssistant";
import SummaryViewer from "@/components/SummaryViewer";

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

interface DocumentDetail {
  id: number;
  filename: string;
  status: string;
  status_message?: string | null;
  slides?: Slide[];
  questions?: Question[];
  summary?: DocumentSummary | null;
}

export default function DocumentDetails() {
  const params = useParams();
  const id = params.id;

  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'summary' | 'slides' | 'quiz' | 'chat'>('summary');
  const pollInterval = useRef<NodeJS.Timeout | null>(null);

  const fetchDocument = async () => {
    try {
      const docRes = await fetch(`http://localhost:8000/documents/${id}`);
      if (docRes.ok) {
        const docData = await docRes.json();
        setDoc(docData);
        return docData;
      } else {
        setError("Failed to fetch document");
      }
    } catch (err) {
      console.error("Error fetching data:", err);
      setError("An error occurred while fetching the document");
    }
    return null;
  };

  const handleSaveSlide = async (slideId: number, updatedSlide: Partial<Slide>) => {
    try {
      const res = await fetch(`http://localhost:8000/documents/slides/${slideId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatedSlide),
      });

      if (res.ok) {
        // Optimistic update or refetch
        setDoc(prev => {
          if (!prev || !prev.slides) return prev;
          return {
            ...prev,
            slides: prev.slides.map(slide =>
              slide.id === slideId ? { ...slide, ...updatedSlide } : slide
            )
          };
        });
      } else {
        throw new Error("Failed to update slide");
      }
    } catch (error) {
      console.error("Error updating slide:", error);
      throw error;
    }
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
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading document...</p>
        </div>
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center text-red-600">
          <p className="text-xl font-semibold">Error</p>
          <p>{error || "Document not found"}</p>
          <Link href="/" className="mt-4 inline-block text-blue-600 hover:underline">
            ← Back to Documents
          </Link>
        </div>
      </div>
    );
  }

  // Processing State
  if (doc.status === 'PENDING' || doc.status === 'RUNNING') {
    const getProgressStep = (statusMessage: string | null | undefined) => {
      if (!statusMessage) return { step: 1, total: 4 };
      if (statusMessage.includes('Extracting')) return { step: 1, total: 4 };
      if (statusMessage.includes('Generating slides')) return { step: 2, total: 4 };
      if (statusMessage.includes('Creating review questions')) return { step: 3, total: 4 };
      if (statusMessage.includes('Building summary')) return { step: 4, total: 4 };
      return { step: 1, total: 4 };
    };

    const progress = getProgressStep(doc.status_message);
    const progressPercentage = (progress.step / progress.total) * 100;

    const steps = [
      { label: 'Extracting content', icon: '📄' },
      { label: 'Generating slides', icon: '📊' },
      { label: 'Creating questions', icon: '❓' },
      { label: 'Building summary', icon: '✨' },
    ];

    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <div className="bg-white p-8 rounded-xl shadow-lg border border-gray-100 max-w-2xl w-full">
          <div className="text-center mb-6">
            <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-900 mb-2">Generating Microcourse</h2>
            <p className="text-gray-500 mb-2">
              Processing <strong>{doc.filename}</strong>
            </p>
            {doc.status_message && (
              <p className="text-sm text-indigo-600 font-medium">{doc.status_message}</p>
            )}
          </div>

          {/* Progress Steps */}
          <div className="space-y-3 mb-6">
            {steps.map((step, index) => {
              const isCompleted = index + 1 < progress.step;
              const isCurrent = index + 1 === progress.step;
              const isPending = index + 1 > progress.step;

              return (
                <div
                  key={index}
                  className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                    isCurrent ? 'bg-indigo-50 border border-indigo-200' :
                    isCompleted ? 'bg-green-50 border border-green-200' :
                    'bg-gray-50 border border-gray-200'
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      isCurrent ? 'bg-indigo-600 text-white' :
                      isCompleted ? 'bg-green-600 text-white' :
                      'bg-gray-300 text-gray-600'
                    }`}
                  >
                    {isCompleted ? '✓' : step.icon}
                  </div>
                  <span
                    className={`text-sm font-medium ${
                      isCurrent ? 'text-indigo-900' :
                      isCompleted ? 'text-green-900' :
                      'text-gray-500'
                    }`}
                  >
                    {step.label}
                  </span>
                  {isCurrent && (
                    <div className="ml-auto">
                      <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progressPercentage}%` }}
            ></div>
          </div>
          <p className="text-xs text-gray-500 text-center">
            Step {progress.step} of {progress.total} • This may take a minute...
          </p>
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
            <Link href="/" className="text-gray-500 hover:text-gray-700">
              ← Back
            </Link>
            <h1 className="text-xl font-semibold text-gray-900 truncate max-w-md">
              {doc.filename}
            </h1>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              doc.status === 'SUCCESS' ? 'bg-green-100 text-green-800' :
              doc.status === 'FAILED' ? 'bg-red-100 text-red-800' :
              'bg-yellow-100 text-yellow-800'
            }`}>
              {doc.status}
            </span>
          </div>
        </div>

        {/* Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('summary')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'summary'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Summary
            </button>
            <button
              onClick={() => setActiveTab('slides')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'slides'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Generated Slides
            </button>
            <button
              onClick={() => setActiveTab('quiz')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'quiz'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Review Quiz
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'chat'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Teaching Assistant
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'summary' && (
          <div className="max-w-6xl mx-auto">
            <SummaryViewer summary={doc.summary} documentId={doc.id} />
          </div>
        )}

        {activeTab === 'slides' && (
          <SlideEditor
            slides={doc.slides || []}
            onSaveSlide={handleSaveSlide}
          />
        )}

        {activeTab === 'quiz' && (
          <div className="max-w-3xl mx-auto">
            <QuizViewer questions={doc.questions || []} />
          </div>
        )}

        {activeTab === 'chat' && (
          <div className="max-w-4xl mx-auto">
            <ChatAssistant documentId={doc.id} />
          </div>
        )}
      </main>
    </div>
  );
}
