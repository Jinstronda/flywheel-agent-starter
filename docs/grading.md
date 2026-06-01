# How you're graded

Grading is AppWorld's own deterministic state oracle (`world.evaluate()['success']`). No LLM
judges you. The held-out split is one you never see. Four things decide it.

## 1. Lift over the baseline

Your grade is `your_TGC - baseline_TGC`. The baseline is a naive agent on your same model — one
model ping, one retrieval, submit, no memory, no self-correction, no tool recovery — that **we
already ran once** and stored. You never touch it. You run **once**, and everything you build
(RAG, `run_code` loops, memory, retry) shows up as lift above that floor. Same model for everyone,
so the lift is pure engineering: discovery, the login flow, pagination, self-correction, bulk
work via `run_code`.

You have to clear the baseline **by a margin**. The tasks are hard on purpose (multi-write,
aggregation): a SOTA agent clears about half, a naive one almost none.

## 2. Memory (required, and it lifts your score)

Memory is required. A real memory persists across the task stream and reuses what generalizes —
login recipes, solved-task procedures, API docs you already paid to discover — so later tasks
cost less and pass more. That reuse is lift. A `memory.json` nobody reads gives none. It is not a
separate pass/fail gate, but you describe it in your writeup and defend it in the call, and a
strong one moves your number.

Self-check it locally — run with memory persisting, then with it wiped, and watch your own TGC:

```bash
python run_local.py --n 8                 # memory carries across tasks
python run_local.py --n 8 --memory-off    # memory wiped between tasks (sanity check)
```

If the two TGCs are equal, your memory isn't doing anything yet. Real AppWorld dev tasks are
independent, so design memory that actually changes a later task's outcome.

## 3. Reliability

We re-run held-out tasks **k times** with memory frozen; all k must pass. A solution that passes
once out of three is not a solution. Make the loop deterministic where you can (constrain the
model with `response_format`, verify before `complete_task`, retry on traceback).

## 4. No collateral, honest traces

The oracle also reports `collateral_damage`: state you mutated that the task didn't ask for. Any
collateral fails the run, so the multi-write tasks reward precision, not spraying writes.

The pass gate reads trusted events emitted by the model, MCP, and memory gateways. Candidate-written
JSONL traces are useful for your own debugging, but they are not accepted as proof. Your graded run
must show real `retrieval`, tool calls (`call_api`/`run_code`), `memory_read`/`memory_write`, and
recovery from a failed step through the gateways. Decorative calls that don't affect the outcome
don't help and read as noise.

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
