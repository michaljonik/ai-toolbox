import os
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from starlette.requests import Request
from starlette.responses import JSONResponse as StarletteJSONResponse
from starlette.routing import Route

from app.services.youtube import fetch_video_data

mcp = FastMCP("ai-toolbox")


async def health(request: Request):
    return StarletteJSONResponse({"status": "ok"})


class APIKeyMiddleware(BaseHTTPMiddleware):
    _public = {"/health"}

    async def dispatch(self, request, call_next):
        if request.url.path in self._public:
            return await call_next(request)
        api_key = os.environ.get("API_KEY", "")
        if api_key and request.headers.get("X-API-Key") != api_key:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return await call_next(request)


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


if __name__ == "__main__":
    from starlette.applications import Starlette
    from starlette.middleware import Middleware
    from starlette.routing import Mount

    app = Starlette(
        routes=[
            Route("/health", health),
            Mount("/", app=mcp.streamable_http_app()),
        ],
        middleware=[Middleware(APIKeyMiddleware)],
    )
    uvicorn.run(app, host="0.0.0.0", port=8000)
