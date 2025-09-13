#!/usr/bin/env python3
"""
Script to scrape Microsoft interview experiences and save to database
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.geeksforgeeks_scraper import GeeksforGeeksScraper
from database.connection import db_manager
from database.models import Company, InterviewExperience
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_microsoft_experiences(limit=5):
    """Scrape Microsoft interview experiences and save to database"""

    logger.info("Starting Microsoft interview experience scraping...")

    # Initialize scraper
    scraper = GeeksforGeeksScraper()

    # Get Microsoft company from database
    with db_manager.get_session() as session:
        microsoft_company = session.query(Company).filter_by(name='Microsoft').first()
        if not microsoft_company:
            logger.error("Microsoft company not found in database!")
            return False

        logger.info(f"Found Microsoft company in database: ID {microsoft_company.id}")

        # Scrape experiences
        experiences_saved = 0

        try:
            # Use the scraper's built-in method to get experiences
            for experience_data in scraper.scrape_company_experiences('Microsoft', max_experiences=limit):
                try:
                    # Create new experience record
                    experience = InterviewExperience(
                        company_id=microsoft_company.id,
                        title=experience_data.get('title', 'Microsoft Interview Experience'),
                        content=experience_data.get('content', ''),
                        role=experience_data.get('role', 'SDE'),
                        source_platform=experience_data.get('source_platform', 'geeksforgeeks'),
                        source_url=experience_data.get('source_url', ''),
                        experience_date=experience_data.get('experience_date', datetime.utcnow()),
                        success=experience_data.get('success', True),
                        time_weight=experience_data.get('time_weight', 1.0),
                        difficulty_score=experience_data.get('difficulty_score', None)
                    )

                    session.add(experience)
                    session.commit()
                    experiences_saved += 1

                    logger.info(f"Saved experience {experiences_saved}: {experience.title[:50]}...")

                except Exception as e:
                    logger.error(f"Error saving experience: {e}")
                    session.rollback()
                    continue

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return False

        logger.info(f"Successfully scraped and saved {experiences_saved} Microsoft experiences")

        # Update company status
        if experiences_saved > 0:
            microsoft_company.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated Microsoft company timestamp")

        return experiences_saved > 0

if __name__ == "__main__":
    success = scrape_microsoft_experiences(limit=5)
    if success:
        print("✅ Microsoft scraping completed successfully!")
    else:
        print("❌ Microsoft scraping failed!")