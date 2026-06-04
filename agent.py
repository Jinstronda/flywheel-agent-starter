"""Your agent. This is the only file you have to write.

OPEN CONTRACT: the model (gemini-3-flash-preview, via the proxy) and the world (AppWorld) are
fixed. Everything else is yours to build and bundle in your repo: your memory (gbrain, a vector
DB, sqlite, a skill library), your RAG, your MCP servers, any framework -- it all runs locally in
your container, offline. This SDK is just a starting surface; replace it if you want.

The harness calls solve(ctx) once per task. Your score is a continuous number in [0,1] --
reliability-weighted solve rate minus a collateral penalty -- and you are ranked against the other
candidates.

THIS IS WHERE THE HIRING SIGNAL IS. The loop below runs end to end and submits, but it is a naive
ReAct loop and scores ~0 on the brutal pool BY DESIGN. Everything that moves the number is yours to
add: retrieve the right docs, act through MCP, do bulk work in one run_code turn, carry login +
pagination recipes across tasks in your own memory (under FLYWHEEL_MEMORY_DIR), and recover when a
step fails. Read the per-task feedback after each trial and iterate. Practice is unlimited.
"""

import re

CODE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

SYSTEM = (
    "You solve AppWorld tasks by writing Python that runs against an `apis` object in a stateful "
    "sandbox. Output EXACTLY ONE ```python``` block per turn; variables persist across turns.\n"
    "Playbook: (1) discover before calling -- apis.api_docs.show_api_doc(app_name=..., api_name=...), "
    "never guess names; (2) log in -- me=apis.supervisor.show_profile(); pw=apis.supervisor."
    "show_account_passwords(); tok=apis.<app>.login(username=me['email'], password=...)"
    "['access_token']; thread access_token=tok; (3) paginate list APIs until empty; (4) finish -- "
    "QUESTION tasks: apis.supervisor.complete_task(answer=...); ACTION tasks: mutate then "
    "apis.supervisor.complete_task() with no answer. Always submit; an unsubmitted task scores 0."
)


def _code(text):
    m = CODE_RE.search(text or "")
    if m:
        return m.group(1).strip()
    return text.strip() if (text and "apis." in text and "```" not in text) else None


def _content(resp):
    try:
        return resp["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        return ""


def solve(ctx):
    instr = ctx.instruction

    # carry login + pagination recipes learned on earlier tasks (this is the compounding part)
    mem = ctx.memory.read()
    recall = "\n".join(f"- {k}: {v}" for k, v in mem.items()) if mem else ""

    # discover the right APIs for this task
    hits = ctx.retrieve(instr)

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": (
            f"TASK:\n{instr}\n\n"
            f"{'LEARNED FROM PRIOR TASKS (reuse):' + chr(10) + recall + chr(10) + chr(10) if recall else ''}"
            f"RETRIEVED API HITS:\n{str(hits)[:1500]}\n\n"
            "Write your first ```python``` block: discover APIs and do the login flow."
        )},
    ]

    submitted = False
    turns = min(ctx.max_steps, 18)
    for turn in range(turns):
        reply = _content(ctx.model(messages))
        code = _code(reply)
        if not code:
            messages.append({"role": "user", "content": "Reply with EXACTLY one ```python``` block."})
            continue
        messages.append({"role": "assistant", "content": reply})
        result = str(ctx.run_code(code))
        if "complete_task" in code:
            submitted = True
            break
        if "Traceback" in result or "Error" in result:
            ctx.reflect("execution error; reading traceback and retrying")
        left = turns - turn - 1
        nudge = " Only a few turns left: if you have the answer, call complete_task now." if left <= 3 else ""
        messages.append({"role": "user", "content": (
            f"RESULT:\n{result[:3000]}\n\nContinue with one ```python``` block. "
            f"When done, call apis.supervisor.complete_task.{nudge}"
        )})

    # unconditional submit: never leave a task unsubmitted (the #1 documented zero)
    if not submitted:
        ctx.reflect("forcing a final complete_task so the task is never left unsubmitted")
        try:
            ctx.run_code(
                "try:\n"
                "    apis.supervisor.complete_task(answer='')\n"
                "except Exception:\n"
                "    apis.supervisor.complete_task()"
            )
        except Exception:
            ctx.mcp.call("complete_task", {})

    # remember the login recipe so a later task does not relearn it
    if "login_recipe" not in mem:
        ctx.memory.write(
            "login_recipe",
            "me=apis.supervisor.show_profile(); pw via apis.supervisor.show_account_passwords(); "
            "tok=apis.<app>.login(username=me['email'], password=pw)['access_token']; "
            "thread access_token=tok (retry with me['phone_number'] if email login fails)",
        )
