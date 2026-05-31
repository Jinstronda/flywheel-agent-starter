"""Your agent. This is the only file you have to write.

The harness calls solve(ctx) once per task. A naive single-shot agent on this model scores
~0. To clear the baseline you need all four capabilities to be REAL, because the grader checks
the trace and runs you with memory on AND wiped:

  - RAG        retrieve the right API docs per task (you can't fit 457 in context)
  - tools      act through AppWorld's `apis` object via ctx.execute(code)
  - memory     carry what you learn across tasks; the on/off gap is graded
  - self-loop  read tracebacks, reflect, retry the fixed call

Read docs/appworld.md first (especially THE LOGIN FLOW) and docs/proxy.md. Then build here.

ctx surface (see flywheel/ and the README):
  ctx.instruction          the task
  ctx.model(messages, tools=None, response_format=None)   the fixed model via the proxy
  ctx.execute(code)        run Python against AppWorld; returns stdout/result/traceback
  ctx.memory.read() / .write(k, v)   persisted across tasks (wiped between tasks on the off-arm)
  ctx.retrieve(query)      your RAG hook (wire flywheel/ctx.py:retrieve to a real retriever)
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

    # 3) PLAN  -- the fixed model (gemini-3.1-flash-lite). It's weak, so give it the retrieved
    #    docs, the supervisor identity, and a tight protocol. Function-calling and structured
    #    output both work through the proxy (docs/proxy.md).
    #    plan = ctx.model([{"role": "system", "content": ...}, {"role": "user", "content": instruction}])

    # 4) ACT via the apis object. Each ctx.execute(code) runs one Python snippet; state
    #    (logins, data) persists across calls within a task. THE LOGIN FLOW (docs/appworld.md)
    #    is the #1 gotcha:
    #       pw = {p['account_name']: p['password'] for p in apis.supervisor.show_account_passwords()}
    #       me = apis.supervisor.show_profile()
    #       tok = apis.spotify.login(username=me['email'], password=pw['spotify'])['access_token']
    #    then pass access_token=tok to authenticated calls. List APIs are paginated.
    #    out = ctx.execute("...your code...")

    # 5) SELF-CORRECT  -- when execute returns a Traceback, read it, fix the exact cause
    #    (wrong api name -> ctx.retrieve / show_api_doc; missing access_token -> add it; wrong
    #    field -> print the dict's keys), ctx.reflect(note), and retry. Don't repeat a failing call.
    #    if "Traceback" in out: ctx.reflect("..."); out = ctx.execute("...fixed...")

    # 6) FINISH  -- you MUST call apis.supervisor.complete_task(answer=...) (answer only for
    #    question tasks; no arg for action tasks). The oracle ONLY sees submitted answers, so a
    #    right answer printed to stdout but never submitted scores 0.
    #    ctx.execute("apis.supervisor.complete_task(answer=...)")

    # 7) REMEMBER  -- persist what worked (a login recipe, a solved-task procedure) for the rest
    #    of the stream. This is what makes the memory gap real.
    #    ctx.memory.write("spotify_login", "...")

    raise NotImplementedError("implement your agent here -- this is the hiring signal")
