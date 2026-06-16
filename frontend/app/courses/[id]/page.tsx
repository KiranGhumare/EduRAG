"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft, Upload, Send, Loader2, FileText,
  CheckCircle, AlertCircle, Clock, BookOpen
} from "lucide-react";
import {
  getCourses, getMaterials, uploadMaterial,
  getChatHistory, sendChatMessage, getQuestions,
  Course, Material, ChatMessage, Question
} from "@/lib/api";

// Status badge for materials

function StatusBadge({ status }: { status: string }) {
  if (status === "ready")
    return (
      <span className="flex items-center gap-1 text-xs text-emerald-600">
        <CheckCircle className="w-3 h-3" /> ready
      </span>
    );
  if (status === "processing" || status === "pending")
    return (
      <span className="flex items-center gap-1 text-xs text-amber-500">
        <Loader2 className="w-3 h-3 animate-spin" /> processing
      </span>
    );
  if (status === "error" || status === "no_text_found")
    return (
      <span className="flex items-center gap-1 text-xs text-red-500">
        <AlertCircle className="w-3 h-3" /> error
      </span>
    );
  return <span className="text-xs text-gray-400">{status}</span>;
}

// Question card
function QuestionCard({ question, index }: { question: Question; index: number }) {
  const [showAnswer, setShowAnswer] = useState(false);
  const bloomColors: Record<number, string> = {
    1: "bg-blue-50 text-blue-700",
    2: "bg-indigo-50 text-indigo-700",
    3: "bg-emerald-50 text-emerald-700",
    4: "bg-amber-50 text-amber-700",
    5: "bg-orange-50 text-orange-700",
    6: "bg-red-50 text-red-700",
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 mt-2">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs font-medium text-gray-400">Q{index + 1}</span>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${bloomColors[question.bloom_level] || "bg-gray-100 text-gray-600"}`}>
          Bloom {question.bloom_level}
        </span>
        <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 font-medium">
          {question.difficulty}
        </span>
      </div>

      <p className="text-sm font-medium text-gray-900 mb-3">{question.question_text}</p>

      {question.question_type === "mcq" && (
        <div className="flex flex-col gap-1.5 mb-3">
          {(["a", "b", "c", "d"] as const).map((opt) => {
            const key = `option_${opt}` as keyof Question;
            const val = question[key];
            if (!val) return null;
            const isCorrect = showAnswer && question.correct_answer === opt.toUpperCase();
            return (
              <div
                key={opt}
                className={`flex items-center gap-2 text-sm px-3 py-2 rounded-lg border transition-colors ${
                  isCorrect
                    ? "border-emerald-300 bg-emerald-50 text-emerald-800"
                    : "border-gray-100 bg-gray-50 text-gray-700"
                }`}
              >
                <span className="font-medium text-xs w-4">{opt.toUpperCase()}.</span>
                {String(val)}
              </div>
            );
          })}
        </div>
      )}

      {question.source_location && (
        <p className="text-xs text-gray-400 mb-2">
          Source: {question.source_location}
        </p>
      )}

      <button
        onClick={() => setShowAnswer(!showAnswer)}
        className="text-xs text-indigo-600 hover:text-indigo-700 font-medium"
      >
        {showAnswer ? "Hide answer" : "Show answer"}
      </button>

      {showAnswer && question.explanation && (
        <p className="text-xs text-gray-600 mt-2 p-2 bg-gray-50 rounded-lg">
          {question.explanation}
        </p>
      )}
    </div>
  );
}

// Chat bubble

function ChatBubble({
  message,
  questions,
}: {
  message: ChatMessage;
  questions?: Question[];
}) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[80%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-1`}>
        <div
          className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? "bg-indigo-600 text-white rounded-tr-sm"
              : "bg-white border border-gray-200 text-gray-800 rounded-tl-sm"
          }`}
        >
          {message.content}
        </div>

        {message.source_location && (
          <p className="text-xs text-gray-400 px-1">
            Source: {message.source_location}
          </p>
        )}

        {message.message_type === "questions" && questions && questions.length > 0 && (
          <div className="w-full">
            {questions.map((q, i) => (
              <QuestionCard key={q.id} question={q} index={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Main page 

export default function CoursePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [course, setCourse] = useState<Course | null>(null);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [questionMap, setQuestionMap] = useState<Record<string, Question[]>>({});
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Load course, materials, history on mount
useEffect(() => {
  getCourses().then((cs) => setCourse(cs.find((c) => c.id === id) || null));
  getMaterials(id).then(setMaterials);
  Promise.all([getChatHistory(id), getQuestions(id)]).then(([history, questions]) => {
    setMessages(history);
    const map: Record<string, Question[]> = {};
    questions.forEach((q) => {
      if (q.chat_message_id) {
        if (!map[q.chat_message_id]) map[q.chat_message_id] = [];
        map[q.chat_message_id].push(q);
      }
    });
    setQuestionMap(map);
  });
}, [id]);

  // Poll materials every 3s until all are ready
  useEffect(() => {
    const hasProcessing = materials.some(
      (m) => m.status === "pending" || m.status === "processing"
    );
    if (!hasProcessing) return;
    const interval = setInterval(() => {
      getMaterials(id).then(setMaterials);
    }, 3000);
    return () => clearInterval(interval);
  }, [materials, id]);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

async function handleSend() {
  if (!input.trim() || sending) return;
  const text = input.trim();
  setInput("");
  setSending(true);

  // add user message
  const tempUserMsg: ChatMessage = {
    id: `temp-${Date.now()}`,
    role: "user",
    content: text,
    message_type: "text",
    created_at: new Date().toISOString(),
  };
  setMessages((prev) => [...prev, tempUserMsg]);

  try {
    const response = await sendChatMessage(id, text);

// Store questions first, keyed by the assistant message ID
if (response.questions && response.questions.length > 0) {
  setQuestionMap((prev) => ({
    ...prev,
    [response.message.id]: response.questions!,
  }));
}

// refetch history
const history = await getChatHistory(id);
setMessages(history);
  } catch {
    setMessages((prev) => prev.filter((m) => m.id !== tempUserMsg.id));
  } finally {
    setSending(false);
  }
}

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const material = await uploadMaterial(id, file);
      setMaterials((prev) => [material, ...prev]);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3 flex-shrink-0">
        <button
          onClick={() => router.push("/")}
          className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 text-gray-500" />
        </button>
        <BookOpen className="w-4 h-4 text-indigo-600" />
        <h1 className="font-semibold text-sm">{course?.name || "Loading..."}</h1>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-56 border-r border-gray-200 bg-white flex flex-col flex-shrink-0">
          <div className="p-3 border-b border-gray-100">
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".pdf,.png,.jpg,.jpeg,.mp4,.mov"
              onChange={handleUpload}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="w-full flex items-center justify-center gap-2 border border-dashed border-gray-300 rounded-lg py-2.5 text-xs text-gray-500 hover:border-indigo-400 hover:text-indigo-600 transition-colors disabled:opacity-50"
            >
              {uploading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Upload className="w-3.5 h-3.5" />
              )}
              {uploading ? "Uploading..." : "Upload material"}
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-2">
            {materials.length === 0 ? (
              <p className="text-xs text-gray-400 text-center mt-4 px-2">
                No materials yet — upload a PDF or video
              </p>
            ) : (
              <div className="flex flex-col gap-1">
                {materials.map((m) => (
                  <div
                    key={m.id}
                    className="flex flex-col gap-0.5 px-2 py-2 rounded-lg hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                      <span className="text-xs text-gray-700 truncate">{m.filename}</span>
                    </div>
                    <div className="pl-5">
                      <StatusBadge status={m.status} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>

        {/* Chat area */}
        <main className="flex-1 flex flex-col overflow-hidden bg-gray-50">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-4 flex flex-col gap-4">
            {messages.length === 0 && (
              <div className="flex-1 flex flex-col items-center justify-center text-center py-20">
                <BookOpen className="w-8 h-8 text-gray-300 mb-3" />
                <p className="text-sm text-gray-500 max-w-xs">
                  Upload your course materials, then ask questions or generate exam questions
                </p>
              </div>
            )}
            {messages.map((msg) => (
              <ChatBubble
                key={msg.id}
                message={msg}
                questions={questionMap[msg.id]}
              />
            ))}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-200 bg-white px-4 py-3 flex-shrink-0">
            <div className="flex items-end gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask a question or request exam questions..."
                rows={1}
                className="flex-1 resize-none border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 max-h-32"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || sending}
                className="p-2.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 transition-colors flex-shrink-0"
              >
                {sending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-1.5 px-1">
              Enter to send · Shift+Enter for new line
            </p>
          </div>
        </main>
      </div>
    </div>
  );
}