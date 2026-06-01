"""Ctx: the single object your solve(ctx) gets. The harness builds it; you read it. One surface,
two backends, so the agent you tune locally is the agent we grade:

  ctx.instruction            the task to solve
  ctx.model(messages, ...)   the fixed model through the metered proxy (OpenAI-shaped dict back)
  ctx.mcp.call(name, args)   the AppWorld MCP meta-tool surface
  ctx.retrieve(query)        your RAG hook over the API docs (search_apis)
  ctx.run_code(code)         run Python with `apis` in scope (loops, pagination, bulk writes)
  ctx.memory.read()/.write() a starter store under FLYWHEEL_MEMORY_DIR; bundle your own here
  ctx.reflect(note)          record a self-correction / retry
  ctx.execute(code)          LOCAL ONLY alias of run_code for fast iteration

OPEN CONTRACT: only the MODEL (the proxy) and the WORLD (AppWorld via the MCP gateway + oracle)
are fixed. Memory is YOURS -- FLYWHEEL_MEMORY_DIR is a persistent dir that survives across tasks;
bring and bundle your own store there (a vector DB, sqlite, gbrain, a skill library). Bring your
own RAG, MCP servers, framework too; the sandbox has no internet, so bundle it to run offline.

GRADED run (the sandbox sets FLYWHEEL_MCP_URL): tools come from FLYWHEEL_MCP_URL, the model from
FLYWHEEL_PROXY_URL with FLYWHEEL_PROXY_TOKEN, your memory from FLYWHEEL_MEMORY_DIR. The trusted
trace the gate reads is the gateways' own, so everything you do has to flow through ctx.

LOCAL run (run_local.py / quickstart.py): no gateways, so AppWorld runs in-process and the model
uses FLYWHEEL_URL + FLYWHEEL_KEY. ctx.mcp, ctx.run_code, and ctx.execute all reach the same
in-process AppWorld so a ctx.mcp-based agent is exercised the same way it will be graded.

Your score is a continuous number in [0,1] -- reliability-weighted solve rate minus a collateral
penalty -- and you are ranked against the other candidates. A naive loop scores ~0.0; a SOTA agent
lands ~0.5 on the brutal pool. You get up to 3 graded trials, each followed by per-task feedback
(logs, tool calls + errors, oracle pass/fail + why), so you improve between attempts; practice is
unlimited, so read the failures and iterate.
"""
import os

from flywheel.memory import Memory
from flywheel.mcp import MCP
from flywheel.proxy import chat
from flywheel.trace import Trace


class Ctx:
    def __init__(self, instruction, proxy_url, key, memory_dir, trace_file=None,
                 max_steps=50, mcp_url=None, env=None, retriever=None):
        self.instruction = instruction
        self._proxy = (proxy_url or "").rstrip("/")
        self._key = key
        self._env = env  # local AppWorld backend, or None on the graded run
        self._mcp_url = mcp_url
        self.max_steps = max_steps
        self._retriever = retriever
        self.trace = Trace(trace_file)
        self.memory = Memory(memory_dir, self.trace)
        self.mcp = MCP(mcp_url, self.trace) if mcp_url else _LocalMCP(env, self.trace)

    @classmethod
    def from_env(cls, task_id=None, experiment_name="flywheel"):
        """Build a Ctx from the environment contract. The graded sandbox sets FLYWHEEL_MCP_URL /
        FLYWHEEL_PROXY_URL / FLYWHEEL_PROXY_TOKEN and a persistent FLYWHEEL_MEMORY_DIR (your own
        store); locally you set FLYWHEEL_KEY / FLYWHEEL_URL / APPWORLD_ROOT (see .env.example)."""
        mcp_url = os.environ.get("FLYWHEEL_MCP_URL")
        trace_file = os.environ.get("FLYWHEEL_TRACE_FILE")
        memory_dir = os.environ.get("FLYWHEEL_MEMORY_DIR", "./.memory")
        max_steps = int(os.environ.get("FLYWHEEL_MAX_STEPS", "50"))
        if mcp_url:  # graded run: gateways, no AppWorld in-process
            return cls(
                instruction=os.environ.get("FLYWHEEL_TASK_INSTRUCTION", ""),
                proxy_url=os.environ.get("FLYWHEEL_PROXY_URL", ""),
                key=os.environ.get("FLYWHEEL_PROXY_TOKEN", ""),
                memory_dir=memory_dir, trace_file=trace_file, max_steps=max_steps,
                mcp_url=mcp_url)
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
        """Your RAG hook over the API docs. Graded run: a `search_apis` MCP call, traced as a
        retrieval. Locally: your wired retriever if set, else the same search_apis path. You
        cannot fit 457 API docs in context, so this is load-bearing -- index the docs
        (tools/dump_api_docs.py) and pass your retriever via Ctx(retriever=...)."""
        self.trace("retrieval", query=query)
        if self._retriever is not None:
            return self._retriever(query)
        return self.mcp.call("search_apis", {"query": query})

    def reflect(self, note):
        """Record a self-correction (a failed step you're about to retry differently)."""
        self.trace("reflect", note=note)
        if self._mcp_url:
            return self.mcp.call("reflect", {"note": note})
        return None

    def run_code(self, code):
        """Run a Python snippet with the AppWorld `apis` object in scope and get stdout back.
        This is for loops, pagination, and bulk writes: a 40-item task is one run_code, not 40
        call_api turns. Graded run: a `run_code` MCP call (traced). Locally: the same in-process
        AppWorld, so the solver runs identically when graded."""
        if self._mcp_url:
            return self.mcp.call("run_code", {"code": code})
        if self._env is None:
            raise RuntimeError("no MCP url and no local AppWorld; set FLYWHEEL_MCP_URL or APPWORLD_ROOT")
        self.trace("tool", name="run_code")
        return {"result": self._env.execute(code)}

    def execute(self, code):
        """LOCAL ONLY: run Python against AppWorld (the `apis` object), returning stdout/repr.
        On the graded run there is no in-process AppWorld -- use ctx.run_code (or ctx.mcp.call)."""
        if self._env is None:
            raise RuntimeError("ctx.execute is local-only; on the graded run use ctx.run_code")
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
    agent runs the same locally as under grading. It exposes the same five meta-tools as the real
    gateway: search_apis, api_doc, call_api, run_code, complete_task."""
    def __init__(self, env, trace):
        self._env = env
        self._t = trace

    def list(self):
        return [
            {"name": "search_apis"},
            {"name": "api_doc"},
            {"name": "call_api"},
            {"name": "run_code"},
            {"name": "complete_task"},
        ]

    def call(self, name, args=None):
        self._t("tool", name=name)
        if self._env is None:
            return {"error": "no MCP url and no local AppWorld; set FLYWHEEL_MCP_URL or APPWORLD_ROOT"}
        args = args or {}
        if name == "search_apis":
            return self._search(args.get("query", ""))
        if name == "api_doc":
            return self._api_doc(args.get("app", ""), args.get("api", ""))
        if name == "call_api":
            return self._call_api(args.get("app", ""), args.get("api", ""), args.get("arguments") or {})
        if name == "run_code":
            return {"result": self._env.execute(args.get("code", ""))}
        if name == "complete_task":
            return self._complete(args.get("answer"))
        return {"error": f"unknown tool {name}"}

    def _run_json(self, code):
        import json
        marker = "__FW_LOCAL__"
        out = self._env.execute(code.replace("__MARKER__", marker))
        for line in reversed((out or "").splitlines()):
            if line.startswith(marker):
                return json.loads(line[len(marker):])
        return {"error": "no_result", "raw": (out or "")[-500:]}

    def _search(self, query):
        import json
        code = (
            "import json\n"
            f"q = {json.dumps(str(query))}.lower()\n"
            "hits = []\n"
            "for app in apis.api_docs.show_app_descriptions():\n"
            "    an = app['name']\n"
            "    for d in apis.api_docs.show_api_descriptions(app_name=an):\n"
            "        blob = (an + ' ' + d['name'] + ' ' + d.get('description','')).lower()\n"
            "        if all(w in blob for w in q.split()):\n"
            "            hits.append({'app': an, 'api': d['name'], 'description': d.get('description','')})\n"
            "print('__MARKER__' + json.dumps({'results': hits[:20]}))")
        return self._run_json(code)

    def _api_doc(self, app, api):
        import json
        code = (
            "import json\n"
            f"doc = apis.api_docs.show_api_doc(app_name={json.dumps(str(app))}, api_name={json.dumps(str(api))})\n"
            "print('__MARKER__' + json.dumps({'doc': doc}, default=str))")
        return self._run_json(code)

    def _call_api(self, app, api, arguments):
        import json
        code = (
            "import json\n"
            f"args = json.loads({json.dumps(json.dumps(arguments or {}))})\n"
            f"res = getattr(getattr(apis, {json.dumps(str(app))}), {json.dumps(str(api))})(**args)\n"
            "print('__MARKER__' + json.dumps({'result': res}, default=str))")
        return self._run_json(code)

    def _complete(self, answer):
        import json
        if answer is None or str(answer).strip() in ("", "<<not_given>>"):
            code = "import json\napis.supervisor.complete_task()\nprint('__MARKER__' + json.dumps({'ok': True}))"
        else:
            code = (
                "import json\n"
                f"apis.supervisor.complete_task(answer={json.dumps(str(answer))})\n"
                "print('__MARKER__' + json.dumps({'ok': True}))")
        return self._run_json(code)
