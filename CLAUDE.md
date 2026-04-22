# ai-toolbox — notes for Claude

## What this is

A self-hosted toolbox for AI agents. Single FastAPI + FastMCP server on port 8000:
- `/youtube_transcript` — REST endpoint
- `/mcp` — MCP Streamable HTTP endpoint
- `/health` — always public, no auth

## Project layout

```
app/
  services/        # shared business logic — add new tools here first
    youtube.py     # fetch_video_data(video_id, languages) -> dict
main.py            # single entrypoint: FastAPI app + MCP tools + auth middleware
```

## How to add a new tool

1. Create `app/services/<name>.py` with core logic as a plain function
2. Add `@app.get("/<name>")` REST route in `main.py`
3. Add `@mcp.tool()` in `main.py` calling the same service function
4. Update README.md

## Auth

Single `APIKeyMiddleware` (Starlette `BaseHTTPMiddleware`) on the FastAPI app covers both REST and MCP endpoints. `/health` is in `_public` set and always bypasses auth. Controlled by `API_KEY` env var — disabled when empty.

## Running locally

```bash
pip install -r requirements.txt
python3 main.py
# → http://localhost:8000
```

## Running with Docker

```bash
cp .env.example .env
docker compose up
```

## Key dependencies

| Package | Why |
|---------|-----|
| `fastapi` | REST API framework (ASGI) |
| `mcp[cli]` | FastMCP server + MCP protocol |
| `uvicorn` | ASGI server for both FastAPI and MCP |
| `yt-dlp` | YouTube metadata (title, channel, views, etc.) |
| `youtube-transcript-api` | Transcript fetch — no API key needed |

## CI

GitHub Actions (`.github/workflows/docker.yml`) builds and pushes to GHCR on every push to `main`. Requires `docker/setup-buildx-action` step — without it, GHA cache export fails with the default Docker driver.

## Things to watch out for

- `yt-dlp` version must exist on PyPI — version numbers follow date format (`YYYY.MM.DD`), not all dates have releases
- MCP endpoint is at `/mcp` (FastMCP default for streamable HTTP)
- The `@mcp.tool()` function name becomes the tool name visible to the AI agent — keep it descriptive
- `app.mount("/mcp", ...)` must come **after** all `@app.get()` route definitions
