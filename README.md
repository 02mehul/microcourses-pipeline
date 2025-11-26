📘 README.md

# 🧠 Microcourses Pipeline

An end-to-end system for automatically generating **multilingual digital micro-courses** from research articles (PDFs).  
This project extracts, standardizes, and summarizes content from academic papers to create concise learning materials in slide format.

---

## 🎯 Project Objective

The main goal of this course project is to simulate a **real-world software development process** where a team collaboratively designs and implements a complete application using **Python** and modern web technologies.

The system automatically:

1. Extracts **text**, **graphics**, and **tables** from uploaded PDFs.
2. Converts the extracted data into a **standardized structured format**.
3. Generates **expressive, learning-oriented summaries** using **LLM models (Ollama / Mistral)**.
4. Prepares the content for micro-course slides (PowerPoint-like).
5. Manages and reviews course sections through a clean **web interface**.

---

## 🚀 Quick Start

### Using Docker (Recommended)

The fastest way to get the entire system running:

```bash
# 1. Clone repository
git clone <your-repo-url>
cd microcourses-pipeline

# 2. Start all services with Docker Compose
cd infra
docker-compose up --build

# 3. Wait for services to be ready (~30-60 seconds)
# Services will be available at:
# - Backend API: http://localhost:8000
# - API Documentation: http://localhost:8000/docs
# - Frontend UI: http://localhost:3000
# - MinIO Console: http://localhost:9001 (credentials: minio / minio123)

# 4. Upload a PDF via the web interface
# Open http://localhost:3000 in your browser
# Or use curl:
curl -X POST "http://localhost:8000/documents" \
  -F "file=@example.pdf"

# 5. View extracted content
# The response will include a document_id
# Navigate to: http://localhost:3000/documents/{document_id}
```

**What's Running:**

- **Backend** (FastAPI) - Port 8000
- **Frontend** (Next.js) - Port 3000
- **PostgreSQL** - Port 5432
- **MinIO** (S3-compatible storage) - Ports 9000, 9001
- **Redis** - Port 6379
- **Ollama** (LLM) - Port 11434

**Stopping the system:**

```bash
cd infra
docker-compose down
```

**Clean restart (removes all data):**

```bash
cd infra
docker-compose down -v
docker-compose up --build
```

---

## 🧩 Features

### 🔹 Core Pipeline

- **PDF Upload:** Users can upload research articles via a web interface.
- **Automatic Processing:**
  - Text extraction (with coordinates)
  - Table and figure detection (planned)
  - Metadata and layout parsing
- **Standardization:** Each content block (text, table, figure) is annotated with page & position data.
- **Chunking:** Groups related text blocks into meaningful course sections.
- **Summarization:** Uses **Ollama / Mistral models** to produce concise, didactic learning text.
- **Multilingual Support:** Can generate translated summaries or learning content (planned).

### 🔹 Web Interface

- Simple **upload UI** built with **Next.js + Tailwind CSS**.
- Displays processing status and extracted document structure.
- Backend exposed via REST API (FastAPI).

### 🔹 Backend API

- **FastAPI** application providing:
  - `/documents` → upload and manage documents
  - `/documents/{id}` → retrieve processing status
  - `/documents/{id}/blocks` → list extracted text blocks with coordinates
- Built-in **CORS** configuration for frontend compatibility.

### 🔹 Data Storage

- **PostgreSQL** for structured metadata (documents, pages, blocks).
- **MinIO / Supabase Storage** for PDF file storage.
- Designed for **cloud compatibility** and containerized deployment.

### 🔹 Planned Enhancements

- Automatic **table** and **graph** extraction.
- **OCR integration** (Mistral OCR / Tesseract) for scanned documents.
- Advanced summarization prompts for educational tone.
- Chunk-level **embeddings** for retrieval / semantic search.
- Export to PowerPoint / JSON course format.

---

## 🏗️ System Architecture

````text
┌─────────────────────────────┐
│         Frontend (Next.js)  │
│  - Upload PDF               │
│  - View Status              │
│  - Interact with API        │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│         FastAPI Backend     │
│  - PDF upload endpoint       │
│  - DB models (Document, Page, Block)
│  - MinIO / Supabase storage  │
│  - Triggers processing       │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│          Worker / Pipeline  │
│  - Extract text & layout     │
│  - OCR / Mistral OCR         │
│  - Summarization (Ollama)    │
│  - Chunking, translation     │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│        PostgreSQL + MinIO   │
│  - Documents + Pages + Blocks│
│  - File storage & retrieval  │
└─────────────────────────────┘

🧱 Tech Stack
Layer	Technology	Purpose
Frontend	Next.js 15
 + TypeScript
 + Tailwind CSS
	Upload UI, results display
Backend	FastAPI
	REST API, DB orchestration
Database	PostgreSQL
	Store document metadata
File Storage	MinIO
 / Supabase Storage
	PDF and assets
Worker	Celery
 (planned)	Background processing
Queue	Redis
 (planned)	Task broker
Summarization	Ollama
 / Mistral
	Text summarization, multilingual output
PDF Parsing	PyMuPDF (fitz)
	Text & coordinate extraction
OCR (optional)	Mistral OCR API
 / Tesseract
	For scanned documents
⚙️ Setup & Installation
Prerequisites

Python 3.11+

Node.js 18+

PostgreSQL (local or Supabase)

MinIO (or Supabase Storage)

(Optional) Docker & Docker Compose for all-in-one setup

Backend Setup
cd backend
python -m venv .venv
# Activate (Windows)
.\.venv\Scripts\activate
# Activate (Linux/macOS)
source .venv/bin/activate
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --port 8000


Backend runs on http://localhost:8000

Frontend Setup
cd frontend
npm install
npm run dev


Frontend runs on http://localhost:3000

## 🌐 API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/documents` | GET | List all documents (supports pagination & filtering) |
| `/documents` | POST | Upload a PDF |
| `/documents/{id}` | GET | Get document details with all extracted content |
| `/documents/{id}/blocks` | GET | List extracted text blocks (flattened view) |

**Interactive API Documentation:** http://localhost:8000/docs

### Example Usage

**Upload a PDF:**
```bash
curl -X POST "http://localhost:8000/documents" \
  -F "file=@example.pdf"
````

**List all documents:**

```bash
curl "http://localhost:8000/documents?limit=10&status=SUCCESS"
```

**Get document details:**

```bash
curl "http://localhost:8000/documents/1"
```

🧠 Summarization & Chunking (Planned Workflow)

Divide extracted text into logical chunks (e.g., sections, paragraphs).

Generate learning-oriented summaries using:

Ollama (local)

or Mistral API (cloud)

Produce multilingual variants (en, de, etc.)

Export structured data for slide creation:

Slide title

Key points

Linked graphics/tables

🧪 Development Notes

Tables and figures are planned to use Camelot / layoutparser.

Summarization prompts are designed to:

extract learning objectives

highlight core insights

compress text without losing meaning.

Future integration of Supabase can simplify deployment (Postgres + Storage + Auth).

📦 Project Structure
microcourses/
│
├── backend/
│ ├── app/
│ │ ├── main.py
│ │ ├── db.py
│ │ ├── config.py
│ │ ├── models.py
│ │ ├── routes/
│ │ ├── services/
│ │ └── schemas.py
│ └── requirements.txt
│
├── frontend/
│ ├── src/
│ │ ├── app/
│ │ │ └── upload/page.tsx
│ │ └── components/
│ ├── package.json
│ └── tsconfig.json
│
├── infra/ # Docker & deployment (planned)
├── docs/ # Documentation, architecture notes
└── README.md
