import os
import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from mcp.server.fastmcp import FastMCP

from app.services.youtube import fetch_video_data

app = FastAPI(title="ai-toolbox", redirect_slashes=False)
mcp = FastMCP("ai-toolbox")


class APIKeyMiddleware(BaseHTTPMiddleware):
    _public = {"/health"}

    async def dispatch(self, request, call_next):
        if request.url.path in self._public:
            return await call_next(request)
        api_key = os.environ.get("API_KEY", "")
        if api_key and request.headers.get("X-API-Key") != api_key:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return await call_next(request)


app.add_middleware(APIKeyMiddleware)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/youtube_transcript")
def youtube_transcript(
    video_id: str = Query(alias="id"),
    lang: str = "pl,en",
):
    try:
        return fetch_video_data(video_id, lang.split(","))
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@mcp.tool()
def youtube_transcript(video_id: str, lang: str = "pl,en") -> dict:
    """
    Fetch YouTube video transcript and metadata.

    Args:
        video_id: YouTube video ID (e.g. 'dQw4w9WgXcQ')
        lang: Comma-separated language codes for transcript, in priority order (e.g. 'pl,en')

    Returns:
        title, channel, published date (YYYYMMDD), duration (seconds),
        tags, description, view count, thumbnail URL, and full transcript text.
    """
    return fetch_video_data(video_id, lang.split(","))


app.mount("/mcp", mcp.streamable_http_app())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
