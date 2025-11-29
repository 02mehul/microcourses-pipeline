# Docker Testing Guide - Milestone 2 & 3

## 🐳 Quick Start with Docker

### Step 1: Reset Database & Rebuild Backend

```bash
./reset_db.sh
```

This will:
- Stop all Docker services
- Clear PostgreSQL database volume
- Rebuild backend container with new code
- Start all services (PostgreSQL, MinIO, Backend)

### Step 2: Start Frontend (Locally)

```bash
cd frontend
npm install  # If first time
npm run dev
```

### Step 3: Test the System

1. **Open browser:** http://localhost:3000
2. **Upload test document:** `docs/dwr-25-45-1.docx`
3. **Wait 2-3 minutes** for processing
4. **View results** in slides and quiz tabs

---

## 📋 Detailed Testing Steps

### 1️⃣ Verify Backend is Running

```bash
curl http://localhost:8000
```

Expected output:
```json
{"detail":"Not Found"}
```
(This is normal - means FastAPI is running)

### 2️⃣ Check Backend Logs

```bash
docker-compose -f infra/docker-compose.yml logs -f backend
```

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3️⃣ Upload Document via Frontend

- Go to http://localhost:3000
- Click "Upload Document"
- Select `docs/dwr-25-45-1.docx`
- Click Upload

### 4️⃣ Monitor Processing

**Watch backend logs:**
```bash
docker-compose -f infra/docker-compose.yml logs -f backend
```

You should see:
```
INFO: Processing document 1: dwr-25-45-1.docx
INFO: Sending to LlamaParse...
INFO: LlamaParse returned X pages
INFO: Saved markdown to: /app/docs/dwr-25-45-1_parsed.md
INFO: Detected X subchapters
INFO: Generated X slides from document
INFO: Generating questions for X subchapters...
INFO: Document 1 processed successfully
```

### 5️⃣ View Parsed Markdown

**Option A - Inside Container:**
```bash
docker-compose -f infra/docker-compose.yml exec backend cat /app/docs/dwr-25-45-1_parsed.md
```

**Option B - From Host (if volume mounted):**
```bash
cat backend/docs/dwr-25-45-1_parsed.md
```

### 6️⃣ Check Results in Frontend

**Slides Tab:**
- Should show chapter/subchapter breadcrumbs at top
- Example:
  ```
  Economic Analysis
  Labor Market Trends
  ───────────────────
  Current Employment Statistics
  • Point 1
  • Point 2
  ```

**Review Quiz Tab:**
- Questions grouped by subchapter
- Each section has header with subchapter name
- 3-4 questions per subchapter

---

## 🔍 Verification Checklist

### ✅ Backend Checks

```bash
# Check container is running
docker ps | grep backend

# Check database tables exist
docker-compose -f infra/docker-compose.yml exec postgres psql -U mcourses -d mcourses -c "\dt"

# Should see: documents, pages, blocks, slides, questions tables
```

### ✅ Database Schema Verification

```bash
# Check slides table has new columns
docker-compose -f infra/docker-compose.yml exec postgres psql -U mcourses -d mcourses -c "SELECT column_name FROM information_schema.columns WHERE table_name='slides';"
```

Should include:
- `chapter_title`
- `subchapter_title`
- `subchapter_id`

### ✅ MinIO Storage Check

```bash
# Open MinIO console
open http://localhost:9001

# Login: minio / minio123
# Check "documents" bucket - should have uploaded file
```

---

## 🐛 Troubleshooting

### Issue: Backend container not starting

```bash
# Check logs
docker-compose -f infra/docker-compose.yml logs backend

# Common issues:
# 1. Missing API keys in .env
# 2. Database not ready
```

**Solution:**
```bash
# Make sure .env exists with:
echo "LLAMA_CLOUD_API_KEY=llx-your-key" > backend/.env
echo "GEMINI_API_KEY=your-key" >> backend/.env

# Restart
./reset_db.sh
```

### Issue: Database migration errors

**Check current schema:**
```bash
docker-compose -f infra/docker-compose.yml exec postgres psql -U mcourses -d mcourses -c "\d slides"
```

**Solution - Force rebuild:**
```bash
cd infra
docker-compose down -v  # Remove volumes
docker-compose up -d
```

### Issue: "Connection refused" to backend

```bash
# Check backend is listening on correct port
docker-compose -f infra/docker-compose.yml ps

# Should show:
# backend    0.0.0.0:8000->8000/tcp
```

### Issue: Frontend can't connect to backend

**Check CORS settings in `backend/app/main.py`:**
```python
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

### Issue: Document stuck in "RUNNING" status

**Check backend logs for errors:**
```bash
docker-compose -f infra/docker-compose.yml logs backend | grep -i error
```

**Common causes:**
- LlamaParse API key invalid
- Gemini API key invalid
- Network timeout

**Manually check document status:**
```bash
curl http://localhost:8000/documents/1
```

---

## 📊 Expected Results

### Processing Timeline

1. **Upload (instant):** Document saved to MinIO
2. **Parsing (1-2 min):** LlamaParse extracts content
3. **Markdown saved (instant):** File written to `/app/docs/`
4. **Block parsing (5-10 sec):** Structure detected
5. **Chunking (instant):** Subchapters identified
6. **Slide generation (30-60 sec):** Gemini creates slides
7. **Question generation (30-60 sec):** Gemini creates questions

**Total:** ~2-4 minutes

### Sample Output

**Markdown file size:** ~20-50 KB depending on document

**Expected slides:**
- Short document (5-10 pages): 3-7 slides
- Medium document (10-20 pages): 8-15 slides

**Expected questions:**
- 3-4 questions per subchapter
- Total: (number of subchapters) × 3-4

---

## 🔧 Useful Commands

### Restart Everything
```bash
cd infra
docker-compose restart
```

### View All Logs
```bash
docker-compose -f infra/docker-compose.yml logs -f
```

### Access Backend Shell
```bash
docker-compose -f infra/docker-compose.yml exec backend bash
```

### Access Database
```bash
docker-compose -f infra/docker-compose.yml exec postgres psql -U mcourses -d mcourses
```

### Check Document Processing Status
```bash
# List all documents
curl http://localhost:8000/documents/

# Get specific document
curl http://localhost:8000/documents/1
```

### Force Rebuild Backend
```bash
cd infra
docker-compose build --no-cache backend
docker-compose up -d backend
```

---

## 📁 File Locations in Docker

### Backend Container (`/app/`)

```
/app/
├── docs/                           # Parsed markdown files
│   └── dwr-25-45-1_parsed.md
├── app/
│   ├── main.py
│   ├── models.py
│   └── services/
│       ├── pipeline.py
│       ├── content_processor.py
│       └── llamaparse.py
└── .env                            # API keys
```

### Volumes

```bash
# Database data
docker volume inspect infra_pgdata

# MinIO data
docker volume inspect infra_minio_data
```

---

## 🎯 Success Criteria

### ✅ You'll know it's working when:

1. **Upload succeeds** - Document appears in list with "PENDING" status
2. **Processing runs** - Status changes to "RUNNING"
3. **Markdown saved** - File exists in `backend/docs/`
4. **Processing completes** - Status changes to "SUCCESS"
5. **Slides visible** - Can navigate slides with chapter/subchapter breadcrumbs
6. **Questions visible** - Questions grouped by subchapter in quiz tab

### ❌ Red flags:

- Status stuck in "RUNNING" for > 5 minutes
- Status changes to "FAILED"
- No slides generated
- No questions generated
- Frontend shows empty state

---

## 💡 Tips

1. **First time setup:**
   ```bash
   # Install frontend dependencies
   cd frontend && npm install

   # Create backend .env
   cat > backend/.env << EOF
   LLAMA_CLOUD_API_KEY=llx-your-key-here
   GEMINI_API_KEY=your-gemini-key-here
   EOF
   ```

2. **Check API keys are loaded:**
   ```bash
   docker-compose -f infra/docker-compose.yml exec backend env | grep API
   ```

3. **Test with smaller document first:**
   - Use a 2-3 page PDF/DOCX to verify setup
   - Then try `dwr-25-45-1.docx`

4. **Monitor resource usage:**
   ```bash
   docker stats
   ```

---

## 🚀 Ready to Test!

Run this to start:
```bash
./reset_db.sh && cd frontend && npm run dev
```

Then open http://localhost:3000 and upload `docs/dwr-25-45-1.docx`!
