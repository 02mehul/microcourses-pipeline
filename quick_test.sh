#!/bin/bash

# Quick Test Script - One command to test everything
# Usage: ./quick_test.sh

echo "🚀 Microcourses Pipeline - Quick Test"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ] && [ ! -d "infra" ]; then
    echo "❌ Error: Must run from project root"
    exit 1
fi

# Step 1: Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Creating backend/.env file..."
    cat > backend/.env << 'EOF'
LLAMA_CLOUD_API_KEY=llx-your-key-here
GEMINI_API_KEY=your-gemini-key-here
EOF
    echo "📝 Please edit backend/.env with your API keys!"
    echo "   Then run this script again."
    exit 0
fi

# Step 2: Reset and start backend
echo "1️⃣  Resetting database and starting backend..."
./reset_db.sh
if [ $? -ne 0 ]; then
    echo "❌ Failed to start backend"
    exit 1
fi

echo ""
echo "2️⃣  Waiting for backend to be ready..."
sleep 5

# Test backend
for i in {1..10}; do
    if curl -s http://localhost:8000 > /dev/null 2>&1; then
        echo "✅ Backend is running at http://localhost:8000"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ Backend not responding after 10 seconds"
        echo "   Check logs: docker-compose -f infra/docker-compose.yml logs backend"
        exit 1
    fi
    sleep 1
done

echo ""
echo "3️⃣  Starting frontend..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

echo ""
echo "✅ All set! Starting frontend..."
echo ""
echo "📋 Test Checklist:"
echo "   1. Browser will open to http://localhost:3000"
echo "   2. Upload docs/dwr-25-45-1.docx"
echo "   3. Wait ~2-3 minutes for processing"
echo "   4. Check slides for chapter/subchapter breadcrumbs"
echo "   5. Check quiz for grouped questions"
echo "   6. View parsed markdown: cat backend/docs/dwr-25-45-1_parsed.md"
echo ""
echo "🔍 Useful commands:"
echo "   - Backend logs: docker-compose -f infra/docker-compose.yml logs -f backend"
echo "   - Check document: curl http://localhost:8000/documents/1"
echo "   - Stop all: docker-compose -f infra/docker-compose.yml down"
echo ""
echo "Press Ctrl+C to stop frontend when done testing"
echo ""

# Start frontend
npm run dev
