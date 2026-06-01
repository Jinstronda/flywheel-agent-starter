"""FLYWHEEL agent SDK. The harness builds a Ctx and calls solve(ctx) once per task.

You only write agent.py. These modules give you the surface the README promises and the
trace the grader reads. One surface, two backends (graded gateways / local AppWorld):

  ctx.instruction          the task to solve
  ctx.model(messages)      the fixed model (gemini-3-flash-preview) through the metered proxy
  ctx.mcp.call(name, args) the AppWorld MCP meta-tool surface
  ctx.retrieve(query)      your RAG hook over the API docs (search_apis)
  ctx.run_code(code)       Python with `apis` in scope: loops, pagination, bulk writes
  ctx.memory.read/write    persisted across the task stream; reuse is lift over baseline
  ctx.reflect(note)        record a self-correction
  ctx.execute(code)        LOCAL ONLY alias of run_code for fast iteration
  ctx.trace(type, **kw)    append a JSONL event

On the graded run the trusted trace comes from the gateways, so everything flows through ctx.
"""
from flywheel.ctx import Ctx

__all__ = ["Ctx"]
