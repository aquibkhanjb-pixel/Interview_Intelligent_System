from flask import Blueprint, jsonify, request
from database.connection import db_manager
from database.models import Company, CompanyInsight, Topic
import logging
from datetime import datetime

comparison_bp = Blueprint('comparison', __name__)
logger = logging.getLogger(__name__)

@comparison_bp.route('/', methods=['POST'])
def compare_companies():
    """Compare insights across multiple companies."""
    try:
        data = request.get_json()
        if not data or 'companies' not in data:
            return jsonify({'error': 'companies list required'}), 400
        
        companies = data['companies']
        if len(companies) < 2:
            return jsonify({'error': 'At least 2 companies required for comparison'}), 400
        
        if len(companies) > 5:
            return jsonify({'error': 'Maximum 5 companies allowed for comparison'}), 400
        
        comparison_data = {}
        
        with db_manager.get_session() as session:
            for company_name in companies:
                company = session.query(Company).filter(
                    Company.name == company_name
                ).first()
                
                if not company:
                    comparison_data[company_name] = {'error': 'Company not found'}
                    continue
                
                # Get insights for this company
                insights = session.query(CompanyInsight).filter(
                    CompanyInsight.company_id == company.id
                ).order_by(CompanyInsight.weighted_frequency.desc()).all()
                
                if not insights:
                    comparison_data[company_name] = {'error': 'No insights available'}
                    continue
                
                # Format company data
                company_insights = {}
                for insight in insights:
                    topic_key = insight.topic.name
                    company_insights[topic_key] = {
                        'topic_name': insight.topic.display_name,
                        'category': insight.topic.category,
                        'frequency': insight.weighted_frequency,
                        'priority': insight.priority_level
                    }
                
                comparison_data[company_name] = {
                    'insights': company_insights,
                    'top_5_topics': list(company_insights.keys())[:5],
                    'sample_size': insights[0].sample_size if insights else 0
                }
        
        # Generate comparison insights
        comparison_insights = _generate_comparison_insights(comparison_data)
        
        return jsonify({
            'companies': companies,
            'comparison_data': comparison_data,
            'comparison_insights': comparison_insights,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in company comparison: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def _generate_comparison_insights(comparison_data):
    """Generate insights from company comparison."""
    insights = {
        'common_topics': [],
        'unique_topics': {},
        'difficulty_comparison': {},
        'recommendations': {}
    }
    
    # Find common topics across companies
    all_topics = {}
    for company, data in comparison_data.items():
        if 'insights' in data:
            for topic, topic_data in data['insights'].items():
                if topic not in all_topics:
                    all_topics[topic] = []
                all_topics[topic].append({
                    'company': company,
                    'frequency': topic_data['frequency'],
                    'priority': topic_data['priority']
                })
    
    # Identify common topics (appear in 2+ companies)
    for topic, company_data in all_topics.items():
        if len(company_data) >= 2:
            insights['common_topics'].append({
                'topic': topic,
                'companies': company_data,
                'average_frequency': sum(d['frequency'] for d in company_data) / len(company_data)
            })
    
    # Sort common topics by average frequency
    insights['common_topics'].sort(key=lambda x: x['average_frequency'], reverse=True)
    
    return insights
