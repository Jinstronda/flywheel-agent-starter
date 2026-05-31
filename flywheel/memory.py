"""Cross-task memory. The grader owns it: on the graded run it is the harness memory service
(FLYWHEEL_MEMORY_URL, POST /read and /write) and the memory_read/memory_write events the gate
trusts come from THAT service, not from a file you write. Locally there is no service, so it
falls back to a JSON file under the memory dir with the same read/write shape.

It survives across the whole task stream on the memory-ON run and is wiped between tasks on the
memory-OFF run. The gap between the two arms is part of your grade, so a memory you never read is
worth nothing: store what generalizes (procedures, login patterns, solved-task recipes), recall
it on later tasks.
"""
import json
import os
import urllib.request


class Memory:
    def __init__(self, dir, trace, url=None):
        self.url = (url or "").rstrip("/")
        self.dir = dir
        self.path = os.path.join(dir, "memory.json")
        self._t = trace
        os.makedirs(dir, exist_ok=True)

    def _post(self, path, body=None):
        req = urllib.request.Request(self.url + path, data=json.dumps(body or {}).encode(),
                                     headers={"content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())

    def _load(self):
        try:
            with open(self.path) as f:
                return json.load(f)
        except Exception:
            return {}

    def read(self):
        if self.url:
            return self._post("/read")
        self._t("memory_read")
        return self._load()

    def write(self, key, value):
        if self.url:
            return self._post("/write", {"key": key, "value": value})
        self._t("memory_write", key=key)
        d = self._load()
        d[key] = value
        with open(self.path, "w") as f:
            json.dump(d, f)
