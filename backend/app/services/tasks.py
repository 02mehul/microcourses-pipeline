from . import config
from celery import Celery
import os

celery = Celery("microcourses", broker=os.getenv("REDIS_URL"), backend=os.getenv("REDIS_URL"))

def enqueue_process_document(document_id: int):
    celery.send_task("worker.process_document", args=[document_id])
