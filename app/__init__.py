from flask import Flask, jsonify
from .auth import require_api_key
from .routes.trans_yt import trans_yt_bp


def create_app():
    app = Flask(__name__)
    app.before_request(require_api_key)
    app.register_blueprint(trans_yt_bp)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    return app
