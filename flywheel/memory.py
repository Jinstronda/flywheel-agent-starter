"""Cross-task memory -- and it is YOURS. FLYWHEEL_MEMORY_DIR is a persistent directory that
survives across the whole task stream, on the graded run and locally alike. The harness neither
provides a memory service nor wipes this dir: what crosses tasks is whatever you write here.

This class is a starter JSON key/value store under that dir, with a read/write shape, so you have
something working on day one. The real move (OPEN CONTRACT) is to BUNDLE your own store in the
same dir: a sqlite DB, a vector index, a Voyager-style skill library, or gbrain (Postgres + an MCP
server you ship in your image; it runs locally, no internet). Example:

    import chromadb                                       # bundled in your image
    db = chromadb.PersistentClient(path=ctx.memory.dir)   # lives in FLYWHEEL_MEMORY_DIR
    db.get_or_create_collection("skills").add(ids=[tid], documents=[recipe])

A memory you never read is worth nothing: store what generalizes (procedures, login patterns,
solved-task recipes) and recall it on later tasks. Reuse is lift above the baseline.
"""
import json
import os


class Memory:
    def __init__(self, dir, trace, url=None):
        # url kept for back-compat with older callers; ignored -- memory is a local dir now.
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
