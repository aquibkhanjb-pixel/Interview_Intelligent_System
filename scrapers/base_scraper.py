import requests
from bs4 import BeautifulSoup
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Generator
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from abc import ABC, abstractmethod
import random
from collections import deque
import hashlib

from utils.robots_checker import RobotsTxtChecker
from utils.rate_limiter import SmartRateLimiter
from utils.time_utils import ExponentialDecayCalculator
from config.settings import Config



class BaseScraper(ABC):
    """
    Advanced base scraper with comprehensive ethical compliance.
    All platform-specific scrapers inherit from this.
    """
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.logger = logging.getLogger(f"scrapers.{platform_name}")
        
        # Ethical compliance components
        self.robots_checker = RobotsTxtChecker()
        self.rate_limiter = SmartRateLimiter(platform_name)
        self.decay_calculator = ExponentialDecayCalculator()
        
        # Session management
        self.session = requests.Session()
        self._setup_session()
        
        # Duplicate detection
        self.seen_urls = set()
        self.content_hashes = set()
        
        # Statistics tracking
        self.stats = {
            'requests_made': 0,
            'successful_scrapes': 0,
            'duplicates_found': 0,
            'robots_blocked': 0,
            'rate_limited': 0,
            'forbidden_errors': 0
        }

        # Track consecutive failures per domain to avoid infinite retries
        self.domain_failures = {}
    
    def _setup_session(self):
        """Setup session with proper headers and configuration."""
        self.session.headers.update({
            'User-Agent': Config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # Set reasonable timeouts
        self.session.timeout = Config.TIMEOUT
    
    def safe_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Make HTTP request with comprehensive safety checks.
        
        Returns:
            Response object or None if request should be skipped
        """
        try:
            # Check for duplicates
            if url in self.seen_urls:
                self.stats['duplicates_found'] += 1
                return None
            
            # Check robots.txt compliance (configurable)
            if Config.RESPECT_ROBOTS_TXT:
                can_fetch, crawl_delay = self.robots_checker.can_fetch(url, Config.USER_AGENT)
                if not can_fetch:
                    self.stats['robots_blocked'] += 1
                    self.logger.warning(f"Robots.txt blocks access to {url}")
                    return None
            else:
                # Skip robots.txt check for educational/research purposes
                crawl_delay = Config.REQUEST_DELAY
                self.logger.debug(f"Bypassing robots.txt check for research purposes: {url}")
            
            # Apply rate limiting
            domain = urlparse(url).netloc
            self.rate_limiter.wait_if_needed(domain, crawl_delay)

            # Check if domain has too many consecutive failures (avoid infinite 403 retries)
            if self.domain_failures.get(domain, 0) >= Config.MAX_CONSECUTIVE_FAILURES:
                self.logger.warning(f"Domain {domain} has too many consecutive failures, skipping")
                return None

            # Make request with retries
            for attempt in range(Config.MAX_RETRIES):
                try:
                    self.stats['requests_made'] += 1
                    response = self.session.get(url, **kwargs)

                    if response.status_code == 200:
                        self.seen_urls.add(url)
                        self.rate_limiter.record_success(domain)
                        self.stats['successful_scrapes'] += 1
                        # Reset failure counter on success
                        self.domain_failures[domain] = 0
                        return response

                    elif response.status_code == 403:  # Forbidden
                        self.stats['forbidden_errors'] += 1
                        self.domain_failures[domain] = self.domain_failures.get(domain, 0) + 1
                        self.logger.warning(f"HTTP 403 Forbidden for {url} (failure #{self.domain_failures[domain]})")

                        # Stop retrying immediately for 403 errors to avoid infinite loops
                        if self.domain_failures[domain] >= 3:
                            self.logger.warning(f"Too many 403 errors for domain {domain}, stopping")
                            break

                        wait_time = 5 * (attempt + 1)  # Longer wait for 403
                        self.logger.info(f"Waiting {wait_time}s before retry for 403 error")
                        time.sleep(wait_time)

                    elif response.status_code == 429:  # Rate limited
                        self.stats['rate_limited'] += 1
                        self.rate_limiter.record_failure(domain)
                        wait_time = 2 ** attempt
                        self.logger.info(f"Rate limited, waiting {wait_time}s")
                        time.sleep(wait_time)

                    elif response.status_code == 404:
                        # Don't spam warnings for 404s - they're expected during URL discovery
                        self.logger.debug(f"HTTP 404 for {url}")
                    else:
                        self.logger.warning(f"HTTP {response.status_code} for {url}")

                except requests.RequestException as e:
                    self.logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                    if attempt == Config.MAX_RETRIES - 1:
                        self.rate_limiter.record_failure(domain)

            return None
            
        except Exception as e:
            self.logger.error(f"Unexpected error in safe_request: {e}")
            return None
    
    def is_duplicate_content(self, content: str) -> bool:
        """Check if content is duplicate using hash comparison."""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        if content_hash in self.content_hashes:
            return True
        self.content_hashes.add(content_hash)
        return False
    
    @abstractmethod
    def discover_experience_urls(self, company: str, max_pages: int = 10) -> List[str]:
        """Discover interview experience URLs for a company."""
        pass
    
    @abstractmethod
    def extract_experience_data(self, url: str, target_company: str = None) -> Optional[Dict]:
        """Extract structured data from an experience page."""
        pass
    
    def scrape_company_experiences(self, company: str, max_experiences: int = 50) -> Generator[Dict, None, None]:
        """
        Complete scraping pipeline for a company.
        
        Yields:
            Structured interview experience data
        """
        self.logger.info(f"Starting {company} experience collection on {self.platform_name}")
        
        # Discover URLs
        urls = self.discover_experience_urls(company, max_pages=20)
        self.logger.info(f"Found {len(urls)} potential URLs")
        
        scraped_count = 0
        for url in urls:
            if scraped_count >= max_experiences:
                break
                
            experience_data = self.extract_experience_data(url, target_company=company)
            
            if experience_data:
                # Check for duplicate content
                if not self.is_duplicate_content(experience_data['content']):
                    # Add metadata
                    experience_data.update({
                        'source_platform': self.platform_name,
                        'scraped_at': datetime.utcnow(),
                        'time_weight': self.decay_calculator.calculate_weight(
                            experience_data.get('experience_date', datetime.utcnow())
                        )
                    })
                    
                    yield experience_data
                    scraped_count += 1
                    
                    self.logger.info(f"Scraped {scraped_count}/{max_experiences}: {experience_data['title'][:50]}...")
                else:
                    self.stats['duplicates_found'] += 1
        
        self.logger.info(f"Completed {company} scraping: {scraped_count} unique experiences")
        self._log_stats()
    
    def _log_stats(self):
        """Log scraping statistics."""
        self.logger.info(f"Scraping stats for {self.platform_name}:")
        for metric, value in self.stats.items():
            self.logger.info(f"  {metric}: {value}")
