from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, String, Text, DateTime, Column, Index, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from src.utils.config import settings
import logging
import time

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

class NewsItem(Base):
    """
    Model representing a single news item (Article, Blog Post, Bulletin).
    """
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512))
    url: Mapped[str] = mapped_column(String(2048))
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    tags: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_notified: Mapped[bool] = mapped_column(default=False)
    
    __table_args__ = (
        Index('idx_notified_published', 'is_notified', 'published_at'),
    )

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
        return cls._instance

    def _init_db(self):
        """Initialize the database and enable WAL mode for better concurrency."""
        logger.info(f"Initializing Database at {settings.DB_URL}")
        
        # Configure connection args for SQLite
        connect_args = {"check_same_thread": False}
        if "sqlite" in settings.DB_URL:
            # Enable autocommit mode for better concurrency
            connect_args["isolation_level"] = None
        
        self._engine = create_engine(
            settings.DB_URL, 
            connect_args=connect_args,
            pool_pre_ping=True  # Check connections before using
        )
        
        # Enable WAL mode for SQLite (better concurrency)
        if "sqlite" in settings.DB_URL:
            with self._engine.connect() as conn:
                conn.execute(text("PRAGMA journal_mode=WAL"))
                conn.execute(text("PRAGMA busy_timeout=5000"))  # 5s timeout
                logger.info("SQLite WAL mode enabled for concurrent access")
        
        self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
        Base.metadata.create_all(bind=self._engine)

    def get_session(self) -> Session:
        """
        Get a new database session with retry logic for locked database.
        """
        if not self._SessionLocal:
            self._init_db()
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                session = self._SessionLocal()
                return session
            except Exception as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(0.5 * (2 ** attempt))  # Exponential backoff
                else:
                    raise

db_manager = DBManager()
