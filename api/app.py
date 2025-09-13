
from flask import Flask, jsonify
from flask_cors import CORS
from config.database import db
from config.settings import config
from utils.logger import project_logger
import os
import logging

def create_app(config_name=None):
    """
    Application factory for creating Flask app instances.
    """
    # Get configuration
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app_config = config.get(config_name, config['default'])
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(app_config)
    
    # Enable CORS for frontend integration
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:3001", "http://localhost:5000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    
    # Initialize database with app
    db.init_app(app)
    
    # Initialize database connection manager
    with app.app_context():
        try:
            from database.connection import db_manager
            db_manager.initialize_with_app(app, db)
            logging.info("Database manager initialized successfully")
        except Exception as e:
            logging.error(f"Database manager initialization failed: {e}")
    
    # Register blueprints - FIXED IMPORT
    try:
        from api.routes import register_routes
        register_routes(app)
    except ImportError as e:
        logging.error(f"Failed to import routes: {e}")
        # Fallback: register routes manually
        _register_routes_fallback(app)
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Endpoint not found',
            'message': 'The requested API endpoint does not exist',
            'available_endpoints': _get_available_endpoints()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad request',
            'message': 'Invalid request data'
        }), 400
    
    # Root endpoint
    @app.route('/')
    def root():
        return jsonify({
            'message': 'Interview Intelligence System API',
            'version': '1.0.0',
            'status': 'running',
            'docs': '/api/docs',
            'endpoints': {
                'companies': '/api/companies/',
                'insights': '/api/insights/<company_name>',
                'analysis': '/api/analysis/<company_name>',
                'comparison': '/api/compare/',
                'health': '/api/health/'
            }
        })
    
    # API documentation endpoint
    @app.route('/api/docs')
    def api_docs():
        return jsonify({
            'title': 'Interview Intelligence System API',
            'version': '1.0.0',
            'description': 'Advanced interview preparation system with AI-powered insights',
            'endpoints': {
                'GET /api/companies/': 'Get list of all tracked companies',
                'GET /api/companies/<name>/experiences': 'Get interview experiences for a company',
                'GET /api/insights/<company>': 'Get comprehensive insights for a company',
                'GET /api/insights/<company>/recommendations': 'Get study recommendations',
                'POST /api/analysis/<company>': 'Trigger analysis for a company',
                'POST /api/analysis/batch': 'Run batch analysis for multiple companies',
                'GET /api/analysis/status': 'Get analysis system status',
                'POST /api/compare/': 'Compare insights across companies',
                'GET /api/health/': 'Basic health check'
            },
            'authentication': 'Currently none required',
            'rate_limits': 'Standard rate limiting applied',
            'data_formats': 'All endpoints return JSON'
        })
    
    def _get_available_endpoints():
        """Helper function to list available endpoints."""
        endpoints = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                endpoints.append({
                    'endpoint': rule.rule,
                    'methods': list(rule.methods - {'HEAD', 'OPTIONS'})
                })
        return endpoints
    
    logging.info(f"Interview Intelligence API initialized in {config_name} mode")
    return app

def _register_routes_fallback(app):
    """Fallback route registration if import fails."""
    try:
        # Import and register each blueprint individually
        from api.routes.analysis import analysis_bp
        from api.routes.companies import companies_bp
        from api.routes.insights import insights_bp
        from api.routes.comparison import comparison_bp
        from api.routes.health import health_bp
        
        app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
        app.register_blueprint(companies_bp, url_prefix='/api/companies')
        app.register_blueprint(insights_bp, url_prefix='/api/insights')
        app.register_blueprint(comparison_bp, url_prefix='/api/compare')
        app.register_blueprint(health_bp, url_prefix='/api/health')
        
        logging.info("Routes registered via fallback method")
        
    except ImportError as e:
        logging.error(f"Fallback route registration also failed: {e}")
        logging.error("Please ensure all route files exist in api/routes/")