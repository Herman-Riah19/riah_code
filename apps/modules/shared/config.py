# apps/modules/shared/config.py
"""Global configuration using Pydantic Settings"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    appName: str = "Riah Code"
    appVersion: str = "0.1.0"
    appEnv: str = "development"  # development, staging, production
    debug: bool = True
    secretKey: str = "dev-secret-change-in-production"

    # Paths
    dataDir: Path = Path("./data")
    logsDir: Path = Path("./logs")

    # Database
    databaseUrl: str = "sqlite:///./data/app.db"

    # Redis (for job queue, caching)
    redisUrl: str = "redis://localhost:6379/0"

    # Training
    defaultModelPreset: str = "125M"
    checkpointDir: Path = Path("./data/checkpoints")
    tensorboardDir: Path = Path("./data/tensorboard")

    # Corpus
    corpusDir: Path = Path("./data/corpus")
    bibleDir: Path = Path("./data/bible")
    tokenizerDir: Path = Path("./data/tokenizer")

    # Chat
    chatHistoryDir: Path = Path("./data/chat")

    # Monitoring
    prometheusPort: int = 9090
    grafanaPort: int = 3001

    # Security
    corsOrigins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    rateLimitRequests: int = 100
    rateLimitWindow: int = 60  # seconds


settings = Settings()
