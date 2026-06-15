import uuid
from pathlib import Path
from typing import Generator

import fitz
import tiktoken
from openai import OpenAI
from app.core.config import settings
from app.services.vector_store import VectorStore

client = OpenAI(api_key = settings.openai_api_key)
tokenizer = tiktoken.encoding_for_model("text-embedding-3-small")
vector_store = VectorStore()

def token_len(text: str) -> int:
    return len(tokenizer.encode(text))

def chunk_text(text: str, chunk_size: int = settings.chunk_size, overlap: int = settings.chunk_overlap) -> Generator[str, None, None]:
    words = text.split()
    current_chunk: list[str] = []
    current_len = 0

    for word in words:
        word_len = token_len(word)
        if current_len + word_len > chunk_size and current_chunk:
            yield " ".join(current_chunk)
            while current_chunk and current_len > overlap:
                removed = current_chunk.pop(0)
                current_len-=token_len(removed)
        current_chunk.append(word)
        current_len+=word_len

    if current_chunk:
        yield " ".join(current_chunk)


def embed(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(
        model = settings.embedding_model,
        input = texts,
    )
    return [item.embedding for item in response.data]

def ingest_pdf(
    file_path: str,
    material_id: str,
    course_id,
    filename: str
) -> int:
    doc = fitz.open(file_path)
    chunks_to_upsert = []
    for page_num, page in enumerate(doc, start=1):
        page_text = page.get_text("text").strip()
        if not page_text:
            continue

        for chunk_text in chunk_text(page_text):
            if token_len(chunk_text) < 20:
                continue

            chunks_to_upsert.append({
                "id": str(uuid.uuid4()),
                "text": chunk_text,
                "payload": {
                    "material_id": material_id,
                    "course_id": course_id,
                    "filename": filename,
                    "source_type": "pdf",
                    "page_number": page_num,
                    "location": f"page {page_num}",
                    "bloom_level": None,
                    "topic_tags": [],
                },
            })
    doc.close()

    if not chunks_to_upsert:
        return 0
    
    BATCH = 100
    for i in range(0, len(chunks_to_upsert), BATCH):
        batch = chunks_to_upsert[i:i+BATCH]
        texts = [c["text"] for c in batch]
        embeddings = embed(texts)
        vector_store.upsert(batch, embeddings)

    return len(chunks_to_upsert)