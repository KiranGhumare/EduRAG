from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import settings

EMBEDDING_DIM = 1536

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            url = settings.qdrant_url, 
            api_key = settings.qdrant_api_key or None,
        )
        self.check_collection()

    def check_collection(self):
        existing = [c.name for c in self.client.get_collections().collections]
        if settings.qdrant_collection not in existing:
            self.client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config = VectorParams(
                    size = EMBEDDING_DIM,
                    distance = Distance.COSINE
                ),
            )
        
    def upsert(self, chunks: list[dict], embeddings: list[list[float]]):
        points = [
            PointStruct(
                id=chunk["id"],
                vector=embeddings,
                payload={**chunk["payload"], "text": chunk["text"]},
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
        self.client.upsert(
            collection_name=settings.qdrant_collection,
            points=points,
        )
    
    def search(self, 
               query_vector:list[float], 
               course_id: str, 
               top_k: int=5, 
               source_type: str|None = None,
               material_id: str|None = None) -> list[dict]:
        must_conditions = [
            FieldCondition(key="course_id", match=MatchValue(value=course_id))
        ]
        if source_type:
            must_conditions.append(
                FieldCondition(key="source_type", match=MatchValue(value=source_type))
            )
        
        if material_id:
            must_conditions.append(
                FieldCondition(key="material_id", match=MatchValue(value=str(material_id)))
            )

        results = self.client.search(
            collection_name = settings.qdrant_collection,
            query_vector = query_vector,
            query_filter = Filter(must=must_conditions),
            limit = top_k,
            with_payload = True,
        ) 

        return [
            {
                "score": hit.score,
                "text": hit.payload.get("text", ""),
                "location": hit.payload.get("location", ""),
                "source_type": hit.payload.get("source_type", ""),
                "filename": hit.payload.get("filename", ""),
                "material_id": hit.payload.get("material_id", ""),
                "bloom_level": hit.payload.get("bloom_level"),
                "topic_tags": hit.payload.get("topic_tags", [])
            }
            for hit in results
        ]

    def delete_by_material(self, material_id: str):
        self.client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=Filter(
                must= [
                    FieldCondition(
                        key="material_id", match = MatchValue(value=material_id)
                    )
                ]
            ),
        )