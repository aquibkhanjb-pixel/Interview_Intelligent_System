import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env if it exists
load_dotenv()

class Config:
    """Base configuration class."""
    
    # Database - psycopg 3.x format
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        os.getenv('SQLALCHEMY_DATABASE_URI', 'postgresql+psycopg://postgres:password@localhost:5432/interview_intel')
    )
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() in ['true', '1', 'yes']
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_timeout': 20,
        'pool_recycle': 3600,
        'max_overflow': 20
    }
    
    # Scraping Configuration - Optimized for research
    USER_AGENT = os.getenv('USER_AGENT', 'Interview Intelligence Research Bot 1.0')
    REQUEST_DELAY = int(os.getenv('REQUEST_DELAY', 1))  # Reduce from 2 to 1 second
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 2))      # Reduce from 3 to 2 retries
    TIMEOUT = int(os.getenv('TIMEOUT', 20))             # Reduce from 30 to 20 seconds
    MAX_CONSECUTIVE_FAILURES = int(os.getenv('MAX_CONSECUTIVE_FAILURES', 3))  # Reduce from 5 to 3

    # Robots.txt Configuration
    # Set to False for educational/research purposes where robots.txt may be overly restrictive
    # Note: Use responsibly and respect website terms of service
    RESPECT_ROBOTS_TXT = os.getenv('RESPECT_ROBOTS_TXT', 'false').lower() == 'true'
    
    # Exponential Decay Parameters
    DECAY_LAMBDA = float(os.getenv('DECAY_LAMBDA', 0.08))
    MAX_AGE_MONTHS = int(os.getenv('MAX_AGE_MONTHS', 60))
    
    # Target Companies
    TARGET_COMPANIES = [
        'Amazon', 'Google', 'Apple', 'Netflix', 'Meta', 'Microsoft',
        'Flipkart', 'Carwale', 'Swiggy', 'Zomato', 'Paytm' ,'Ola' ,
        'Uber' ,'Byju', 'Razorpay' , 'Freshworks' , 'Zoho' , 'InMobi',
        'ShareChat' , 'Dream11' , 'PhonePe' , 'Myntra' , 'BigBasket' ,
        'Grofers' , 'Dunzo' , 'Nykaa' , 'PolicyBazaar' , 'MakeMyTrip',
        'BookMyShow' , 'Lenskart' ,'UrbanClap' , 'Cred' , 'Unacademy',
        'Vedantu'# Add Indian companies
]
    
    # Platform URLs
    PLATFORM_URLS = {
        'geeksforgeeks': 'https://www.geeksforgeeks.org',
        'leetcode': 'https://leetcode.com',
        'glassdoor': 'https://www.glassdoor.com'
    }
    
    # Redis Configuration (optional)
    REDIS_URL = os.getenv('REDIS_URL', '')
    USE_REDIS = bool(REDIS_URL)
    
    # Rate Limiting
    API_RATE_LIMIT = int(os.getenv('API_RATE_LIMIT', 100))
    API_BURST_LIMIT = int(os.getenv('API_BURST_LIMIT', 10))

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE_URL = 'postgresql+psycopg://postgres:test@localhost:5432/interview_intel_test'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
