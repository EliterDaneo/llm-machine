# PDF Intelligence - Backend Setup Guide

## Tech Stack

- **FastAPI** - Web framework
- **PostgreSQL** + asyncpg - Database
- **SQLAlchemy 2.0** (async) - ORM
- **PyMuPDF** - PDF extraction
- **Google Gemini** → **Groq** - AI providers (auto-fallback)
- **JWT** (python-jose) + **bcrypt** - Auth

---

## Quick Start

### 1. Clone & navigate

```bash
cd pdf-intelligence-app/backend
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your values:
# - DATABASE_URL (your PostgreSQL connection)
# - GEMINI_API_KEY (from Google AI Studio)
# - GROQ_API_KEY (from console.groq.com)
# - SECRET_KEY (random 32+ char string)
```

### 5. Create PostgreSQL database

```sql
CREATE DATABASE pdf_intelligence;
```

### 6. Run the server

```bash
# Development (auto-creates tables)
uvicorn app.main:app --reload --port 8000

# Or using the main.py entrypoint
python -m app.main
```

### 7. Access API docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

---

## API Endpoints

### Authentication

| Method | Path                       | Description              |
| ------ | -------------------------- | ------------------------ |
| POST   | `/api/v1/auth/register`    | Register new user        |
| POST   | `/api/v1/auth/login`       | Login, get JWT tokens    |
| POST   | `/api/v1/auth/refresh`     | Refresh access token     |
| GET    | `/api/v1/auth/me`          | Get current user profile |
| PUT    | `/api/v1/auth/me`          | Update profile           |
| PUT    | `/api/v1/auth/me/password` | Change password          |

### Documents

| Method | Path                                           | Description             |
| ------ | ---------------------------------------------- | ----------------------- |
| POST   | `/api/v1/documents/upload`                     | Upload PDF              |
| POST   | `/api/v1/documents/analyze`                    | Run AI analysis         |
| POST   | `/api/v1/documents/chat`                       | Chat with document      |
| PUT    | `/api/v1/documents/chat/{id}/feedback`         | Rate a response         |
| GET    | `/api/v1/documents/`                           | List all documents      |
| GET    | `/api/v1/documents/{id}`                       | Get document detail     |
| DELETE | `/api/v1/documents/{id}`                       | Delete document         |
| GET    | `/api/v1/documents/history`                    | Chat & analysis history |
| GET    | `/api/v1/documents/chat/{session_id}/messages` | Get chat session        |
| GET    | `/api/v1/documents/stats`                      | Dashboard statistics    |

---

## AI Provider Setup

### Google Gemini (Primary)

1. Go to https://aistudio.google.com
2. Create an API key
3. Add to `.env`: `GEMINI_API_KEY=your-key`

### Groq (Fallback)

1. Go to https://console.groq.com
2. Create an API key
3. Add to `.env`: `GROQ_API_KEY=your-key`

The system automatically falls back to Groq if Gemini fails.

---

## Database Migration (Production)

```bash
# Initialize Alembic
alembic init alembic

# Generate migration
alembic revision --autogenerate -m "initial schema"

# Apply migration
alembic upgrade head
```

---

## Quota System

| Plan       | Daily Analyses | Storage |
| ---------- | -------------- | ------- |
| Free       | 5/day          | 50 MB   |
| Pro        | 50/day         | 500 MB  |
| Enterprise | 500/day        | 5 GB    |
