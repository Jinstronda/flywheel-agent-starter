"""FLYWHEEL agent SDK. The harness builds a Ctx and calls solve(ctx) once per task.

You only write agent.py. These modules give you the surface the README promises and the
trace the grader reads:

  ctx.instruction          the task to solve
  ctx.model(messages)      the fixed model (gemini-3.1-flash-lite) through the metered proxy
  ctx.execute(code)        run Python against AppWorld (the `apis` object); returns output
  ctx.memory.read/write    persisted across tasks (wiped between tasks on the off-arm)
  ctx.retrieve(query)      your RAG hook over the API docs (wire it to your retriever)
  ctx.reflect(note)        record a self-correction
  ctx.trace(type, **kw)    append a JSONL event

Everything flows through here, so the trace is a faithful record of what your agent did.
"""
from flywheel.ctx import Ctx

__all__ = ["Ctx"]
