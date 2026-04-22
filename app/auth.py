import os
from flask import request, jsonify

_API_KEY = os.environ.get("API_KEY", "")


_PUBLIC_PATHS = {"/health"}


def require_api_key():
    if not _API_KEY or request.path in _PUBLIC_PATHS:
        return
    key = request.headers.get("X-API-Key", "")
    if key != _API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
