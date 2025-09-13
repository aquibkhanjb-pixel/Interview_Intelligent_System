
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import locale
import os

class ProjectLogger:
    """
    Windows-compatible logging setup for the Interview Intelligence System.
    Handles Unicode encoding issues on Windows systems.
    """
    
    def __init__(self, log_level: str = 'INFO', log_dir: str = 'logs'):
        self.log_level = getattr(logging, log_level.upper())
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Detect Windows and set appropriate encoding
        self.is_windows = os.name == 'nt'
        self.console_encoding = 'utf-8' if not self.is_windows else 'cp1252'
        
        # Configure root logger
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup comprehensive logging configuration with Windows compatibility."""
        
        # Create formatters with ASCII-safe symbols
        if self.is_windows:
            # Windows-safe formatters
            detailed_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            simple_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
        else:
            # Unix/Linux formatters (can handle Unicode)
            detailed_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            simple_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
        
        # Console handler with proper encoding
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(simple_formatter)
        
        # File handlers (UTF-8 encoding for files)
        all_logs_file = self.log_dir / 'interview_intelligence.log'
        file_handler = logging.FileHandler(all_logs_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        error_logs_file = self.log_dir / 'errors.log'
        error_handler = logging.FileHandler(error_logs_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Add our handlers
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)
        
        # Set specific logger levels
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        
        # Log startup message (Windows-safe)
        logging.info("Interview Intelligence System logging initialized")
        logging.info(f"Log level: {logging.getLevelName(self.log_level)}")
        logging.info(f"Log directory: {self.log_dir.absolute()}")
        logging.info(f"Platform: {'Windows' if self.is_windows else 'Unix/Linux'}")
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the specified name."""
        return logging.getLogger(name)
    
    def log_scraping_session(self, company: str, status: str, details: Optional[dict] = None):
        """Log details about a scraping session (Windows-safe)."""
        logger = self.get_logger("scraping")
        msg = f"Scraping session for {company} | Status={status}"
        if details:
            msg += f" | Details={details}"
        logger.info(msg)
        
    def log_analysis_results(self, company: str, topic_count: int, 
                        confidence: float, session_id: str):
        """Log analysis results (Windows-safe)."""
        analysis_logger = self.get_logger('analysis')
        
        analysis_logger.info(f"Analysis completed for {company}")
        analysis_logger.info(f"Topics extracted: {topic_count}")
        analysis_logger.info(f"Overall confidence: {confidence}")
        analysis_logger.info(f"Session ID: {session_id}")

# Initialize global logger with Windows compatibility
project_logger = ProjectLogger()