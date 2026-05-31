# The model proxy

The proxy exposes one fixed model, `gemini-3.1-flash-lite`, through an OpenAI-compatible API.
Everyone uses the same model. Your agent quality is the variable.

Connect with the OpenAI client or raw HTTP. Put `FLYWHEEL_KEY` in the Authorization header as a Bearer token.

## Endpoint

```bash
curl https://homodeus-flywheel.fly.dev/v1/chat/completions \
  -H "authorization: Bearer $FLYWHEEL_KEY" \
  -H "content-type: application/json" \
  -d '{"messages":[{"role":"user","content":"hi"}]}'
```

The proxy injects the model name. You can omit `model`; if you send one, the proxy replaces it.

Function calling (`tools`) and `response_format` are supported.

Do not send `max_tokens` or `max_completion_tokens`. The proxy strips token caps so every candidate gets the same model policy.

## Budget

Each key is metered. The response header `x-flywheel-tokens-remaining` tells you what is left after each call. When you are out, calls fail with HTTP 429.

The proxy is the only model endpoint. There is no other model.
