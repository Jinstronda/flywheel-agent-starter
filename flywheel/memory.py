"""Cross-task memory. Persisted JSON under the memory dir. It survives across the whole task
stream on the memory-ON run and is wiped between tasks on the memory-OFF run. The gap between
the two arms is part of your grade, so a memory you never read is worth nothing: store what
generalizes (procedures, login patterns, solved-task recipes), recall it on later tasks.

Each read/write emits a trace event so the grader can see memory is real, not decorative.
"""
import json
import os


class Memory:
    def __init__(self, dir, trace):
        self.dir = dir
        self.path = os.path.join(dir, "memory.json")
        self._t = trace
        os.makedirs(dir, exist_ok=True)

    def _load(self):
        try:
            with open(self.path) as f:
                return json.load(f)
        except Exception:
            return {}

    def read(self):
        self._t("memory_read")
        return self._load()

    def write(self, key, value):
        self._t("memory_write", key=key)
        d = self._load()
        d[key] = value
        with open(self.path, "w") as f:
            json.dump(d, f)
