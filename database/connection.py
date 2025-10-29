import logging
from contextlib import contextmanager
import os
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from config.settings import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Enhanced database manager compatible with your existing pipeline architecture.
    Supports both Flask-SQLAlchemy and direct SQLAlchemy usage.
    """
    
    def __init__(self, database_url=None):
        self.database_url = database_url or Config.DATABASE_URL
        self.logger = logger
        
        # Flask-SQLAlchemy compatibility
        self._db = None
        self._app = None
        
        # Direct SQLAlchemy support for pipeline
        self.engine = None
        self.SessionLocal = None
        
        # Initialize direct SQLAlchemy connection for pipeline compatibility
        self._initialize_direct_connection()
    
    def _initialize_direct_connection(self):
        """Initialize direct SQLAlchemy connection for pipeline usage."""
        try:
            # Determine if we need SSL (for production databases like Render)
            connect_args = {
                "options": "-c timezone=utc",
                "connect_timeout": 30
            }

            # Add SSL for production databases (Render, AWS RDS, etc.)
            if os.getenv('FLASK_ENV') == 'production' or 'render.com' in self.database_url:
                connect_args["sslmode"] = "require"

            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=Config.DEBUG,
                connect_args=connect_args
            )
            
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            
            self.logger.info("Direct SQLAlchemy connection initialized")
            
        except Exception as e:
            self.logger.error(f"Direct SQLAlchemy initialization failed: {e}")
            raise
    
    def initialize_with_app(self, app, db_instance):
        """Initialize with Flask app and db instance for API usage."""
        self._app = app
        self._db = db_instance
        
        with app.app_context():
            try:
                # Test Flask-SQLAlchemy connection
                db_instance.engine.connect()
                self.logger.info("Flask-SQLAlchemy connection successful")
                
                # Update direct connection to use same engine
                self.engine = db_instance.engine
                self.SessionLocal = sessionmaker(
                    bind=self.engine,
                    autocommit=False,
                    autoflush=False,
                    expire_on_commit=False
                )
                
                return True
            except Exception as e:
                self.logger.error(f"Flask-SQLAlchemy connection failed: {e}")
                return False
    
    def create_tables(self):
        """Create all database tables."""
        try:
            if self._app and self._db:
                # Use Flask-SQLAlchemy if available
                with self._app.app_context():
                    self._db.create_all()
                    self.logger.info("Database tables created via Flask-SQLAlchemy")
                    return True
            elif self.engine:
                # Use direct SQLAlchemy
                from database.models import db
                db.metadata.create_all(bind=self.engine)
                self.logger.info("Database tables created via direct SQLAlchemy")
                return True
            else:
                self.logger.error("Database not properly initialized")
                return False
        except Exception as e:
            self.logger.error(f"Table creation failed: {e}")
            return False
    
    @contextmanager
    def get_session(self):
        """
        Get database session with automatic Flask-SQLAlchemy or direct session selection.
        This maintains compatibility with your pipeline_scraper.py usage.
        """
        if self._app and self._db:
            # Use Flask-SQLAlchemy session when in app context
            try:
                from flask import has_app_context
                if has_app_context():
                    session = self._db.session
                    try:
                        yield session
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        self.logger.error(f"Flask-SQLAlchemy session error: {e}")
                        raise
                    finally:
                        # Flask-SQLAlchemy manages session lifecycle
                        pass
                    return
            except ImportError:
                # Flask not available, fall through to direct session
                pass
        
        # Use direct SQLAlchemy session (for pipeline usage)
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Direct SQLAlchemy session error: {e}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check database health using available connection method."""
        try:
            # Try Flask-SQLAlchemy first
            if self._app and self._db:
                try:
                    from flask import has_app_context
                    if has_app_context():
                        self._db.session.execute(text("SELECT 1"))
                        return True
                except ImportError:
                    pass
            
            # Fall back to direct connection
            if self.engine:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def initialize(self):
        """
        Legacy method for backward compatibility.
        Already handled in __init__ via _initialize_direct_connection.
        """
        if not self.engine or not self.SessionLocal:
            self._initialize_direct_connection()

# Global instance
db_manager = DatabaseManager()

def initialize_database(app, db_instance):
    """Initialize database with Flask app and seed data."""
    try:
        # Initialize connection
        success = db_manager.initialize_with_app(app, db_instance)
        if not success:
            return False
        
        # Create tables
        success = db_manager.create_tables()
        if not success:
            return False
        
        # Seed initial data
        _seed_initial_data(app, db_instance)
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def _seed_initial_data(app, db_instance):
    """Seed initial data."""
    try:
        with app.app_context():
            from database.models import Company, Topic
            
            # Seed companies - include all target companies
            companies_data = [
                # International Companies
                {'name': 'Amazon', 'display_name': 'Amazon', 'industry': 'Cloud/E-commerce', 'size': 'large'},
                {'name': 'Google', 'display_name': 'Google', 'industry': 'Technology', 'size': 'large'},
                {'name': 'Apple', 'display_name': 'Apple', 'industry': 'Technology', 'size': 'large'},
                {'name': 'Netflix', 'display_name': 'Netflix', 'industry': 'Entertainment', 'size': 'large'},
                {'name': 'Meta', 'display_name': 'Meta (Facebook)', 'industry': 'Social Media', 'size': 'large'},
                {'name': 'Microsoft', 'display_name': 'Microsoft', 'industry': 'Technology', 'size': 'large'},

                # Indian E-commerce & Tech
                {'name': 'Flipkart', 'display_name': 'Flipkart', 'industry': 'E-commerce', 'size': 'large'},
                {'name': 'Myntra', 'display_name': 'Myntra', 'industry': 'Fashion E-commerce', 'size': 'medium'},
                {'name': 'BigBasket', 'display_name': 'BigBasket', 'industry': 'Grocery E-commerce', 'size': 'medium'},

                # Transportation & Logistics
                {'name': 'Swiggy', 'display_name': 'Swiggy', 'industry': 'Food Delivery', 'size': 'large'},
                {'name': 'Zomato', 'display_name': 'Zomato', 'industry': 'Food Delivery', 'size': 'large'},
                {'name': 'Ola', 'display_name': 'Ola', 'industry': 'Transportation', 'size': 'large'},
                {'name': 'Uber', 'display_name': 'Uber', 'industry': 'Transportation', 'size': 'large'},
                {'name': 'Dunzo', 'display_name': 'Dunzo', 'industry': 'Hyperlocal Delivery', 'size': 'startup'},

                # Fintech
                {'name': 'Paytm', 'display_name': 'Paytm', 'industry': 'Fintech', 'size': 'large'},
                {'name': 'Razorpay', 'display_name': 'Razorpay', 'industry': 'Fintech', 'size': 'medium'},
                {'name': 'PhonePe', 'display_name': 'PhonePe', 'industry': 'Fintech', 'size': 'large'},
                {'name': 'Cred', 'display_name': 'Cred', 'industry': 'Fintech', 'size': 'startup'},

                # Automotive & Real Estate
                {'name': 'Carwale', 'display_name': 'Carwale', 'industry': 'Automotive', 'size': 'medium'},
                {'name': 'PolicyBazaar', 'display_name': 'PolicyBazaar', 'industry': 'Insurance', 'size': 'medium'},

                # Entertainment & Travel
                {'name': 'Dream11', 'display_name': 'Dream11', 'industry': 'Gaming', 'size': 'medium'},
                {'name': 'MakeMyTrip', 'display_name': 'MakeMyTrip', 'industry': 'Travel', 'size': 'large'},
                {'name': 'BookMyShow', 'display_name': 'BookMyShow', 'industry': 'Entertainment', 'size': 'medium'},

                # Education
                {'name': 'Byju', 'display_name': 'Byju\'s', 'industry': 'EdTech', 'size': 'large'},
                {'name': 'Unacademy', 'display_name': 'Unacademy', 'industry': 'EdTech', 'size': 'medium'},
                {'name': 'Vedantu', 'display_name': 'Vedantu', 'industry': 'EdTech', 'size': 'medium'},

                # Enterprise Software
                {'name': 'Freshworks', 'display_name': 'Freshworks', 'industry': 'Enterprise Software', 'size': 'medium'},
                {'name': 'Zoho', 'display_name': 'Zoho', 'industry': 'Enterprise Software', 'size': 'large'},

                # Social & Marketing
                {'name': 'InMobi', 'display_name': 'InMobi', 'industry': 'AdTech', 'size': 'medium'},
                {'name': 'ShareChat', 'display_name': 'ShareChat', 'industry': 'Social Media', 'size': 'medium'},

                # Retail & Services
                {'name': 'Nykaa', 'display_name': 'Nykaa', 'industry': 'Beauty & Fashion', 'size': 'medium'},
                {'name': 'Lenskart', 'display_name': 'Lenskart', 'industry': 'Eyewear', 'size': 'medium'},
                {'name': 'UrbanClap', 'display_name': 'UrbanCompany', 'industry': 'Home Services', 'size': 'medium'},
                {'name': 'Grofers', 'display_name': 'Blinkit (Grofers)', 'industry': 'Grocery Delivery', 'size': 'medium'},
            ]
            
            for comp_data in companies_data:
                existing = Company.query.filter_by(name=comp_data['name']).first()
                if not existing:
                    company = Company(**comp_data)
                    db_instance.session.add(company)
            
            # Seed base topics
            base_topics = [
                {'name': 'algorithms.dynamic_programming', 'display_name': 'Dynamic Programming', 'category': 'algorithms', 'difficulty_level': 'hard'},
                {'name': 'algorithms.searching', 'display_name': 'Searching Algorithms', 'category': 'algorithms', 'difficulty_level': 'medium'},
                {'name': 'data_structures.tree', 'display_name': 'Trees', 'category': 'data_structures', 'difficulty_level': 'medium'},
                {'name': 'data_structures.hash_table', 'display_name': 'Hash Tables', 'category': 'data_structures', 'difficulty_level': 'easy'},
                {'name': 'system_design.scalability', 'display_name': 'System Scalability', 'category': 'system_design', 'difficulty_level': 'hard'},
            ]
            
            for topic_data in base_topics:
                existing = Topic.query.filter_by(name=topic_data['name']).first()
                if not existing:
                    topic = Topic(**topic_data)
                    db_instance.session.add(topic)
            
            db_instance.session.commit()
            logger.info("Initial data seeded successfully")
            
    except Exception as e:
        db_instance.session.rollback()
        logger.error(f"Error seeding initial data: {e}")