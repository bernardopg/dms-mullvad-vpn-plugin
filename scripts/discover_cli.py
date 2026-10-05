#!/usr/bin/env python3
"""Read-only snapshot of the CLI grammar; never invokes an action."""
import json
import re
import subprocess
from pathlib import Path


def discover(binary="mullvad"):
    tree = {}
    pending = [()]
    while pending:
        path = pending.pop(0)
        result = subprocess.run([binary, *path, "--help"], capture_output=True, text=True, timeout=10)
        if result.returncode:
            raise RuntimeError(result.stderr)
        tree[" ".join(path)] = result.stdout
        commands = result.stdout.split("Commands:\n", 1)
        if len(commands) == 2:
            for name in re.findall(r"^  ([a-z][a-z0-9-]*)\s", commands[1].split("\nOptions:")[0], re.M):
                if name != "help":
                    pending.append((*path, name))
    return tree


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "tests/fixtures/cli-help-2026.5.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(discover(), indent=2) + "\n")
