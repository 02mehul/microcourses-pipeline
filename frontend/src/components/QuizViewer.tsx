import { useState } from "react";
import { CheckCircle, HelpCircle, BookOpen } from "lucide-react";

interface Question {
  id: number;
  question_text: string;
  answer_text: string;
  subchapter_id?: string;
  subchapter_title?: string;
}

interface QuizViewerProps {
  questions: Question[];
}

export default function QuizViewer({ questions }: QuizViewerProps) {
  const [revealedAnswers, setRevealedAnswers] = useState<Set<number>>(new Set());

  if (!questions || questions.length === 0) {
    return <div className="text-gray-500 italic">No review questions available.</div>;
  }

  const toggleAnswer = (id: number) => {
    const newRevealed = new Set(revealedAnswers);
    if (newRevealed.has(id)) {
      newRevealed.delete(id);
    } else {
      newRevealed.add(id);
    }
    setRevealedAnswers(newRevealed);
  };

  // Group questions by subchapter
  const groupedQuestions: { [key: string]: Question[] } = {};
  questions.forEach(q => {
    const key = q.subchapter_id || "general";
    if (!groupedQuestions[key]) {
      groupedQuestions[key] = [];
    }
    groupedQuestions[key].push(q);
  });

  return (
    <div className="space-y-8">
      <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <HelpCircle className="w-5 h-5 text-indigo-600" />
        Review Questions
      </h3>

      {Object.entries(groupedQuestions).map(([subchapterId, subchapterQuestions]) => {
        const firstQuestion = subchapterQuestions[0];
        const subchapterTitle = firstQuestion.subchapter_title || "General Questions";

        return (
          <div key={subchapterId} className="space-y-4">
            {/* Subchapter Header */}
            {firstQuestion.subchapter_title && (
              <div className="flex items-center gap-2 pb-2 border-b border-gray-200">
                <BookOpen className="w-4 h-4 text-indigo-600" />
                <h4 className="text-sm font-semibold text-indigo-900">
                  {subchapterTitle}
                </h4>
                <span className="text-xs text-gray-500">
                  ({subchapterQuestions.length} {subchapterQuestions.length === 1 ? 'question' : 'questions'})
                </span>
              </div>
            )}

            {/* Questions for this subchapter */}
            <div className="grid gap-4">
              {subchapterQuestions.map((q, idx) => (
                <div key={q.id} className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-start gap-4">
                    <span className="shrink-0 w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-sm">
                      {idx + 1}
                    </span>
                    <div className="flex-1">
                      <p className="text-gray-900 font-medium text-lg mb-4">{q.question_text}</p>

                      {revealedAnswers.has(q.id) ? (
                        <div className="bg-green-50 rounded-md p-4 border border-green-100 animate-in fade-in slide-in-from-top-2">
                          <div className="flex items-start gap-2">
                            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                            <div>
                              <p className="text-sm font-semibold text-green-800 mb-1">Answer:</p>
                              <p className="text-green-700">{q.answer_text}</p>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <button
                          onClick={() => toggleAnswer(q.id)}
                          className="text-sm text-indigo-600 hover:text-indigo-800 font-medium hover:underline focus:outline-none"
                        >
                          Show Answer
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
