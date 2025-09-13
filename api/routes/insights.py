"""
Insights routes with real data queries.
"""

from flask import Blueprint, request, jsonify
from database.connection import db_manager
from database.models import Company, InterviewExperience, CompanyInsight, Topic
import logging
from datetime import datetime

# Initialize blueprint
insights_bp = Blueprint('insights', __name__)
logger = logging.getLogger(__name__)

@insights_bp.route('/<company_name>', methods=['GET'])
def get_company_insights(company_name):
    """Get insights for a specific company using real data."""
    try:
        logger.info(f"Getting insights for {company_name}")

        with db_manager.get_session() as session:
            # Find company
            company = session.query(Company).filter(
                Company.name == company_name
            ).first()

            if not company:
                return jsonify({
                    'error': 'Company not found',
                    'company': company_name
                }), 404

            # Get actual experience count
            total_experiences = session.query(InterviewExperience).filter(
                InterviewExperience.company_id == company.id
            ).count()

            if total_experiences == 0:
                return jsonify({
                    'company': company_name,
                    'insights': {},
                    'analysis_metadata': {
                        'sample_size': 0,
                        'last_updated': datetime.utcnow().isoformat(),
                        'data_quality_score': 0.0,
                        'confidence_threshold': 0.7
                    },
                    'status': 'no_data',
                    'message': f'No interview experiences found for {company_name}. Please run data collection first.'
                })

            # Get stored insights or generate basic ones
            stored_insights = session.query(CompanyInsight).filter(
                CompanyInsight.company_id == company.id
            ).all()

            insights_data = {}

            if stored_insights:
                # Use stored insights
                for insight in stored_insights:
                    topic_key = insight.topic.name
                    insights_data[topic_key] = {
                        'topic_name': insight.topic.display_name,
                        'category': insight.topic.category,
                        'weighted_frequency': insight.weighted_frequency,
                        'priority_level': insight.priority_level.upper(),
                        'confidence_score': insight.confidence_score,
                        'sample_size': insight.sample_size,
                        'last_updated': insight.analysis_date.isoformat()
                    }
            else:
                # Generate basic insights from experiences
                experiences = session.query(InterviewExperience).filter(
                    InterviewExperience.company_id == company.id
                ).order_by(InterviewExperience.experience_date.desc()).all()

                # Basic topic frequency analysis
                topic_mentions = {}

                for exp in experiences:
                    # Simple keyword-based analysis
                    content_lower = exp.content.lower()

                    # Algorithm topics
                    if any(keyword in content_lower for keyword in ['dynamic programming', 'dp', 'memoization']):
                        topic_mentions['algorithms.dynamic_programming'] = topic_mentions.get('algorithms.dynamic_programming', 0) + 1

                    if any(keyword in content_lower for keyword in ['tree', 'binary tree', 'bst', 'dfs', 'bfs']):
                        topic_mentions['data_structures.tree'] = topic_mentions.get('data_structures.tree', 0) + 1

                    if any(keyword in content_lower for keyword in ['system design', 'scalability', 'architecture', 'distributed']):
                        topic_mentions['system_design.scalability'] = topic_mentions.get('system_design.scalability', 0) + 1

                    if any(keyword in content_lower for keyword in ['array', 'string', 'hash', 'sorting']):
                        topic_mentions['algorithms.basic'] = topic_mentions.get('algorithms.basic', 0) + 1

                    if any(keyword in content_lower for keyword in ['graph', 'dijkstra', 'shortest path']):
                        topic_mentions['algorithms.graph'] = topic_mentions.get('algorithms.graph', 0) + 1

                # Convert to insights format
                topic_mappings = {
                    'algorithms.dynamic_programming': {'name': 'Dynamic Programming', 'category': 'Algorithms'},
                    'data_structures.tree': {'name': 'Tree Data Structures', 'category': 'Data Structures'},
                    'system_design.scalability': {'name': 'System Design - Scalability', 'category': 'System Design'},
                    'algorithms.basic': {'name': 'Basic Algorithms', 'category': 'Algorithms'},
                    'algorithms.graph': {'name': 'Graph Algorithms', 'category': 'Algorithms'}
                }

                for topic_key, count in topic_mentions.items():
                    if count > 0:
                        frequency = (count / total_experiences) * 100
                        topic_info = topic_mappings.get(topic_key, {'name': topic_key, 'category': 'General'})

                        priority = 'HIGH' if frequency > 30 else 'MEDIUM' if frequency > 15 else 'LOW'
                        confidence = min(0.9, 0.5 + (count / total_experiences))

                        insights_data[topic_key] = {
                            'topic_name': topic_info['name'],
                            'category': topic_info['category'],
                            'weighted_frequency': round(frequency, 1),
                            'priority_level': priority,
                            'confidence_score': round(confidence, 2),
                            'sample_size': total_experiences,
                            'last_updated': datetime.utcnow().isoformat()
                        }

            # Sort by weighted frequency
            sorted_insights = dict(sorted(insights_data.items(),
                                        key=lambda x: x[1]['weighted_frequency'],
                                        reverse=True))

            # Get latest update
            latest_experience = session.query(InterviewExperience).filter(
                InterviewExperience.company_id == company.id
            ).order_by(InterviewExperience.scraped_at.desc()).first()

            return jsonify({
                'company': company_name,
                'insights': sorted_insights,
                'top_5_topics': list(sorted_insights.keys())[:5],
                'high_priority_topics': [k for k, v in sorted_insights.items()
                                       if v['priority_level'] == 'HIGH'],
                'analysis_metadata': {
                    'sample_size': total_experiences,
                    'last_updated': latest_experience.scraped_at.isoformat() if latest_experience else datetime.utcnow().isoformat(),
                    'data_quality_score': 85.0 if total_experiences >= 10 else 60.0 if total_experiences >= 5 else 30.0,
                    'confidence_threshold': 0.7,
                    'total_topics': len(sorted_insights)
                },
                'status': 'live_data',
                'message': f'Generated insights from {total_experiences} interview experiences'
            })

    except Exception as e:
        logger.error(f"Error getting insights for {company_name}: {e}")
        return jsonify({
            'error': str(e),
            'company': company_name,
            'message': 'Insights temporarily unavailable'
        }), 500

@insights_bp.route('/<company_name>/recommendations', methods=['GET'])
def get_recommendations(company_name):
    """Get study recommendations for a company based on real data."""
    try:
        with db_manager.get_session() as session:
            # Find company
            company = session.query(Company).filter(
                Company.name == company_name
            ).first()

            if not company:
                return jsonify({
                    'error': 'Company not found',
                    'company': company_name
                }), 404

            # Get experience count
            total_experiences = session.query(InterviewExperience).filter(
                InterviewExperience.company_id == company.id
            ).count()

            if total_experiences == 0:
                return jsonify({
                    'company': company_name,
                    'recommendations': {
                        'high_priority': [],
                        'medium_priority': [],
                        'low_priority': []
                    },
                    'study_plan': {
                        'estimated_weeks': 0,
                        'hours_per_week': 0,
                        'focus_areas': []
                    },
                    'status': 'no_data',
                    'message': f'No data available for {company_name}. Please run data collection first.'
                })

            # Get recent experiences for analysis
            experiences = session.query(InterviewExperience).filter(
                InterviewExperience.company_id == company.id
            ).order_by(InterviewExperience.experience_date.desc()).all()

            # Analyze topics from experiences
            topic_frequency = {}
            role_analysis = {}
            difficulty_analysis = {'easy': 0, 'medium': 0, 'hard': 0}

            for exp in experiences:
                content_lower = exp.content.lower()

                # Role analysis
                if exp.role:
                    role_analysis[exp.role] = role_analysis.get(exp.role, 0) + 1

                # Difficulty analysis
                if exp.difficulty_score:
                    if exp.difficulty_score <= 3:
                        difficulty_analysis['easy'] += 1
                    elif exp.difficulty_score <= 7:
                        difficulty_analysis['medium'] += 1
                    else:
                        difficulty_analysis['hard'] += 1

                # Topic frequency analysis
                topics = {
                    'Dynamic Programming': ['dynamic programming', 'dp', 'memoization', 'knapsack'],
                    'Tree Data Structures': ['tree', 'binary tree', 'bst', 'dfs', 'bfs', 'traversal'],
                    'System Design': ['system design', 'scalability', 'architecture', 'distributed', 'microservices'],
                    'Graph Algorithms': ['graph', 'dijkstra', 'shortest path', 'topology', 'mst'],
                    'Array & String': ['array', 'string', 'two pointer', 'sliding window'],
                    'Hash Tables': ['hash', 'hashmap', 'dictionary', 'frequency'],
                    'Sorting & Searching': ['sorting', 'binary search', 'merge sort', 'quick sort'],
                    'Behavioral Questions': ['behavioral', 'leadership', 'conflict', 'teamwork', 'culture fit']
                }

                for topic, keywords in topics.items():
                    if any(keyword in content_lower for keyword in keywords):
                        topic_frequency[topic] = topic_frequency.get(topic, 0) + 1

            # Categorize topics by frequency
            high_priority = []
            medium_priority = []
            low_priority = []

            total_mentions = sum(topic_frequency.values()) if topic_frequency else 1

            for topic, count in sorted(topic_frequency.items(), key=lambda x: x[1], reverse=True):
                frequency_percentage = (count / total_experiences) * 100

                if frequency_percentage >= 30:
                    high_priority.append(topic)
                elif frequency_percentage >= 15:
                    medium_priority.append(topic)
                else:
                    low_priority.append(topic)

            # Generate study plan
            total_topics = len(topic_frequency)
            estimated_weeks = max(4, min(12, total_topics))
            hours_per_week = 15 if total_experiences >= 10 else 12

            # Determine focus areas
            focus_areas = ['Coding']
            if 'System Design' in high_priority or 'System Design' in medium_priority:
                focus_areas.append('System Design')
            if 'Behavioral Questions' in topic_frequency:
                focus_areas.append('Behavioral')

            # Most common role
            primary_role = max(role_analysis.keys(), key=role_analysis.get) if role_analysis else 'Software Engineer'

            return jsonify({
                'company': company_name,
                'recommendations': {
                    'high_priority': high_priority[:5],
                    'medium_priority': medium_priority[:5],
                    'low_priority': low_priority[:3]
                },
                'study_plan': {
                    'estimated_weeks': estimated_weeks,
                    'hours_per_week': hours_per_week,
                    'focus_areas': focus_areas,
                    'primary_role': primary_role
                },
                'analysis_insights': {
                    'total_experiences_analyzed': total_experiences,
                    'difficulty_distribution': difficulty_analysis,
                    'role_distribution': role_analysis,
                    'topic_coverage': len(topic_frequency)
                },
                'status': 'data_driven',
                'message': f'Recommendations based on analysis of {total_experiences} interview experiences'
            })

    except Exception as e:
        logger.error(f"Error getting recommendations for {company_name}: {e}")
        return jsonify({
            'error': str(e),
            'company': company_name
        }), 500