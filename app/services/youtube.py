from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp


def fetch_video_data(video_id: str, languages: list[str]) -> dict:
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

    return {
        "title":       info.get("title"),
        "channel":     info.get("uploader"),
        "published":   info.get("upload_date"),
        "duration":    info.get("duration"),
        "tags":        info.get("tags", []),
        "description": info.get("description"),
        "views":       info.get("view_count"),
        "thumbnail":   info.get("thumbnail"),
        "transcript":  transcript,
    }
