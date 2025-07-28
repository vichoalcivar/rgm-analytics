"""
Configuration settings for RGM Analytics Platform
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator

# Project root directory
ROOT_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = Field(default="RGM Analytics", env="APP_NAME")
    app_env: str = Field(default="development", env="APP_ENV")
    debug: bool = Field(default=True, env="DEBUG")
    secret_key: str = Field(default="secret-key", env="SECRET_KEY")
    
    # Database
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="rgm_analytics", env="DB_NAME")
    db_user: str = Field(default="rgm_user", env="DB_USER")
    db_password: str = Field(default="password", env="DB_PASSWORD")
    
    # Redis
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # API
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    
    # Paths
    data_dir: Path = ROOT_DIR / "data"
    models_dir: Path = ROOT_DIR / "models"
    logs_dir: Path = ROOT_DIR / "logs"
    
    # ML Configuration
    mlflow_tracking_uri: Optional[str] = Field(default=None, env="MLFLOW_TRACKING_URI")
    model_registry_path: Path = Field(default=ROOT_DIR / "models", env="MODEL_REGISTRY_PATH")
    
    # External APIs
    weather_api_key: Optional[str] = Field(default=None, env="WEATHER_API_KEY")
    economic_api_key: Optional[str] = Field(default=None, env="ECONOMIC_API_KEY")
    
    @property
    def database_url(self) -> str:
        """Construct database URL"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL"""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @validator("app_env")
    def validate_environment(cls, v):
        """Validate environment"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create settings instance
settings = Settings()

# Create directories if they don't exist
for directory in [settings.data_dir, settings.models_dir, settings.logs_dir]:
    directory.mkdir(parents=True, exist_ok=True)