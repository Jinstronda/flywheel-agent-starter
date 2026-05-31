"""FLYWHEEL agent SDK. The harness builds a Ctx and calls solve(ctx) once per task.

You only write agent.py. These modules give you the surface the README promises and the
trace the grader reads. One surface, two backends (graded gateways / local AppWorld):

  ctx.instruction          the task to solve
  ctx.model(messages)      the fixed model (gemini-3.1-flash-lite) through the metered proxy
  ctx.mcp.call(name, args) the tool surface (the 457 AppWorld APIs, names like spotify__login)
  ctx.retrieve(query)      your RAG hook over the API docs
  ctx.memory.read/write    persisted across tasks (wiped between tasks on the off-arm)
  ctx.reflect(note)        record a self-correction
  ctx.execute(code)        LOCAL ONLY: run Python against AppWorld for fast iteration
  ctx.trace(type, **kw)    append a JSONL event

On the graded run the trusted trace comes from the gateways, so everything flows through ctx.
"""
from flywheel.ctx import Ctx

__all__ = ["Ctx"]
