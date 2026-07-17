# Model Hub Provider Scaffold

This directory is a **source scaffold** for a future custom Dify model provider
plugin that fronts your own third-party model hub / proxy.

It does **not** register a live plugin package inside Dify by itself. Instead,
it captures the parts we want the real plugin to implement:

- provider identity, label, icon, description
- provider credential form
- remote model catalog contract
- credential validation contract
- minimal LLM invocation payload shape

## Intended provider behavior

The target provider should appear in Dify as its own provider, not as OpenAI.

### Provider ID

`your-company/model-hub/proxy`

### Supported configuration methods

- `predefined-model`
- `customizable-model`

This combination gives us:

- remote catalog discovery from the proxy at runtime while surfacing fetched models as predefined entries
- manual model fallback when the proxy does not expose every model

## Required proxy endpoints

### 1. Credential validation

```http
GET /provider/ping
Authorization: Bearer <proxy_api_key>
```

Expected success response:

```json
{
  "ok": true,
  "provider": "model-hub",
  "message": "pong"
}
```

### 2. Model catalog

```http
GET /provider/models
Authorization: Bearer <proxy_api_key>
```

Expected response:

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

## Files

- `provider_schema.py`
  - Dify-facing provider declaration scaffold
- `catalog_client.py`
  - Proxy ping / model list client and normalization rules
- `runtime_adapter.py`
  - Minimal payload-shaping helper for future LLM runtime wiring
- `entities.py`
  - typed response / credential shapes

## Next integration step

Wire this scaffold into a real external plugin package that can be installed by
Dify's plugin daemon. The real package must implement:

1. provider declaration export
2. provider credential validation
3. remote model list fetch
4. llm runtime invocation
5. optional embedding / rerank / tts / speech2text invocation
