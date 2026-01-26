#!/bin/bash

# Database Reset Script for Docker Compose
# This script clears the PostgreSQL database and rebuilds everything

echo "🔄 Resetting database for milestone testing..."

# Navigate to infra directory
cd "$(dirname "$0")/infra"

# Stop all services
echo "📦 Stopping all services..."
docker-compose down

# Remove database volume to clear all data
echo "🗑️  Removing database volume..."
docker volume rm infra_pgdata 2>/dev/null || echo "Volume already removed or doesn't exist"

# Rebuild backend (to pick up new code changes)
echo "🔨 Rebuilding backend with new code..."
docker-compose build backend

# Start all services
echo "🚀 Starting all services with fresh database..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "✅ Database reset complete!"
echo ""
echo "Services running:"
echo "- Backend API: http://localhost:8000"
echo "- Frontend: http://localhost:3000 (if started separately)"
echo "- MinIO Console: http://localhost:9001"
echo ""
echo "Next steps:"
echo "1. Start frontend: cd frontend && npm run dev"
echo "2. Open browser: http://localhost:3000"
echo "3. Upload docs/dwr-25-45-1.docx"
echo "4. Check backend/docs/ for parsed markdown"
echo ""
echo "To view logs: docker-compose -f infra/docker-compose.yml logs -f backend"
echo ""
