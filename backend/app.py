"""Flask application entry point."""
import os
from flask import Flask
from flask_cors import CORS

from backend.config.settings import (
    FLASK_ENV,
    FLASK_DEBUG,
    SECRET_KEY,
    CORS_ORIGINS,
    LOG_LEVEL
)
from backend.api.auth import auth_bp


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__, static_folder="../frontend", static_url_path="")
    
    # Configuration
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["ENV"] = FLASK_ENV
    app.config["DEBUG"] = FLASK_DEBUG
    
    # CORS configuration
    CORS(app, origins=CORS_ORIGINS, supports_credentials=True)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    
    # Root route - serve frontend
    @app.route("/")
    def index():
        return app.send_static_file("index.html")
    
    # Health check endpoint
    @app.route("/health")
    def health():
        return {"status": "ok", "service": "osc-finops"}, 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": {"code": "NOT_FOUND", "message": "Resource not found"}}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {"error": {"code": "INTERNAL_ERROR", "message": "An internal error occurred"}}, 500
    
    return app


if __name__ == "__main__":
    app = create_app()
    from backend.config.settings import SERVER_HOST, SERVER_PORT
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=FLASK_DEBUG)

