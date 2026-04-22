from flask import Blueprint, request, jsonify
from app.services.youtube import fetch_video_data

trans_yt_bp = Blueprint("trans_yt", __name__)


@trans_yt_bp.route("/trans-yt")
def trans_yt():
    video_id = request.args.get("id")
    if not video_id:
        return jsonify({"error": "Missing required parameter: id"}), 400

    languages = request.args.get("lang", "pl,en").split(",")
    return jsonify(fetch_video_data(video_id, languages))
