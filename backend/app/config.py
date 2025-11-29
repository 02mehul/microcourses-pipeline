from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # IMPORTANT: default for local dev
    DATABASE_URL: str = "postgresql+psycopg2://mcourses:mcourses@localhost:5432/mcourses"

    MINIO_ENDPOINT: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minio"
    MINIO_SECRET_KEY: str = "minio123"
    MINIO_BUCKET: str = "documents"

    LLAMA_CLOUD_API_KEY: str = "llx-..."  # Set in .env
    GEMINI_API_KEY: str = ""  # Set in .env - required for slide/question generation

    class Config:
        # This is relative to the directory where you run uvicorn (backend/)
        env_file = ".env"


settings = Settings()
