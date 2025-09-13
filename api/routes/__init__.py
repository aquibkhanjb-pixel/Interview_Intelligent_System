"""
API Routes registration module.
This file was missing and causing your 404 errors.
"""

def register_routes(app):
    """Register all API route blueprints with comprehensive error handling."""
    
    registered_routes = []
    failed_routes = []
    
    # List of all expected blueprint modules
    blueprint_modules = [
        ('analysis', 'analysis_bp', '/api/analysis'),
        ('companies', 'companies_bp', '/api/companies'),
        ('insights', 'insights_bp', '/api/insights'),
        ('comparison', 'comparison_bp', '/api/compare'),
        ('health', 'health_bp', '/api/health')
    ]
    
    for module_name, blueprint_name, url_prefix in blueprint_modules:
        try:
            # Dynamic import of each blueprint
            module = __import__(f'api.routes.{module_name}', fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            
            # Register the blueprint
            app.register_blueprint(blueprint, url_prefix=url_prefix)
            registered_routes.append(f"{module_name} -> {url_prefix}")
            
        except ImportError as e:
            failed_routes.append(f"{module_name}: ImportError - {e}")
        except AttributeError as e:
            failed_routes.append(f"{module_name}: Blueprint '{blueprint_name}' not found - {e}")
        except Exception as e:
            failed_routes.append(f"{module_name}: Unexpected error - {e}")
    
    # Report results (using ASCII characters for Windows compatibility)
    if registered_routes:
        print(f"SUCCESS: Successfully registered {len(registered_routes)} route modules:")
        for route in registered_routes:
            print(f"   - {route}")

    if failed_routes:
        print(f"WARNING: Failed to register {len(failed_routes)} route modules:")
        for failure in failed_routes:
            print(f"   X {failure}")
        print("\nNOTE: Some API endpoints may not be available")
    
    # Return success status
    return len(registered_routes) > 0