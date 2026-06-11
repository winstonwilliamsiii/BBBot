import json
import re
import subprocess


since = "2026-01-25"
commits = subprocess.check_output(
    ["git", "log", f"--since={since}", "--pretty=format:%H"],
    text=True,
).splitlines()

rows = []
for commit in commits:
    date = subprocess.check_output(
        ["git", "show", "-s", "--format=%ad", "--date=short", commit],
        text=True,
    ).strip()
    subject = subprocess.check_output(
        ["git", "show", "-s", "--format=%s", commit],
        text=True,
    ).strip()
    diff = subprocess.check_output(
        [
            "git",
            "show",
            "--unified=0",
            "--pretty=format:",
            commit,
            "--",
            "*.sql",
            "*.py",
            "*.js",
            "*.ts",
        ],
        text=True,
        errors="ignore",
    )

    current = ""
    for line in diff.splitlines():
        match = re.match(r"^\+\+\+ b/(.+)$", line)
        if match:
            current = match.group(1)
            continue

        match = re.match(
            r"^\+\s*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([`\"\[]?[A-Za-z0-9_\.]+[`\"\]]?)\s*\(",
            line,
            re.I,
        )
        if match:
            name = match.group(1).strip("`\"[]")
            rows.append(
                {
                    "table": name,
                    "commit": commit,
                    "date": date,
                    "file": current,
                    "subject": subject,
                }
            )

seen = set()
out = []
for row in sorted(rows, key=lambda x: (x["table"], x["date"], x["commit"], x["file"])):
    key = (row["table"], row["commit"], row["file"])
    if key in seen:
        continue
    seen.add(key)
    out.append(row)

print(json.dumps(out, indent=2))
