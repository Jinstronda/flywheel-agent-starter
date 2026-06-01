"""Your agent. This is the only file you have to write.

OPEN CONTRACT: only the MODEL (gemini-3-flash-preview, via the proxy -- the only LLM you may call)
and the WORLD (AppWorld via the MCP gateway + oracle) are fixed. EVERYTHING else is yours to build
and BUNDLE in this repo: your memory (gbrain, a vector DB, sqlite, a skill library), your RAG, your
MCP servers, any framework. It all runs locally in your container; the sandbox has no internet, so
package your stack to run offline. This SDK is a starting surface, not a cage -- replace it.

The harness calls solve(ctx) once per task. Your score is a continuous number in [0,1] --
reliability-weighted solve rate minus a collateral penalty -- and you are RANKED against the other
candidates. A naive loop scores ~0.0; a SOTA agent lands ~0.5 on the brutal pool. Every capability
you build moves your number up:

  - RAG        retrieve the right API docs per task (you can't fit 457 in context)
  - tools      act through the MCP tool surface (ctx.mcp), not hardcoded calls
  - run_code   loop/paginate over `apis` in one turn -- the hard tasks are bulk, multi-write
  - memory     YOUR store under FLYWHEEL_MEMORY_DIR, carried across tasks; reuse raises your score (REQUIRED)
  - self-loop  read tool errors, reflect, retry the fixed call

The tasks are HARD on purpose (multi-write, aggregation); even a SOTA agent clears about half on a
single attempt. Each hard task is run k frozen times and contributes passes/k, so reliability is
in the score (pass^k). The brutal ones need schema inspection, constraint parsing, and multi-app
fact-finding, not a generic ReAct loop. You get up to 3 graded trials, each followed by per-task
feedback (your logs, the tool calls + errors, the oracle's pass/fail + why), so you improve between
attempts; practice is unlimited. FLYWHEEL_MAX_STEPS is 50, so a bulk task has room -- but burning a
turn per item still runs out; that's what run_code is for.

Act through ctx.mcp.call(name, args): on the graded run that's the MCP gateway, and it is what
the gate counts. (Locally, ctx.run_code / ctx.execute run the same AppWorld in-process for fast
iteration -- but write your solver against ctx.mcp so it runs identically when graded.)

Read docs/appworld.md first (especially THE LOGIN FLOW) and docs/proxy.md. Then build here.

ctx surface (see flywheel/ and the README):
  ctx.instruction          the task
  ctx.model(messages, tools=None, response_format=None)   the fixed model via the proxy
  ctx.mcp.call(name, args) the surface: search_apis, api_doc, call_api, run_code, complete_task
  ctx.retrieve(query)      your RAG hook (wire flywheel/ctx.py:retrieve to a real retriever)
  ctx.run_code(code)       python with `apis` in scope: loops, pagination, bulk writes
  ctx.memory.read() / .write(k, v)   persisted across the task stream; reuse raises your score
  ctx.reflect(note)        record a self-correction
  ctx.trace(type, **kw)    append a JSONL event
"""


def solve(ctx):
    instruction = ctx.instruction

    # 1) RECALL  -- pull procedures/recipes you stored on earlier tasks. Some tasks are only
    #    solvable by recalling a fact a previous task revealed. Memory persists across the task
    #    stream, so what you store has to generalize; reuse raises your solve rate and your score.
    #    mem = ctx.memory.read()

    # 2) RETRIEVE  -- get the API docs relevant to THIS task. Dump them first with
    #    `python tools/dump_api_docs.py`, index them (your retriever, your call), and wire
    #    flywheel/ctx.py:retrieve to it. 457 APIs do not fit in context.
    #    docs = ctx.retrieve(instruction)

    # 3) PLAN  -- the fixed model (gemini-3-flash-preview). It's small, so give it the retrieved
    #    docs, the supervisor identity, and a tight protocol. Function-calling and structured
    #    output both work through the proxy (docs/proxy.md).
    #    plan = ctx.model([{"role": "system", "content": ...}, {"role": "user", "content": instruction}])

    # 4) ACT through ctx.mcp.call. State (logins, data) persists
    #    across calls within a task. THE LOGIN FLOW (docs/appworld.md) is the #1 gotcha:
    #       pw = {p['account_name']: p['password']
    #             for p in ctx.mcp.call("call_api", {"app": "supervisor",
    #                                                "api": "show_account_passwords",
    #                                                "arguments": {}})["result"]}
    #       me = ctx.mcp.call("call_api", {"app": "supervisor", "api": "show_profile",
    #                                      "arguments": {}})["result"]
    #       tok = ctx.mcp.call("call_api", {"app": "spotify", "api": "login",
    #                                      "arguments": {"username": me["email"],
    #                                                    "password": pw["spotify"]}})["result"]["access_token"]
    #    then pass access_token=tok to authenticated calls. List APIs are paginated.
    #    r = ctx.mcp.call("call_api", {"app": "spotify", "api": "show_song_library",
    #                                  "arguments": {"access_token": tok, "page_index": 0}})

    # 4b) BULK with run_code. call_api is one call; the hard tasks are aggregation/multi-write,
    #    so do the loop server-side in ONE turn instead of N. `apis` is in scope; print a result.
    #    out = ctx.mcp.call("run_code", {"code":
    #        "ids, page = [], 0\n"
    #        "while True:\n"
    #        "    rows = apis.spotify.show_song_library(access_token=tok, page_index=page)\n"
    #        "    if not rows: break\n"
    #        "    ids += [r['song_id'] for r in rows]; page += 1\n"
    #        "print(len(set(ids)))"})
    #    (state from earlier call_api logins persists within the task, so `tok` is usable here.)

    # 5) SELF-CORRECT  -- when a call returns an error, read it, fix the exact cause (wrong tool
    #    name -> ctx.retrieve; missing access_token -> add it; wrong field -> inspect the result),
    #    ctx.reflect(note), and retry through ctx.mcp. Don't repeat a failing call. The grade gate
    #    trusts gateway events, so the recovery has to happen through the real tools.
    #    if r and r.get("error"): ctx.reflect("..."); r = ctx.mcp.call("call_api", fixed)

    # 6) FINISH  -- you MUST submit through complete_task. The oracle ONLY sees submitted
    #    answers, so a right answer you never submit scores 0.
    #    ctx.mcp.call("complete_task", {"answer": ...}) for question tasks
    #    ctx.mcp.call("complete_task", {}) for action tasks

    # 7) REMEMBER  -- persist what worked (a login recipe, a solved-task procedure) for the rest
    #    of the stream. ctx.memory is a starter JSON store under FLYWHEEL_MEMORY_DIR; bundle your
    #    own (a vector DB / sqlite / gbrain) in that dir. Reuse on later tasks raises your score.
    #    ctx.memory.write("spotify_login", "...")

    raise NotImplementedError("implement your agent here -- this is the hiring signal")
