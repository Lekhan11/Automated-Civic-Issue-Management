from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "complaint_db"

    # JWT
    secret_key: str = "your-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days

    # Cloudinary
    cloudinary_cloud_name: Optional[str] = None
    cloudinary_api_key: Optional[str] = None
    cloudinary_api_secret: Optional[str] = None

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None

    # Escalation
    escalation_days: int = 3  # Legacy single-level (deprecated)
    escalation_level1_days: int = 2  # Local -> Zonal
    escalation_level2_days: int = 5  # Zonal -> District Officer (total from assignment)

    # Geocoding
    nominatim_user_agent: str = "CivicFix/1.0"
    geocode_cache_ttl: int = 86400  # 24 hours

    class Config:
        env_file = "../.env"
        case_sensitive = False


settings = Settings()
