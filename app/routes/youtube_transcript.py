from flask import Blueprint, request, jsonify
from app.services.youtube import fetch_video_data

youtube_transcript_bp = Blueprint("youtube_transcript", __name__)


@youtube_transcript_bp.route("/youtube_transcript")
def youtube_transcript():
    video_id = request.args.get("id")
    if not video_id:
        return jsonify({"error": "Missing required parameter: id"}), 400

    languages = request.args.get("lang", "pl,en").split(",")
    return jsonify(fetch_video_data(video_id, languages))
