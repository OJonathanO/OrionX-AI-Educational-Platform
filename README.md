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


