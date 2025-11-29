# 🚀 Quick Start - Docker Testing

## One-Command Test

```bash
./quick_test.sh
```

This will:
1. ✅ Check/create `.env` file
2. ✅ Reset database and rebuild backend
3. ✅ Start all Docker services
4. ✅ Install frontend dependencies
5. ✅ Start frontend development server
6. ✅ Open browser to http://localhost:3000

---

## Manual Testing Steps

If you prefer step-by-step:

### 1. Setup API Keys (First Time Only)

```bash
cat > backend/.env << 'EOF'
LLAMA_CLOUD_API_KEY=llx-your-actual-key
GEMINI_API_KEY=your-actual-gemini-key
EOF
```

### 2. Reset Database & Start Backend

```bash
./reset_db.sh
```

### 3. Start Frontend

```bash
cd frontend
npm install  # First time only
npm run dev
```

### 4. Test!

1. Open http://localhost:3000
2. Upload `docs/dwr-25-45-1.docx`
3. Wait ~2-3 minutes
4. View results!

---

## What to Expect

### ✅ Slides Tab

You should see:
```
┌─────────────────────────────────┐
│ Chapter Name                   │ ← Shows chapter context
│ Subchapter Name                │ ← Shows subchapter context
├─────────────────────────────────┤
│ Slide Title                    │
│ • Key point 1                  │
│ • Key point 2                  │
│ • Key point 3                  │
└─────────────────────────────────┘
```

### ✅ Review Quiz Tab

You should see questions grouped by subchapter:
```
📖 Subchapter Name (4 questions)
───────────────────────────────────
❶ Question 1 about this section...
❷ Question 2 about this section...
❸ Question 3 about this section...
❹ Question 4 about this section...

📖 Another Subchapter (3 questions)
───────────────────────────────────
❶ Question 1 about this section...
...
```

### ✅ Parsed Markdown

Check the markdown output:
```bash
cat backend/docs/dwr-25-45-1_parsed.md
```

This shows exactly what LlamaParse extracted from your document.

---

## Monitoring

### View Backend Logs
```bash
docker-compose -f infra/docker-compose.yml logs -f backend
```

### Check Processing Status
```bash
# List all documents
curl http://localhost:8000/documents/

# Get specific document details
curl http://localhost:8000/documents/1 | jq
```

### Check Database
```bash
docker-compose -f infra/docker-compose.yml exec postgres psql -U mcourses -d mcourses

# Then run SQL:
SELECT id, filename, status FROM documents;
SELECT id, slide_number, chapter_title, subchapter_title FROM slides;
SELECT id, subchapter_title, question_text FROM questions;
```

---

## Troubleshooting

### Backend won't start

```bash
# Check logs
docker-compose -f infra/docker-compose.yml logs backend

# Common fix: rebuild
cd infra
docker-compose down
docker-compose build backend
docker-compose up -d
```

### Document stuck in RUNNING

```bash
# Check backend logs for errors
docker-compose -f infra/docker-compose.yml logs backend | grep -i error

# Common causes:
# - Invalid API keys
# - Network timeout
# - Gemini rate limit

# Check API keys are loaded
docker-compose -f infra/docker-compose.yml exec backend env | grep API
```

### No markdown file created

```bash
# Check if docs directory exists in container
docker-compose -f infra/docker-compose.yml exec backend ls -la /app/docs/

# Check if volume is mounted
docker-compose -f infra/docker-compose.yml exec backend df -h | grep docs
```

### Frontend can't connect

```bash
# Verify backend is accessible
curl http://localhost:8000/documents/

# Check CORS settings
curl -H "Origin: http://localhost:3000" http://localhost:8000/documents/
```

---

## File Locations

### On Your Computer (Host)
```
backend/docs/dwr-25-45-1_parsed.md  ← Parsed markdown
backend/.env                         ← API keys
backend/backend.log                  ← Application logs (if exists)
```

### Inside Docker Container
```
/app/docs/dwr-25-45-1_parsed.md     ← Parsed markdown (same as host)
/app/app/services/pipeline.py       ← Processing logic
/app/migrations/                     ← Database migrations
```

---

## Success Criteria ✅

You know it's working when:

1. ✅ Upload shows "SUCCESS" status after ~2-3 minutes
2. ✅ Markdown file exists in `backend/docs/`
3. ✅ Slides show chapter/subchapter breadcrumbs
4. ✅ Questions are grouped by subchapter in quiz tab
5. ✅ Each subchapter has 3-4 questions

---

## Clean Up

### Stop Everything
```bash
cd infra
docker-compose down
```

### Remove All Data (Fresh Start)
```bash
cd infra
docker-compose down -v  # -v removes volumes
./reset_db.sh
```

---

## Additional Resources

- **Full Docker Guide:** See `DOCKER_TESTING.md`
- **Implementation Details:** See `MILESTONE_IMPLEMENTATION.md`
- **Backend API Docs:** http://localhost:8000/docs (when running)

---

## Quick Commands Reference

```bash
# Start everything
./quick_test.sh

# Just reset backend
./reset_db.sh

# View logs
docker-compose -f infra/docker-compose.yml logs -f backend

# Stop everything
docker-compose -f infra/docker-compose.yml down

# Rebuild backend
cd infra && docker-compose build backend

# Access database
docker-compose -f infra/docker-compose.yml exec postgres psql -U mcourses -d mcourses
```

---

Happy Testing! 🎉
