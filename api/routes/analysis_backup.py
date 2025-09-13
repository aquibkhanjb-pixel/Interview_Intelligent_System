from flask import Blueprint, jsonify, request
from scrapers.pipeline_manager import get_pipeline_manager
import logging

analysis_bp = Blueprint('analysis', __name__)
logger = logging.getLogger(__name__)

@analysis_bp.route('/<company_name>', methods=['POST'])
def trigger_company_analysis(company_name):
    """Trigger fresh analysis for a company."""
    try:
        # Get parameters
        data = request.get_json() or {}
        max_experiences = data.get('max_experiences', 20)
        force_refresh = data.get('force_refresh', False)
        
        logger.info(f"Starting analysis for {company_name}")
        
        # Run analysis pipeline
        pipeline = get_pipeline_manager()
        results = pipeline.run_complete_analysis(
            company_name, 
            max_experiences=max_experiences,
            force_refresh=force_refresh
        )
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error running analysis for {company_name}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'company': company_name
        }), 500

@analysis_bp.route('/batch', methods=['POST'])
def trigger_batch_analysis():
    """Trigger analysis for multiple companies."""
    try:
        data = request.get_json()
        if not data or 'companies' not in data:
            return jsonify({'error': 'companies list required'}), 400
        
        companies = data['companies']
        max_experiences_each = data.get('max_experiences_each', 20)
        
        if len(companies) > 5:
            return jsonify({'error': 'Maximum 5 companies allowed in batch'}), 400
        
        logger.info(f"Starting batch analysis for {companies}")
        
        # Run batch analysis
        pipeline = get_pipeline_manager()
        results = pipeline.run_batch_analysis(companies, max_experiences_each)
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@analysis_bp.route('/status', methods=['GET'])
def get_analysis_status():
    """Get current analysis system status."""
    try:
        pipeline = get_pipeline_manager()
        health_metrics = pipeline.get_system_health_metrics()
        
        return jsonify(health_metrics)
        
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        return jsonify({'error': 'Internal server error'}), 500
