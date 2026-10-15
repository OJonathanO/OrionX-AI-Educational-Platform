# API Documentation

> Complete REST API reference for the AI Educational Platform.

---

## Table of Contents

- [Authentication](#authentication)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Endpoints](#endpoints)
  - [Auth](#auth)
  - [Users](#users)
  - [Documents](#documents)
  - [Chat](#chat)
  - [Conversations](#conversations)
  - [Quizzes](#quizzes)
  - [Recommendations](#recommendations)
  - [Analytics](#analytics)
  - [Admin](#admin)
  - [Health](#health)

---

## Authentication

All endpoints except `/api/auth/register`, `/api/auth/login`, and `/api/health` require a valid JWT token.

### Obtaining a Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "securepassword123"
  }'
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Using the Token

Include the token in the `Authorization` header:

```bash
curl http://localhost:8000/api/documents \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Token Expiration

- Tokens expire after **24 hours** (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Expired tokens return `401 Unauthorized`
- Re-authenticate to obtain a new token

---

## Error Codes

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request succeeded |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid input data |
| `401` | Unauthorized | Missing or invalid token |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource does not exist |
| `409` | Conflict | Resource already exists |
| `413` | Payload Too Large | File exceeds size limit |
| `422` | Unprocessable Entity | Validation error |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Unexpected server error |

### Error Response Format

```json
{
  "detail": "Human-readable error message"
}
```

### Common Error Scenarios

| Scenario | Status | Response |
|----------|--------|----------|
| Invalid credentials | 401 | `{"detail": "Incorrect email or password"}` |
| Token expired | 401 | `{"detail": "Token has expired"}` |
| File too large | 413 | `{"detail": "File size exceeds 20 MB limit"}` |
| Unsupported file type | 400 | `{"detail": "Unsupported file type. Allowed: pdf, docx, txt"}` |
| Document not found | 404 | `{"detail": "Document not found"}` |
| Rate limit exceeded | 429 | `{"detail": "Rate limit exceeded. Try again later."}` |

---

## Rate Limiting

| Setting | Value |
|---------|-------|
| Default limit | 60 requests per minute |
| Scope | Per user (authenticated) or per IP (unauthenticated) |
| Response | `429 Too Many Requests` with `Retry-After` header |

### Rate Limit Headers

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1697300000
```

---

## Pagination

List endpoints support pagination via query parameters.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | Integer | 1 | Page number (1-indexed) |
| `page_size` | Integer | 20 | Items per page (max 100) |

### Response Format

```json
{
  "items": [ ... ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

### Example

```bash
curl "http://localhost:8000/api/documents?page=2&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Endpoints

### Auth

#### POST `/api/auth/register`

Register a new user account.

**Request:**

```json
{
  "email": "student@example.com",
  "password": "securepassword123",
  "full_name": "Jane Student"
}
```

**Response (201):**

```json
{
  "id": 1,
  "email": "student@example.com",
  "full_name": "Jane Student",
  "role": "student",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

#### POST `/api/auth/login`

Authenticate and receive a JWT token.

**Request:**

```json
{
  "email": "student@example.com",
  "password": "securepassword123"
}
```

**Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

---

#### POST `/api/auth/refresh`

Refresh an expiring token.

**Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

---

### Users

#### GET `/api/users/me`

Get the current user's profile.

**Response (200):**

```json
{
  "id": 1,
  "email": "student@example.com",
  "full_name": "Jane Student",
  "role": "student",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

#### PUT `/api/users/me`

Update the current user's profile.

**Request:**

```json
{
  "full_name": "Jane M. Student"
}
```

**Response (200):**

```json
{
  "id": 1,
  "email": "student@example.com",
  "full_name": "Jane M. Student",
  "role": "student",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

---

### Documents

#### POST `/api/documents/upload`

Upload a new document for ingestion.

**Request:** `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `file` | File | The document file (PDF, DOCX, TXT) |

**Response (201):**

```json
{
  "id": 7,
  "filename": "biology_chapter3.pdf",
  "file_type": "pdf",
  "file_size": 2457600,
  "title": "Biology Chapter 3: Cell Structure",
  "content_preview": "The cell is the basic unit of life...",
  "created_at": "2024-01-15T10:35:00Z"
}
```

---

#### GET `/api/documents`

List all documents for the current user.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | Integer | Page number |
| `page_size` | Integer | Items per page |
| `file_type` | String | Filter by type (pdf, docx, txt) |
| `search` | String | Search in title |

**Response (200):**

```json
{
  "items": [
    {
      "id": 7,
      "filename": "biology_chapter3.pdf",
      "file_type": "pdf",
      "file_size": 2457600,
      "title": "Biology Chapter 3: Cell Structure",
      "content_preview": "The cell is the basic unit of life...",
      "created_at": "2024-01-15T10:35:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

#### GET `/api/documents/{document_id}`

Get a specific document's details.

**Response (200):**

```json
{
  "id": 7,
  "filename": "biology_chapter3.pdf",
  "file_type": "pdf",
  "file_size": 2457600,
  "title": "Biology Chapter 3: Cell Structure",
  "content_preview": "The cell is the basic unit of life...",
  "chunk_count": 42,
  "created_at": "2024-01-15T10:35:00Z"
}
```

---

#### DELETE `/api/documents/{document_id}`

Delete a document and all its associated chunks and vectors.

**Response (204):** No content

---

### Chat

#### POST `/api/chat/message`

Send a message and receive an AI-generated response.

**Request:**

```json
{
  "conversation_id": 12,
  "message": "What is the role of mitochondria in the cell?"
}
```

**Response (200):**

```json
{
  "id": 156,
  "conversation_id": 12,
  "role": "assistant",
  "content": "The mitochondria is known as the powerhouse of the cell because it generates most of the cell's ATP through oxidative phosphorylation [Source 1].\n\nKey functions include:\n- ATP production via the electron transport chain [Source 1]\n- Regulation of cellular metabolism [Source 2]\n\n**Sources:**\n- [Source 1] Biology Chapter 3, Page 12\n- [Source 2] Cell Biology Textbook, Page 45",
  "citations": [
    {
      "source_index": 1,
      "document_id": 7,
      "document_title": "Biology Chapter 3",
      "page_number": 12,
      "chunk_index": 3
    },
    {
      "source_index": 2,
      "document_id": 8,
      "document_title": "Cell Biology Textbook",
      "page_number": 45,
      "chunk_index": 12
    }
  ],
  "created_at": "2024-01-15T10:40:00Z"
}
```

---

#### GET `/api/chat/{conversation_id}/messages`

Get all messages in a conversation.

**Response (200):**

```json
{
  "items": [
    {
      "id": 155,
      "conversation_id": 12,
      "role": "user",
      "content": "What is the role of mitochondria in the cell?",
      "citations": null,
      "created_at": "2024-01-15T10:39:00Z"
    },
    {
      "id": 156,
      "conversation_id": 12,
      "role": "assistant",
      "content": "The mitochondria is known as the powerhouse...",
      "citations": [ ... ],
      "created_at": "2024-01-15T10:40:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

---

### Conversations

#### POST `/api/conversations`

Create a new conversation.

**Request:**

```json
{
  "title": "Biology Study Session"
}
```

**Response (201):**

```json
{
  "id": 12,
  "user_id": 1,
  "title": "Biology Study Session",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

#### GET `/api/conversations`

List all conversations for the current user.

**Response (200):**

```json
{
  "items": [
    {
      "id": 12,
      "title": "Biology Study Session",
      "message_count": 8,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:40:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

#### GET `/api/conversations/{conversation_id}`

Get a specific conversation.

**Response (200):**

```json
{
  "id": 12,
  "title": "Biology Study Session",
  "message_count": 8,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:40:00Z"
}
```

---

#### DELETE `/api/conversations/{conversation_id}`

Delete a conversation and all its messages.

**Response (204):** No content

---

### Quizzes

#### POST `/api/quizzes/generate`

Generate a quiz from uploaded documents.

**Request:**

```json
{
  "topic": "Cell Biology",
  "question_count": 5,
  "difficulty": "medium"
}
```

**Response (201):**

```json
{
  "id": 3,
  "title": "Cell Biology Quiz",
  "topic": "Cell Biology",
  "question_count": 5,
  "questions": [
    {
      "id": 1,
      "question": "What is the primary function of mitochondria?",
      "options": [
        "Protein synthesis",
        "ATP production",
        "Lipid storage",
        "Cell division"
      ],
      "correct_answer": "ATP production",
      "explanation": "Mitochondria generate most of the cell's ATP through oxidative phosphorylation."
    }
  ],
  "created_at": "2024-01-15T10:45:00Z"
}
```

---

#### GET `/api/quizzes`

List all quizzes for the current user.

**Response (200):**

```json
{
  "items": [
    {
      "id": 3,
      "title": "Cell Biology Quiz",
      "topic": "Cell Biology",
      "question_count": 5,
      "best_score": null,
      "created_at": "2024-01-15T10:45:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

#### GET `/api/quizzes/{quiz_id}`

Get a specific quiz with questions.

**Response (200):**

```json
{
  "id": 3,
  "title": "Cell Biology Quiz",
  "topic": "Cell Biology",
  "questions": [ ... ],
  "created_at": "2024-01-15T10:45:00Z"
}
```

---

#### POST `/api/quizzes/{quiz_id}/submit`

Submit quiz answers.

**Request:**

```json
{
  "answers": [
    {
      "question_id": 1,
      "selected_answer": "ATP production"
    },
    {
      "question_id": 2,
      "selected_answer": "Nucleus"
    }
  ]
}
```

**Response (200):**

```json
{
  "quiz_id": 3,
  "score": 4,
  "total": 5,
  "percentage": 80.0,
  "results": [
    {
      "question_id": 1,
      "selected_answer": "ATP production",
      "correct_answer": "ATP production",
      "is_correct": true
    },
    {
      "question_id": 2,
      "selected_answer": "Nucleus",
      "correct_answer": "Ribosome",
      "is_correct": false
    }
  ]
}
```

---

### Recommendations

#### GET `/api/recommendations`

Get personalized document and topic recommendations.

**Response (200):**

```json
{
  "documents": [
    {
      "id": 9,
      "title": "Advanced Cell Biology",
      "reason": "Based on your interest in cell structure",
      "relevance_score": 0.87
    }
  ],
  "topics": [
    {
      "name": "Protein Synthesis",
      "reason": "Related to your recent quiz on cell biology",
      "relevance_score": 0.72
    }
  ],
  "generated_at": "2024-01-15T10:50:00Z"
}
```

---

### Analytics

#### GET `/api/analytics/overview`

Get learning analytics overview for the current user.

**Response (200):**

```json
{
  "documents_uploaded": 7,
  "conversations_count": 12,
  "messages_sent": 156,
  "quizzes_taken": 5,
  "average_quiz_score": 82.5,
  "total_study_time_minutes": 340,
  "topic_mastery": [
    {
      "topic": "Cell Biology",
      "mastery_score": 0.85
    },
    {
      "topic": "Genetics",
      "mastery_score": 0.62
    }
  ],
  "recent_activity": [
    {
      "type": "quiz_completed",
      "description": "Scored 80% on Cell Biology Quiz",
      "timestamp": "2024-01-15T10:50:00Z"
    }
  ]
}
```

---

#### GET `/api/analytics/progress`

Get detailed progress metrics over time.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | Date | Start date (ISO 8601) |
| `end_date` | Date | End date (ISO 8601) |
| `metric` | String | Specific metric to retrieve |

**Response (200):**

```json
{
  "daily_scores": [
    {
      "date": "2024-01-15",
      "quiz_average": 80.0,
      "documents_uploaded": 2,
      "messages_sent": 24
    }
  ],
  "topic_progress": [
    {
      "topic": "Cell Biology",
      "scores": [75, 80, 85],
      "trend": "improving"
    }
  ]
}
```

---

### Admin

#### GET `/api/admin/users`

List all users (Admin only).

**Response (200):**

```json
{
  "items": [
    {
      "id": 1,
      "email": "student@example.com",
      "full_name": "Jane Student",
      "role": "student",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

---

#### PUT `/api/admin/users/{user_id}/role`

Update a user's role (Admin only).

**Request:**

```json
{
  "role": "instructor"
}
```

**Response (200):**

```json
{
  "id": 1,
  "email": "student@example.com",
  "full_name": "Jane Student",
  "role": "instructor",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

---

#### GET `/api/admin/stats`

Get system-wide statistics (Admin only).

**Response (200):**

```json
{
  "total_users": 50,
  "total_documents": 234,
  "total_conversations": 1024,
  "total_messages": 5678,
  "active_users_today": 12,
  "storage_used_mb": 512.5
}
```

---

### Health

#### GET `/api/health`

System health check (no authentication required).

**Response (200):**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "vector_store": "connected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

<div align="center">

**[Back to Top](#api-documentation)**

</div>
