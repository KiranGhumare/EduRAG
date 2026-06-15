"""
Chat service — handles a single turn of conversation.

For each user message:
1. Retrieve recent chat history (for conversational context)
2. Embed the user's message and retrieve relevant chunks from Qdrant
3. Build one prompt: history + retrieved chunks + user message + instructions
4. Call the LLM: it decides whether to answer, generate questions, or grade
5. Parse the response, save it, return it
"""

import re
from app.db.session import SessionLocal
from app.models.models import ChatMessage, Material, Question
from app.schemas.schemas import ChatResponse, ChatMessageOut, QuestionOut
from app.services.vector_store import VectorStore
from openai import OpenAI
from app.core.config import settings

vector_store = VectorStore()
client = OpenAI(api_key=settings.openai_api_key)

HISTORY_LIMIT = 10

def _find_referenced_material(user_message: str, materials: list[Material]) -> Material | None:
    """
    Lightweight heuristic: check if the user's message mentions a word
    from any material's filename. No LLM call, no embeddings —
    if nothing matches, we just fall back to course-wide search.
    """
    message_lower = user_message.lower()
    for material in materials:
        name_without_ext = material.filename.lower().rsplit(".", 1)[0]
        name_parts = re.split(r"[_\-\.\s]", name_without_ext)
        if any(part in message_lower for part in name_parts if len(part) > 2):
            return material
    return None

def embed_query(text: str) -> list[float]:
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=[text],
    )
    return response.data[0].embedding

def handle_chat_message(course_id: str, user_message: str, db) -> ChatResponse:
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.course_id == course_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    history = list(reversed(history))

    # Step 1: retrieve relevant chunks
    materials = (
        db.query(Material)
        .filter(Material.course_id == course_id, Material.status == "ready")
        .all()
    )
    referenced_material = _find_referenced_material(user_message, materials)

    query_vector = embed_query(user_message)
    chunks = vector_store.search(
        query_vector=query_vector,
        course_id=course_id,
        top_k=6,
        material_id=referenced_material.id if referenced_material else None,
    )

    # Step 2: build prompt 
    # Step 3: call LLM
    # Step 4: parse + save response

    assistant_message = ChatMessage(
        course_id=course_id,
        role="assistant",
        content="(stub response: LLM logic not yet implemented)",
        message_type="text",
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return ChatResponse(
        message=ChatMessageOut.model_validate(assistant_message),
        questions=None,
    )