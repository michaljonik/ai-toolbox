from flask import Blueprint, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

trans_yt_bp = Blueprint("trans_yt", __name__)


@trans_yt_bp.route("/trans-yt")
def trans_yt():
    video_id = request.args.get("id")
    if not video_id:
        return jsonify({"error": "Missing required parameter: id"}), 400

    languages = request.args.get("lang", "pl,en").split(",")
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    try:
        api = YouTubeTranscriptApi()
        data = api.fetch(video_id, languages=languages)
        transcript = " ".join([x.text for x in data])
    except Exception:
        transcript = None

    return jsonify({
        "title":       info.get("title"),
        "channel":     info.get("uploader"),
        "published":   info.get("upload_date"),
        "duration":    info.get("duration"),
        "tags":        info.get("tags", []),
        "description": info.get("description"),
        "views":       info.get("view_count"),
        "thumbnail":   info.get("thumbnail"),
        "transcript":  transcript,
    })
