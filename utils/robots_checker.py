import requests
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
import logging
from typing import Tuple, Optional
import time

class RobotsTxtChecker:
    """
    Professional robots.txt compliance checker with caching and proper error handling.
    Ensures ethical scraping practices.
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = {}
        self.cache_duration = 3600  # 1 hour cache
        self.logger = logging.getLogger(__name__)
    
    def can_fetch(self, url: str, user_agent: str = '*') -> Tuple[bool, int]:
        """
        Check if URL can be fetched according to robots.txt.
        
        Args:
            url: URL to check
            user_agent: User agent string
            
        Returns:
            Tuple of (is_allowed, crawl_delay_seconds)
        """
        try:
            domain = urlparse(url).netloc
            
            # Check cache validity
            if domain in self.cache:
                if time.time() - self.cache_ttl.get(domain, 0) < self.cache_duration:
                    rp = self.cache[domain]
                else:
                    # Cache expired, reload
                    self._load_robots_txt(domain)
                    rp = self.cache.get(domain)
            else:
                # Not in cache, load
                self._load_robots_txt(domain)
                rp = self.cache.get(domain)
            
            if not rp:
                # No robots.txt found, be conservative
                self.logger.info(f"No robots.txt for {domain}, using conservative defaults")
                return True, 5
            
            # Check permissions
            is_allowed = rp.can_fetch(user_agent, url)
            crawl_delay = rp.crawl_delay(user_agent) or 2
            
            if not is_allowed:
                self.logger.warning(f"Robots.txt DISALLOWS access to {url}")
            else:
                self.logger.debug(f"Robots.txt allows access to {url} (delay: {crawl_delay}s)")
            
            return is_allowed, max(crawl_delay, 2)  # Minimum 2 second delay
            
        except Exception as e:
            self.logger.error(f"Error checking robots.txt for {url}: {e}")
            return True, 5  # Conservative fallback
    
    def _load_robots_txt(self, domain: str):
        """Load and parse robots.txt for a domain."""
        try:
            robots_url = f"https://{domain}/robots.txt"
            self.logger.debug(f"Loading robots.txt from {robots_url}")
            
            response = requests.get(robots_url, timeout=10)
            if response.status_code == 200:
                rp = RobotFileParser()
                rp.set_url(robots_url)
                
                # Parse the content line by line
                for line in response.text.split('\n'):
                    rp.read()
                
                self.cache[domain] = rp
                self.cache_ttl[domain] = time.time()
                self.logger.info(f"Successfully loaded robots.txt for {domain}")
            else:
                self.cache[domain] = None
                self.cache_ttl[domain] = time.time()
                self.logger.info(f"No robots.txt found for {domain} (HTTP {response.status_code})")
                
        except Exception as e:
            self.logger.warning(f"Failed to load robots.txt for {domain}: {e}")
            self.cache[domain] = None
            self.cache_ttl[domain] = time.time()
    
    def clear_cache(self):
        """Clear the robots.txt cache."""
        self.cache.clear()
        self.cache_ttl.clear()
        self.logger.info("Robots.txt cache cleared")