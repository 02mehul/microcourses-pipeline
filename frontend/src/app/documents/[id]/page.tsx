"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

interface Block {
  page: number;
  type: string;
  semantic_role: string;
  hierarchy_level: number | null;
  text: string;
  bbox: any;
  table_data?: {
    headers: string[];
    rows: { text: string; colspan: number; rowspan: number }[][];
  };
}

interface DocumentDetail {
  id: number;
  filename: string;
  status: string;
}

export default function DocumentDetails() {
  const params = useParams();
  const id = params.id;
  
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState<number | null>(null);

  useEffect(() => {
    if (!id) return;

    const fetchData = async () => {
      try {
        const docRes = await fetch(`http://localhost:8000/documents/${id}`);
        if (docRes.ok) setDocument(await docRes.json());

        const blocksRes = await fetch(`http://localhost:8000/documents/${id}/blocks`);
        if (blocksRes.ok) setBlocks(await blocksRes.json());
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
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

  // Filter headings for TOC
  const toc = blocks.filter(b => 
    ['title', 'chapter_heading', 'section_heading'].includes(b.semantic_role)
  );

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-16 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
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
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          
          {/* Sidebar TOC */}
          <aside className="lg:w-64 flex-shrink-0">
            <div className="sticky top-40 bg-white rounded-lg shadow-sm border border-gray-200 p-4 max-h-[calc(100vh-12rem)] overflow-y-auto">
              <h3 className="font-semibold text-gray-900 mb-4 uppercase text-xs tracking-wider">Contents</h3>
              <nav className="space-y-1">
                {toc.map((item, idx) => (
                  <a
                    key={idx}
                    href={`#block-${idx}`} // In real app, use stable IDs
                    onClick={(e) => {
                      e.preventDefault();
                      window.document.getElementById(`block-${idx}`)?.scrollIntoView({ behavior: 'smooth' });
                      setActiveSection(idx);
                    }}
                    className={`block py-1.5 text-sm transition-colors ${
                      item.semantic_role === 'title' ? 'font-bold text-gray-900' :
                      item.semantic_role === 'chapter_heading' ? 'pl-2 font-medium text-gray-800' :
                      'pl-4 text-gray-600 hover:text-indigo-600'
                    } ${activeSection === idx ? 'text-indigo-600' : ''}`}
                  >
                    {item.text || "Untitled Section"}
                  </a>
                ))}
                {toc.length === 0 && <p className="text-sm text-gray-400 italic">No headings found</p>}
              </nav>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 min-w-0">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 sm:p-12">
              <div className="prose prose-indigo max-w-none">
                {blocks.map((block, idx) => {
                  // Assign ID for TOC linking (using index for MVP simplicity)
                  const id = toc.includes(block) ? `block-${toc.indexOf(block)}` : undefined;

                  switch (block.semantic_role) {
                    case 'title':
                      return <h1 key={idx} id={id} className="text-4xl font-bold mb-6 text-gray-900">{block.text}</h1>;
                    case 'chapter_heading':
                      return <h2 key={idx} id={id} className="text-2xl font-bold mt-8 mb-4 text-gray-800 border-b pb-2">{block.text}</h2>;
                    case 'section_heading':
                      return <h3 key={idx} id={id} className="text-xl font-semibold mt-6 mb-3 text-gray-800">{block.text}</h3>;
                    case 'table':
                      // If we have structured table data, use it (legacy/fallback)
                      if (block.table_data) {
                        return (
                          <div key={idx} className="my-6 overflow-x-auto">
                             <table className="min-w-full divide-y divide-gray-300 border border-gray-200">
                               <thead className="bg-gray-50">
                                 <tr>
                                   {block.table_data.headers.map((h, i) => (
                                     <th key={i} className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 border-b border-gray-200">
                                       {h}
                                     </th>
                                   ))}
                                 </tr>
                               </thead>
                               <tbody className="divide-y divide-gray-200 bg-white">
                                 {block.table_data.rows.map((row, rIdx) => (
                                   <tr key={rIdx}>
                                     {row.map((cell, cIdx) => (
                                       <td 
                                         key={cIdx} 
                                         colSpan={cell.colspan} 
                                         rowSpan={cell.rowspan}
                                         className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 border-r border-gray-100 last:border-r-0"
                                       >
                                         {cell.text}
                                       </td>
                                     ))}
                                   </tr>
                                 ))}
                               </tbody>
                             </table>
                          </div>
                        );
                      }
                      // Fallthrough to default markdown rendering for raw table text
                    default: 
                      // Use ReactMarkdown for paragraphs and other text content to handle 
                      // raw markdown (like tables, lists, bold/italic) that might be in the text.
                      return (
                        <div key={idx} className="mb-4 text-gray-700 leading-relaxed prose prose-indigo max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                            {block.text}
                          </ReactMarkdown>
                        </div>
                      );
                  }
                })}
              </div>
            </div>
          </main>

        </div>
      </div>
    </div>
  );
}
