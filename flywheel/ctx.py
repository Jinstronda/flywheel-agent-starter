"""Ctx: the single object your solve(ctx) gets. It bundles the task instruction, the fixed
model (through the metered proxy), AppWorld execution, cross-task memory, a RAG hook, reflect,
and the trace. The harness builds it; you read it. The README contract is exactly this surface.
"""
import os

from flywheel.appworld_env import AppWorldEnv
from flywheel.memory import Memory
from flywheel.proxy import chat
from flywheel.trace import Trace


class Ctx:
    def __init__(self, env, proxy_url, key, memory_dir, trace_file=None,
                 max_steps=20, retriever=None):
        self._env = env
        self._proxy = proxy_url
        self._key = key
        self.instruction = env.instruction
        self.trace = Trace(trace_file)
        self.memory = Memory(memory_dir, self.trace)
        self.max_steps = max_steps
        self._retriever = retriever  # wire your own: a callable query -> results

    @classmethod
    def from_env(cls, task_id=None, experiment_name="flywheel"):
        """Build a Ctx from the environment contract (FLYWHEEL_KEY / FLYWHEEL_URL / APPWORLD_ROOT).
        The sandbox grader sets FLYWHEEL_TASK_ID and the trace/memory dirs; pass task_id to
        override when you run locally."""
        os.environ.setdefault("APPWORLD_ROOT", os.environ.get("APPWORLD_ROOT", "./aw"))
        tid = task_id or os.environ.get("FLYWHEEL_TASK_ID")
        if not tid:
            raise SystemExit("no task id: set FLYWHEEL_TASK_ID or pass task_id=")
        env = AppWorldEnv(tid, experiment_name=experiment_name)
        return cls(
            env,
            proxy_url=os.environ.get("FLYWHEEL_URL", "https://homodeus-flywheel.fly.dev") + "/v1",
            key=os.environ.get("FLYWHEEL_KEY", ""),
            memory_dir=os.environ.get("FLYWHEEL_MEMORY_DIR", "./.memory"),
            trace_file=os.environ.get("FLYWHEEL_TRACE_FILE"),
            max_steps=int(os.environ.get("FLYWHEEL_MAX_STEPS", "20")),
        )

    def model(self, messages, tools=None, response_format=None):
        """The fixed model through the metered proxy. Returns the raw OpenAI response dict.
        `messages` is the usual list; pass `tools` for function-calling, `response_format`
        for structured output. The proxy pins the model and temperature."""
        self.trace("model")
        data, remaining = chat(self._proxy, self._key, messages, tools=tools,
                               response_format=response_format)
        if remaining is not None:
            self.trace("budget", remaining=remaining)
        return data

    def execute(self, code):
        """Run Python against AppWorld (the `apis` object). Returns stdout/result/traceback."""
        self.trace("execute")
        return self._env.execute(code)

    def retrieve(self, query):
        """Your RAG hook. The starter ships a stub so the contract is wired; you replace the
        retriever (dump the API docs with tools/dump_api_docs.py, index them, return the top-k
        for `query`). You cannot fit 457 API docs in context, so this is load-bearing."""
        self.trace("retrieval", query=query)
        if self._retriever is None:
            return []
        return self._retriever(query)

    def reflect(self, note):
        """Record a self-correction (a failed step you're about to retry differently)."""
        self.trace("reflect", note=note)

    def evaluate(self):
        """Deterministic oracle for the current task (local self-testing only; the real grader
        calls this itself). True iff the goal state was reached."""
        return self._env.evaluate()
