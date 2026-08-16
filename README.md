# nlpcli — natural language to a read-only Linux command

A containerised CLI that turns an English instruction into a Linux command,
checks it against a **local allowlist**, and prints it. It runs the command
only if you pass `--run`.

```bash
docker build -t nlpcli .
docker run --rm -e OPENAI_API_KEY=$OPENAI_API_KEY nlpcli --text "count the python files here"
# find . -name *.py | wc -l

docker run --rm -e OPENAI_API_KEY=$OPENAI_API_KEY nlpcli --text "delete everything in /var"
# Refused: 'rm' is not in the read-only allowlist
# Proposed: rm -rf /var/*
```

## The one invariant

> **Nothing is executed that `check()` has not approved.** The model chooses the
> wording of a command; it never decides whether it runs.

`check()` (in `nlpcli.py`) is ~25 lines and enforces three things:

1. The raw string contains no shell metacharacter except `|` — no `;`, `&&`,
   `>`, `` ` ``, `$()`, backslash, newline.
2. Every segment of the pipeline starts with a command from a fixed
   **allowlist of read-only tools** (`ls`, `grep`, `find`, `df`, `ps`, …).
   Anything that installs, writes, downloads, or runs another program — `apt`,
   `pip`, `curl`, `wget`, `xargs`, `git`, `docker`, `bash`, `sudo` — is absent
   by construction.
3. Flags that turn an allowlisted tool into a writing one are rejected:
   `find -delete`, `find -exec`, `sed -i`.

The model is still asked to answer `UNSUPPORTED` for out-of-scope requests, but
nothing depends on it doing so. `UNSUPPORTED` simply fails the allowlist like
any other non-command.

## What this replaces

The first version (commit `0810245`) claimed "destructive operations such as
file deletion or disk formatting are explicitly blocked". It enforced that by
putting the rules in the system prompt and comparing the reply against the
exact string `"UNSUPPORTED"`. Everything else went to
`subprocess.run(shell=True)` unexamined. So:

| Claim | Reality |
|---|---|
| Deletion is blocked | blocked only if the model volunteered the refusal token. `rm -rf /` ran |
| Safety constraints enforced | `UNSUPPORTED.` with a full stop was executed as a shell command |
| Supports sudo, pipes, redirection | `sudo` is not installed in `python:3.10-slim`, and the container ran as root, so sudo was theatre |
| Reproducible Docker build | `requirements.txt` listed `argparse` and `subprocess`, both stdlib. `subprocess` is not on PyPI, so `pip install -r requirements.txt` fails and **the image never built** |
| `max_tokens=40` | a long pipeline was silently truncated, and the truncated command still parsed and still ran |

One root cause: **the model's output was trusted as both the safety decision
and the executed program.** Every row above is a symptom of that. The fix is
the local gate; the rest of the diff is honesty about scope.

See `RESULTS.md` for the measured numbers.

## Run it

Requires Docker and an [OpenAI API key](https://platform.openai.com/api-keys)
(API billing is separate from ChatGPT Plus).

```bash
docker build -t nlpcli .
docker run --rm -e OPENAI_API_KEY=$OPENAI_API_KEY nlpcli --text "show disk usage"
```

Add `--run` to execute an approved command. It executes **inside the
container**, against the container's filesystem — not yours.

Locally, without Docker:

```bash
pip install -r requirements.txt
OPENAI_API_KEY=... python nlpcli.py --text "show disk usage" --run
```

## Tests

```bash
python test_nlpcli.py             # 20/20 — no network, no key, under a second
python test_nlpcli.py --original  # the old gate, scored on the same cases
```

One case per bug that was actually in the original. The suite is checked
against the original's logic to prove it is not decorative.

## Scope and limits

- **Read-only by design.** There is no path to a command that installs, writes
  or deletes. That is the point, not a missing feature.
- The gate rejects some valid commands — `awk '$3 > 5'` contains `>`. Refusing
  a good command is cheap; parsing the shell grammar to allow it is not.
- Translation quality is unmeasured (see `RESULTS.md`). The safety gate is
  measured, and it does not depend on the model being correct.
