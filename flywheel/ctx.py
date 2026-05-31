"""Ctx: the single object your solve(ctx) gets. The harness builds it; you read it. One surface,
two backends, so the agent you tune locally is the agent we grade:

  ctx.instruction            the task to solve
  ctx.model(messages, ...)   the fixed model through the metered proxy (OpenAI-shaped dict back)
  ctx.mcp.call(name, args)   the tool surface (the 457 AppWorld APIs, names like spotify__login)
  ctx.retrieve(query)        your RAG hook over the API docs
  ctx.memory.read()/.write() persisted across tasks (wiped between tasks on the off-arm)
  ctx.reflect(note)          record a self-correction / retry
  ctx.execute(code)          LOCAL ONLY: run Python against AppWorld for fast iteration

GRADED run (the sandbox sets FLYWHEEL_MCP_URL): tools come from FLYWHEEL_MCP_URL, memory from
FLYWHEEL_MEMORY_URL, the model from FLYWHEEL_PROXY_URL with FLYWHEEL_PROXY_TOKEN. The trusted
trace the gate reads is the gateways' own, so everything you do has to flow through ctx.

LOCAL run (run_local.py / quickstart.py): no gateways, so AppWorld runs in-process, memory is a
JSON file, and the model uses FLYWHEEL_URL + FLYWHEEL_KEY. ctx.mcp and ctx.execute both reach the
same in-process AppWorld so a ctx.mcp-based agent is exercised the same way it will be graded.
"""
import os

from flywheel.memory import Memory
from flywheel.mcp import MCP
from flywheel.proxy import chat
from flywheel.trace import Trace


class Ctx:
    def __init__(self, instruction, proxy_url, key, memory_dir, trace_file=None,
                 max_steps=20, mcp_url=None, memory_url=None, env=None, retriever=None):
        self.instruction = instruction
        self._proxy = (proxy_url or "").rstrip("/")
        self._key = key
        self._env = env  # local AppWorld backend, or None on the graded run
        self.max_steps = max_steps
        self._retriever = retriever
        self.trace = Trace(trace_file)
        self.memory = Memory(memory_dir, self.trace, url=memory_url)
        self.mcp = MCP(mcp_url, self.trace) if mcp_url else _LocalMCP(env, self.trace)

    @classmethod
    def from_env(cls, task_id=None, experiment_name="flywheel"):
        """Build a Ctx from the environment contract. The graded sandbox sets FLYWHEEL_MCP_URL /
        FLYWHEEL_MEMORY_URL / FLYWHEEL_PROXY_URL / FLYWHEEL_PROXY_TOKEN; locally you set
        FLYWHEEL_KEY / FLYWHEEL_URL / APPWORLD_ROOT (see .env.example)."""
        mcp_url = os.environ.get("FLYWHEEL_MCP_URL")
        trace_file = os.environ.get("FLYWHEEL_TRACE_FILE")
        memory_dir = os.environ.get("FLYWHEEL_MEMORY_DIR", "./.memory")
        max_steps = int(os.environ.get("FLYWHEEL_MAX_STEPS", "20"))
        if mcp_url:  # graded run: gateways, no AppWorld in-process
            return cls(
                instruction=os.environ.get("FLYWHEEL_TASK_INSTRUCTION", ""),
                proxy_url=os.environ.get("FLYWHEEL_PROXY_URL", ""),
                key=os.environ.get("FLYWHEEL_PROXY_TOKEN", ""),
                memory_dir=memory_dir, trace_file=trace_file, max_steps=max_steps,
                mcp_url=mcp_url, memory_url=os.environ.get("FLYWHEEL_MEMORY_URL"))
        from flywheel.appworld_env import AppWorldEnv  # local-only import
        os.environ.setdefault("APPWORLD_ROOT", os.environ.get("APPWORLD_ROOT", "./aw"))
        tid = task_id or os.environ.get("FLYWHEEL_TASK_ID")
        if not tid:
            raise SystemExit("no task id: set FLYWHEEL_TASK_ID or pass task_id= (local run)")
        env = AppWorldEnv(tid, experiment_name=experiment_name)
        return cls(
            instruction=env.instruction,
            proxy_url=os.environ.get("FLYWHEEL_URL", "https://homodeus-flywheel.fly.dev") + "/v1",
            key=os.environ.get("FLYWHEEL_KEY", ""),
            memory_dir=memory_dir, trace_file=trace_file, max_steps=max_steps, env=env)

    def model(self, messages, tools=None, response_format=None):
        """The fixed model through the metered proxy. Returns the raw OpenAI response dict.
        Pass `tools` for function-calling, `response_format` for structured output. The proxy
        pins the model and temperature; never send `model` or `max_tokens`."""
        self.trace("model")
        data, remaining = chat(self._proxy, self._key, messages, tools=tools,
                               response_format=response_format)
        if remaining is not None:
            self.trace("budget", remaining=remaining)
        return data

    def retrieve(self, query):
        """Your RAG hook over the API docs. Graded run: a `search_docs` MCP call, traced as a
        retrieval. Locally: your wired retriever if set, else the same search_docs path. You
        cannot fit 457 API docs in context, so this is load-bearing -- index the docs
        (tools/dump_api_docs.py) and pass your retriever via Ctx(retriever=...)."""
        self.trace("retrieval", query=query)
        if self._retriever is not None:
            return self._retriever(query)
        return self.mcp.call("search_docs", {"query": query})

    def reflect(self, note):
        """Record a self-correction (a failed step you're about to retry differently)."""
        self.trace("reflect", note=note)

    def execute(self, code):
        """LOCAL ONLY: run Python against AppWorld (the `apis` object). On the graded run there is
        no in-process AppWorld -- act through ctx.mcp.call instead."""
        if self._env is None:
            raise RuntimeError("ctx.execute is local-only; on the graded run act through ctx.mcp.call")
        self.trace("execute")
        return self._env.execute(code)

    def evaluate(self):
        """Deterministic oracle for the current task (local self-testing only; the real grader
        calls it itself). True iff the goal state was reached."""
        if self._env is None:
            raise RuntimeError("ctx.evaluate is local-only; the grader runs the oracle itself")
        return self._env.evaluate()


class _LocalMCP:
    """Local stand-in for the graded MCP gateway, backed by in-process AppWorld so a ctx.mcp-based
    agent runs the same locally as under grading. `search_docs` reads api_docs; every other tool is
    `{app}__{api}` -> apis.<app>.<api>(**args). Traces a `tool` event like the gateway does."""
    def __init__(self, env, trace):
        self._env = env
        self._t = trace

    def list(self):
        if self._env is None:
            return []
        out = self._env.execute(
            "import json\n"
            "t=[]\n"
            "for a in apis.api_docs.show_app_descriptions():\n"
            "  app=a['name']\n"
            "  for d in apis.api_docs.show_api_descriptions(app_name=app):\n"
            "    t.append(app+'__'+d['name'])\n"
            "print(json.dumps(t))")
        try:
            import json
            return [{"name": n} for n in json.loads(out.strip().splitlines()[-1])]
        except Exception:
            return []

    def call(self, name, args=None):
        self._t("tool", name=name)
        if self._env is None:
            return {"error": "no MCP url and no local AppWorld; set FLYWHEEL_MCP_URL or APPWORLD_ROOT"}
        args = args or {}
        if name == "search_docs":
            q = (args.get("query") or "").replace('"', "'")
            out = self._env.execute(f"print(apis.api_docs.show_api_descriptions(app_name={q!r}))")
            return {"results": [out.strip()]}
        if "__" not in name:
            return {"error": f"tool names are app__api; got {name!r}"}
        app, api = name.split("__", 1)
        kw = ", ".join(f"{k}={v!r}" for k, v in args.items())
        out = self._env.execute(f"print(apis.{app}.{api}({kw}))")
        return {"result": out.strip()}
