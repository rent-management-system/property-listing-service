from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    USER_MANAGEMENT_URL: str
    PAYMENT_SERVICE_URL: str
    PAYMENT_SERVICE_API_KEY: str
    NOTIFICATION_URL: str
    JWT_SECRET: str
    REDIS_URL: str
    CORS_ORIGINS: str = "*" # New line for CORS origins

    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    BUCKET_NAME: str
    GEBETA_API_KEY: str # Added Gebeta API Key
    MAX_FILE_MB: int = 5 # Added Max File MB with a default

    # Payment specific settings
    PAYMENT_AMOUNT: float = 500.00 # Fixed amount for property approval
    PAYMENT_CURRENCY: str = "ETB"
    CHAPA_IS_TEST_MODE: bool = True # Flag for Chapa sandbox/test mode
    PROPERTY_WEBHOOK_API_KEY: str # API key for incoming webhooks to this service

    class Config:
        env_file = ".env"

settings = Settings()
