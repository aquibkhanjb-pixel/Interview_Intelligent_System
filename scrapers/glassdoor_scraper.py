import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from urllib.parse import urljoin, quote_plus
from scrapers.base_scraper import BaseScraper
from bs4 import BeautifulSoup
from typing import List, Dict, Optional


class GlassdoorScraper(BaseScraper):
    """
    Glassdoor interview review scraper.
    Note: Glassdoor has anti-bot protection, so this scraper is more conservative.
    """
    
    def __init__(self):
        super().__init__('glassdoor')
        self.base_url = 'https://www.glassdoor.com'
        
        # Company name mappings for Glassdoor URLs
        self.company_mappings = {
            'Amazon': 'Amazon.com',
            'Google': 'Google',
            'Apple': 'Apple',
            'Netflix': 'Netflix',
            'Meta': 'Meta',
            'Microsoft': 'Microsoft'
        }
        
        # Enhanced headers to appear more browser-like
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            # Realistic browser fingerprint
            'sec-ch-ua': '"Chromium";v="120", "Google Chrome";v="120", "Not:A-Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows" '
        })
        
        # Track 403 errors to skip problematic patterns
        self.blocked_patterns = set()
    
    def discover_experience_urls(self, company: str, max_pages: int = 3) -> List[str]:
        """Limited discovery due to anti-bot protection."""
        urls = set()

        public_patterns = [
            f"/Reviews/{company}-Reviews-E",
            f"/Interview/{company}-Interview-Questions-E"
        ]
        known_company_ids = {
            'Amazon': '6036',
            'Google': '9079',
            'Apple': '1138',
            'Microsoft': '1651',
            'Netflix': '11891',
            'Meta': '40772'
        }
        
        company_id = known_company_ids.get(company)
        if company_id:
            for pattern in public_patterns:
                test_url = f"{self.base_url}{pattern}{company_id}.htm"
                
                # Very slow requests with long delays
                time.sleep(self.min_delay)
                
                response = self.safe_request(test_url)
                if response and response.status_code == 200:
                    # Extract interview links from the page
                    soup = BeautifulSoup(response.content, 'html.parser')
                    interview_links = soup.find_all('a', href=lambda x: x and 'Interview' in x)
                    
                    for link in interview_links[:3]:  # Limit to 3 links
                        full_url = urljoin(self.base_url, link.get('href'))
                        urls.add(full_url)
                        
                    break  # Stop after first success
        # Only try if we haven't been completely blocked
        if len(self.blocked_patterns) < 5:
            try:
                urls.update(self._conservative_company_search(company))
            except Exception as e:
                self.logger.error(f"Glassdoor scraping failed: {e}")
                # Mark as problematic
                self.blocked_patterns.add('all')
        
        return list(urls)

    
    def _get_company_interview_page(self, company: str) -> set:
        """Get interviews from company's main interview page."""
        urls = set()
        
        company_name = self.company_mappings.get(company, company)
        
        # Try different URL patterns Glassdoor uses
        url_patterns = [
            f"/Interview/{company_name}-Interview-Questions-E",
            f"/Interview/{company_name.replace(' ', '-')}-Interview-Questions-E"
        ]
        
        for pattern in url_patterns:
            # We need company ID, but for now try common patterns
            for company_id in range(1000, 50000, 1000):  # Sample common IDs
                interview_url = f"{self.base_url}{pattern}{company_id}.htm"
                
                response = self.safe_request(interview_url)
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for individual interview links
                    interview_links = soup.find_all('a', href=lambda x: x and 'Interview' in x and 'QTN' in x)
                    
                    for link in interview_links:
                        full_url = urljoin(self.base_url, link.get('href'))
                        urls.add(full_url)
                    
                    # If we found the right company page, no need to try other IDs
                    if interview_links:
                        break
                
                # Rate limiting - Glassdoor is strict
                self.rate_limiter.wait_if_needed('glassdoor.com', 5)  # 5 second delays
        
        return urls
    
    def _search_interview_reviews(self, company: str, max_pages: int) -> set:
        """Search for interview reviews (very limited due to anti-bot)."""
        urls = set()
        
        search_query = f"{company} software engineer interview"
        encoded_query = quote_plus(search_query)
        
        for page in range(1, min(max_pages, 3) + 1):  # Limit to 3 pages max
            search_url = f"{self.base_url}/Interview/index.htm"
            
            params = {
                'sc.keyword': search_query,
                'locT': 'C',
                'locId': 1147401,  # United States
                'p': page
            }
            
            response = self.safe_request(search_url, params=params)
            if not response:
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for interview result links
            result_links = soup.find_all('a', href=lambda x: x and '/Interview/' in x)
            
            for link in result_links:
                if self._matches_company_content(link.get_text(), company):
                    full_url = urljoin(self.base_url, link.get('href'))
                    urls.add(full_url)
            
            # Extended delay between pages
            self.rate_limiter.wait_if_needed('glassdoor.com', 8)
        
        return urls
    
    def _matches_company_content(self, text: str, company: str) -> bool:
        """Check if content matches target company."""
        if not text:
            return False
        
        text_lower = text.lower()
        company_lower = company.lower()
        company_name = self.company_mappings.get(company, company).lower()
        
        return company_lower in text_lower or company_name in text_lower
    
    def extract_experience_data(self, url: str, target_company: str = None) -> Optional[Dict]:
        """Extract structured data from Glassdoor interview page."""
        response = self.safe_request(url)
        if not response:
            return None
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            if not title:
                return None
            
            # Extract main content
            content = self._extract_content(soup)
            if not content or len(content.strip()) < 50:
                return None
            
            # Extract metadata
            experience_date = self._extract_date(soup)
            company = self._extract_company_from_content(title, content, target_company)
            role = self._extract_role_from_content(title, content)
            
            # Extract Glassdoor-specific data
            difficulty_rating = self._extract_difficulty_rating(soup)
            interview_experience = self._extract_interview_experience(soup)
            outcome = self._extract_outcome(soup)
            
            return {
                'title': title.strip(),
                'content': content.strip(),
                'source_url': url,
                'company': company,
                'role': role,
                'experience_date': experience_date,
                'difficulty_rating': difficulty_rating,
                'interview_experience': interview_experience,
                'outcome': outcome,
                'interview_questions': self._extract_questions(content)
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting data from {url}: {e}")
            return None
    
    def _extract_title(self, soup) -> Optional[str]:
        """Extract interview title/position."""
        title_selectors = [
            '.interview-details h2',
            '.interviewQuestion',
            'h1',
            '.jobTitle',
            '[data-test="interview-question-title"]'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return None
    
    def _extract_content(self, soup) -> str:
        """Extract main interview content."""
        # Remove scripts and styles
        for unwanted in soup.find_all(['script', 'style', 'nav', 'footer']):
            unwanted.decompose()
        
        content_selectors = [
            '.interviewQuestionDetails',
            '.interview-question-content',
            '.interviewContent',
            '.reviewText',
            '[data-test="interview-content"]'
        ]
        
        content_parts = []
        
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(separator='\n', strip=True)
                if text and len(text) > 20:
                    content_parts.append(text)
        
        if not content_parts:
            # Fallback: get all meaningful paragraphs
            paragraphs = soup.find_all('p')
            content_parts = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20]
        
        return '\n\n'.join(content_parts)
    
    def _extract_date(self, soup) -> datetime:
        """Extract interview date."""
        date_selectors = [
            '.interview-date',
            '.reviewDate',
            'time[datetime]',
            '.date'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = date_elem.get('datetime') or date_elem.get_text()
                
                try:
                    return date_parser.parse(date_text)
                except:
                    # Try to extract date from text patterns
                    date_match = re.search(r'(\w+ \d{1,2}, \d{4})', date_text)
                    if date_match:
                        try:
                            return date_parser.parse(date_match.group(1))
                        except:
                            continue
        
        # Fallback: assume recent
        return datetime.utcnow() - timedelta(days=30)
    
    def _extract_company_from_content(self, title: str, content: str, target_company: str = None) -> str:
        """Extract company name using centralized extraction service."""
        from utils.company_extractor import extract_company_from_content
        return extract_company_from_content(title, content, target_company)
    
    def _extract_role_from_content(self, title: str, content: str) -> str:
        """Extract role/position."""
        text = (title + " " + content).lower()
        
        role_patterns = {
            'Software Engineer Intern': ['intern', 'internship', 'summer'],
            'Senior Software Engineer': ['senior', 'sr', 'staff', 'principal'],
            'Software Engineer II': ['software engineer ii', 'swe ii', 'level 2'],
            'Software Engineer': ['software engineer', 'swe', 'developer', 'engineer']
        }
        
        for role, patterns in role_patterns.items():
            if any(pattern in text for pattern in patterns):
                return role
        
        return "Software Engineer"
    
    def _extract_difficulty_rating(self, soup) -> Optional[float]:
        """Extract difficulty rating if available."""
        rating_selectors = [
            '.difficultyRating',
            '.ratingNumber',
            '[data-test="difficulty-rating"]'
        ]
        
        for selector in rating_selectors:
            element = soup.select_one(selector)
            if element:
                rating_text = element.get_text().strip()
                
                # Extract number from rating (e.g., "4.0/5.0" -> 4.0)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    try:
                        return float(rating_match.group(1))
                    except:
                        continue
        
        return None
    
    def _extract_interview_experience(self, soup) -> str:
        """Extract overall interview experience rating."""
        experience_selectors = [
            '.interviewExperience',
            '.experience-rating',
            '[data-test="experience-rating"]'
        ]
        
        for selector in experience_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text().strip().lower()
                
                if 'positive' in text:
                    return 'positive'
                elif 'negative' in text:
                    return 'negative'
                elif 'neutral' in text:
                    return 'neutral'
        
        return 'unknown'
    
    def _extract_outcome(self, soup) -> str:
        """Extract interview outcome."""
        # Look for outcome indicators
        outcome_selectors = [
            '.interviewOutcome',
            '.outcome',
            '[data-test="interview-outcome"]'
        ]
        
        for selector in outcome_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text().strip().lower()
                
                if any(word in text for word in ['offer', 'hired', 'accepted']):
                    return 'offer'
                elif any(word in text for word in ['rejected', 'declined', 'no offer']):
                    return 'rejected'
        
        # Fallback: check content
        content = soup.get_text().lower()
        
        if any(phrase in content for phrase in ['got the job', 'received offer', 'was hired']):
            return 'offer'
        elif any(phrase in content for phrase in ['did not get', 'was rejected', 'no offer']):
            return 'rejected'
        
        return 'unknown'
    
    def _conservative_company_search(self, company: str) -> set:
        """Very conservative search approach."""
        urls = set()
        
        # Try only one or two specific URL patterns
        test_patterns = [
            f"/Interview/{company}-Interview-Questions-E6036.htm",  # Amazon's actual ID
            f"/Interview/{company}-Software-Engineer-Interview-Questions-E6036_P2.htm"
        ]
        
        for pattern in test_patterns:
            if pattern in self.blocked_patterns:
                continue
                
            test_url = f"{self.base_url}{pattern}"
            
            try:
                response = self.safe_request(test_url)
                
                if response and response.status_code == 200:
                    # Success! Extract interview links
                    soup = BeautifulSoup(response.content, 'html.parser')
                    interview_links = soup.find_all('a', href=lambda x: x and 'Interview' in x)
                    
                    for link in interview_links[:10]:  # Limit to 10 links
                        full_url = urljoin(self.base_url, link.get('href'))
                        urls.add(full_url)
                    
                    break  # Stop after first success
                    
                elif response and response.status_code == 403:
                    self.blocked_patterns.add(pattern)
                    self.logger.warning(f"Glassdoor blocked pattern: {pattern}")
                
            except Exception as e:
                self.logger.error(f"Error testing Glassdoor pattern {pattern}: {e}")
                self.blocked_patterns.add(pattern)
        
        return urls
    
    def _extract_questions(self, content: str) -> List[str]:
        """Extract specific interview questions mentioned."""
        questions = []
        
        # Look for question patterns
        question_patterns = [
            r'Q\d*[:\.]?\s*([^?]+\?)',
            r'Question\s*\d*[:\.]?\s*([^?]+\?)',
            r'They asked[^.]*([^?]+\?)',
            r'Asked about[^.]*([^?.]+[?.])'
        ]
        
        for pattern in question_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                question = match.group(1).strip()
                if len(question) > 10 and len(question) < 200:  # Reasonable length
                    questions.append(question)
        
        return questions[:5]  # Limit to 5 questions