# OrionX : AI Educational Platform

> An intelligent, RAG-powered learning platform that transforms static educational materials into interactive, citation-backed conversations.

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Features](#features)
- [Screenshots](#screenshots)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [RAG Workflow](#rag-workflow)
- [Document Ingestion](#document-ingestion)
- [Database Design](#database-design)
- [Getting Started](#getting-started)
- [LLM Provider Configuration](#llm-provider-configuration)
- [Document Ingestion Guide](#document-ingestion-guide)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Docker](#docker)
- [Deployment](#deployment)
- [Known Limitations](#known-limitations)
- [Future Enhancements](#future-enhancements)
- [License & Acknowledgments](#license--acknowledgments)

---

## Problem Statement

Traditional online learning platforms deliver content passively — students read, watch, and hope they retain the information. There is no intelligent intermediary that can:

- Answer questions **in context** of the specific course materials a student is studying
- Provide **cited, verifiable answers** rather than hallucinated responses
- Adapt to individual learning patterns and recommend personalized study paths
- Ingest **arbitrary document formats** (PDF, DOCX, plain text) and make them instantly queryable

The **OrionX : AI Educational Platform** solves these problems by leveraging **Retrieval-Augmented Generation (RAG)** — a technique that grounds Large Language Model responses in a curated knowledge base of uploaded educational documents. The result is an AI tutor that only answers from the source material, with citations, every single time.

---

## Features

### Core Platform

| Feature | Description |
|---------|-------------|
| **RAG-Powered Chat** | Students ask questions in natural language and receive grounded, citation-backed answers from their uploaded course materials |
| **Document Ingestion** | Upload PDF, DOCX, and TXT files; the system automatically chunks, embeds, and indexes them for retrieval |
| **Smart Citations** | Every AI answer includes inline citations linking back to the exact source document and page/chunk |
| **Quiz Generation** | Automatically generate quizzes from uploaded materials to test comprehension |
| **Recommendations** | Personalized document and topic recommendations based on chat history and quiz performance |
| **Analytics Dashboard** | Visualize learning progress, quiz scores, document engagement, and topic mastery |
| **Multi-Conversation** | Organize chats by topic or course; each conversation maintains its own context |
| **Admin Dashboard** | Manage users, monitor system health, and view aggregate usage analytics |

### User Management

- [x] User registration and authentication (JWT-based)
- [x] Role-based access control (Student, Instructor, Admin)
- [x] User profile management
- [x] Secure password hashing with bcrypt

### Document Management

- [x] Drag-and-drop file upload (PDF, DOCX, TXT)
- [x] Document listing, search, and filtering
- [x] Automatic text extraction and chunking
- [x] Vector embedding generation and storage
- [x] Document deletion with cascade vector cleanup

### AI & RAG

- [x] Configurable embedding providers (scikit-learn TF-IDF, Sentence-Transformers)
- [x] ChromaDB vector store for efficient similarity search
- [x] Configurable LLM providers (OpenAI, mock for development)
- [x] Retrieval-Augmented Generation with configurable top-k and similarity thresholds
- [x] Context-aware conversation memory
- [x] Citation validation to prevent hallucinated references

### Developer Experience

- [x] Full REST API with OpenAPI/Swagger documentation
- [x] Docker Compose for one-command local development
- [x] Comprehensive test suite (pytest)
- [x] Environment-based configuration
- [x] Structured logging and health checks

---

## Screenshots

> **Placeholder** — Add screenshots of the platform here once available.

| Dashboard | Chat Interface | Documents |
|-----------|---------------|-----------|
| ![Dashboard](docs/images/dashboard.png) | ![Chat](docs/images/chat.png) | ![Documents](docs/images/documents.png) |

| Analytics | Quiz Center | Admin |
|-----------|-------------|-------|
| ![Analytics](docs/images/analytics.png) | ![Quiz](docs/images/quiz.png) | ![Admin](docs/images/admin.png) |

---

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend Framework** | React | 18.3 |
| **Build Tool** | Vite | 6.0 |
| **Styling** | Tailwind CSS | 3.4 |
| **Routing** | React Router | 6.28 |
| **HTTP Client** | Axios | 1.7 |
| **Charts** | Recharts | 2.12 |
| **Icons** | Lucide React | 0.460 |
| **Markdown** | React Markdown + remark-gfm | 9.0 / 4.0 |
| **Backend Framework** | FastAPI | 0.143 |
| **ASGI Server** | Uvicorn | 0.54 |
| **ORM** | SQLAlchemy | 2.1 |
| **Database Migrations** | Alembic | 1.20 |
| **Database** | SQLite (dev) / PostgreSQL (prod) | — |
| **Vector Store** | ChromaDB | — |
| **Embeddings** | scikit-learn / Sentence-Transformers | 1.3.2 |
| **LLM Client** | OpenAI Python SDK | 3.31 |
| **Auth** | python-jose (JWT), passlib (bcrypt) | — |
| **File Processing** | PyMuPDF (fitz), python-docx | 1.28 / 1.2 |
| **Validation** | Pydantic | 2.10 |
| **Testing** | pytest, Vitest (frontend) | — |
| **Containerization** | Docker, Docker Compose | — |

---

## Architecture

```mermaid
graph LR
    A[React Frontend] --> B[FastAPI Backend]
    B --> C[Auth & Services]
    C --> D[RAG Pipeline]
    D --> E[Embedding Model]
    E --> F[ChromaDB Retrieval]
    F --> G[LLM Generation]
    G --> H[Cited Answer]
    H --> I[Student Dashboard]
```

The system follows a classic client-server architecture with a clear separation between the React SPA frontend and the FastAPI backend. All AI processing (embedding, retrieval, generation, citation validation) is encapsulated within the RAG pipeline module.

---

## RAG Workflow

```mermaid
graph LR
    A[Student Question] --> B[Query Embedding]
    B --> C[Retrieval]
    C --> D[Context Construction]
    D --> E[LLM]
    E --> F[Citation Validation]
    F --> G[Answer]
```

Every question follows this path:

1. **Query Embedding** — The student's question is converted into a vector using the same embedding model as the documents.
2. **Retrieval** — ChromaDB performs a similarity search to find the top-k most relevant document chunks.
3. **Context Construction** — Retrieved chunks are assembled into a prompt context with metadata (document name, page number).
4. **LLM Generation** — The context + question are sent to the configured LLM, which generates a grounded response.
5. **Citation Validation** — The system verifies that all citations in the response correspond to actual retrieved chunks.
6. **Answer** — The final answer with valid citations is returned to the student.

---

## Document Ingestion

```mermaid
graph LR
    A[Upload Document] --> B[Validate]
    B --> C[Extract Text]
    C --> D[Chunk Text]
    D --> E[Generate Embeddings]
    E --> F[Store Vectors + Metadata]
    F --> G[Retrieve Relevant Chunks]
```

The ingestion pipeline processes uploaded documents through five stages:

1. **Validation** — File type, size, and integrity checks.
2. **Text Extraction** — PyMuPDF for PDFs, python-docx for DOCX, standard I/O for TXT.
3. **Chunking** — Text is split into overlapping chunks (default: 800 tokens, 120 overlap).
4. **Embedding Generation** — Each chunk is converted to a vector embedding.
5. **Storage** — Vectors and metadata are persisted in ChromaDB for fast retrieval.

---

## Database Design

### Entity-Relationship Overview

```mermaid
erDiagram
    USERS ||--o{ CONVERSATIONS : creates
    USERS ||--o{ DOCUMENTS : uploads
    USERS ||--o{ QUIZZES : takes
    USERS ||--o{ ANALYTICS : generates
    CONVERSATIONS ||--o{ MESSAGES : contains
    DOCUMENTS ||--o{ DOCUMENT_CHUNKS : split_into
    QUIZZES ||--o{ QUESTIONS : contains
    QUESTIONS ||--o{ QUIZ_RESPONSES : answers
    USERS ||--o{ QUIZZES_RESPONDS : responds

    USERS {
        int id PK
        string email UK
        string hashed_password
        string full_name
        string role
        datetime created_at
    }

    CONVERSATIONS {
        int id PK
        int user_id FK
        string title
        datetime created_at
    }

    MESSAGES {
        int id PK
        int conversation_id FK
        string role
        text content
        json citations
        datetime created_at
    }

    DOCUMENTS {
        int id PK
        int user_id FK
        string filename
        string file_type
        int file_size
        string title
        text content_preview
        datetime created_at
    }

    DOCUMENT_CHUNKS {
        int id PK
        int document_id FK
        int chunk_index
        text content
        int page_number
        string embedding_id
    }

    QUIZZES {
        int id PK
        int user_id FK
        string title
        string topic
        int question_count
        datetime created_at
    }

    QUESTIONS {
        int id PK
        int quiz_id FK
        text question
        json options
        text correct_answer
        text explanation
    }

    ANALYTICS {
        int id PK
        int user_id FK
        string metric_type
        float value
        json metadata
        datetime created_at
    }
```

---

## Getting Started

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |
| Docker (optional) | 24+ |
| Docker Compose (optional) | 2.20+ |

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/your-org/ai-educational-platform.git
cd ai-educational-platform

# Create environment file
cp .env.example .env

# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Create data directory
mkdir -p data

# Initialize database
python ../scripts/initialize_db.py

# Start the server
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## Environment Setup

Copy `.env.example` to `.env` and configure the following variables:

### `.env.example`

```env
# ─── Application ───────────────────────────────────────────────
APP_NAME=OrionX : AI Educational Platform
DEBUG=true
API_V1_PREFIX=/api

# ─── Database ─────────────────────────────────────────────────
DATABASE_URL=sqlite:///./data/app.db
# For PostgreSQL: postgresql://user:password@localhost:5432/ai_edu

# ─── Vector Store ─────────────────────────────────────────────
VECTOR_STORE_PATH=./data/chroma

# ─── Embeddings ───────────────────────────────────────────────
EMBEDDING_PROVIDER=sklearn
# Options: sklearn, sentence-transformers
EMBEDDING_MODEL=tfidf
# For sentence-transformers: all-MiniLM-L6-v2, all-mpnet-base-v2

# ─── LLM Configuration ────────────────────────────────────────
LLM_PROVIDER=openai
# Options: openai, mock
LLM_MODEL=gpt-3.5-turbo
# Options: gpt-3.5-turbo, gpt-4, gpt-4-turbo
LLM_API_KEY=sk-your-openai-api-key
LLM_BASE_URL=
# Optional: for Azure OpenAI or compatible endpoints
# https://your-resource.openai.azure.com

# ─── RAG Parameters ───────────────────────────────────────────
CHUNK_SIZE=800
CHUNK_OVERLAP=120
RETRIEVAL_TOP_K=5
SIMILARITY_THRESHOLD=0.1

# ─── Authentication ───────────────────────────────────────────
SECRET_KEY=change-me-to-a-long-random-string-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM=HS256

# ─── File Uploads ─────────────────────────────────────────────
MAX_UPLOAD_SIZE_MB=20
UPLOAD_DIR=./data/uploads

# ─── CORS ─────────────────────────────────────────────────────
FRONTEND_ORIGIN=http://localhost:5173

# ─── Rate Limiting ────────────────────────────────────────────
RATE_LIMIT_PER_MINUTE=60
```

---

## LLM Provider Configuration

### OpenAI (Default)

```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_MODEL=gpt-3.5-turbo
```

### Mock Provider (Development/Testing)

```env
LLM_PROVIDER=mock
```

The mock provider returns canned responses without calling any external API. Useful for development, testing, and CI/CD pipelines.

### Azure OpenAI

```env
LLM_PROVIDER=openai
LLM_API_KEY=your-azure-key
LLM_BASE_URL=https://your-resource.openai.azure.com
LLM_MODEL=gpt-35-turbo
```

### Custom OpenAI-Compatible Endpoint

```env
LLM_PROVIDER=openai
LLM_API_KEY=your-key
LLM_BASE_URL=https://your-custom-endpoint.com/v1
LLM_MODEL=your-model-name
```

---

## Document Ingestion Guide

### Supported Formats

| Format | Extension | Max Size |
|--------|-----------|----------|
| PDF | `.pdf` | 20 MB |
| Word Document | `.docx` | 20 MB |
| Plain Text | `.txt` | 20 MB |

### Ingestion Steps

1. **Upload** — Use the Documents page to upload files via drag-and-drop or file picker.
2. **Processing** — The backend validates, extracts text, chunks, embeds, and stores the document.
3. **Indexing** — Vectors are stored in ChromaDB with metadata (document ID, chunk index, page number).
4. **Ready** — The document appears in your library and is immediately available for chat queries.

### Via API

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@path/to/your/document.pdf"
```

### Via Script

```bash
cd scripts
python ingest_sample_documents.py
```

---

## API Documentation

Full interactive API documentation is available via Swagger UI:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

See [`docs/api.md`](docs/api.md) for detailed endpoint documentation.

---

## Testing

### Backend Tests

```bash
cd backend

# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_rag.py -v
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage
```

---

## Docker

### Build and Run All Services

```bash
docker-compose up --build
```

### Run Individual Services

```bash
# Backend only
docker-compose up --build backend

# Frontend only
docker-compose up --build frontend
```

### Production Build

```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

---

## Deployment

See [`docs/deployment.md`](docs/deployment.md) for comprehensive deployment instructions covering:

- Docker Compose production setup
- Environment variable management
- Persistent storage configuration
- CORS configuration
- Hosting provider guides (AWS, GCP, Azure, Railway, Render)
- Backup strategies

---

## Known Limitations

- **SQLite in development**: The default database is SQLite, which is not suitable for high-concurrency production workloads. Use PostgreSQL for production.
- **Single-process**: The current architecture runs as a single backend process. Horizontal scaling requires a shared database and vector store.
- **File format support**: Only PDF, DOCX, and TXT are supported. PowerPoint, Excel, and image-based documents are not yet supported.
- **Embedding quality**: The default scikit-learn TF-IDF embedding is fast but less semantic than neural alternatives. Use Sentence-Transformers for better retrieval quality at higher computational cost.
- **No real-time collaboration**: Multi-user real-time features (shared whiteboard, live discussion) are not implemented.
- **Limited LLM providers**: Only OpenAI-compatible APIs are supported. Anthropic, Google, and open-source model hosting are not yet integrated.

---

## Future Enhancements

- [ ] **Multi-modal ingestion** — Support for images, slides, and scanned documents with OCR
- [ ] **Advanced RAG strategies** — HyDE, re-ranking, multi-query retrieval, and fusion
- [ ] **Learning path generation** — AI-generated structured curricula based on course materials
- [ ] **Spaced repetition** — Integrate SRS algorithms for long-term retention
- [ ] **Classroom mode** — Instructor-led cohorts with assignment tracking
- [ ] **Plugin system** — Extensible architecture for custom RAG strategies and LLM providers
- [ ] **Mobile application** — React Native companion app
- [ ] **Multilingual support** — Cross-lingual embeddings and LLM responses
- [ ] **WebSocket streaming** — Real-time token streaming for chat responses
- [ ] **PostgreSQL full-text search** — Hybrid search combining BM25 with vector similarity

---

## License & Acknowledgments

### License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

### Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) — Modern, fast web framework for building APIs
- [ChromaDB](https://www.trychroma.com/) — The AI-native open-source embedding database
- [OpenAI](https://openai.com/) — GPT models powering the generation layer
- [Sentence-Transformers](https://www.sbert.net/) — State-of-the-art sentence embedding models
- [PyMuPDF](https://pymupdf.readthedocs.io/) — High-performance PDF text extraction
- [React](https://react.dev/) — The library for web and native user interfaces
- [Tailwind CSS](https://tailwindcss.com/) — A utility-first CSS framework

---

<div align="center">

**[Back to Top](#ai-educational-platform)**

</div>
