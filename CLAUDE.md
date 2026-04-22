# ai-toolbox — notes for Claude

## What this is

A self-hosted toolbox for AI agents. Exposes tools as both a REST API (Flask, port 5000) and an MCP server (FastMCP Streamable HTTP, port 8000). Both use the same service logic.

## Project layout

```
app/
  services/        # shared business logic — add new tools here first
    youtube.py     # fetch_video_data(video_id, languages) -> dict
  routes/          # Flask blueprints (one file per tool)
    youtube_transcript.py
  __init__.py      # Flask app factory, registers blueprints + /health
  auth.py          # API key middleware for Flask (reads API_KEY env var)
mcp_server.py      # FastMCP server — registers tools, adds auth middleware
app.py             # Flask entry point
```

## How to add a new tool

1. Create `app/services/<tool>.py` with the core logic as a plain function
2. Create `app/routes/<tool>.py` with a Flask Blueprint calling that function
3. Register the blueprint in `app/__init__.py`
4. Add a `@mcp.tool()` in `mcp_server.py` calling the same service function
5. Update README.md (tool table + usage example)

## Auth

- Controlled by `API_KEY` env var
- Flask: `app/auth.py` runs as `before_request`, returns 401 if key wrong
- MCP: `APIKeyMiddleware` (Starlette `BaseHTTPMiddleware`) wraps the FastMCP ASGI app
- If `API_KEY` is empty/unset, auth is disabled for both

## Running locally (no Docker)

```bash
# Flask API
python app.py

# MCP server
python mcp_server.py

# Both need packages from requirements.txt
pip install -r requirements.txt
```

## Running with Docker

```bash
cp .env.example .env
docker compose up --build
# api → localhost:5000
# mcp → localhost:8000/mcp
```

## Key dependencies

| Package | Why |
|---------|-----|
| `yt-dlp` | YouTube metadata (title, channel, views, etc.) |
| `youtube-transcript-api` | Transcript fetch — no API key needed |
| `mcp[cli]` | FastMCP server + MCP protocol implementation |
| `uvicorn` | ASGI server for the MCP HTTP transport |
| `gunicorn` | WSGI server for Flask in production |

## CI

GitHub Actions (`.github/workflows/docker.yml`) builds and pushes to GHCR on every push to `main`. Uses `docker/setup-buildx-action` (required for GHA cache support with the default Docker driver).

## Things to watch out for

- `yt-dlp` version must exist on PyPI — version numbers follow a date format (`YYYY.MM.DD`) and not all dates have releases
- The MCP endpoint is `/mcp` (FastMCP default for streamable HTTP transport)
- Both services share the same Docker image; `mcp` service overrides CMD in docker-compose
