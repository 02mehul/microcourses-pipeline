FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/app ./app

# Copy migrations for Alembic
COPY backend/migrations ./migrations
COPY backend/alembic.ini .

# Create docs directory for markdown output
RUN mkdir -p /app/docs

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
