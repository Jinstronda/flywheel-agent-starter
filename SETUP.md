# Setup

A Python venv with AppWorld + its data, and your key. ~10 minutes, mostly the data download.

## 1. venv + deps

Python 3.11 is the reference. It also installs cleanly on 3.13 with the pins below (AppWorld is
pydantic v1; the `typer`/`click` pins avoid a known break).

```bash
python3.11 -m venv .venv
source .venv/bin/activate

pip install -r requirements-dev.txt
```

## 2. install AppWorld + download the data

```bash
appworld install                       # unpacks AppWorld's encrypted code
appworld download data --root ./aw     # downloads the task data + DBs into ./aw/data
```

`./aw` is your `APPWORLD_ROOT`. The download is a few hundred MB and only happens once.

## 3. your key

```bash
cp .env.example .env
$EDITOR .env        # paste your FLYWHEEL_KEY (we gave you one); leave FLYWHEEL_URL/APPWORLD_ROOT as-is
```

`.env` holds:

| var | value |
|---|---|
| `FLYWHEEL_KEY` | your personal proxy key (metered; do not commit it) |
| `FLYWHEEL_URL` | `https://homodeus-flywheel.fly.dev` |
| `APPWORLD_ROOT` | `./aw` |

These tools read `.env` themselves only if you `export` them or use a loader; the simplest is:

```bash
set -a; source .env; set +a
```

## 4. verify

```bash
appworld verify                  # checks the AppWorld install + data
python examples/quickstart.py    # logs in, reads a doc, pings the model, completes a task, evaluates
python tools/dump_api_docs.py    # writes ./api_docs_dump/ (the docs you'll RAG over)
```

If `quickstart.py` prints `logged in: True` and an `[evaluate] success = ...` line, you're set.
Then build `agent.py` and iterate with `python run_local.py --n 5`. See the `docs/`.

> **Ship your RAG corpus.** The graded sandbox is offline, so `python tools/dump_api_docs.py` won't run there. Generate `api_docs_dump/` locally and **commit it** (it is no longer gitignored) so `git add .` includes it and your retriever has the 457 docs in the sandbox.
