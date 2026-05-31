# AppWorld

AppWorld is the substrate your agent acts in: a simulated digital world of apps with a real
relational state behind them, exposed as **457 Python APIs**. Grading is AppWorld's own
deterministic state oracle, so this is not vibes: either the world ended up in the goal state
or it didn't.

## The 9 apps (+ 2 system)

`spotify`, `amazon`, `gmail`, `phone`, `venmo`, `splitwise`, `todoist`, `simple_note`,
`file_system` — plus two system apps you'll lean on:

- `supervisor` — who you act for (profile, account passwords) and how you finish (`complete_task`).
- `api_docs` — the discovery surface (app/API descriptions and full docs).

## How you act: the MCP tool surface (graded) and `execute` (local)

On the graded run you act through **MCP tools**: `ctx.mcp.call(name, args)`, where names are
`{app}__{api}` (e.g. `spotify__login`, `supervisor__complete_task`). That call is what the gate
counts, and it reaches the 457 APIs over the MCP gateway.

```python
r = ctx.mcp.call("api_docs__show_app_descriptions", {})
```

Locally there is also `ctx.execute(code)` (the same in-process AppWorld, `apis.<app>.<method>(...)`)
for fast iteration -- it returns stdout / a repr / a traceback. **State persists across calls
within a task** (logins, created records), but Python *variables do not unless you keep them in
one snippet or reprint them*. Build your solver against `ctx.mcp` so it runs identically when
graded; reach for `ctx.execute` only to poke at AppWorld while developing.

```python
out = ctx.execute("print(apis.api_docs.show_app_descriptions())")  # local only
```

## Discovering APIs (do this, don't guess names)

You do not know method names or argument schemas. Read them:

```python
apis.api_docs.show_app_descriptions()
apis.api_docs.show_api_descriptions(app_name='spotify')          # -> [{'name','description'}, ...]
apis.api_docs.show_api_doc(app_name='spotify', api_name='login') # -> full params + response schema
```

For RAG, dump all of them with `python tools/dump_api_docs.py` (writes `./api_docs_dump/`).
457 docs do not fit in context; retrieve the relevant ones per task.

## THE LOGIN FLOW (the #1 thing that trips people up)

Almost every authenticated call needs `access_token=`. Get it like this:

```python
# 1. your identity (you act on the supervisor's behalf)
me = apis.supervisor.show_profile()                 # me['email'], me['phone_number']

# 2. passwords: a LIST of {'account_name','password'} -- make a dict
pw = {p['account_name']: p['password'] for p in apis.supervisor.show_account_passwords()}

# 3. log into the app you need; thread the token through every authed call
tok = apis.spotify.login(username=me['email'], password=pw['spotify'])['access_token']
songs = apis.spotify.show_song_library(access_token=tok, page_index=0, page_limit=20)
```

For the **phone** app log in with `username=me['phone_number']`. If an email login 401s, retry
with the phone number. Get the token once and reuse it.

## Finishing: complete_task (mandatory)

The oracle ONLY sees what you submit. A correct answer printed to stdout but never submitted
scores **0**. Always finish:

```python
apis.supervisor.complete_task(answer=<value>)   # QUESTION tasks: a concise answer
apis.supervisor.complete_task()                 # ACTION tasks: no answer arg
```

`answer` should be concise and EXACT: a number, a name, yes/no, or a comma-separated list of
titles in their stored casing. `world.task_completed()` tells you whether you've called it.

## The oracle

`world.evaluate().to_dict()` returns the verdict; read the `success` boolean (the SDK wraps
this as `ctx.evaluate()` / `AppWorldEnv.evaluate()`). It also reports `collateral_damage`
(did you mutate state you shouldn't have) and `difficulty`. Grading re-runs held-out tasks; the
graded split is one you never see.

## Common pitfalls

- **You must call `complete_task`** or you score 0 even with the right answer in stdout.
- **List/search APIs are paginated** (`page_index`, `page_limit`): loop `page_index=0,1,2,...`
  until a page comes back short/empty, or you'll silently miss items.
- **Song IDs live on albums/playlists, not the song list.** "across my song, album and playlist
  libraries" = union of `song_id` from `show_song_library` + every album's `song_ids` + every
  playlist's `song_ids`. De-dup with a set.
- **`play_count` / `genre` / `title` are not on the library item** — call
  `apis.spotify.show_song(access_token=tok, song_id=sid)` to get them. "Top N most played" =
  sort those by `play_count` desc, take N.
- **Venmo `search_users` returns `email`, not `user_id`** — transactions go by `receiver_email`.
- **Inspect a response's keys before indexing** (`print(record)`); field names vary by app.
- **Don't repeat an identical failing call** — read the traceback, fix the exact cause (wrong
  api name -> look it up; missing `access_token` -> add it; wrong field -> print keys), retry.
