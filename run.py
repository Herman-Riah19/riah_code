# run.py
"""Riah Code - Application Entry Point"""

import os
from flask import Flask, jsonify, request

from apps.modules.shared.config import Settings, settings

# Import all modules to register blueprints
from apps.modules.corpus import corpusBlueprint
from apps.modules.tokenizer import tokenizerBlueprint
#from apps.modules.model import trainingBlueprint, inferenceBlueprint
from apps.modules.shared.kernel.exceptions import RiahAppError

def createApp(config: Settings | None = None) -> Flask:
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    appConfig = config or settings
    app.config.from_object(appConfig)
    
    # Ensure data directories exist
    appConfig.dataDir.mkdir(parents=True, exist_ok=True)
    appConfig.logsDir.mkdir(parents=True, exist_ok=True)
    appConfig.checkpointDir.mkdir(parents=True, exist_ok=True)
    appConfig.corpusDir.mkdir(parents=True, exist_ok=True)
    appConfig.tokenizerDir.mkdir(parents=True, exist_ok=True)
    appConfig.chatHistoryDir.mkdir(parents=True, exist_ok=True)
    
    # Initialize Flask-Sock for WebSocket (when chat module is ready)
    # chatSock.init_app(app)
    
    # Register blueprints
    app.register_blueprint(corpusBlueprint)
    app.register_blueprint(tokenizerBlueprint)
    #app.register_blueprint(trainingBlueprint)
    #app.register_blueprint(inferenceBlueprint)
    
    # Health check endpoint
    @app.route("/health")
    def health():
        return jsonify({
            "status": "ok",
            "version": appConfig.appVersion,
            "env": appConfig.appEnv,
        })
    
    # Global error handler
    @app.errorhandler(Exception)
    def handleError(e):
        if isinstance(e, RiahAppError):
            response = jsonify(e.to_dict())
            response.status_code = e.statusCode
            return response
        
        # Log unexpected errors
        app.logger.exception("Unhandled error")
        response = jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Erreur interne du serveur",
                "details": {},
            }
        })
        response.status_code = 500
        return response
    
    # CORS headers for development
    if appConfig.debug:
        @app.after_request
        def addCorsHeaders(response):
            origin = request.headers.get("Origin")
            if origin in appConfig.corsOrigins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            return response
    
    return app


# Create app instance for direct execution
app = createApp()

if __name__ == "__main__":
    # Development server
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=settings.debug)