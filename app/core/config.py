from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    #Application JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    #Microsoft Enter ID settings
    MICROSOFT_ADMIN_EMAIL: str
    INITIAL_SUPER_ADMIN_ROLE: str = "super_admin"
    MICROSOFT_CLIENT_ID: str
    MICROSOFT_CLIENT_SECRET: str
    MICROSOFT_TENANT_ID: str
    MICROSOFT_REDIRECT_URI: str = ("http://localhost:8000/auth/microsoft/callback")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
