"""nlpcli — translate natural language into a read-only Linux command.

INVARIANT: nothing is executed that `check()` has not approved.
The model chooses the wording of a command; it never decides whether it runs.

The original version (commit 0810245) enforced safety by asking the model to
print the string "UNSUPPORTED" and comparing against it. Anything else the
model produced was passed to `subprocess.run(shell=True)` unexamined.
"""

import argparse
import os
import shlex
import subprocess
import sys

MODEL = "gpt-4o-mini"
MAX_LEN = 300

# Read-only inspection tools only. Anything that installs, writes, downloads or
# runs another program (apt, pip, curl, wget, xargs, docker, git, bash) is out
# by construction — adding one is a deliberate act, not an oversight.
ALLOWED = frozenset("""
ls pwd whoami id date uptime uname hostname arch
cat head tail nl wc sort uniq cut tr column
grep egrep fgrep awk sed
find stat file basename dirname readlink
df du free ps lsblk lscpu blkid
env printenv which echo printf
ip ss netstat dmesg
""".split())

# Flags that turn an allowlisted read-only tool into a writing one.
BANNED_ARGS = {
    "find": frozenset({"-delete", "-exec", "-execdir", "-ok", "-okdir",
                       "-fprint", "-fprintf", "-fls"}),
    "sed": frozenset({"-i", "--in-place"}),
}

# `|` is the only shell operator allowed. Everything here can chain, redirect,
# substitute or escape, so it is rejected in the raw string before parsing.
# ponytail: this also rejects legitimate uses like awk '$3 > 5'. Refusing a
# valid command is cheap; the alternative is parsing the shell grammar.
UNSAFE_CHARS = set(";&`$><(){}\n\\")

SYSTEM_PROMPT = """\
You are a Linux command-line assistant. Translate the user's instruction into
a single Linux command.

OUTPUT RULES
- Output ONLY the command, on one line. No explanation, no markdown, no sudo.
- Pipelines with | are allowed. Redirection, ;, &&, $(), and backticks are not.
- Only these commands may be used: {allowed}
- If the instruction cannot be satisfied under these rules, output UNSUPPORTED.

EXAMPLES
"list files in the directory" -> ls
"list files with details" -> ls -l
"check disk usage" -> df -h
"find errors in app.log" -> grep -i error app.log
"count the python files here" -> find . -name *.py | wc -l
"delete all files" -> UNSUPPORTED
"install nginx" -> UNSUPPORTED
""".format(allowed=" ".join(sorted(ALLOWED)))


def check(command):
    """Return None if the command is safe to run, else the reason it is not."""
    if not command:
        return "no command produced"
    if len(command) > MAX_LEN:
        return "longer than %d characters" % MAX_LEN
    bad = sorted(set(command) & UNSAFE_CHARS)
    if bad:
        return "contains shell metacharacter(s): %s" % " ".join(
            repr(c) for c in bad)

    for segment in command.split("|"):
        try:
            argv = shlex.split(segment)
        except ValueError as exc:
            return "unparseable: %s" % exc
        if not argv:
            return "empty pipeline segment"
        prog = argv[0]
        if prog not in ALLOWED:
            return "%r is not in the read-only allowlist" % prog
        banned = BANNED_ARGS.get(prog, frozenset()).intersection(argv[1:])
        if banned:
            return "%s %s can modify the system" % (prog, sorted(banned)[0])
    return None


def clean(text):
    """Keep the first real line of a model reply, dropping any markdown fence."""
    lines = (text or "").replace("```", "\n").splitlines()
    for line in (ln.strip() for ln in lines):
        if line and not line.startswith(("bash", "sh", "#")):
            return line
    return ""


def translate(text):
    from openai import OpenAI

    key = os.getenv("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY is not set.")

    choice = OpenAI(api_key=key).chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": text}],
        temperature=0,
        max_tokens=200,
    ).choices[0]

    # A truncated command is a different command: `find / -name x | head` cut
    # short still parses and still runs. Refuse instead.
    if choice.finish_reason == "length":
        sys.exit("Model output was truncated; refusing to run a partial command.")
    return clean(choice.message.content)


def main():
    parser = argparse.ArgumentParser(
        description="Translate natural language into a read-only Linux command.")
    parser.add_argument("--text", "-t", required=True,
                        help="natural language instruction")
    parser.add_argument("--run", action="store_true",
                        help="execute the command if it passes the safety "
                             "check (default: print it and stop)")
    args = parser.parse_args()

    command = translate(args.text)
    reason = check(command)
    if reason:
        print("Refused: %s" % reason)
        print("Proposed: %s" % command)
        return 1

    print(command)
    if not args.run:
        return 0

    # ponytail: shell=True is acceptable only because check() rejected every
    # metacharacter except `|`. The allowlist is the trust boundary, not this.
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
