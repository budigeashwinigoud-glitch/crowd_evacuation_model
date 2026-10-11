"""Flask application entry point for the crowd evacuation prototype."""

from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask
from flask_cors import CORS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.routes import api

FRONTEND_DIR = PROJECT_ROOT / "frontend"


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
    CORS(app)
    app.register_blueprint(api)

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
    host="127.0.0.1",
    port=5000,
    debug=False,
    use_reloader=False
)