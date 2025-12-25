from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, String, Text, DateTime, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from src.utils.config import settings
import logging

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

class NewsItem(Base):
    """
    Model representing a single news item (Article, Blog Post, Bulletin).
    """
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(String(255), unique=True, index=True) # Unique ID from the feed (e.g. GUID)
    title: Mapped[str] = mapped_column(String(512))
    url: Mapped[str] = mapped_column(String(2048))
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Raw content
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Generated Summary
    published_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    tags: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Comma separated tags
    is_notified: Mapped[bool] = mapped_column(default=False) # Notification Tracking

    def __repr__(self) -> str:
        return f"<NewsItem(id={self.id}, title='{self.title[:30]}...')>"

class DBManager:
    """
    Singleton class to manage Database connection and sessions.
    """
    _instance = None
    _engine = None
    _SessionLocal = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        logger.info(f"Initializing Database at {settings.DB_URL}")
        self._engine = create_engine(settings.DB_URL, connect_args={"check_same_thread": False} if "sqlite" in settings.DB_URL else {})
        self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
        
        # Create tables
        Base.metadata.create_all(bind=self._engine)

    def get_session(self) -> Session:
        if not self._SessionLocal:
            self._init_db()
        return self._SessionLocal()

# Global instance
db_manager = DBManager()

def get_db():
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()
