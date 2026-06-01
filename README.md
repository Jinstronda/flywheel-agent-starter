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
    # ctx.mcp.call(name, args)          search_apis/api_doc/call_api/run_code/complete_task
    # ctx.run_code(code)      run python with `apis` in scope (loops/pagination/bulk); graded + local
    # ctx.retrieve(query)     your RAG hook (wire it to your retriever over the API docs)
    # ctx.memory.read()/.write(k, v)    persisted across tasks (wiped between tasks on the off-arm)
    # ctx.reflect(note)       record a self-correction
    # ctx.execute(code)       alias of ctx.run_code
    ...
```

We run this exact function to grade you. Build whatever you want inside it.

The harness runs your repo (`flywheel.json` declares the entrypoint, default `python main.py`)
once per task in an isolated sandbox with the environment wired up:

| env | what |
|---|---|
| `FLYWHEEL_PROXY_URL` / `FLYWHEEL_PROXY_TOKEN` | the fixed model, OpenAI-compatible, metered |
| `FLYWHEEL_MCP_URL` | the AppWorld MCP surface: search_apis, api_doc, call_api, run_code, complete_task |
| `FLYWHEEL_MEMORY_URL` | the memory service (POST `/read`, `/write {key,value}`) |
| `FLYWHEEL_TASK_ID` | current task id |
| `FLYWHEEL_TASK_INSTRUCTION` | the task to solve |
| `FLYWHEEL_MAX_STEPS` | per-task step cap |

`Ctx.from_env()` reads these. The trusted model, memory, and MCP **trace events the gate reads
come from those gateways**, not from files you write, so act through `ctx` (not hardcoded HTTP).
Act through `ctx` (not hardcoded HTTP). `ctx.run_code` and `ctx.mcp.call` both work identically
locally and graded, so the agent you tune locally is the agent we grade.

## Quickstart

```bash
# 1. set up (see SETUP.md): a Python 3.11 venv with AppWorld + its data, and your key
cp .env.example .env && $EDITOR .env        # put your FLYWHEEL_KEY in
set -a; source .env; set +a                 # export it for the tools below

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
- **Honest traces.** Genuine retrieval, tool calls, memory reads/writes, and error recovery through the trusted gateways.

Grading is AppWorld's own deterministic state oracle. No LLM judges you. The held-out split is one you never see.

## Docs

- `docs/appworld.md` — how AppWorld works: the apps, the `apis` interface, discovering APIs, **the login flow** (the #1 thing that trips people up), completing a task, the oracle.
- `docs/proxy.md` — the model proxy: the OpenAI-compatible surface, function-calling, structured output, your budget.
- `docs/grading.md` — exactly how you're scored, and how to self-test locally.
- `SETUP.md` — install AppWorld + its data + your venv.
