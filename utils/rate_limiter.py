import time
import random
from collections import deque, defaultdict
from typing import Dict, Optional
import logging

class SmartRateLimiter:
    """
    Advanced rate limiter with multiple strategies:
    - Per-domain rate limiting
    - Exponential backoff on failures
    - Adaptive delays based on server response
    - Jitter to avoid thundering herd effects
    """
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.logger = logging.getLogger(f'rate_limiter.{platform_name}')
        
        # Per-domain tracking
        self.domain_requests: Dict[str, deque] = defaultdict(deque)
        self.domain_failures: Dict[str, int] = defaultdict(int)
        self.domain_last_request: Dict[str, float] = {}
        
        # Configuration - Optimized for research use
        self.base_requests_per_minute = 20  # Increase from 10 to 20
        self.failure_backoff_base = 1.5    # Reduce from 2 to 1.5 for faster recovery
        self.max_backoff_time = 60         # Reduce from 300 to 60 seconds max
        self.jitter_range = (0.8, 1.2)     # Reduce jitter range
        
        # Adaptive parameters
        self.success_streak: Dict[str, int] = defaultdict(int)
        self.adaptive_multiplier: Dict[str, float] = defaultdict(lambda: 1.0)
    
    def wait_if_needed(self, domain: str, base_delay: int = 1):
        """
        Intelligent rate limiting with multiple factors considered.

        Args:
            domain: Target domain
            base_delay: Base delay from robots.txt (default reduced to 1)
        """
        now = time.time()

        # Calculate required wait time
        wait_time = self._calculate_wait_time(domain, base_delay, now)

        if wait_time > 0:
            # Add jitter to prevent synchronized requests
            jitter = random.uniform(*self.jitter_range)
            total_wait = min(wait_time * jitter, 10)  # Cap wait time at 10 seconds

            if total_wait > 5:  # Only log longer waits
                self.logger.info(f"Rate limiting: waiting {total_wait:.1f}s for {domain}")
            else:
                self.logger.debug(f"Rate limiting: waiting {total_wait:.1f}s for {domain}")
            time.sleep(total_wait)

        # Record this request
        self._record_request(domain, now)
    
    def _calculate_wait_time(self, domain: str, base_delay: int, current_time: float) -> float:
        """Calculate how long to wait before next request."""
        
        # Factor 1: Base delay from robots.txt
        wait_time = base_delay
        
        # Factor 2: Sliding window rate limiting
        requests = self.domain_requests[domain]
        
        # Remove old requests (older than 1 minute)
        while requests and current_time - requests[0] > 60:
            requests.popleft()
        
        # Check rate limit
        requests_per_minute = len(requests)
        if requests_per_minute >= self.base_requests_per_minute:
            # Calculate time until we can make another request
            oldest_request = requests[0] if requests else current_time
            time_until_next = 60 - (current_time - oldest_request)
            wait_time = max(wait_time, time_until_next)
        
        # Factor 3: Exponential backoff for failures
        failure_count = self.domain_failures[domain]
        if failure_count > 0:
            backoff_time = min(
                self.failure_backoff_base ** failure_count,
                self.max_backoff_time
            )
            wait_time = max(wait_time, backoff_time)
            self.logger.debug(f"Applying exponential backoff: {backoff_time}s for {domain}")
        
        # Factor 4: Adaptive delay based on success patterns
        adaptive_mult = self.adaptive_multiplier[domain]
        wait_time *= adaptive_mult
        
        # Factor 5: Minimum delay since last request
        last_request_time = self.domain_last_request.get(domain, 0)
        time_since_last = current_time - last_request_time
        if time_since_last < wait_time:
            wait_time = wait_time - time_since_last
        else:
            wait_time = 0
        
        return max(wait_time, 0)
    
    def _record_request(self, domain: str, timestamp: float):
        """Record a request for rate limiting tracking."""
        self.domain_requests[domain].append(timestamp)
        self.domain_last_request[domain] = timestamp
    
    def record_success(self, domain: str):
        """Record successful request for adaptive rate limiting."""
        # Reset failure count
        self.domain_failures[domain] = 0
        
        # Increase success streak
        self.success_streak[domain] += 1
        
        # Gradually reduce adaptive multiplier for successful domains
        if self.success_streak[domain] >= 5:
            current_mult = self.adaptive_multiplier[domain]
            self.adaptive_multiplier[domain] = max(0.8, current_mult * 0.9)
            self.success_streak[domain] = 0
        
        self.logger.debug(f"Recorded success for {domain}")
    
    def record_failure(self, domain: str):
        """Record failed request for exponential backoff."""
        self.domain_failures[domain] += 1
        self.success_streak[domain] = 0
        
        # Increase adaptive multiplier for problematic domains
        current_mult = self.adaptive_multiplier[domain]
        self.adaptive_multiplier[domain] = min(3.0, current_mult * 1.2)
        
        self.logger.warning(
            f"Recorded failure for {domain} (count: {self.domain_failures[domain]})"
        )
    
    def get_stats(self) -> Dict:
        """Get rate limiting statistics."""
        return {
            'domains_tracked': len(self.domain_requests),
            'total_failures': sum(self.domain_failures.values()),
            'average_adaptive_multiplier': sum(self.adaptive_multiplier.values()) / 
                                         max(len(self.adaptive_multiplier), 1),
            'domains_with_failures': len([d for d, f in self.domain_failures.items() if f > 0])
        }