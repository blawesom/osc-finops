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
from backend.utils.errors import APIError
from backend.database import init_db, close_db


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__, static_folder="../frontend", static_url_path="")
    
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
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(404)
    def not_found(error):
        return {"error": {"code": "NOT_FOUND", "message": "Resource not found"}}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
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

