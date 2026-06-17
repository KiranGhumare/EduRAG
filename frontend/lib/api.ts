const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface Course {
    id: string;
    name: string;
    description?: string;
}

export interface Material {
    id: string;
    course_id: string;
    filename: string;
    source_type: string;
    status: string;
    chunk_count: number;
}

export interface Question {
    id: string;
    question_text: string;
    question_type: string;
    chat_message_id?: string;
    bloom_level: number;
    difficulty: string;
    source_location?: string;
    source_excerpt?: string;
    option_a?: string;
    option_b?: string;
    option_c?: string;
    option_d?: string;
    correct_answer?: string;
    explanation?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  message_type: "text" | "questions";
  source_location?: string;
  source_excerpt?: string;
  created_at: string;
}

export interface ChatResponse {
  message: ChatMessage;
  questions?: Question[];
}


export async function getCourses(): Promise<Course[]> {
    const res = await fetch(`${API_BASE}/courses/`);
    if (!res.ok) throw new Error("Failed to fetch courses");
    return res.json();
}

export async function createCourse(name: string, description?: string): Promise<Course> {
    const res = await fetch(`${API_BASE}/courses/`, {
        method: "POST", 
        headers: {"Content-Type": "application/json", 'Access-Control-Allow-Origin': '*'},
        body: JSON.stringify({name, description}),
    });
    if (!res.ok) throw new Error("Failed to create course");
    return res.json();
}

export async function getMaterials(courseId: string): Promise<Material[]> {
  const res = await fetch(`${API_BASE}/courses/${courseId}/materials/`);
  if (!res.ok) throw new Error("Failed to fetch materials");
  return res.json();
}

export async function uploadMaterial(courseId: string, file: File): Promise<Material> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/courses/${courseId}/materials/`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to upload material");
  return res.json();
}

export async function getChatHistory(courseId: string): Promise<ChatMessage[]> {
  const res = await fetch(`${API_BASE}/courses/${courseId}/chat/`);
  if (!res.ok) throw new Error("Failed to fetch chat history");
  return res.json();
}

export async function sendChatMessage(courseId: string, message: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/courses/${courseId}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", 'Access-Control-Allow-Origin': '*' },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error("Failed to send message");
  return res.json();
}

export async function getQuestions(courseId: string): Promise<Question[]> {
  const res = await fetch(`${API_BASE}/questions/course/${courseId}`);
  if (!res.ok) throw new Error("Failed to fetch questions");
  return res.json();
}