from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine
from .routes import document

# DEV ONLY: auto-create tables.
Base.metadata.create_all(bind=engine)

import logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Microcourses Backend", version="0.1.0")

# Allow frontend (Next.js on 3000) to call backend (8000)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(document.router)
