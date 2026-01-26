import { useState } from "react";
import { CheckCircle, XCircle, HelpCircle, BookOpen, AlertCircle } from "lucide-react";

interface Question {
  id: number;
  question_text: string;
  answer_text: string;
  subchapter_id?: string;
  subchapter_title?: string;
  question_type?: "short_answer" | "sentence" | "multiple_choice";
  options?: string[];
  correct_answer?: string;
}

interface QuizViewerProps {
  questions: Question[];
}

interface QuestionState {
  userAnswer: string;
  isSubmitted: boolean;
  isCorrect: boolean | null;
}

export default function QuizViewer({ questions }: QuizViewerProps) {
  const [questionStates, setQuestionStates] = useState<Map<number, QuestionState>>(
    new Map()
  );

  if (!questions || questions.length === 0) {
    return <div className="text-gray-500 italic">No review questions available.</div>;
  }

  const getQuestionState = (qId: number): QuestionState => {
    return questionStates.get(qId) || { userAnswer: "", isSubmitted: false, isCorrect: null };
  };

  const updateQuestionState = (qId: number, update: Partial<QuestionState>) => {
    const newStates = new Map(questionStates);
    const currentState = getQuestionState(qId);
    newStates.set(qId, { ...currentState, ...update });
    setQuestionStates(newStates);
  };

  const checkAnswer = (question: Question, userAnswer: string): boolean => {
    const qType = question.question_type || "sentence";

    if (qType === "multiple_choice") {
      return userAnswer === question.correct_answer;
    }

    if (qType === "short_answer") {
      // Fuzzy matching for short answers
      const correctAnswer = question.answer_text?.toLowerCase().trim() || "";
      const userAnswerClean = userAnswer.toLowerCase().trim();

      // Exact match or contains key terms
      return correctAnswer === userAnswerClean || correctAnswer.includes(userAnswerClean) || userAnswerClean.includes(correctAnswer);
    }

    if (qType === "sentence") {
      // For sentence answers, check if user answer contains key concepts
      const correctAnswer = question.answer_text?.toLowerCase() || "";
      const userAnswerClean = userAnswer.toLowerCase();

      // Extract key words from correct answer (remove common words)
      const stopWords = ["the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for", "of", "and", "or", "but"];
      const keyWords = correctAnswer.split(/\s+/).filter(word =>
        word.length > 3 && !stopWords.includes(word)
      );

      // Check if user answer contains at least 50% of key words
      if (keyWords.length === 0) return true; // No key words to check
      const matchCount = keyWords.filter(keyword => userAnswerClean.includes(keyword)).length;
      return matchCount / keyWords.length >= 0.5;
    }

    return false;
  };

  const handleSubmit = (question: Question) => {
    const state = getQuestionState(question.id);
    const isCorrect = checkAnswer(question, state.userAnswer);

    updateQuestionState(question.id, {
      isSubmitted: true,
      isCorrect: isCorrect
    });
  };

  const handleTryAgain = (qId: number) => {
    updateQuestionState(qId, {
      userAnswer: "",
      isSubmitted: false,
      isCorrect: null
    });
  };

  const renderQuestionInput = (question: Question) => {
    const state = getQuestionState(question.id);
    const qType = question.question_type || "sentence";

    if (state.isSubmitted) {
      return (
        <div className={`rounded-lg p-4 border-2 ${
          state.isCorrect
            ? "bg-green-50 border-green-200"
            : "bg-red-50 border-red-200"
        }`}>
          <div className="flex items-start gap-2 mb-3">
            {state.isCorrect ? (
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 shrink-0" />
            ) : (
              <XCircle className="w-5 h-5 text-red-600 mt-0.5 shrink-0" />
            )}
            <div className="flex-1">
              <p className={`text-sm font-semibold mb-1 ${
                state.isCorrect ? "text-green-800" : "text-red-800"
              }`}>
                {state.isCorrect ? "Correct!" : "Not quite right"}
              </p>

              {!state.isCorrect && (
                <div className="mb-3">
                  <p className="text-sm text-red-700 mb-2">
                    <strong>Your answer:</strong> {qType === "multiple_choice"
                      ? question.options?.[["A", "B", "C", "D"].indexOf(state.userAnswer)]
                      : state.userAnswer}
                  </p>
                </div>
              )}

              <div className={qType === "multiple_choice" && state.isCorrect ? "" : "bg-white rounded p-3 border border-gray-200"}>
                <p className={`text-sm font-semibold mb-1 ${
                  state.isCorrect ? "text-green-700" : "text-gray-700"
                }`}>
                  Correct answer:
                </p>
                <p className={state.isCorrect ? "text-green-700" : "text-gray-800"}>
                  {qType === "multiple_choice" && question.correct_answer
                    ? `${question.correct_answer}) ${question.options?.[["A", "B", "C", "D"].indexOf(question.correct_answer)]}`
                    : question.answer_text}
                </p>
              </div>
            </div>
          </div>

          {!state.isCorrect && (
            <button
              onClick={() => handleTryAgain(question.id)}
              className="text-sm text-red-600 hover:text-red-800 font-medium hover:underline focus:outline-none"
            >
              Try Again
            </button>
          )}
        </div>
      );
    }

    // Multiple Choice
    if (qType === "multiple_choice" && question.options) {
      return (
        <div className="space-y-3">
          {question.options.map((option, idx) => {
            const optionLetter = ["A", "B", "C", "D"][idx];
            const isSelected = state.userAnswer === optionLetter;

            return (
              <button
                key={idx}
                onClick={() => updateQuestionState(question.id, { userAnswer: optionLetter })}
                className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                  isSelected
                    ? "border-indigo-600 bg-indigo-50"
                    : "border-gray-200 bg-white hover:border-indigo-300 hover:bg-indigo-50"
                }`}
              >
                <div className="flex items-start gap-3">
                  <span className={`flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center text-sm font-semibold ${
                    isSelected
                      ? "border-indigo-600 bg-indigo-600 text-white"
                      : "border-gray-300 bg-white text-gray-600"
                  }`}>
                    {optionLetter}
                  </span>
                  <span className={`text-sm ${isSelected ? "text-indigo-900 font-medium" : "text-gray-700"}`}>
                    {option}
                  </span>
                </div>
              </button>
            );
          })}

          <button
            onClick={() => handleSubmit(question)}
            disabled={!state.userAnswer}
            className="w-full mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Submit Answer
          </button>
        </div>
      );
    }

    // Short Answer
    if (qType === "short_answer") {
      return (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
            <AlertCircle className="w-4 h-4" />
            <span>Enter a short answer (one word or phrase)</span>
          </div>
          <input
            type="text"
            value={state.userAnswer}
            onChange={(e) => updateQuestionState(question.id, { userAnswer: e.target.value })}
            placeholder="Type your answer..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
            onKeyDown={(e) => {
              if (e.key === "Enter" && state.userAnswer.trim()) {
                handleSubmit(question);
              }
            }}
          />
          <button
            onClick={() => handleSubmit(question)}
            disabled={!state.userAnswer.trim()}
            className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Submit Answer
          </button>
        </div>
      );
    }

    // Sentence Answer
    if (qType === "sentence") {
      return (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
            <AlertCircle className="w-4 h-4" />
            <span>Write a complete sentence explaining your answer</span>
          </div>
          <textarea
            value={state.userAnswer}
            onChange={(e) => updateQuestionState(question.id, { userAnswer: e.target.value })}
            placeholder="Type your answer..."
            rows={4}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none"
          />
          <button
            onClick={() => handleSubmit(question)}
            disabled={!state.userAnswer.trim()}
            className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Submit Answer
          </button>
        </div>
      );
    }

    return null;
  };

  const getQuestionTypeLabel = (type?: string) => {
    switch (type) {
      case "short_answer":
        return "Short Answer";
      case "sentence":
        return "Sentence";
      case "multiple_choice":
        return "Multiple Choice";
      default:
        return "Question";
    }
  };

  // Group questions by subchapter
  const groupedQuestions: { [key: string]: Question[] } = {};
  questions.forEach((q) => {
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
                <h4 className="text-sm font-semibold text-indigo-900">{subchapterTitle}</h4>
                <span className="text-xs text-gray-500">
                  ({subchapterQuestions.length}{" "}
                  {subchapterQuestions.length === 1 ? "question" : "questions"})
                </span>
              </div>
            )}

            {/* Questions for this subchapter */}
            <div className="grid gap-6">
              {subchapterQuestions.map((q, idx) => (
                <div
                  key={q.id}
                  className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start gap-4">
                    <span className="shrink-0 w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-sm">
                      {idx + 1}
                    </span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2 py-1 rounded">
                          {getQuestionTypeLabel(q.question_type)}
                        </span>
                      </div>
                      <p className="text-gray-900 font-medium text-lg mb-4">{q.question_text}</p>
                      {renderQuestionInput(q)}
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
