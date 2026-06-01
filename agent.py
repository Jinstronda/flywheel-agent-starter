"""Your agent. This is the only file you have to write.

The harness calls solve(ctx) once per task. A naive single-shot agent on this model scores ~0.
To clear the baseline you need all four capabilities to be REAL, because the grader checks the
trace and runs you with memory on AND wiped:

  - RAG        retrieve the right API docs per task (you can't fit 457 in context)
  - tools      act through the MCP tool surface (ctx.mcp), not hardcoded calls
  - memory     carry what you learn across tasks; the on/off gap is graded
  - self-loop  read tool errors, reflect, retry the fixed call

Act through ctx.mcp.call(name, args): on the graded run that's the MCP gateway, and it is what
the gate counts. (Locally, ctx.execute(code) runs the same AppWorld in-process for fast
iteration -- but write your solver against ctx.mcp so it runs identically when graded.)

Read docs/appworld.md first (especially THE LOGIN FLOW) and docs/proxy.md. Then build here.

ctx surface (see flywheel/ and the README):
  ctx.instruction          the task
  ctx.model(messages, tools=None, response_format=None)   the fixed model via the proxy
  ctx.mcp.call(name, args) the tool surface: search_apis, api_doc, call_api, run_code, complete_task
  ctx.retrieve(query)      your RAG hook (wire flywheel/ctx.py:retrieve to a real retriever)
  ctx.memory.read() / .write(k, v)   persisted across tasks (wiped between tasks on the off-arm)
  ctx.reflect(note)        record a self-correction
  ctx.trace(type, **kw)    append a JSONL event
"""


def solve(ctx):
    instruction = ctx.instruction

    # 1) RECALL  -- pull procedures/recipes you stored on earlier tasks. Some tasks are only
    #    solvable by recalling a fact a previous task revealed. Memory carries on the on-arm
    #    and is wiped on the off-arm, so what you store has to generalize.
    #    mem = ctx.memory.read()

    # 2) RETRIEVE  -- get the API docs relevant to THIS task. Dump them first with
    #    `python tools/dump_api_docs.py`, index them (your retriever, your call), and wire
    #    flywheel/ctx.py:retrieve to it. 457 APIs do not fit in context.
    #    docs = ctx.retrieve(instruction)

    # 3) PLAN  -- the fixed model (gemini-3-flash-preview). It's weak, so give it the retrieved
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
    #    of the stream. This is what makes the memory gap real.
    #    ctx.memory.write("spotify_login", "...")

    raise NotImplementedError("implement your agent here -- this is the hiring signal")
