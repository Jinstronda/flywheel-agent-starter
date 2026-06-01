# How you're graded

Grading is AppWorld's own deterministic state oracle (`world.evaluate()['success']`). No LLM
judges you. The held-out split is one you never see. You get **one continuous score in `[0,1]`**
and you are **ranked against the other candidates** on a leaderboard. The hire is top of the
board, not "cleared a bar".

## 1. The score

```
score = reliability-weighted solve rate − collateral penalty
```

Each hard task is run **k frozen times** and contributes `passes/k`, so solving a task 2 of 3
times is 0.67. One number that rewards both **solving** the hard task and doing it **reliably**
(pass^k). Same model for everyone, so the whole number is your engineering: discovery, the login
flow, pagination, self-correction, bulk work via `run_code`.

For context, the leaderboard shows the **naive baseline** (a generic loop on your same model —
one model ping, one retrieval, submit, no memory, no recovery) and your **rank**. That baseline
scores about **0.0** on the brutal pool. A SOTA agent lands near **0.5**. Your number is where you
land between them; your rank is where you land against the others.

The tasks are hard on purpose (multi-write, aggregation): a SOTA agent clears about half, a naive
one almost none.

## 2. Reliability is baked into the score

We re-run held-out tasks **k times** with memory frozen, and the task's contribution is `passes/k`.
A solution that passes once out of three contributes 0.33, not a clean pass. Make the loop
deterministic where you can (constrain the model with `response_format`, verify before
`complete_task`, retry on traceback) so every one of the k runs lands.

## 3. Memory (yours, required, and it raises your score)

Memory is required, and it's **yours**. `FLYWHEEL_MEMORY_DIR` is a persistent directory that
survives across the whole task stream; we never provide a memory service and never wipe it. Put
your own store there — the starter ships a JSON store, but bundle a vector index, sqlite, a
Voyager-style skill library, or gbrain (Postgres + an MCP server in your image) if you want. A
real memory reuses what generalizes — login recipes, solved-task procedures, API docs you already
paid to discover — so later tasks cost less and pass more. That reuse raises your solve rate, and
so your score. A `memory.json` nobody reads gives none. You describe it in your writeup and defend
it in the call.

Self-check it locally — run with memory persisting, then with it wiped, and watch your own solve
rate:

```bash
python run_local.py --n 8                 # memory carries across tasks
python run_local.py --n 8 --memory-off    # memory wiped between tasks (sanity check)
```

If the two solve rates are equal, your memory isn't doing anything yet. Real AppWorld dev tasks
are independent, so design memory that actually changes a later task's outcome.

## 4. No collateral, honest traces

The oracle also reports `collateral_damage`: state you mutated that the task didn't ask for. Any
collateral is penalized straight off your score, so the multi-write tasks reward precision, not
spraying writes.

The score reads trusted events emitted by the model and MCP gateways. Candidate-written JSONL
traces are useful for your own debugging, but they are not part of the score. Your graded run must
show real `retrieval`, tool calls (`call_api`/`run_code`), and recovery from a failed step through
the gateways. Decorative calls that don't affect the outcome don't help and read as noise.

## Up to 3 graded trials, with per-trial feedback

You get **up to 3 graded trials**, and **after each one** full per-task feedback: your agent's
stdout/stderr, the gateway trace (the tool calls + `run_code` snippets + the errors they threw),
and the oracle's pass/fail with the exact failing check, plus timing and tokens. That feedback is
there so you **improve between attempts**. Practice is **unlimited** and returns the same feedback
— read why each task failed and fix it. The API response and the SPA both carry these per-task
logs.

## Submit

You submit your **full system**, not just a repo: the tools, the MCP servers, the RAG, the
memory/database, the self-improving loop, and your key prompts. All of it is read in review.

```bash
curl https://homodeus-flywheel.fly.dev/api/submit \
  -H "content-type: application/json" \
  -d '{"token":"'$FLYWHEEL_KEY'",
       "repo":"https://github.com/you/your-agent",
       "writeup":"what you built and why (a few real paragraphs)",
       "systems":{
         "tools":"the tool surface your model can call",
         "mcp":"the MCP server(s) you stood up",
         "rag":"your retriever over the API docs (index, embedder, top-k)",
         "memory":"the store and what crosses tasks",
         "self_loop":"verify / reflect / retry",
         "prompts":"your key prompts"
       }}'
```

The `systems` object is mandatory and every field is read. Be concrete.
