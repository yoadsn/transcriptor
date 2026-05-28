from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/transcriptor"
    test_database_url: str = "postgresql://postgres:postgres@localhost:5432/transcriptor_test"
    secret_key: str = "dev-secret-key"
    consent_version: str = "1.0"
    dev_mode: bool = False


settings = Settings()
