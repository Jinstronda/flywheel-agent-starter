# The model proxy

One fixed model, `gemini-3.1-flash-lite`, behind an OpenAI-compatible, metered proxy at
`https://homodeus-flywheel.fly.dev/v1`. Everyone gets the same model — the only thing that
separates you from the baseline is how you engineer the loop. The model and temperature are
pinned server-side; you can't swap them, and that's the point.

## Endpoint + auth

`POST /v1/chat/completions`, OpenAI request/response shape. Your key goes in the header:

```bash
curl https://homodeus-flywheel.fly.dev/v1/chat/completions \
  -H "authorization: Bearer $FLYWHEEL_KEY" \
  -H "content-type: application/json" \
  -d '{"messages":[{"role":"user","content":"hi"}]}'
```

In the SDK, `ctx.model(messages, tools=None, response_format=None)` does this and returns the
raw response dict. Point any OpenAI client at the same base URL with your key if you'd rather.

## What works

- **Function-calling** — pass `tools` (OpenAI tool schema) and read `tool_calls` back. Use this
  to give the model a real tool surface instead of hardcoded calls.
- **Structured output** — pass `response_format` (e.g. `{"type":"json_object"}` or a JSON
  schema). The weak model is far more reliable when you constrain its output shape.
- Both are supported by the proxy and forwarded to the model.

```python
data = ctx.model(
    [{"role": "user", "content": "extract the song title"}],
    response_format={"type": "json_object"},
)
text = (data["choices"][0]["message"]["content"])
```

## Don't send

- `model` — pinned server-side (ignored / overridden).
- `max_tokens` / `max_completion_tokens` — stripped server-side; let the model decide length.

## Budget

Your key is **metered**. Every response carries `x-flywheel-tokens-remaining` — what's left on
your key. The SDK surfaces it: `flywheel.proxy.chat(...)` returns `(data, remaining)`, and
`ctx.model` traces a `budget` event. Spend it on the loop that matters (discovery, self-
correction), not on re-printing full API descriptions every turn. A 429 means you're out.

## Failure shape

On a hard error the SDK returns `{"error": "..."}` instead of a normal response; check for it.
The model is weak: expect malformed code, wrong API names, and skipped logins. Your job is the
loop that recovers — retrieve the doc, reflect, retry — not a single perfect prompt.
