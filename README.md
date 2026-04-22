# ai-toolbox

A self-hosted toolbox for AI agents. Exposes tools as both a REST API and MCP server — on a single port.

## Architecture

One service, one port (8000):

| Endpoint | Protocol | Use case |
|----------|----------|----------|
| `/youtube_transcript` | REST HTTP | Direct HTTP calls, n8n HTTP node, testing |
| `/mcp` | MCP (Streamable HTTP) | Claude Desktop, n8n MCP node, any MCP client |
| `/health` | HTTP | Docker healthcheck (no auth required) |

## Running

```bash
cp .env.example .env       # optionally set API_KEY
docker compose up
```

## Authentication

Set `API_KEY` in `.env`. When set, all requests (except `/health`) must include:

```
X-API-Key: your-key-here
```

If `API_KEY` is empty or unset, auth is disabled.

---

## REST API

### `GET /youtube_transcript`

Fetch YouTube video transcript and metadata.

**Parameters:**

| Param | Required | Default | Description |
|-------|----------|---------|-------------|
| `id`  | yes | — | YouTube video ID |
| `lang` | no | `pl,en` | Comma-separated language priority |

**Example:**

```bash
curl "http://localhost:8000/youtube_transcript?id=dQw4w9WgXcQ&lang=en"
# with auth:
curl -H "X-API-Key: your-key" "http://localhost:8000/youtube_transcript?id=dQw4w9WgXcQ"
```

**Response:**

```json
{
  "title": "...",
  "channel": "...",
  "published": "20240101",
  "duration": 212,
  "tags": ["..."],
  "description": "...",
  "views": 1234567,
  "thumbnail": "https://...",
  "transcript": "full transcript text..."
}
```

---

## MCP Server

**Endpoint:** `http://localhost:8000/mcp`

### Available tools

#### `youtube_transcript`

```
video_id: str        — YouTube video ID
lang: str = "pl,en"  — comma-separated language codes, priority order
```

### Connecting Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-toolbox": {
      "type": "http",
      "url": "http://localhost:8000/mcp",
      "headers": {
        "X-API-Key": "your-key-here"
      }
    }
  }
}
```

### Connecting from n8n (MCP node)

Use the **MCP Client** node with:
- Transport: `Streamable HTTP`
- URL: `http://<host>:8000/mcp`
- Header: `X-API-Key: your-key`

---

## Adding a new tool

1. Add shared logic to `app/services/<name>.py`
2. Add REST route in `main.py` (`@app.get(...)`)
3. Add MCP tool in `main.py` (`@mcp.tool()`)
4. Update this README

## CI/CD

GitHub Actions builds and pushes the Docker image to GHCR on every push to `main`:

```
ghcr.io/michaljonik/ai-toolbox:latest
ghcr.io/michaljonik/ai-toolbox:sha-<commit>
```
