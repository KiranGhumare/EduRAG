from typing import Optional
from uuid import UUID
from pydantic import BaseModel

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
