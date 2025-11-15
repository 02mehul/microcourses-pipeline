FROM python:3.11-slim

WORKDIR /app

# Copy worker requirements and install
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app (needed for models and config imports)
COPY backend/app ./backend/app

# Copy worker code
COPY worker/worker.py .
COPY worker/tasks ./tasks

CMD ["celery", "-A", "worker.celery_app", "worker", "--loglevel=info"]
