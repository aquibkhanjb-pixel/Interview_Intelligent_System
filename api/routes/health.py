from flask import Blueprint, jsonify
from database.connection import db_manager
from datetime import datetime
import logging

health_bp = Blueprint('health', __name__)
logger = logging.getLogger(__name__)

@health_bp.route('/', methods=['GET'])
def health_check():
    """Basic health check."""
    try:
        db_healthy = db_manager.health_check()
        
        return jsonify({
            'status': 'healthy' if db_healthy else 'degraded',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected' if db_healthy else 'disconnected',
            'version': '1.0.0'
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503