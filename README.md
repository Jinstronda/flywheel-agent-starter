# FLYWHEEL — agent starter

This is everything you need to build your agent for the HomoDeus founding-engineer challenge. Clone it, read it, build in `agent.py`, test locally against the real environment, and submit.

## The challenge

You build one agent that works through a stream of real tasks in **AppWorld** (9 simulated apps — Spotify, Venmo, Amazon, Gmail, Phone, Files… — exposed as **457 APIs**) and **gets better as it goes**. It runs on a **fixed weak model**, `gemini-3.1-flash-lite`, behind our metered, OpenAI-compatible proxy. The model is the same for everyone, so the only thing that separates you from the baseline is how well you engineer the loop.

A naive agent on this model scores ~0 on real tasks. A properly engineered one clears it. You have to be the second kind.

## What you must use

This is non-negotiable, and it's what we grade for:

1. **MCP tools** — act through a tool surface, not hardcoded calls.
2. **RAG** — you cannot fit 457 API docs in context. Retrieve the right ones for each task. (Your data, your retriever — see `tools/dump_api_docs.py` to get the docs.)
3. **Any tools at your disposal** — any framework, function-calling, structured output, vector DB, whatever. Go SOTA. The proxy is OpenAI-compatible.
4. **Self-learning / self-improving loops** — memory that **compounds across tasks**, plus self-correction (verify, reflect, retry). Memory must be real: we run your agent with memory **on** and with memory **wiped between tasks**, and the gap is part of your grade. A decorative `memory.json` nobody reads fails.

## The contract

Your agent is one function in `agent.py`:

```python
def solve(ctx):
    # ctx.instruction        the task to solve
    # ctx.model(messages, tools=None)   the fixed model, through the metered proxy
    # ctx.execute(code)       run Python against AppWorld (the `apis` object); returns output/tracebacks
    # ctx.memory.read()/.write(k, v)    persisted across tasks (wiped between tasks on the off-arm)
    # ctx.retrieve(query)     your RAG hook (wire it to your retriever over the API docs)
    # ctx.reflect(note)       record a self-correction
    ...
```

We run this exact function to grade you. Build whatever you want inside it.

## Quickstart

```bash
# 1. set up (see SETUP.md): a Python 3.11 venv with AppWorld + its data, and your key
cp .env.example .env && $EDITOR .env        # put your FLYWHEEL_KEY in

# 2. see the environment work end-to-end (login + docs + complete a task)
python examples/quickstart.py

# 3. get the API docs to RAG over
python tools/dump_api_docs.py               # writes ./api_docs_dump/

# 4. build your agent in agent.py, then test it on real dev tasks
python run_local.py --n 5                   # runs YOUR solve(ctx), grades on the real oracle

# 5. submit (below)
```

## Connect to the model

OpenAI-compatible. Your key goes in the header. Use any client/framework.

```bash
curl https://homodeus-flywheel.fly.dev/v1/chat/completions \
  -H "authorization: Bearer $FLYWHEEL_KEY" \
  -H "content-type: application/json" \
  -d '{"messages":[{"role":"user","content":"hi"}],"tools":[...]}'
```

Function-calling and `response_format` (structured output) both work. Budget is metered per key; the response header `x-flywheel-tokens-remaining` tells you what's left. See `docs/proxy.md`.

## Submit

When you're ready, submit your repo and your full design:

```bash
curl https://homodeus-flywheel.fly.dev/api/submit \
  -H "content-type: application/json" \
  -d '{"token":"'$FLYWHEEL_KEY'",
       "repo":"https://github.com/you/your-agent",
       "writeup":"what you built and why (a few real paragraphs)",
       "systems":{"tools":"…","mcp":"…","rag":"…","memory":"…","self_loop":"…","prompts":"…"}}'
```

You submit your **full system**, not just a repo: the tools your model can call, the MCP servers, the RAG, the memory/database, the self-improving loop, and your key prompts. All of it is read in review.

## How you're graded

- **Beat the baseline.** A naive agent on your same model sets the floor. Clear it by a margin.
- **A real memory gap.** memory-on must pull ahead of memory-wiped.
- **Reliability.** We re-run held-out tasks k times — all must pass.
- **Honest traces.** Genuine retrieval, tool calls, memory reads/writes, and retries.

Grading is AppWorld's own deterministic state oracle. No LLM judges you. The held-out split is one you never see.

## Docs

- `docs/appworld.md` — how AppWorld works: the apps, the `apis` interface, discovering APIs, **the login flow** (the #1 thing that trips people up), completing a task, the oracle.
- `docs/proxy.md` — the model proxy: the OpenAI-compatible surface, function-calling, structured output, your budget.
- `docs/grading.md` — exactly how you're scored, and how to self-test locally.
- `SETUP.md` — install AppWorld + its data + your venv.
