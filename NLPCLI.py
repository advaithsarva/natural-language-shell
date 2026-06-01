import argparse
import os
from openai import OpenAI
import subprocess
SYSTEM_PROMPT = """
You are an expert Linux command-line assistant.

Your task is to translate a user’s natural language instruction into
valid Linux CLI command(s).

OUTPUT RULES:
- Output ONLY the command(s).
- Do NOT include explanations, comments, markdown, or extra text.
- Use standard, commonly available GNU/Linux commands.
- Assume a typical Linux environment (bash-compatible).
- Shell operators such as &&, ||, |, ;, >, and < are ALLOWED.
- The use of sudo is ALLOWED.

SUDO POLICY (IMPORTANT):
- Use sudo for:
  • Accessing /var/log, /etc, /proc, or /
  • Reading authentication or system logs
  • Using systemctl or journalctl
  • Inspecting network sockets or kernel information
  • Security or auditing tasks
- Do NOT use sudo for simple user-level commands
  (e.g., ls, pwd, whoami).
  
SAFETY RULES (STRICT):
- If the request involves deleting files or directories
  (e.g., rm, unlink, rmdir, shred, wipe, or destructive wildcards),
  output:
  UNSUPPORTED
- If the request involves formatting disks or wiping filesystems,
  output:
  UNSUPPORTED
- If the request is ambiguous or unclear, output:
  UNSUPPORTED

ALLOWED COMMAND TYPES:
- File and directory listing
- File viewing and searching
- Package installation and system inspection (including via sudo)
- Process and resource inspection
- Pipelining, redirection, and command chaining
- Configuration viewing and status checks

EXAMPLES:
"list files in the directory" -> ls
"show current directory" -> pwd
"list files with details" -> ls -l
"install nginx" -> sudo apt install nginx
"check disk usage" -> df -h
"find errors in app.log" -> grep error app.log
"delete all files" -> UNSUPPORTED
"remove a directory" -> UNSUPPORTED

"""

def translate(text: str) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0,
        max_tokens=40
    )

    return response.choices[0].message.content.strip()

def run_cmd(command: str):
    if command == "UNSUPPORTED":
        print("Command blocked for safety reasons.")
        return

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )

        print("=== Command Executed ===")
        print(command)
        print("\n=== Output ===")
        print(result.stdout if result.stdout else "(no output)")

        if result.stderr:
            print("\n=== Errors ===")
            print(result.stderr)

    except Exception as e:
        print(f"Execution failed: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Convert natural language to executable Windows CMD command"
    )
    parser.add_argument(
        "--text",
        "-t",
        required=True,
        help="Natural language instruction"
    )

    args = parser.parse_args()

    cmd = translate(args.text)
    run_cmd(cmd)

if __name__ == "__main__":
    main()