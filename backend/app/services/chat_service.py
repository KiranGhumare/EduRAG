"""
Chat service — handles a single turn of conversation.

For each user message:
1. Retrieve recent chat history (for conversational context)
2. Identify referenced material (if any) and retrieve relevant chunks from Qdrant
3. Build one prompt: history+retrieved chunks+user message+instructions
4. Call the LLM: it decides whether to answer, generate questions, or grade
5. Parse the response, save it, return it
"""

import json
import re

from openai import OpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.models.models import ChatMessage, Material, Question
from app.schemas.schemas import (
    ChatResponse,
    ChatMessageOut,
    QuestionOut,
    LLMChatOutput,
)
from app.services.vector_store import VectorStore

client = OpenAI(api_key=settings.openai_api_key)
vector_store = VectorStore()

HISTORY_LIMIT = 10


def embed_query(text: str) -> list[float]:
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=[text],
    )
    return response.data[0].embedding


def find_referenced_material(user_message: str, materials: list[Material]) -> Material | None:
    message_lower = user_message.lower()
    for material in materials:
        name_without_ext = material.filename.lower().rsplit(".", 1)[0]
        name_parts = re.split(r"[_\-\.\s]", name_without_ext)
        if any(part in message_lower for part in name_parts if len(part) > 2):
            return material
    return None


def build_prompt(
    history: list[ChatMessage],
    chunks: list[dict],
    user_message: str,
    db,
) -> str:
    history_lines = []
    for msg in history:
        if msg.role == "user":
            history_lines.append(f"USER: {msg.content}")
        elif msg.message_type == "questions":
            # Fetch the actual questions linked to this message
            questions = db.query(Question).filter(
                Question.chat_message_id == msg.id
            ).all()
            question_text = msg.content + "\n"
            for i, q in enumerate(questions, 1):
                question_text += f"\nQ{i}: {q.question_text}"
                if q.question_type == "mcq":
                    question_text += f"\n  A) {q.option_a}"
                    question_text += f"\n  B) {q.option_b}"
                    question_text += f"\n  C) {q.option_c}"
                    question_text += f"\n  D) {q.option_d}"
                    question_text += f"\n  Correct: {q.correct_answer}"
                    question_text += f"\n  Explanation: {q.explanation}"
            history_lines.append(f"ASSISTANT: {question_text}")
        else:
            history_lines.append(f"ASSISTANT: {msg.content}")

    history_text = "\n".join(history_lines) or "(no previous messages)"

    context_text = "\n\n---\n\n".join(
        f"[Source: {c['filename']}, {c['location']}]\n{c['text']}"
        for c in chunks
    ) or "(no relevant materials found)"

    return f"""You are a helpful teaching assistant for a course...
    
CONVERSATION HISTORY:
{history_text}

RELEVANT COURSE MATERIAL:
{context_text}

STUDENT'S NEW MESSAGE:
{user_message}

INSTRUCTIONS:
Decide which of these the student is doing, and respond accordingly:

1. ASKING A FACTUAL QUESTION (e.g. "What is Newton's first law?")
   -> Answer directly and clearly, using ONLY the course material above.
   -> Set message_type to "text".
   -> Include source_location and source_excerpt from the chunk you used.

2. REQUESTING GENERATED QUESTIONS (e.g. "Generate 5 hard MCQs on thermodynamics")
   -> Determine Bloom's Taxonomy level(s) from any difficulty words used:
      "easy"/"simple" -> Bloom 1-2, "medium" -> Bloom 3-4, "hard"/"difficult" -> Bloom 5-6.
      If no difficulty is mentioned, use a mixed spread.
   -> Set message_type to "questions".
   -> content should be a short intro like "Here are 5 questions on thermodynamics:"
   -> Include a "questions" array.

3. ANSWERING A PREVIOUSLY GENERATED QUESTION (e.g. "my answer is B")
   -> Look at the conversation history to find the question being answered.
   -> Grade it: say whether it's correct, and explain why.
   -> Set message_type to "text".

RULES:
- Never invent information not present in the course material.
- If the course material doesn't cover the topic, say so honestly.
- Keep "content" conversational and concise.

Return ONLY a JSON object with this EXACT structure (no markdown fences, no preamble):

{{
  "content": "...",
  "message_type": "text" or "questions",
  "source_location": "..." or null,
  "source_excerpt": "..." or null,
  "questions": null OR [
    {{
      "question_text": "...",
      "question_type": "mcq" or "short_answer",
      "bloom_level": <integer 1-6>,
      "difficulty": "easy" or "medium" or "hard",
      "option_a": "..." or null,
      "option_b": "..." or null,
      "option_c": "..." or null,
      "option_d": "..." or null,
      "correct_answer": "A" or "B" or "C" or "D" or null,
      "explanation": "...",
      "source_location": "...",
      "source_excerpt": "..."
    }}
  ]
}}

For "text" responses (modes 1 and 3), "questions" must be null.
For "questions" responses (mode 2), "option_a"-"option_d" and "correct_answer" are null for short_answer questions."""


def handle_chat_message(course_id: str, user_message: str, db) -> ChatResponse:
    # Step 1: recent history
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.course_id == course_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    history = list(reversed(history))

    # Step 2: identify referenced material, then retrieve chunks
    materials = (
        db.query(Material)
        .filter(Material.course_id == course_id, Material.status == "ready")
        .all()
    )
    referenced_material = find_referenced_material(user_message, materials)

    query_vector = embed_query(user_message)
    chunks = vector_store.search(
        query_vector=query_vector,
        course_id=course_id,
        top_k=6,
        material_id=referenced_material.id if referenced_material else None,
    )

    # Step 3: build prompt
    prompt = build_prompt(history, chunks, user_message, db)

    # Step 4: call the LLM
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        response_format={"type": "json_object"},
    )
    raw_text = response.choices[0].message.content

    # Step 5: parse, save, return
    try:
        raw = json.loads(raw_text)
        parsed = LLMChatOutput(**raw)
    except (json.JSONDecodeError, ValidationError):
        parsed = LLMChatOutput(
            content="Sorry, I had trouble processing that. Could you rephrase?",
            message_type="text",
        )

    assistant_message = ChatMessage(
        course_id=course_id,
        role="assistant",
        content=parsed.content,
        message_type=parsed.message_type,
        source_location=parsed.source_location,
        source_excerpt=parsed.source_excerpt,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    saved_questions = []
    if parsed.message_type == "questions" and parsed.questions:
        material_id = referenced_material.id if referenced_material else (
            chunks[0]["material_id"] if chunks else None
        )
        for q in parsed.questions:
            question = Question(
                course_id=course_id,
                chat_message_id=assistant_message.id,
                source_material_id=material_id,
                question_text=q.question_text,
                question_type=q.question_type,
                bloom_level=q.bloom_level,
                difficulty=q.difficulty,
                option_a=q.option_a,
                option_b=q.option_b,
                option_c=q.option_c,
                option_d=q.option_d,
                correct_answer=q.correct_answer,
                explanation=q.explanation,
                source_location=q.source_location,
                source_excerpt=q.source_excerpt,
            )
            db.add(question)
            saved_questions.append(question)
        db.commit()
        for q in saved_questions:
            db.refresh(q)

    return ChatResponse(
        message=ChatMessageOut.model_validate(assistant_message),
        questions=[QuestionOut.model_validate(q) for q in saved_questions] or None,
    )