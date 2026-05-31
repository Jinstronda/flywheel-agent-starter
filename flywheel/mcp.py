"""The MCP tool surface. On the graded run the 457 AppWorld APIs reach your agent as MCP tools
over JSON-RPC at FLYWHEEL_MCP_URL (tools/list to discover, tools/call to act). Tool names are
`{app}__{api}` (e.g. spotify__login, supervisor__complete_task). You log in in-band: read the
supervisor credentials through the tools, then thread the access token through authed calls.

Every tools/call is traced as a `tool` event by the gateway, and that is what the gate counts,
so acting through here (not hardcoded HTTP) is load-bearing.
"""
import json
import urllib.request


class MCP:
    def __init__(self, url, trace):
        self.url = (url or "").rstrip("/")
        self._t = trace
        self._id = 0

    def _rpc(self, method, params):
        self._id += 1
        body = json.dumps({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}).encode()
        req = urllib.request.Request(self.url, data=body,
                                     headers={"content-type": "application/json", "accept": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())

    def list(self):
        return self._rpc("tools/list", {}).get("result", {}).get("tools", [])

    def call(self, name, args=None):
        self._t("tool", name=name)
        return self._rpc("tools/call", {"name": name, "arguments": args or {}}).get("result")
