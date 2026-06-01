"""Local trace sink for debugging.

The graded gate reads trusted gateway events from the model, memory, and MCP services. This
file is still useful while developing locally, but writing here never satisfies the pass gate.
When no trace file is set, events are dropped.
"""
import json


class Trace:
    def __init__(self, path=None):
        self.path = path

    def __call__(self, type, **kw):
        if not self.path:
            return
        with open(self.path, "a") as f:
            f.write(json.dumps({"type": type, **kw}) + "\n")
