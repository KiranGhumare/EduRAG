from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import courses, materials, questions, chat
from app.db.session import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "EduRAG API",
    description = "RAG-powered exam question generator from course materials",
    version = "0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses.router, prefix="/api/v1")
app.include_router(materials.router, prefix="/api/v1")
app.include_router(questions.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}