#!/bin/bash

echo "🧪 Testing Table Support in Slides"
echo "=================================="
echo ""

# Check if backend is running
echo "1️⃣  Checking if backend is running..."
if ! curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "❌ Backend is not running on http://localhost:8000"
    echo "   Start it with: cd infra && docker-compose up"
    exit 1
fi
echo "✅ Backend is running"
echo ""

# Delete old documents
echo "2️⃣  Clearing old documents..."
DOC_COUNT=$(curl -s "http://localhost:8000/documents/" | jq '. | length')
echo "   Found $DOC_COUNT existing documents"

if [ "$DOC_COUNT" != "null" ] && [ "$DOC_COUNT" -gt 0 ]; then
    echo "   Deleting old documents from database..."
    docker-compose -f infra/docker-compose.yml exec -T postgres psql -U mcourses -d mcourses -c "DELETE FROM questions; DELETE FROM slides; DELETE FROM blocks; DELETE FROM pages; DELETE FROM documents;" > /dev/null 2>&1
    echo "✅ Cleared database"
else
    echo "✅ No documents to clear"
fi
echo ""

# Find a test document with tables
echo "3️⃣  Looking for test documents..."
if [ -f "backend/docs/dwr-25-40-2_parsed.md" ]; then
    TEST_DOC="backend/docs/dwr-25-40-2_parsed.md"
    echo "   Using: dwr-25-40-2_parsed.md (contains tables)"
elif [ -f "backend/docs/dwr-25-45-1_parsed.md" ]; then
    TEST_DOC="backend/docs/dwr-25-45-1_parsed.md"
    echo "   Using: dwr-25-45-1_parsed.md (contains tables)"
else
    echo "❌ No test documents found in backend/docs/"
    echo "   Please upload a PDF/DOCX file first"
    exit 1
fi
echo ""

# Note: We can't actually upload a markdown file, we need a PDF/DOCX
echo "⚠️  NOTE: To test table support, you need to:"
echo "   1. Upload a new PDF/DOCX file with tables via the frontend or:"
echo "      curl -X POST 'http://localhost:8000/documents/' \\"
echo "        -H 'Content-Type: multipart/form-data' \\"
echo "        -F 'file=@/path/to/your/document.pdf'"
echo ""
echo "   2. Wait 30-60 seconds for processing"
echo ""
echo "   3. Check the document:"
echo "      curl http://localhost:8000/documents/1 | jq '.slides[] | {slide_number, title, has_table}'"
echo ""
echo "   4. Open frontend at http://localhost:3000/documents/1"
echo ""

# Check if there are any documents
echo "4️⃣  Checking current documents..."
RESPONSE=$(curl -s "http://localhost:8000/documents/")
if [ "$RESPONSE" = "[]" ]; then
    echo "   No documents found - ready for upload!"
else
    echo "   Current documents:"
    echo "$RESPONSE" | jq -r '.[] | "   - ID \(.document_id): \(.filename) (\(.status))"'
fi
echo ""

echo "✅ Setup complete! Ready to test table support."
echo ""
echo "📝 Next Steps:"
echo "   1. Upload a document with tables (PDF/DOCX)"
echo "   2. Tables will appear in slides where AI deems them helpful"
echo "   3. Frontend will show side-by-side layout: bullet points | table"
echo ""
