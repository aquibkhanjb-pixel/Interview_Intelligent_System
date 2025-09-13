# config/database.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from config.settings import Config
import logging
from contextlib import contextmanager

# Initialize SQLAlchemy - this was missing!
db = SQLAlchemy()

class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self, database_url=None):
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = None
        self.SessionLocal = None
        self.logger = logging.getLogger(__name__)
        
    def initialize(self):
        """Initialize database connection."""
        try:
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=Config.DEBUG,
                connect_args={
                    "options": "-c timezone=utc",
                    "connect_timeout": 30
                }
            )
            
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            
            self.logger.info("Database connection initialized")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get database session with proper cleanup."""
        if not self.SessionLocal:
            self.initialize()
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check database connection health."""
        try:
            with self.get_session() as session:
                session.execute('SELECT 1')
            return True
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False
    
    def create_tables(self):
        """Create all database tables."""
        try:
            if not self.engine:
                self.initialize()
            
            # Import models here to avoid circular imports
            from database.models import Base
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("Database tables created successfully")
        except Exception as e:
            self.logger.error(f"Table creation failed: {e}")
            raise

# Global database manager instance
db_manager = DatabaseManager()