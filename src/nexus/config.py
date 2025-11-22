"""
Centralized configuration management for Nexus Platform
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Environment
    env: str = Field(default="development", alias="ENV")

    # Claude AI
    anthropic_api_key: str = Field(alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-3-5-sonnet-20241022", alias="CLAUDE_MODEL")

    # Database
    database_url: str = Field(default="sqlite:///./nexus.db", alias="DATABASE_URL")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Session 56: Browser Automation
    browser_headless: bool = Field(default=True, alias="BROWSER_HEADLESS")
    browser_timeout: int = Field(default=30000, alias="BROWSER_TIMEOUT")

    # Session 57: Workflow Automation
    workflow_executor: str = Field(default="celery", alias="WORKFLOW_EXECUTOR")
    workflow_max_workers: int = Field(default=4, alias="WORKFLOW_MAX_WORKERS")

    # Session 58: API Integrations
    google_client_id: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_SECRET")
    microsoft_client_id: Optional[str] = Field(default=None, alias="MICROSOFT_CLIENT_ID")
    microsoft_client_secret: Optional[str] = Field(default=None, alias="MICROSOFT_CLIENT_SECRET")
    slack_bot_token: Optional[str] = Field(default=None, alias="SLACK_BOT_TOKEN")
    slack_client_id: Optional[str] = Field(default=None, alias="SLACK_CLIENT_ID")
    slack_client_secret: Optional[str] = Field(default=None, alias="SLACK_CLIENT_SECRET")
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")

    # Session 59: Voice Assistant
    voice_engine: str = Field(default="whisper", alias="VOICE_ENGINE")
    voice_language: str = Field(default="en", alias="VOICE_LANGUAGE")
    tts_engine: str = Field(default="gtts", alias="TTS_ENGINE")

    # Session 60: Translation
    translation_engine: str = Field(default="google", alias="TRANSLATION_ENGINE")
    translation_cache_enabled: bool = Field(default=True, alias="TRANSLATION_CACHE_ENABLED")

    # Session 61: OCR Engine
    ocr_engine: str = Field(default="easyocr", alias="OCR_ENGINE")
    ocr_languages: str = Field(default="en", alias="OCR_LANGUAGES")
    ocr_gpu_enabled: bool = Field(default=False, alias="OCR_GPU_ENABLED")

    # Session 62: Sentiment Analysis
    sentiment_model: str = Field(
        default="distilbert-base-uncased-finetuned-sst-2-english",
        alias="SENTIMENT_MODEL"
    )
    ner_model: str = Field(default="en_core_web_sm", alias="NER_MODEL")

    # Session 63: Chatbot Builder
    chatbot_engine: str = Field(default="rasa", alias="CHATBOT_ENGINE")
    chatbot_model_path: str = Field(default="./models/chatbot", alias="CHATBOT_MODEL_PATH")

    # Session 64: Document Parser
    document_parser_cache: bool = Field(default=True, alias="DOCUMENT_PARSER_CACHE")
    tesseract_path: str = Field(default="/usr/bin/tesseract", alias="TESSERACT_PATH")

    # Session 65: Data Pipeline
    pipeline_scheduler: str = Field(default="prefect", alias="PIPELINE_SCHEDULER")
    pipeline_backend: str = Field(default="local", alias="PIPELINE_BACKEND")
    data_warehouse_url: str = Field(default="sqlite:///./warehouse.db", alias="DATA_WAREHOUSE_URL")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # Security
    secret_key: str = Field(default="dev-secret-key", alias="SECRET_KEY")
    allowed_origins: str = Field(default="http://localhost:8501", alias="ALLOWED_ORIGINS")

    # Performance
    cache_enabled: bool = Field(default=True, alias="CACHE_ENABLED")
    cache_ttl: int = Field(default=3600, alias="CACHE_TTL")
    max_upload_size: int = Field(default=100000000, alias="MAX_UPLOAD_SIZE")

    class Config:
        env_file = ".env"
        case_sensitive = False


class Config:
    """Main configuration class"""

    BASE_DIR = Path(__file__).parent.parent.parent

    # Initialize settings
    settings: Settings = None

    # Module configurations
    MODULES_CONFIG: Dict[int, Dict[str, Any]] = {
        56: {
            "name": "AI Browser Automation",
            "icon": "🌐",
            "description": "Web scraping, form filling, vision-based detection",
            "features": ["web_scraping", "form_filling", "vision_detection"]
        },
        57: {
            "name": "Workflow Automation",
            "icon": "⚙️",
            "description": "Visual builder, triggers, actions, 100+ integrations",
            "features": ["visual_builder", "triggers", "actions", "integrations"]
        },
        58: {
            "name": "API Integrations",
            "icon": "🔌",
            "description": "Google/Microsoft/Slack/GitHub connectors, OAuth",
            "features": ["google", "microsoft", "slack", "github", "oauth"]
        },
        59: {
            "name": "Voice Assistant",
            "icon": "🎤",
            "description": "Speech-to-text, voice commands, multi-language",
            "features": ["speech_to_text", "voice_commands", "multilingual"]
        },
        60: {
            "name": "Translation",
            "icon": "🌍",
            "description": "60+ languages, document translation, real-time",
            "features": ["multilingual", "document_translation", "realtime"]
        },
        61: {
            "name": "OCR Engine",
            "icon": "📄",
            "description": "Text extraction, handwriting, tables, batch processing",
            "features": ["text_extraction", "handwriting", "tables", "batch"]
        },
        62: {
            "name": "Sentiment Analysis",
            "icon": "😊",
            "description": "Emotion detection, entity recognition",
            "features": ["emotion_detection", "entity_recognition", "nlp"]
        },
        63: {
            "name": "Chatbot Builder",
            "icon": "💬",
            "description": "No-code, intents, dialog flows",
            "features": ["no_code", "intents", "dialog_flows", "training"]
        },
        64: {
            "name": "Document Parser",
            "icon": "📋",
            "description": "Invoices, receipts, template matching",
            "features": ["invoice_parsing", "receipt_parsing", "template_matching"]
        },
        65: {
            "name": "Data Pipeline",
            "icon": "🔄",
            "description": "ETL, transformations, scheduling",
            "features": ["etl", "transformations", "scheduling", "monitoring"]
        }
    }

    @classmethod
    def initialize(cls):
        """Initialize configuration from environment"""
        from dotenv import load_dotenv
        load_dotenv()
        cls.settings = Settings()
        return cls.settings

    @classmethod
    def get_module_config(cls, session: int) -> Optional[Dict[str, Any]]:
        """Get configuration for specific module"""
        return cls.MODULES_CONFIG.get(session)
