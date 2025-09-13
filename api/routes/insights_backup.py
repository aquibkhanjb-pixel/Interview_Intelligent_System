from flask import Blueprint, jsonify, request
from scrapers.pipeline_manager import get_pipeline_manager
from database.connection import db_manager
from database.models import Company, CompanyInsight, Topic
import logging

insights_bp = Blueprint('insights', __name__)
logger = logging.getLogger(__name__)

@insights_bp.route('/<company_name>', methods=['GET'])
def get_company_insights(company_name):
    """Get comprehensive insights for a company."""
    try:
        # Check if we have recent insights
        with db_manager.get_session() as session:
            company = session.query(Company).filter(
                Company.name == company_name
            ).first()
            
            if not company:
                return jsonify({'error': 'Company not found'}), 404
            
            # Get stored insights
            insights = session.query(CompanyInsight).filter(
                CompanyInsight.company_id == company.id
            ).all()
            
            if not insights:
                return jsonify({
                    'error': 'No insights available',
                    'message': f'Run analysis for {company_name} first using POST /api/analysis/{company_name}'
                }), 404
            
            # Format insights
            insights_data = {}
            for insight in insights:
                topic_key = insight.topic.name
                insights_data[topic_key] = {
                    'topic_name': insight.topic.display_name,
                    'category': insight.topic.category,
                    'weighted_frequency': insight.weighted_frequency,
                    'confidence_score': insight.confidence_score,
                    'priority_level': insight.priority_level.upper(),
                    'sample_size': insight.sample_size,
                    'study_recommendation': insight.study_recommendation,
                    'last_updated': insight.analysis_date.isoformat()
                }
            
            # Sort by weighted frequency
            sorted_insights = dict(sorted(insights_data.items(), 
                                        key=lambda x: x[1]['weighted_frequency'], 
                                        reverse=True))
            
            return jsonify({
                'company': company_name,
                'insights': sorted_insights,
                'top_5_topics': list(sorted_insights.keys())[:5],
                'high_priority_topics': [k for k, v in sorted_insights.items() 
                                       if v['priority_level'] == 'HIGH'],
                'analysis_metadata': {
                    'total_topics': len(sorted_insights),
                    'sample_size': insights[0].sample_size if insights else 0,
                    'last_updated': max(insight.analysis_date for insight in insights).isoformat()
                }
            })
            
    except Exception as e:
        logger.error(f"Error fetching insights for {company_name}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@insights_bp.route('/<company_name>/recommendations', methods=['GET'])
def get_study_recommendations(company_name):
    """Get personalized study recommendations for a company."""
    try:
        # Get fresh recommendations from pipeline manager
        pipeline = get_pipeline_manager()
        
        # This would typically generate fresh recommendations
        # For now, return structured recommendations based on insights
        with db_manager.get_session() as session:
            company = session.query(Company).filter(
                Company.name == company_name
            ).first()
            
            if not company:
                return jsonify({'error': 'Company not found'}), 404
            
            insights = session.query(CompanyInsight).filter(
                CompanyInsight.company_id == company.id
            ).order_by(CompanyInsight.weighted_frequency.desc()).limit(10).all()
            
            if not insights:
                return jsonify({'error': 'No insights available for recommendations'}), 404
            
            # Generate recommendations
            recommendations = {
                'study_plan': {},
                'priority_topics': [],
                'time_allocation': {},
                'practice_resources': {}
            }
            
            # Top priority topics
            high_priority = [i for i in insights if i.priority_level == 'high'][:3]
            
            for insight in high_priority:
                recommendations['priority_topics'].append({
                    'topic': insight.topic.display_name,
                    'category': insight.topic.category,
                    'frequency': insight.weighted_frequency,
                    'recommendation': insight.study_recommendation
                })
            
            # 4-week study plan
            top_topics = insights[:4]
            for i, insight in enumerate(top_topics, 1):
                recommendations['study_plan'][f'week_{i}'] = {
                    'focus_topic': insight.topic.display_name,
                    'category': insight.topic.category,
                    'importance': insight.weighted_frequency,
                    'estimated_hours': 15 if insight.topic.category == 'algorithms' else 10
                }
            
            # Time allocation
            recommendations['time_allocation'] = {
                'high_priority': '50%',
                'medium_priority': '30%',
                'review_and_practice': '20%'
            }
            
            return jsonify({
                'company': company_name,
                'recommendations': recommendations,
                'generated_at': insights[0].analysis_date.isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error generating recommendations for {company_name}: {e}")
        return jsonify({'error': 'Internal server error'}), 500
