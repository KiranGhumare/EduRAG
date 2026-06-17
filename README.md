# EduRAG

> A conversational AI study assistant — upload your course materials (PDFs, diagrams, lecture recordings) and chat with them. Ask factual questions, generate Bloom's taxonomy-aware exam questions, and get your answers graded, all grounded in your actual course content with citations.

**Live demo:** [your-deployment-url]  
**Backend API docs:** [your-railway-url]/docs

---

## What makes this different from ChatGPT

- **Handles full lecture recordings** — a 2-hour video is transcribed via Whisper, chunked with timestamps, and indexed. ChatGPT's context window can't handle this.
- **Persistent course library** — upload once, query forever. Your entire semester lives in the vector store.
- **Every answer is cited** — responses trace back to a specific page number in your actual materials. No hallucination without a source.
- **Three conversational modes in one chat** — ask factual questions, generate exam questions, and get your answers graded, all in the same thread.
- **Bloom's taxonomy awareness** — the system infers difficulty from your language ("hard MCQs", "simple questions") and maps it to Bloom's levels 1–6 automatically.

---

## Demo

**Factual Q&A:**
> "What is Newton's first law?"
→ Direct answer grounded in your lecture notes, with page citation.

**Question generation:**
> "Generate 5 hard MCQs on bitmap indexes"
→ 5 structured MCQs at Bloom's levels 5–6, each with options, correct answer, explanation, and source citation.

**Answer grading:**
> "My answer to question 2 is B"
→ "Correct! Bitmap indexes are ideal for low-cardinality columns because..."

---

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | Next.js 14 + Tailwind CSS | App Router, TypeScript, fast iteration |
| Backend API | FastAPI | Async, Python-native, auto-generates /docs |
| Vector store | Qdrant | Self-hostable, first-class metadata filtering |
| Relational DB | PostgreSQL | Courses, materials, questions, chat history |
| Embeddings | OpenAI text-embedding-3-small | Best cost/quality ratio, 1536 dimensions |
| LLM | GPT-4o-mini | Fast, cheap, structured JSON output |
| PDF parsing | PyMuPDF | Page-by-page text extraction with page numbers |
| Deployment | Railway (backend) + Vercel (frontend) + Qdrant Cloud | |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        INGESTION                            │
│                                                             │
│  PDF upload → PyMuPDF → token-aware chunks (500 tok, 50     │
│  overlap) → OpenAI embeddings → Qdrant vector store         │
│                                                             │
│  Each chunk stores: text, course_id, material_id,           │
│  page_number, location, filename                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      CHAT SERVICE                           │
│                                                             │
│  1. Fetch last 10 messages (conversation memory)            │
│  2. Heuristic material matching (filename keyword search)   │
│  3. Embed user query → cosine similarity search in Qdrant   │
│     (filtered by course_id + optional material_id)          │
│  4. One LLM call: history + chunks + query → structured     │
│     JSON response (answer / questions / grading)            │
│  5. Save ChatMessage + Questions to Postgres                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       FRONTEND                              │
│                                                             │
│  Course dashboard → Course chat page                        │
│  Sidebar: upload materials, see processing status           │
│  Chat: user bubbles (right) + AI bubbles (left)             │
│  Question cards: Bloom badge + difficulty + MCQ options +   │
│  source citation + reveal answer toggle                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Key technical decisions

**1. Token-based chunking, not character-based**

Embedding models have token limits (8,192 for text-embedding-3-small), not character limits. Character splitting can silently produce oversized chunks that get truncated mid-sentence, destroying semantic coherence. We count tokens via `tiktoken` before chunking, ensuring every chunk fits within the model's limit.

**2. Course-scoped vector retrieval**

Every Qdrant search filters by `course_id` as a hard constraint before running cosine similarity. This means a question about Course A never accidentally pulls chunks from Course B — critical for correctness at scale, and a prerequisite for multi-user support.

**3. Heuristic material matching over a second LLM call**

When a user says "generate questions from the lecture5 video", we match against material filenames using simple keyword splitting rather than making a dedicated LLM routing call. False negatives gracefully fall back to course-wide search. This eliminates an entire LLM call per message — significant cost and latency savings.

**4. One LLM call per chat turn**

Rather than separate calls for intent classification, retrieval, and generation, a single comprehensive prompt handles all three conversational modes (answer / generate / grade) based on conversation context. The LLM returns a discriminated JSON object (`message_type: "text" | "questions"`).

**5. Background ingestion with session-scoped DB sessions**

PDF ingestion runs as a FastAPI BackgroundTask with its own `SessionLocal()` database session — not the request's `Depends(get_db)` session, which closes when the HTTP response returns. This prevents a subtle "closed session" bug that would leave materials stuck in processing status indefinitely.

**6. Normalized question storage**

Generated questions are stored in a dedicated `questions` table linked to `chat_messages` via `chat_message_id`, rather than as JSON blobs inside the message content. This enables independent queries ("all MCQs for this course", "filter by Bloom level") without deserializing chat history.

---

## Data model

```
courses
  └── materials (PDFs, videos, images — ingested into Qdrant)
  └── chat_messages (conversation history, role: user/assistant)
        └── questions (generated exam questions, linked to chat_message)

Qdrant collection: examgpt_chunks
  Each point: { vector: [1536 floats], payload: { course_id, material_id,
               filename, location, page_number, text, source_type } }
```

---

## Local setup

### Prerequisites
- Python 3.12
- Node.js 18+
- Docker Desktop

### 1. Clone and start infrastructure

```bash
git clone https://github.com/YOUR_USERNAME/EduRAG.git
cd EduRAG
docker-compose up -d
```

This starts Postgres (port 5432), Qdrant (port 6333), and Redis (port 6379).

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Fill in OPENAI_API_KEY

uvicorn app.main:app --reload
```

API explorer at `http://localhost:8000/docs`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App at `http://localhost:3000`

### 4. Environment variables

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key (required) | — |
| `DATABASE_URL` | Postgres connection string | `postgresql://edurag:edurag@localhost:5432/edurag` |
| `QDRANT_URL` | Qdrant instance URL | `http://localhost:6333` |
| `QDRANT_API_KEY` | Qdrant API key (empty for local) | `""` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |

---

## API reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/courses/` | Create a course |
| `GET` | `/api/v1/courses/` | List all courses |
| `POST` | `/api/v1/courses/{id}/materials/` | Upload a file (PDF, image, video) |
| `GET` | `/api/v1/courses/{id}/materials/` | List materials + processing status |
| `POST` | `/api/v1/courses/{id}/chat/` | Send a chat message |
| `GET` | `/api/v1/courses/{id}/chat/` | Get conversation history |
| `GET` | `/api/v1/questions/course/{id}` | Get all generated questions for a course |

---

## Deployment

| Service | Platform | Notes |
|---|---|---|
| Frontend | Vercel | Set `NEXT_PUBLIC_API_URL` env var to Railway URL |
| Backend | Railway | Set root directory to `backend`, add Postgres + Redis plugins |
| Vector store | Qdrant Cloud | Free tier (1GB), set `QDRANT_URL` + `QDRANT_API_KEY` |

---

## Known limitations

- Scanned/image-only PDFs are not supported — status shows `no_text_found`.
- Chat memory is limited to the last 10 messages.
- Material matching is heuristic — vague references like "the video" fall back to course-wide search.
- Switching embedding models requires re-indexing all materials.
