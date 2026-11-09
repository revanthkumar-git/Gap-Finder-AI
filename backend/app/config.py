import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "Nexqile - WealthAgent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "nexqile-wealthagent-production-secret-key-2026-secure-384bit")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # SQLite Database
    DB_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wealthagent.db")
    
    @property
    def DATABASE_URL(self) -> str:
        # SQLite with absolute path
        normalized_path = self.DB_PATH.replace("\\", "/")
        return f"sqlite:///{normalized_path}"

settings = Settings()
