import os
from flask import request, jsonify

_API_KEY = os.environ.get("API_KEY", "")


def require_api_key():
    if not _API_KEY:
        return  # auth disabled when key not set
    key = request.headers.get("X-API-Key", "")
    if key != _API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
