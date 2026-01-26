# 🧠 Microcourses Pipeline

An end-to-end system for automatically generating **multilingual digital micro-courses** from research articles (PDFs).  
This project extracts, standardizes, and summarizes content from academic papers to create concise learning materials in slide format.

---

## 🎯 Project Objective

The main goal of this course project is to simulate a **real-world software development process** where a team collaboratively designs and implements a complete application using **Python** and modern web technologies.

The system automatically:

1. Extracts **text**, **graphics**, **charts** and **tables** from uploaded PDFs.
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
  - Table extraction and rendering
  - Chart and graph extraction
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

---

## 🏗️ System Architecture

```text
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
│  - PDF upload endpoint      │
│  - DB models (Document, Page, Block)
│  - MinIO / Supabase storage │
│  - Triggers processing      │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│          Worker / Pipeline  │
│  - Text extraction          │
│  - Table extraction         │
│  - Chart/Graph extraction   │
│  - Summarization (Ollama)   │
│  - Chunking, translation    │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│        PostgreSQL + MinIO   │
│  - Documents + Pages + Blocks│
│  - File storage & retrieval │
└─────────────────────────────┘
```

---

## 🧱 Tech Stack

| Layer         | Technology                             | Purpose                                 |
| ------------- | -------------------------------------- | --------------------------------------- |
| Frontend      | Next.js 15 + TypeScript + Tailwind CSS | Upload UI, results display              |
| Backend       | FastAPI                                | REST API, DB orchestration              |
| Database      | PostgreSQL                             | Store document metadata                 |
| File Storage  | MinIO / Supabase Storage               | PDF and assets                          |
| Worker        | Celery                                 | Background processing                   |
| Summarization | Gemini                                 | Text summarization, multilingual output |
| PDF Parsing   | Text extraction service                | Text, table, chart & graph extraction   |

---

## 📂 Frontend

The frontend is built with **Next.js 15** and provides a modern, responsive interface for interacting with the pipeline.

### Key Components

| Component          | File                            | Description                                       |
| ------------------ | ------------------------------- | ------------------------------------------------- |
| **DragDropUpload** | `components/DragDropUpload.tsx` | Drag-and-drop file upload with progress indicator |
| **DocumentList**   | `components/DocumentList.tsx`   | Displays all uploaded documents with status       |
| **SlideViewer**    | `components/SlideViewer.tsx`    | View generated slides in presentation mode        |
| **SlideEditor**    | `components/SlideEditor.tsx`    | Edit slide content and structure                  |
| **ChartRenderer**  | `components/ChartRenderer.tsx`  | Renders extracted charts and graphs               |
| **QuizViewer**     | `components/QuizViewer.tsx`     | Interactive quiz based on generated questions     |
| **SummaryViewer**  | `components/SummaryViewer.tsx`  | View document summary and key insights            |
| **ChatAssistant**  | `components/ChatAssistant.tsx`  | AI-powered chat for document Q&A                  |
| **Navbar**         | `components/Navbar.tsx`         | Navigation header                                 |

### Pages

| Route             | Description                                         |
| ----------------- | --------------------------------------------------- |
| `/`               | Home page with upload form and document list        |
| `/documents/[id]` | Document detail page with slides, quiz, and summary |
| `/courses`        | Course management (planned)                         |

### Tech Stack

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **React Hooks** - State management

---

## ⚙️ Backend

The backend is a **FastAPI** application that handles document upload, processing, and API endpoints.

### Models

| Model               | Description                                              |
| ------------------- | -------------------------------------------------------- |
| **Document**        | Main document record with status and metadata            |
| **Page**            | Individual pages from the document                       |
| **Block**           | Content blocks (text, table, figure) with coordinates    |
| **Slide**           | Generated slide with title, summary, and visualizations  |
| **Question**        | Review questions for quizzes                             |
| **DocumentSummary** | Executive summary, key concepts, and learning objectives |

### Processing Pipeline

1. **Upload** - Document uploaded via API and stored in MinIO
2. **Text Extraction** - Content extracted from PDF (text, tables, charts)
3. **Parsing** - Raw content parsed into structured blocks
4. **Slide Generation** - Slides created from content blocks using LLM
5. **Quiz Generation** - Review questions generated per subchapter
6. **Summary** - Document summary and insights created

**Interactive API Documentation:** http://localhost:8000/docs

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (local or Supabase)
- MinIO (or Supabase Storage)
- (Optional) Docker & Docker Compose for all-in-one setup

### Backend Setup

```bash
cd backend
python -m venv .venv
# Activate (Windows)
.\.venv\Scripts\activate
# Activate (Linux/macOS)
source .venv/bin/activate
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --port 8000
```

Backend runs on http://localhost:8000

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:3000

---

## 🧪 Development Notes

- Tables and figures are extracted and rendered in slides
- Summarization prompts are designed to:
  - Extract learning objectives
  - Highlight core insights
  - Compress text without losing meaning
- Future integration of Supabase can simplify deployment (Postgres + Storage + Auth)

---

## 📄 License

This project is for educational purposes as part of a university course project.
