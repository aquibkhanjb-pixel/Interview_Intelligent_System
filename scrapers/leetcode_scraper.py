import re
import json
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from urllib.parse import urljoin, quote
from scrapers.base_scraper import BaseScraper
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from config.settings import Config


class LeetCodeScraper(BaseScraper):
    """
    Advanced LeetCode discussion scraper for interview experiences.
    Updated to match GeeksforGeeks scraper format with enhanced functionality.
    """

    def __init__(self):
        super().__init__('leetcode')
        self.base_url = 'https://leetcode.com'

        # Expanded company name mappings including Indian companies
        self.company_mappings = {
            # International Companies
            'Amazon': ['amazon', 'amzn', 'aws', 'amazon.com', 'amazon inc'],
            'Google': ['google', 'alphabet', 'goog', 'google.com', 'alphabet inc'],
            'Apple': ['apple', 'aapl', 'apple inc', 'apple.com'],
            'Netflix': ['netflix', 'nflx', 'netflix.com', 'netflix inc'],
            'Meta': ['meta', 'facebook', 'fb', 'instagram', 'whatsapp', 'meta platforms'],
            'Microsoft': ['microsoft', 'msft', 'ms', 'microsoft.com', 'microsoft corporation'],

            # Indian Companies
            'Flipkart': ['flipkart', 'flipkart.com', 'flipkart india'],
            'Carwale': ['carwale', 'carwale.com', 'car wale'],
            'Swiggy': ['swiggy', 'swiggy.com'],
            'Zomato': ['zomato', 'zomato.com'],
            'Paytm': ['paytm', 'paytm.com', 'one97'],
            'Ola': ['ola', 'ola cabs', 'ola.com'],
            'Uber': ['uber', 'uber.com'],
            'Byju': ['byju', 'byjus', 'byju\'s'],
            'Razorpay': ['razorpay', 'razorpay.com'],
            'Freshworks': ['freshworks', 'freshdesk', 'freshservice'],
            'Zoho': ['zoho', 'zoho.com'],
            'InMobi': ['inmobi', 'inmobi.com'],
            'ShareChat': ['sharechat', 'share chat'],
            'Dream11': ['dream11', 'dream 11'],
            'PhonePe': ['phonepe', 'phone pe'],
            'Myntra': ['myntra', 'myntra.com'],
            'BigBasket': ['bigbasket', 'big basket'],
            'Grofers': ['grofers', 'blinkit'],
            'Dunzo': ['dunzo', 'dunzo.com'],
            'Nykaa': ['nykaa', 'nykaa.com'],
            'PolicyBazaar': ['policybazaar', 'policy bazaar'],
            'MakeMyTrip': ['makemytrip', 'make my trip', 'mmt'],
            'BookMyShow': ['bookmyshow', 'book my show', 'bms'],
            'Lenskart': ['lenskart', 'lenskart.com'],
            'UrbanClap': ['urbanclap', 'urban clap', 'urbancompany', 'urban company'],
            'Cred': ['cred', 'cred.com'],
            'Unacademy': ['unacademy', 'unacademy.com'],
            'Vedantu': ['vedantu', 'vedantu.com']
        }
        
        # LeetCode specific headers
        self.session.headers.update({
            'Referer': 'https://leetcode.com/',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest'
        })
    
    def discover_experience_urls(self, company: str, max_pages: int = 10) -> List[str]:
        """Discover interview experience URLs from LeetCode discussions."""
        urls = set()
        
        # Strategy 1: Company-specific discussion topics
        urls.update(self._search_company_discussions(company, max_pages))
        
        # Strategy 2: Interview category browsing
        urls.update(self._browse_interview_category(company))
        
        # Strategy 3: Recent interview posts
        urls.update(self._get_recent_interview_posts(company))
        
        return list(urls)
    
    def _search_company_discussions(self, company: str, max_pages: int) -> set:
        """Search LeetCode discussions for company-specific posts."""
        urls = set()

        company_variations = self.company_mappings.get(company, [company.lower()])
        consecutive_failures = 0
        max_consecutive_failures = 3  # Limit consecutive failures to avoid infinite loops

        for variation in company_variations:
            # LeetCode discussion search URL pattern
            search_url = f"{self.base_url}/discuss/interview-question"

            params = {
                'currentPage': 1,
                'orderBy': 'most_relevant',
                'query': f"{variation} interview"
            }

            for page in range(1, min(max_pages + 1, 5)):  # Limit to 5 pages to avoid excessive requests
                params['currentPage'] = page

                # Check if we've had too many consecutive failures
                if consecutive_failures >= max_consecutive_failures:
                    self.logger.warning(f"Too many consecutive failures for LeetCode, stopping search for {variation}")
                    break

                # LeetCode uses AJAX for discussions, need to handle JSON response
                response = self.safe_request(search_url, params=params)
                if not response:
                    consecutive_failures += 1
                    continue
                
                # Reset consecutive failures on successful response
                consecutive_failures = 0

                try:
                    # Parse JSON response if available
                    if 'application/json' in response.headers.get('content-type', ''):
                        data = response.json()
                        posts = data.get('data', {}).get('categoryTopicList', {}).get('edges', [])

                        for post in posts:
                            node = post.get('node', {})
                            if self._is_interview_experience_post(node, company):
                                post_id = node.get('id')
                                if post_id:
                                    urls.add(f"{self.base_url}/discuss/interview-question/{post_id}")
                    else:
                        # Fallback: parse HTML response
                        soup = BeautifulSoup(response.content, 'html.parser')
                        links = soup.find_all('a', href=True)

                        for link in links:
                            href = link.get('href')
                            if href and '/discuss/interview-question/' in href:
                                if self._matches_company_content(link.get_text(), company):
                                    full_url = urljoin(self.base_url, href)
                                    urls.add(full_url)

                except Exception as e:
                    consecutive_failures += 1
                    self.logger.warning(f"Error parsing LeetCode response: {e}")
                    if consecutive_failures >= max_consecutive_failures:
                        self.logger.warning(f"Too many parse errors for LeetCode, stopping")
                        break
        
        return urls
    
    def _browse_interview_category(self, company: str) -> set:
        """Browse LeetCode interview question category."""
        urls = set()
        
        category_url = f"{self.base_url}/discuss/interview-question"
        
        response = self.safe_request(category_url)
        if not response:
            return urls
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for discussion posts
        post_links = soup.find_all('a', href=lambda x: x and '/discuss/interview-question/' in x)
        
        for link in post_links:
            if self._matches_company_content(link.get_text(), company):
                full_url = urljoin(self.base_url, link.get('href'))
                urls.add(full_url)
        
        return urls
    
    def _get_recent_interview_posts(self, company: str) -> set:
        """Get recent interview posts from various LeetCode sources."""
        urls = set()
        
        # Recent discussions endpoint
        recent_url = f"{self.base_url}/discuss/interview-question"
        
        response = self.safe_request(recent_url)
        if not response:
            return urls
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find recent posts
        recent_posts = soup.find_all('div', class_='discuss-topic')
        
        for post in recent_posts:
            title_link = post.find('a', href=True)
            if title_link and self._matches_company_content(title_link.get_text(), company):
                full_url = urljoin(self.base_url, title_link.get('href'))
                urls.add(full_url)
        
        return urls
    
    def _is_interview_experience_post(self, post_node: Dict, company: str) -> bool:
        """Check if a post node represents an interview experience."""
        title = post_node.get('title', '').lower()
        content = post_node.get('content', '').lower()
        
        # Check for company match
        company_variations = self.company_mappings.get(company, [company.lower()])
        company_match = any(var in title or var in content for var in company_variations)
        
        # Check for interview keywords
        interview_keywords = [
            'interview', 'onsite', 'phone interview', 'coding interview',
            'behavioral', 'system design', 'offer', 'rejected', 'hired'
        ]
        
        interview_match = any(keyword in title or keyword in content for keyword in interview_keywords)
        
        return company_match and interview_match
    
    def _matches_company_content(self, text: str, company: str) -> bool:
        """Check if text content matches the target company."""
        if not text:
            return False
        
        text_lower = text.lower()
        company_variations = self.company_mappings.get(company, [company.lower()])
        
        return any(variation in text_lower for variation in company_variations)
    
    def extract_experience_data(self, url: str, target_company: str = None) -> Optional[Dict]:
        """Extract structured data from LeetCode discussion post."""
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
            if not content or len(content.strip()) < 100:
                return None
            
            # Extract metadata
            experience_date = self._extract_date(soup)
            company = self._extract_company_from_content(title, content, target_company)
            role = self._extract_role_from_content(title, content)
            
            # Extract difficulty and outcome
            difficulty_indicators = self._extract_difficulty_indicators(content)
            outcome = self._extract_outcome(content)
            
            # Extract questions mentioned
            coding_questions = self._extract_coding_questions(content)
            
            # Extract interview rounds information
            rounds_info = self._extract_rounds_info(content)

            return {
                'title': title.strip(),
                'content': content.strip(),
                'source_url': url,
                'source_platform': 'leetcode',
                'company': company,
                'role': role,
                'experience_date': experience_date,
                'rounds_count': rounds_info['count'],
                'rounds_details': rounds_info['details'],
                'difficulty_indicators': difficulty_indicators,
                'outcome': outcome,
                'coding_questions': coding_questions,
                'interview_type': self._determine_interview_type(content),
                'time_weight': self._calculate_time_weight(experience_date)
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting data from {url}: {e}")
            return None
    
    def _extract_title(self, soup) -> Optional[str]:
        """Extract post title."""
        title_selectors = [
            '.discuss-topic-title',
            'h1',
            '.topic-title',
            '[data-cy="topic-title"]'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return None
    
    def _extract_content(self, soup) -> str:
        """Extract main post content."""
        # Remove unwanted elements
        for unwanted in soup.find_all(['script', 'style', 'nav', 'header', 'aside']):
            unwanted.decompose()
        
        content_selectors = [
            '.discuss-markdown-container',
            '.topic-content',
            '.discuss-topic-content',
            '.markdown-body',
            '[data-cy="topic-content"]'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                return content_elem.get_text(separator='\n', strip=True)
        
        # Fallback to all paragraphs
        paragraphs = soup.find_all('p')
        return '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
    
    def _extract_date(self, soup) -> datetime:
        """Extract post date."""
        date_selectors = [
            '.discuss-topic-date',
            '.topic-date',
            'time',
            '[datetime]'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = date_elem.get('datetime') or date_elem.get_text()
                try:
                    return date_parser.parse(date_text)
                except:
                    continue
        
        # Fallback: recent date
        return datetime.utcnow() - timedelta(days=15)
    
    def _extract_company_from_content(self, title: str, content: str, target_company: str = None) -> str:
        """Extract company name using centralized extraction service."""
        from utils.company_extractor import extract_company_from_content
        return extract_company_from_content(title, content, target_company)
    
    def _extract_role_from_content(self, title: str, content: str) -> str:
        """Extract role information."""
        text = (title + " " + content).lower()
        
        role_patterns = {
            'SDE Intern': ['intern', 'internship', 'summer intern', 'new grad'],
            'Senior SDE': ['senior', 'staff', 'principal', 'l6', 'l7'],
            'SDE-2': ['sde-2', 'sde 2', 'mid level', 'l5'],
            'SDE-1': ['sde-1', 'sde 1', 'junior', 'l4'],
            'SDE': ['sde', 'software engineer', 'developer']
        }
        
        for role, patterns in role_patterns.items():
            if any(pattern in text for pattern in patterns):
                return role
        
        return "Software Engineer"
    
    def _extract_difficulty_indicators(self, content: str) -> List[str]:
        """Extract difficulty indicators."""
        content_lower = content.lower()
        indicators = []
        
        difficulty_patterns = {
            'easy': ['easy', 'simple', 'straightforward', 'basic'],
            'medium': ['medium', 'moderate', 'standard', 'average'],
            'hard': ['hard', 'difficult', 'challenging', 'tough', 'complex']
        }
        
        for difficulty, keywords in difficulty_patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                indicators.append(difficulty)
        
        return indicators
    
    def _extract_outcome(self, content: str) -> str:
        """Extract interview outcome."""
        content_lower = content.lower()
        
        positive_indicators = [
            'got offer', 'received offer', 'accepted', 'hired', 'passed',
            'success', 'offer letter', 'joined'
        ]
        
        negative_indicators = [
            'rejected', 'failed', 'did not get', 'unsuccessful',
            'declined', 'no offer'
        ]
        
        if any(indicator in content_lower for indicator in positive_indicators):
            return 'offer'
        elif any(indicator in content_lower for indicator in negative_indicators):
            return 'rejected'
        else:
            return 'unknown'
    
    def _extract_coding_questions(self, content: str) -> List[str]:
        """Extract mentioned coding questions/problems."""
        questions = []
        
        # Look for LeetCode problem patterns
        leetcode_patterns = [
            r'leetcode\.com/problems/([a-z-]+)',
            r'problem #?(\d+)',
            r'lc[#\s]?(\d+)',
            r'question[#\s]?(\d+)'
        ]
        
        for pattern in leetcode_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                questions.append(match.group(1))
        
        # Look for algorithm/topic mentions
        algorithm_patterns = [
            r'(two sum|three sum|merge sort|quick sort|binary search)',
            r'(sliding window|two pointer|dynamic programming|dfs|bfs)',
            r'(backtracking|greedy|divide and conquer)'
        ]
        
        for pattern in algorithm_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                questions.append(match.group(1))
        
        return list(set(questions))  # Remove duplicates
    
    def _determine_interview_type(self, content: str) -> str:
        """Determine the type of interview."""
        content_lower = content.lower()

        type_indicators = {
            'phone_screen': ['phone', 'call', 'screen'],
            'onsite': ['onsite', 'in-person', 'office'],
            'virtual': ['virtual', 'video', 'zoom', 'online'],
            'behavioral': ['behavioral', 'culture', 'leadership'],
            'system_design': ['system design', 'architecture', 'scalability'],
            'coding': ['coding', 'algorithm', 'data structure', 'leetcode']
        }

        for interview_type, keywords in type_indicators.items():
            if any(keyword in content_lower for keyword in keywords):
                return interview_type

        return 'general'

    def _extract_rounds_info(self, content: str) -> Dict:
        """Extract information about interview rounds."""
        content_lower = content.lower()

        # Count round mentions
        round_patterns = [
            r'round\s*(\d+)',
            r'(\d+)\s*round',
            r'round\s*[:\-]',
            r'interview\s*(\d+)',
        ]

        rounds_found = set()
        for pattern in round_patterns:
            matches = re.finditer(pattern, content_lower)
            for match in matches:
                if match.group(1).isdigit():
                    rounds_found.add(int(match.group(1)))

        # Extract round descriptions
        round_descriptions = []
        round_sections = re.split(r'round\s*\d+|interview\s*\d+', content, flags=re.IGNORECASE)

        for i, section in enumerate(round_sections[1:], 1):  # Skip first split part
            if len(section.strip()) > 50:  # Only meaningful sections
                round_descriptions.append({
                    'round_number': i,
                    'description': section[:500]  # Limit length
                })

        return {
            'count': len(rounds_found) if rounds_found else max(len(round_descriptions), 1),
            'details': round_descriptions
        }

    def _calculate_time_weight(self, experience_date: datetime) -> float:
        """Calculate time-based weight for the experience."""
        days_old = (datetime.utcnow() - experience_date).days
        months_old = days_old / 30.44

        # Use exponential decay
        import math
        decay_lambda = Config.DECAY_LAMBDA
        weight = math.exp(-decay_lambda * months_old)

        # Ensure minimum weight
        return max(weight, 0.1)