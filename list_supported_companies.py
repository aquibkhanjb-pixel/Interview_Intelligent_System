#!/usr/bin/env python3
"""
List all supported companies and their current status.

This script shows:
1. All companies supported by the extraction service
2. Which companies currently have data (appear in frontend)
3. Quick stats for each company
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.company_extractor import company_extractor
from database.connection import db_manager
from database.models import Company, InterviewExperience
import logging

logging.basicConfig(level=logging.WARNING)  # Reduce noise

def get_company_stats():
    """Get comprehensive company statistics."""
    try:
        with db_manager.get_session() as session:
            # Get all companies from extraction service
            supported_companies = company_extractor.get_all_companies()

            # Get database stats
            db_companies = {}
            for company in session.query(Company).all():
                exp_count = session.query(InterviewExperience).filter(
                    InterviewExperience.company_id == company.id
                ).count()

                # Get success rate
                success_count = session.query(InterviewExperience).filter(
                    InterviewExperience.company_id == company.id,
                    InterviewExperience.success == True
                ).count()

                success_rate = (success_count / exp_count * 100) if exp_count > 0 else 0

                db_companies[company.name] = {
                    'experience_count': exp_count,
                    'success_count': success_count,
                    'success_rate': success_rate,
                    'status': 'active' if exp_count > 0 else 'inactive'
                }

            # Combine supported companies with database stats
            company_stats = []
            for company in supported_companies:
                stats = db_companies.get(company, {
                    'experience_count': 0,
                    'success_count': 0,
                    'success_rate': 0,
                    'status': 'not_scraped'
                })

                patterns = company_extractor.get_patterns_for_company(company)

                company_stats.append({
                    'name': company,
                    'patterns': patterns,
                    'pattern_count': len(patterns),
                    **stats
                })

            return company_stats

    except Exception as e:
        print(f"Error getting company stats: {e}")
        return []

def show_supported_companies():
    """Show all supported companies with their patterns."""
    print("="*80)
    print("ALL SUPPORTED COMPANIES (with patterns)")
    print("="*80)

    supported = company_extractor.get_all_companies()

    print(f"Total supported companies: {len(supported)}\n")

    # Group by category
    categories = {
        'High Priority': ['PhonePe', 'Myntra', 'PayPal', 'PayTM'],
        'Tech Giants': ['Google', 'Amazon', 'Microsoft', 'Apple', 'Meta', 'Netflix'],
        'Indian Tech': [c for c in supported if c not in ['PhonePe', 'Myntra', 'PayPal', 'PayTM', 'Google', 'Amazon', 'Microsoft', 'Apple', 'Meta', 'Netflix']]
    }

    for category, companies in categories.items():
        if not companies:
            continue

        print(f"{category} ({len(companies)} companies):")
        print("-" * 40)

        for company in companies:
            if company in supported:  # Only show if actually supported
                patterns = company_extractor.get_patterns_for_company(company)
                print(f"  {company:<20} -> {patterns}")

        print()

def show_database_status():
    """Show companies that currently have data (appear in frontend)."""
    print("="*80)
    print("COMPANIES WITH DATA (appear in frontend dropdown)")
    print("="*80)

    company_stats = get_company_stats()
    active_companies = [c for c in company_stats if c['status'] == 'active']

    if not active_companies:
        print("No companies found with data.")
        return

    # Sort by experience count
    active_companies.sort(key=lambda x: x['experience_count'], reverse=True)

    print(f"Found {len(active_companies)} companies with data:\n")

    print(f"{'#':<3} {'Company':<20} {'Experiences':<12} {'Success':<8} {'Rate':<8} {'Status'}")
    print("-" * 70)

    for i, company in enumerate(active_companies, 1):
        print(f"{i:<3} {company['name']:<20} "
              f"{company['experience_count']:<12} "
              f"{company['success_count']:<8} "
              f"{company['success_rate']:.1f}%{'':<4} "
              f"{company['status']}")

def show_ready_to_scrape():
    """Show companies that are configured but don't have data yet."""
    print("="*80)
    print("READY TO SCRAPE (configured but no data yet)")
    print("="*80)

    company_stats = get_company_stats()
    ready_companies = [c for c in company_stats if c['status'] == 'not_scraped']

    if not ready_companies:
        print("All configured companies have been scraped!")
        return

    print(f"Found {len(ready_companies)} companies ready to scrape:\n")

    for i, company in enumerate(ready_companies, 1):
        patterns = ', '.join(company['patterns'][:3])  # Show first 3 patterns
        if len(company['patterns']) > 3:
            patterns += f", ... (+{len(company['patterns'])-3} more)"

        print(f"{i:2d}. {company['name']:<20} -> {patterns}")

def show_summary():
    """Show overall summary."""
    print("="*80)
    print("SUMMARY")
    print("="*80)

    company_stats = get_company_stats()

    total_supported = len(company_stats)
    active_count = len([c for c in company_stats if c['status'] == 'active'])
    ready_count = len([c for c in company_stats if c['status'] == 'not_scraped'])
    total_experiences = sum(c['experience_count'] for c in company_stats)

    print(f"Total supported companies:     {total_supported}")
    print(f"Companies with data (active):  {active_count}")
    print(f"Companies ready to scrape:     {ready_count}")
    print(f"Total experiences collected:   {total_experiences}")

    print(f"\nTop companies by experience count:")
    top_companies = sorted(
        [c for c in company_stats if c['status'] == 'active'],
        key=lambda x: x['experience_count'],
        reverse=True
    )[:5]

    for i, company in enumerate(top_companies, 1):
        print(f"  {i}. {company['name']}: {company['experience_count']} experiences")

def main():
    """Main function."""
    print("Interview Intelligence System - Company Status Report")
    print(f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if len(sys.argv) > 1:
        if sys.argv[1] == '--patterns':
            show_supported_companies()
        elif sys.argv[1] == '--active':
            show_database_status()
        elif sys.argv[1] == '--ready':
            show_ready_to_scrape()
        elif sys.argv[1] == '--summary':
            show_summary()
        else:
            print("Usage: python list_supported_companies.py [--patterns|--active|--ready|--summary]")
    else:
        # Show everything
        show_summary()
        print()
        show_database_status()
        print()
        show_ready_to_scrape()

        print("\n" + "="*80)
        print("USAGE EXAMPLES:")
        print("  python test_new_company.py 'Razorpay'     # Test specific company")
        print("  python list_supported_companies.py --patterns    # Show all patterns")
        print("  python list_supported_companies.py --active      # Show active companies")
        print("  python list_supported_companies.py --ready       # Show ready to scrape")

if __name__ == "__main__":
    main()