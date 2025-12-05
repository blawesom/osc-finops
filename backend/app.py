"""Flask application entry point."""
import os
from flask import Flask, jsonify
from flask_cors import CORS

from backend.config.settings import (
    FLASK_ENV,
    FLASK_DEBUG,
    SECRET_KEY,
    CORS_ORIGINS,
    LOG_LEVEL
)
from backend.api.auth import auth_bp
from backend.api.catalog import catalog_bp
from backend.api.quote import quote_bp
from backend.api.consumption import consumption_bp
from backend.api.cost import cost_bp
from backend.api.trends import trends_bp
from backend.utils.errors import APIError
from backend.database import init_db, close_db
from backend.utils.logger import setup_logging
from backend.utils.error_logger import log_exception, log_error_message


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__, static_folder="../frontend", static_url_path="")
    
    # Initialize logging first (before other operations)
    setup_logging()
    
    # Configuration
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["ENV"] = FLASK_ENV
    app.config["DEBUG"] = FLASK_DEBUG
    
    # CORS configuration
    CORS(app, origins=CORS_ORIGINS, supports_credentials=True)
    
    # Initialize database
    init_db()
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(catalog_bp, url_prefix='/api')
    app.register_blueprint(quote_bp, url_prefix='/api')
    app.register_blueprint(consumption_bp, url_prefix='/api')
    app.register_blueprint(cost_bp, url_prefix='/api')
    app.register_blueprint(trends_bp, url_prefix='/api')
    
    # Root route - serve frontend
    @app.route("/")
    def index():
        return app.send_static_file("index.html")
    
    # Health check endpoint
    @app.route("/health")
    def health():
        return {"status": "ok", "service": "osc-finops"}, 200
    
    # Error handlers
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle APIError exceptions."""
        # Log the API error
        log_exception(error, status_code=error.status_code)
        
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        log_error_message(
            "Resource not found",
            status_code=404,
            additional_context={"error_type": "NOT_FOUND"}
        )
        return {"error": {"code": "NOT_FOUND", "message": "Resource not found"}}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        # Log the exception if it's an Exception instance
        if isinstance(error, Exception):
            log_exception(error, status_code=500)
        else:
            log_error_message(
                "Internal server error occurred",
                status_code=500,
                additional_context={"error_type": "INTERNAL_ERROR"}
            )
        return {"error": {"code": "INTERNAL_ERROR", "message": "An internal error occurred"}}, 500
    
    @app.errorhandler(Exception)
    def handle_all_exceptions(error):
        """Handle all unhandled exceptions."""
        # Log the exception
        log_exception(error, status_code=500)
        
        # Return appropriate error response
        if FLASK_DEBUG:
            # In debug mode, include error details
            return {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(error),
                    "type": type(error).__name__
                }
            }, 500
        else:
            # In production, return generic error
            return {"error": {"code": "INTERNAL_ERROR", "message": "An internal error occurred"}}, 500

    # Register teardown handler for database cleanup
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Close database session on app context teardown."""
        close_db()

    return app


if __name__ == "__main__":
    app = create_app()
    from backend.config.settings import SERVER_HOST, SERVER_PORT
    try:
        app.run(host=SERVER_HOST, port=SERVER_PORT, debug=FLASK_DEBUG)
    finally:
        close_db()

