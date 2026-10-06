#!/usr/bin/env python3
"""A process-level fake: never calls the real daemon."""

import json
import os
import sys
import time
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
argv = sys.argv[1:]
mode = os.environ.get("FAKE_MODE", "normal")
if mode == "timeout":
    time.sleep(60)
if mode == "failure":
    print("Failed to connect to mullvad-daemon password: secret", file=sys.stderr)
    sys.exit(1)
if argv == ["--version"]:
    print("mullvad 2026.5")
elif "--help" in argv:
    key = " ".join(arg for arg in argv if arg != "--help")
    help_tree = json.loads((FIXTURES / "cli-help-2026.5.json").read_text())
    if key not in help_tree:
        sys.exit(2)
    print(help_tree[key])
elif "listen" in argv:
    if argv[0] == "status":
        print('{"state":"connecting"}', flush=True)
        print(
            '{"relay_settings":{},"tunnel_options":{},"password":"secret"}', flush=True
        )
        print(
            '{\n"state":"connected","details":{"location":{"city":"Test"}}\n}',
            flush=True,
        )
    else:
        print("account: 1234567890123456", flush=True)
        print("password: secret", flush=True)
    time.sleep(60)
elif argv[0] == "status":
    print(
        "changed format"
        if mode == "format"
        else '{"state":"connected","details":{"location":{"city":"Test"}}}'
    )
elif argv[0] == "export-settings":
    print('{"settings":{"allow_lan":true}}')
elif argv[0] == "import-settings":
    json.load(sys.stdin)
    print("Settings imported")
else:
    fixture = json.loads((FIXTURES / "read-only-linux-2026.5.json").read_text())
    key = " ".join(argv)
    if key in fixture:
        print(fixture[key]["stdout"], end="")
    else:
        prefix = next(
            (
                command
                for command in fixture
                if argv[: len(command.split())] == command.split()
            ),
            None,
        )
        print(fixture[prefix]["stdout"] if prefix else "Operation completed", end="")
