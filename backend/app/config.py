from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://mcourses:mcourses@localhost:5432/mcourses"

    MINIO_ENDPOINT: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minio"
    MINIO_SECRET_KEY: str = "minio123"
    MINIO_BUCKET: str = "documents"

    LLAMA_CLOUD_API_KEY: str = "llx-..."
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
