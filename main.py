"""Entrypoint the sandbox grader invokes once per task. It builds the Ctx from the environment
(FLYWHEEL_KEY / FLYWHEEL_URL / APPWORLD_ROOT, and the grader's FLYWHEEL_TASK_ID + memory/trace
dirs) and runs your solve(ctx). Don't change the contract; put your work in agent.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flywheel import Ctx  # noqa: E402
from agent import solve  # noqa: E402

if __name__ == "__main__":
    solve(Ctx.from_env())
