from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    app_env: str = "development"
    groq_api_key: str = ""
    llm_model: str = "openai/gpt-oss-20b"
    jwt_secret: str = "local-development-secret-change-before-deploy"
    database_url: str = f"sqlite:///{ROOT / 'study_diagnostic.db'}"
    chroma_path: str = str(ROOT / "chroma")
    upload_path: str = str(ROOT / "uploads")
    cors_origins: str = "http://localhost:5173"
    seed_demo: bool = False
    demo_email: str = "demo@gapfinder.ai"
    demo_password: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def validate_production(self):
        if self.app_env.casefold() != "production":
            return
        if len(self.jwt_secret) < 32 or self.jwt_secret == "local-development-secret-change-before-deploy":
            raise ValueError("Production requires a unique JWT_SECRET of at least 32 characters.")
        if not self.cors_origin_list or "*" in self.cors_origin_list:
            raise ValueError("Production requires explicit trusted CORS_ORIGINS.")


settings = Settings()
