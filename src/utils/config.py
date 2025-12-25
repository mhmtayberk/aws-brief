import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr

class Settings(BaseSettings):
    """
    Application settings model.
    Loads values from environment variables and .env file.
    """
    # General
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    DB_URL: str = Field("sqlite:///aws_brief.db", env="DB_URL")

    # AI Engines
    OLLAMA_HOST: str = Field("http://localhost:11434", env="OLLAMA_HOST")
    OPENAI_API_KEY: SecretStr | None = Field(None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: SecretStr | None = Field(None, env="ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: SecretStr | None = Field(None, env="GOOGLE_API_KEY")
    GROQ_API_KEY: SecretStr | None = Field(None, env="GROQ_API_KEY")

    # Defaults for Automation
    DEFAULT_AI_ENGINE: str = Field("ollama", env="DEFAULT_AI_ENGINE")
    DEFAULT_AI_MODEL: str = Field("llama2", env="DEFAULT_AI_MODEL")
    DEFAULT_NOTIFY_CHANNELS: str = Field("slack", env="DEFAULT_NOTIFY_CHANNELS")
    SUMMARY_LANGUAGE: str = Field("English", env="SUMMARY_LANGUAGE")
    
    # Notifications
    SLACK_WEBHOOK_URL: SecretStr | None = Field(None, env="SLACK_WEBHOOK_URL")
    TEAMS_WEBHOOK_URL: SecretStr | None = Field(None, env="TEAMS_WEBHOOK_URL")
    DISCORD_WEBHOOK_URL: SecretStr | None = Field(None, env="DISCORD_WEBHOOK_URL")
    
    # SMTP Settings for Email
    SMTP_HOST: str | None = Field(None, env="SMTP_HOST")
    SMTP_PORT: int = Field(587, env="SMTP_PORT")
    SMTP_USER: str | None = Field(None, env="SMTP_USER")
    SMTP_PASS: SecretStr | None = Field(None, env="SMTP_PASS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
