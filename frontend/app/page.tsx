"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, BookOpen, ChevronRight, Loader2, Sparkles } from "lucide-react";
import { getCourses, createCourse, Course } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  useEffect(() => {
    getCourses()
      .then(setCourses)
      .finally(() => setLoading(false));
  }, []);

  async function handleCreate() {
    if (!name.trim()) return;
    setCreating(true);
    try {
      const course = await createCourse(name.trim(), description.trim() || undefined);
      setCourses((prev) => [course, ...prev]);
      setName("");
      setDescription("");
      setShowForm(false);
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white/80 backdrop-blur-md border-b border-slate-100">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-slate-900 tracking-tight">EduRAG</span>
          </div>
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 text-white px-3.5 py-2 rounded-lg text-sm font-medium transition-colors shadow-sm shadow-indigo-200"
          >
            <Plus className="w-4 h-4" />
            New course
          </button>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-10">
        {/* Hero */}
        <div className="mb-10">
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">
            Your courses
          </h1>
          <p className="text-slate-500 text-sm">
            Upload materials, ask questions, generate exam practice — all in one place.
          </p>
        </div>

        {/* New course form */}
        {showForm && (
          <div className="bg-white border border-slate-200 rounded-2xl p-6 mb-6 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-700 mb-4">New course</h2>
            <div className="flex flex-col gap-3">
              <input
                type="text"
                placeholder="Course name — e.g. Organic Chemistry"
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                className="border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder:text-slate-400"
                autoFocus
              />
              <input
                type="text"
                placeholder="Short description (optional)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder:text-slate-400"
              />
              <div className="flex gap-2 pt-1">
                <button
                  onClick={handleCreate}
                  disabled={!name.trim() || creating}
                  className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-40 transition-colors"
                >
                  {creating && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  Create course
                </button>
                <button
                  onClick={() => { setShowForm(false); setName(""); setDescription(""); }}
                  className="px-4 py-2 rounded-lg text-sm text-slate-500 hover:bg-slate-100 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Course list */}
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="w-5 h-5 animate-spin text-slate-300" />
          </div>
        ) : courses.length === 0 ? (
          <div className="text-center py-24">
            <div className="w-14 h-14 bg-indigo-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <BookOpen className="w-6 h-6 text-indigo-400" />
            </div>
            <p className="font-medium text-slate-700 mb-1">No courses yet</p>
            <p className="text-sm text-slate-400">Create your first course to get started</p>
          </div>
        ) : (
          <div className="flex flex-col gap-2.5">
            {courses.map((course) => (
              <button
                key={course.id}
                onClick={() => router.push(`/courses/${course.id}`)}
                className="group bg-white border border-slate-200 hover:border-indigo-300 rounded-2xl px-6 py-5 text-left transition-all hover:shadow-md hover:shadow-indigo-100/50"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-indigo-50 group-hover:bg-indigo-100 rounded-xl flex items-center justify-center transition-colors flex-shrink-0">
                      <BookOpen className="w-4 h-4 text-indigo-500" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900 group-hover:text-indigo-700 transition-colors text-sm">
                        {course.name}
                      </p>
                      {course.description && (
                        <p className="text-xs text-slate-400 mt-0.5">{course.description}</p>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-indigo-400 transition-colors" />
                </div>
              </button>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}