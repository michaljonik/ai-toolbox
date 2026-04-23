import os
import secrets
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.services.youtube import fetch_video_data

mcp = FastMCP(
    "ai-toolbox",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)
mcp_asgi = mcp.streamable_http_app()  # Streamable HTTP transport (MCP 2025-03-26)
mcp_sse_asgi = mcp.sse_app()          # SSE transport (legacy, for n8n / older clients)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="ai-toolbox", redirect_slashes=False, lifespan=lifespan)

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

_PUBLIC_PATHS = {"/health", "/oauth/token", "/.well-known/oauth-authorization-server"}


def _api_key() -> str:
    return os.environ.get("API_KEY", "")


def _is_authorized(request: Request) -> bool:
    api_key = _api_key()
    if not api_key:
        return True  # auth disabled

    # X-API-Key header (legacy)
    if request.headers.get("X-API-Key") == api_key:
        return True

    # Bearer token
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer ") and auth[7:] == api_key:
        return True

    return False


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)
        if not _is_authorized(request):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return await call_next(request)


app.add_middleware(APIKeyMiddleware)

# ---------------------------------------------------------------------------
# OAuth endpoints
# ---------------------------------------------------------------------------

_SERVER_BASE = os.environ.get("SERVER_BASE_URL", "http://localhost:8000")


@app.get("/.well-known/oauth-authorization-server")
def oauth_metadata():
    return {
        "issuer": _SERVER_BASE,
        "token_endpoint": f"{_SERVER_BASE}/oauth/token",
        "grant_types_supported": ["client_credentials"],
        "token_endpoint_auth_methods_supported": ["client_secret_post"],
    }


@app.post("/oauth/token")
async def oauth_token(request: Request):
    form = await request.form()
    grant_type = form.get("grant_type")
    client_id = form.get("client_id", "")
    client_secret = form.get("client_secret", "")

    if grant_type != "client_credentials":
        return JSONResponse(
            {"error": "unsupported_grant_type"}, status_code=400
        )

    expected_id = os.environ.get("OAUTH_CLIENT_ID", "")
    expected_secret = os.environ.get("OAUTH_CLIENT_SECRET", "")

    if not expected_id or not expected_secret:
        return JSONResponse({"error": "server_misconfiguration"}, status_code=500)

    # Use secrets.compare_digest to avoid timing attacks
    id_ok = secrets.compare_digest(client_id, expected_id)
    secret_ok = secrets.compare_digest(client_secret, expected_secret)
    if not (id_ok and secret_ok):
        return JSONResponse({"error": "invalid_client"}, status_code=401)

    return JSONResponse(
        {
            "access_token": _api_key(),
            "token_type": "bearer",
            "expires_in": 3600,
        }
    )


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Mount MCP transports
# Explicit routes above take priority over mounted sub-apps.
#
# Streamable HTTP → POST/GET /mcp   (MCP 2025-03-26, Claude Desktop, n8n ≥ 1.68)
# SSE             → GET /sse        (legacy transport, older n8n / LangChain)
# ---------------------------------------------------------------------------

app.mount("/mcp", mcp_asgi)
app.mount("/sse", mcp_sse_asgi)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
