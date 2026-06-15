from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

class CourseCreate(BaseModel):
    name: str 
    description: Optional[str] = None

class CourseOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


class MaterialOut(BaseModel):
    id: UUID
    course_id: UUID
    filename: str
    source_type: str
    status: str
    chunk_count: int

    class Config:
        from_attributes = True


class GenerateQuestionsRequest(BaseModel):
    course_id: UUID
    num_questions: int = 10
    question_type: str = "mcq"
    difficulty: str = "mixed"
    topic_focus: Optional[str] = None


class QuestionOut(BaseModel):
    id: UUID
    question_text: str
    question_type: str
    bloom_level: int
    difficulty: str
    source_location: Optional[str]
    source_excerpt: Optional[str]
    option_a: Optional[str]
    option_b: Optional[str]
    option_c: Optional[str]
    option_d: Optional[str]
    correct_answer: Optional[str]
    explanation: Optional[str]

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str

class ChatMessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    message_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    message: ChatMessageOut
    questions: Optional[list[QuestionOut]] = None

class LLMQuestionOutput(BaseModel):
    question_text: str
    question_type: str
    bloom_level: int
    difficulty: str
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: str
    source_location: str
    source_excerpt: str


class LLMChatOutput(BaseModel):
    content: str
    message_type: str
    source_location: Optional[str] = None
    source_excerpt: Optional[str] = None
    questions: Optional[list[LLMQuestionOutput]] = None