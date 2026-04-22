# ai-toolbox

A self-hosted API and MCP server providing tools for AI agents. Currently exposes one tool: fetching YouTube video transcripts and metadata.

## Architecture

Two services, one Docker image:

| Service | Port | Protocol | Use case |
|---------|------|----------|----------|
| `api`   | 5000 | REST HTTP | Direct HTTP calls, n8n HTTP node, testing |
| `mcp`   | 8000 | MCP (Streamable HTTP) | Claude Desktop, n8n MCP node, any MCP client |

Both share the same underlying logic (`app/services/`).

## Running locally

```bash
cp .env.example .env       # optionally set API_KEY
docker compose up --build
```

## Authentication

Set `API_KEY` in `.env`. When set, all requests must include:

```
X-API-Key: your-key-here
```

If `API_KEY` is empty or unset, auth is disabled.

---

## REST API

### `GET /trans-yt`

Fetch YouTube video transcript and metadata.

**Parameters:**

| Param | Required | Default | Description |
|-------|----------|---------|-------------|
| `id`  | yes | — | YouTube video ID |
| `lang` | no | `pl,en` | Comma-separated language priority |

**Example:**

```bash
curl "http://localhost:5000/trans-yt?id=dQw4w9WgXcQ&lang=en"
# with auth:
curl -H "X-API-Key: your-key" "http://localhost:5000/trans-yt?id=dQw4w9WgXcQ"
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

### `GET /health`

Returns `{"status": "ok"}`. Used by Docker healthcheck.

---

## MCP Server

The MCP server runs on port 8000 using the Streamable HTTP transport.

**MCP endpoint:** `http://localhost:8000/mcp`

### Available tools

#### `trans_yt`

```
video_id: str       — YouTube video ID
lang: str = "pl,en" — comma-separated language codes, priority order
```

Returns the same fields as the REST endpoint.

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

### Connecting from a remote machine

The MCP server accepts HTTP connections, so it works across machines. Point the client at your server's IP/hostname instead of `localhost`.

---

## Adding a new tool

1. Add shared logic to `app/services/<name>.py`
2. Add Flask route in `app/routes/<name>.py` and register it in `app/__init__.py`
3. Add MCP tool in `mcp_server.py` using `@mcp.tool()`
4. Update this README

## CI/CD

GitHub Actions builds and pushes the Docker image to GHCR on every push to `main`:

```
ghcr.io/michaljonik/ai-toolbox:latest
ghcr.io/michaljonik/ai-toolbox:sha-<commit>
```
