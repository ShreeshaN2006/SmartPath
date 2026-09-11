import os
from pathlib import Path

from api.routes import api_bp
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from utils.cache import init_cache
from utils.graph_loader import load_graph

BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend" / "dist"


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
    CORS(app)

    init_cache()

    app.config["GRAPH"] = load_graph()

    app.register_blueprint(api_bp)

    @app.route("/")
    def serve_frontend() -> jsonify:
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return send_from_directory(str(FRONTEND_DIR), "index.html")
        return jsonify({
            "message": "SmartPath API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/api/health",
                "route": "/api/route",
                "replan": "/api/replan",
                "weather": "/api/weather",
                "traffic": "/api/traffic",
                "incidents": "/api/incidents",
                "vehicles": "/api/vehicles",
                "analytics": "/api/analytics",
            }
        })

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
