#!/usr/bin/env python3
"""Collect read-only CLI output, masking accounts, keys and proxy credentials."""
import json
import re
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import backend

READS = ["auto-connect get", "beta-program get", "lockdown-mode get", "dns get", "lan get", "relay get", "relay override get", "relay list", "api-access get", "api-access list", "anti-censorship get", "split-tunnel list", "tunnel get", "custom-list list", "account get", "account list-devices", "version"]


def redact(text):
    text = re.sub(r"\b\d{16}\b", "[ACCOUNT]", text)
    text = re.sub(r"(?im)^([^\n]*(?:password|username|account number|public key|private key)[^:\n]*:)\s*.*$", r"\1 [REDACTED]", text)
    return text


if __name__ == "__main__":
    if "--adapter" in sys.argv:
        adapter = backend.Adapter()
        try:
            initialized = adapter.handle({"id":1, "op":"init"})
            snapshot = adapter.handle({"id":2, "op":"snapshot"})
            if not initialized["ok"] or not snapshot["ok"]:
                raise SystemExit("Adapter read-only validation failed")
            checks = {name: result["ok"] for name, result in snapshot["data"].items()}
            errors = {name: result["error"] for name, result in snapshot["data"].items() if not result["ok"]}
            event_ready = threading.Event()
            events = []
            def received(message):
                events.append(message)
                event_ready.set()
            adapter.emit = received
            adapter.handle({"id":3, "op":"status.listen"})
            event_ready.wait(timeout=3)
            adapter.stop_stream("status.listen")
            checks["status.listen"] = any(event.get("event") == "status.listen" and event["ok"] for event in events)
            if not checks["status.listen"]: errors["status.listen"] = {"code":"stream", "detail":"No initial state event"}
            summary = {"date":"2026-10-05", "cli_version":initialized["data"]["version"], "supported_forms":sum(initialized["data"]["supported"].values()), "read_checks":checks, "errors":errors, "mutations_executed":False}
            (ROOT / "docs/read-only-validation.json").write_text(json.dumps(summary, indent=2) + "\n")
            print(json.dumps(summary, indent=2))
            if errors: raise SystemExit(1)
        finally:
            adapter.close()
        raise SystemExit(0)
    outputs = {}
    for command in READS:
        result = subprocess.run(["mullvad", *command.split()], capture_output=True, text=True, timeout=20, env={**__import__("os").environ, "LC_ALL": "C", "LANG": "C"})
        outputs[command] = {"code": result.returncode, "stdout": redact(result.stdout), "stderr": redact(result.stderr)}
    result = subprocess.run(["mullvad", "export-settings", "-"], capture_output=True, text=True, timeout=20)
    outputs["exported-settings"] = {"code":result.returncode, "stdout":json.dumps(backend.redact(json.loads(result.stdout))) if result.returncode == 0 else "", "stderr":backend.redact(result.stderr)}
    target = Path(__file__).resolve().parents[1] / "tests/fixtures/read-only-linux-2026.5.json"
    target.write_text(json.dumps(outputs, indent=2) + "\n")
    for command, result in outputs.items():
        print(command, result["code"], result["stdout"][:300] or result["stderr"][:100])
