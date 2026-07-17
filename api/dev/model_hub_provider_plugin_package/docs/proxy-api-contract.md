# Proxy API Contract

This plugin package expects the upstream model hub / proxy to expose two
endpoints.

## 1. Credential validation

```http
GET /provider/ping
Authorization: Bearer <proxy_api_key>
```

Success response:

```json
{
  "ok": true,
  "provider": "model-hub",
  "message": "pong"
}
```

## 2. Model catalog

```http
GET /provider/models
Authorization: Bearer <proxy_api_key>
```

Success response:

```json
{
  "models": [
    {
      "id": "gpt-5.5",
      "type": "llm",
      "label": "GPT-5.5",
      "context_size": 128000,
      "features": ["stream-tool-call", "structured-output"],
      "mode": "chat"
    },
    {
      "id": "claude-3-5-sonnet",
      "type": "llm",
      "label": "Claude 3.5 Sonnet",
      "mode": "chat"
    },
    {
      "id": "text-embedding-3-large",
      "type": "text-embedding",
      "label": "Text Embedding 3 Large"
    }
  ]
}
```
