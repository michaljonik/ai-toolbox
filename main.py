import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.services.youtube import fetch_video_data

mcp = FastMCP(
    "ai-toolbox",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)
mcp_asgi = mcp.streamable_http_app()  # initializes session manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="ai-toolbox", redirect_slashes=False, lifespan=lifespan)


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
def youtube_transcript_rest(
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


# Mount at "/" so the sub-app receives the full path "/mcp"
# matching FastMCP's internal route. Explicit routes above take priority.
app.mount("/", mcp_asgi)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
