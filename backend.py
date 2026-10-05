#!/usr/bin/env python3
"""Mullvad 2026.5 JSONL adapter. Python stdlib only, no shell or disk secrets."""
import base64
import ipaddress
import json
import os
import queue
import re
import signal
import stat
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOG = json.loads((ROOT / "operations.json").read_text())
OPERATIONS = {op["id"]: op for op in CATALOG}
LIMIT = 1024 * 1024
ENV = {**os.environ, "LC_ALL": "C", "LANG": "C", "NO_COLOR": "1"}


class AdapterError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(detail)
        self.code = code


def redact(value, secrets=()):
    if isinstance(value, dict):
        return {k: "[REDACTED]" if re.search(r"password|username|account_number|token|voucher|private_key|public_key", k, re.I) else redact(v, secrets) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, secrets) for v in value]
    if not isinstance(value, str):
        return value
    for secret in sorted((s for s in secrets if s), key=len, reverse=True):
        value = value.replace(secret, "[REDACTED]")
    value = re.sub(r"\b(?:\d[ -]?){16}\b", "[ACCOUNT]", value)
    value = re.sub(r"(?im)^([^\n]*(?:password|username|voucher|account|public key|private key|pubkey)[^:\n]*:)[ \t]*[^\n]*", r"\1 [REDACTED]", value)
    value = re.sub(r"\b[A-Za-z0-9+/]{43}=", "[KEY]", value)
    return value


def scalar(field, value):
    kind = field["kind"]
    if kind == "bool":
        if type(value) is not bool:
            raise ValueError("expected boolean")
        return value
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        raise ValueError("expected text or integer")
    value = str(value)
    if len(value) > field.get("max_length", 8192) or any(ord(c) < 32 for c in value):
        raise ValueError("invalid length or control character")
    if len(value.encode()) > field.get("max_bytes", 32768):
        raise ValueError("value exceeds byte limit")
    if value.startswith("-") and not field.get("flag"):
        raise ValueError("value cannot be a CLI option")
    if kind == "enum" and value not in field["choices"]:
        raise ValueError("choose a listed value")
    if kind == "cipher" and not re.fullmatch(r"[a-z0-9-]{1,80}", value):
        raise ValueError("invalid cipher name")
    if kind in ("integer", "port") and not (field.get("allow_any") and value == "any"):
        if not value.isascii() or not value.isdigit() or not field.get("minimum", 1) <= int(value) <= field.get("maximum", 65535):
            raise ValueError("integer outside allowed range")
    if kind == "ip":
        ipaddress.ip_address(value)
    if kind == "account" and not re.fullmatch(r"\d{16}", value, re.ASCII):
        raise ValueError("expected 16 digits")
    if kind == "key" and len(base64.b64decode(value, validate=True)) != 32:
        raise ValueError("expected 32 byte base64 key")
    if kind == "cidrs":
        for item in value.split(",") if value else []:
            ipaddress.ip_network(item.strip(), strict=True)
    if kind == "location" and not re.fullmatch(r"any|[a-z]{2}|[a-z]{2}-[a-z]{3}-wg-\d{3}", value):
        raise ValueError("expected country code, any, or relay hostname")
    if kind == "city" and not re.fullmatch(r"[a-z]{3}", value):
        raise ValueError("expected three letter city code")
    if kind in ("file", "executable") and (not Path(value).is_absolute() or value == "-"):
        raise ValueError("expected absolute path")
    if kind == "executable" and (not Path(value).is_file() or not os.access(value, os.X_OK)):
        raise ValueError("executable not found")
    return value


def arguments(op, params):
    if not isinstance(params, dict) or set(params) - {f["name"] for f in op["fields"]}:
        raise AdapterError("validation", "Unknown parameter")
    argv = list(op["argv"])
    skipped_position = False
    for field in op["fields"]:
        name = field["name"]
        value = params.get(name)
        missing = value is None or value == "" or value == []
        if field.get("allow_empty") and value == "":
            missing = False
        if missing:
            if field["required"]:
                raise AdapterError("validation", name + ": required")
            if not field.get("flag"):
                skipped_position = True
            continue
        try:
            if field["kind"] in ("multi", "argv") or field.get("many"):
                if not isinstance(value, list) or len(value) > 128 or not value:
                    raise ValueError("expected a non-empty list")
                if field["kind"] == "argv":
                    # Application arguments are data, and may start with '-'.
                    if any(not isinstance(v, str) or "\x00" in v or len(v) > 8192 for v in value):
                        raise ValueError("invalid application argument")
                    values = value
                elif field["kind"] == "multi":
                    if any(v not in field["choices"] for v in value):
                        raise ValueError("choose listed values")
                    values = value
                else:
                    values = [scalar(field, v) for v in value]
            else:
                value = scalar(field, value)
                values = [value]
            if field["kind"] == "bool":
                if value:
                    argv.append(field["flag"])
                continue
            if field.get("stdin"):
                continue
            if not field.get("flag") and skipped_position:
                raise ValueError("preceding positional field is required")
            if field.get("flag"):
                if len(values) == 1 and str(values[0]).startswith("-"):
                    argv.append(field["flag"] + "=" + values[0])
                    continue
                argv.append(field["flag"])
            argv.extend(values)
        except (ValueError, TypeError) as error:
            raise AdapterError("validation", name + ": " + str(error)) from None
    if op["id"] in ("factory-reset", "reset-settings"):
        argv.append("--assume-yes")
    if op["id"] == "relay.override.clear-all":
        argv.append("--confirm")
    if op["id"] == "status" and params.get("verbose") and params.get("debug"):
        raise AdapterError("validation", "verbose/debug: mutually exclusive")
    if op["id"] == "status.listen" or (op["id"] == "status" and not params.get("verbose") and not params.get("debug")):
        argv.insert(1, "--json")
    if op["id"].endswith("ipv4") and "address" in params and ipaddress.ip_address(params["address"]).version != 4:
        raise AdapterError("validation", "address: expected IPv4")
    if op["id"].endswith("ipv6") and "address" in params and ipaddress.ip_address(params["address"]).version != 6:
        raise AdapterError("validation", "address: expected IPv6")
    for name, version in (("v4_gateway", 4), ("v6_gateway", 6)):
        if params.get(name) and ipaddress.ip_address(params[name]).version != version:
            raise AdapterError("validation", name + ": wrong address family")
    if op["id"] == "api-access.add.socks5.remote" and bool(params.get("username")) != bool(params.get("password")):
        raise AdapterError("validation", "username/password: both required for authentication")
    return argv


def parse_output(operation, text):
    """Recognize English CLI output. Unknown read formats fail visibly."""
    if operation == "status":
        try:
            warnings = []
            while text.startswith(("Warning: You are not logged in to an account.\n", "Warning: This device has been revoked.\n")):
                warning, text = text.split("\n", 1)
                warnings.append(warning)
            data = json.loads(text)
            if not isinstance(data, dict) or data.get("state") not in ("connected", "connecting", "disconnected", "disconnecting", "error"):
                raise ValueError()
            if warnings: data["warnings"] = warnings
            return data
        except (ValueError, TypeError):
            raise AdapterError("format", "Invalid status JSON") from None
    if operation == "exported-settings":
        try:
            data = json.loads(text)
            if not isinstance(data, dict): raise ValueError()
            return redact(data)
        except ValueError:
            raise AdapterError("format", "Invalid exported settings JSON") from None
    text = redact(text).strip()
    if operation in ("version", "cli.version"):
        match = re.search(r"\b(20\d{2}\.\d+(?:-[\w.]+)?)\b", text)
        if not match:
            raise AdapterError("format", "Version format changed")
        return {"version": match[1], "text": text}
    policies = {"auto-connect.get": r"Autoconnect: (on|off)", "beta-program.get": r"Beta program: (on|off)", "lockdown-mode.get": r"Block traffic when the VPN is disconnected: (on|off)", "lan.get": r"Local network sharing setting: (allow|block)"}
    if operation in policies:
        match = re.fullmatch(policies[operation], text)
        if not match:
            raise AdapterError("format", operation + ": format changed")
        return {"value": match[1], "text": text}
    if operation == "split-tunnel.list":
        if not text.startswith("Excluded PIDs:") or any(not line.strip().isdigit() for line in text.splitlines()[1:] if line.strip()):
            raise AdapterError("format", "PID list format changed")
        return {"pids": [int(line) for line in text.splitlines()[1:] if line.strip()], "text": text}
    if operation == "api-access.list":
        entries = []
        for line in text.splitlines():
            if not line.strip():
                continue
            match = re.fullmatch(r"(\d+)\. (.+?)( \*)?", line)
            detail = re.fullmatch(r"\s+(Protocol|Peer|Password|Username|Local port):\s*(.+)", line)
            if detail and entries:
                entries[-1].setdefault("settings", {})[detail[1]] = detail[2]
                continue
            if not match:
                raise AdapterError("format", "API list format changed")
            entries.append({"index": int(match[1]), "name": match[2], "enabled": bool(match[3])})
        return {"entries": entries, "text": text}
    if operation == "relay.list":
        entries = []
        country = city = ""
        for line in text.splitlines():
            if not line.strip():
                continue
            match = re.fullmatch(r"([^\t].+) \(([a-z]{2})\)", line)
            city_match = re.fullmatch(r"\t(.+) \(([a-z]{3})\) @ .+", line)
            relay = re.fullmatch(r"\t\t([a-z]{2}-[a-z]{3}-wg-\d+) \(([^)]+)\) - hosted by (.+) \((Mullvad-owned|rented)\)(.*)", line)
            if match:
                country = match[2]
            elif city_match:
                city = city_match[2]
            elif relay and country and city:
                entries.append(dict(hostname=relay[1], country=country, city=city, addresses=relay[2], provider=relay[3], ownership="owned" if relay[4] == "Mullvad-owned" else "rented", features=relay[5].strip()))
            else:
                raise AdapterError("format", "Relay list format changed")
        return {"entries": entries, "text": text}
    if operation == "dns.get":
        lines = text.splitlines()
        if lines and lines[0] == "Custom DNS: no":
            keys = ["Block ads", "Block trackers", "Block malware", "Block adult content", "Block gambling", "Block social media"]
            if len(lines) != 7 or any(not re.fullmatch(re.escape(key) + r": (true|false)", line) for key, line in zip(keys, lines[1:])):
                raise AdapterError("format", "DNS flags format changed")
            return {"custom": False, "blocks": {key: line.endswith("true") for key, line in zip(keys, lines[1:])}, "text": text}
        if len(lines) >= 2 and lines[:2] == ["Custom DNS: yes", "Servers:"]:
            try:
                servers = [str(ipaddress.ip_address(line)) for line in lines[2:]]
            except ValueError:
                raise AdapterError("format", "DNS server format changed") from None
            return {"custom": True, "servers": servers, "text": text}
        raise AdapterError("format", "DNS format changed")
    prefixes = {"relay.get": ("Generic constraints", "Custom endpoint:"), "anti-censorship.get": ("mode:",), "tunnel.get": ("WireGuard options",), "account.get": ("Mullvad account:", "Not logged in on any account", "The current device has been revoked"), "account.list-devices": ("Devices on the account:",), "relay.override.get": ("",), "custom-list.list": ("",), "api-access.get": ("",)}
    if operation in prefixes:
        if not any(text.startswith(prefix) for prefix in prefixes[operation]):
            raise AdapterError("format", operation + ": format changed")
        if operation == "relay.override.get":
            patterns = [r".+ \([a-z]{2}\)", r"\s+.+ \([a-z]{3}\)", r"\s+[^\s:]+:", r"\s+ipv[46]: [a-fA-F\d:.]+", r"Overrides for unrecognized servers\. Consider removing these!"]
            if any(not any(re.fullmatch(pattern, line) for pattern in patterns) for line in text.splitlines()):
                raise AdapterError("format", "Override list format changed")
        if operation == "custom-list.list":
            entries = []
            for line in text.splitlines():
                if not line.strip(): continue
                if line.startswith("\t"):
                    if not entries: raise AdapterError("format", "Custom list format changed")
                    entries[-1]["locations"].append(line.strip())
                elif line.startswith(" "):
                    raise AdapterError("format", "Custom list format changed")
                else:
                    entries.append({"name":line, "locations":[]})
            return {"entries":entries, "text":text}
        if operation == "api-access.get":
            lines = text.splitlines()
            if not lines or any(not re.fullmatch(r"\s+(Protocol|Peer|Password|Username|Local port):\s*.+", line) for line in lines[1:] if line.strip()):
                raise AdapterError("format", "API method format changed")
        option_text = re.sub(r"(?m)^\s+Created [^\n]+$", "", text)
        values = dict(re.findall(r"(?m)^[ \t]*([^:\n]+):[^\S\n]*([^\n]*)$", option_text))
        expected = {"relay.get": {"Location", "Provider(s)", "Ownership", "IP protocol", "Multihop state", "Multihop entry"}, "anti-censorship.get": {"mode", "udp2tcp settings", "shadowsocks settings", "wireguard-port settings", "lwo settings"}, "tunnel.get": {"MTU", "Quantum resistance", "DAITA", "Public key", "Rotation interval", "Allowed IPs", "IPv6"}}
        if operation in expected and not text.startswith("Custom endpoint:") and set(values) != expected[operation]:
            raise AdapterError("format", operation + ": settings format changed")
        return {"text": text, "values": values}
    return {"text": text}


def status_event(data):
    if not isinstance(data, dict):
        raise AdapterError("format", "Invalid daemon event")
    if "state" in data:
        return "status.listen", parse_output("status", json.dumps(data))
    known = {"settings": {"relay_settings", "tunnel_options"}, "relays": {"countries"}, "version": {"supported", "suggested_upgrade"}, "device": {"cause", "new_state"}, "removed-device": {"devices"}, "access-method": {"access_method"}, "leak": {"interface", "reachable"}}
    for kind, keys in known.items():
        if keys <= data.keys():
            return "daemon.changed", {"kind":kind}
    raise AdapterError("format", "Unrecognized daemon event")


class Adapter:
    def __init__(self, emit=lambda message: None, binary=None, timeout=20, mock=False):
        self.emit = emit
        self.binary = binary or shutil.which("mullvad")
        self.timeout = timeout
        self.mock = mock
        self.lock = threading.RLock()
        self.process_lock = threading.Lock()
        self.processes = set()
        self.streams = {}
        self.closed = threading.Event()
        self.supported = {}
        self.version = ""
        self.mock_status = {"state": "connected", "details": {"location": {"country": "Brazil", "city": "Fortaleza", "hostname": "br-for-wg-001"}}}

    def run(self, argv, stdin=None, secrets=()):
        if not self.binary:
            raise AdapterError("binary", "mullvad not found")
        if self.closed.is_set():
            raise AdapterError("closed")
        try:
            with self.process_lock:
                process = subprocess.Popen([self.binary, *argv], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=ENV)
                self.processes.add(process)
            try:
                stdout, stderr = process.communicate(stdin, timeout=self.timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                raise AdapterError("timeout", "Command timed out") from None
            finally:
                with self.process_lock:
                    self.processes.discard(process)
            if process.returncode:
                detail = redact(stderr or stdout, secrets)[:4096]
                code = "daemon" if "mullvad-daemon" in detail or "Management RPC" in detail else "command"
                raise AdapterError(code, detail)
            if len(stdout) > 8 * LIMIT:
                raise AdapterError("format", "Output exceeds limit")
            return stdout
        except OSError:
            raise AdapterError("binary", "Unable to execute mullvad") from None

    def initialize(self):
        self.version = parse_output("cli.version", self.run(["--version"]))["version"]
        for op in CATALOG:
            if op["id"] == "split.launch":
                self.supported[op["id"]] = bool(shutil.which("mullvad-exclude"))
                continue
            try:
                help_text = self.run([*op["argv"], "--help"])
                self.supported[op["id"]] = all(not f.get("flag") or f["flag"] in help_text for f in op["fields"])
            except AdapterError:
                self.supported[op["id"]] = False
        return {"version": self.version, "supported": self.supported, "catalog": CATALOG}

    def stop_stream(self, operation):
        entry = self.streams.pop(operation, None)
        if entry:
            process, thread = entry
            process.intentional_stop = True
            if process.poll() is None:
                process.terminate()
            thread.join(timeout=2)
            if process.poll() is None:
                process.kill()
                thread.join(timeout=2)

    def start_stream(self, operation, argv):
        self.stop_stream(operation)
        if not self.binary:
            raise AdapterError("binary")
        try:
            process = subprocess.Popen([self.binary, *argv], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=ENV)
        except OSError:
            raise AdapterError("binary") from None
        def watch():
            buffer = ""
            try:
                for line in process.stdout:
                    if self.closed.is_set():
                        break
                    if operation == "status.listen":
                        if not buffer and line.strip() in ("Warning: You are not logged in to an account.", "Warning: This device has been revoked."):
                            self.emit({"event":"daemon.changed", "ok":True, "data":{"kind":"device"}})
                            continue
                        buffer += line
                        if len(buffer) > LIMIT:
                            raise AdapterError("format", "Status event exceeds limit")
                        if buffer.strip() and not buffer.lstrip().startswith("{"):
                            raise AdapterError("format", "Invalid status event")
                        try:
                            data = json.loads(buffer)
                        except ValueError:
                            continue
                        event, data = status_event(data)
                        buffer = ""
                    else:
                        event = operation
                        data = {"text": redact(line.rstrip())[:4096]}
                    self.emit({"event": event, "ok": True, "data": redact(data)})
                if buffer.strip():
                    raise AdapterError("format", "Incomplete status event")
                stderr = process.stderr.read(4096)
                if not self.closed.is_set() and not getattr(process, "intentional_stop", False):
                    self.emit({"event": operation, "ok": False, "error": {"code": "stream", "detail": redact(stderr) or "Stream ended"}})
            except (AdapterError, ValueError) as error:
                self.emit({"event": operation, "ok": False, "error": {"code": "format", "detail": str(error)}})
                if process.poll() is None:
                    process.terminate()
            finally:
                process.stdout.close()
                process.stderr.close()
                process.wait()
        thread = threading.Thread(target=watch, daemon=True)
        self.streams[operation] = (process, thread)
        thread.start()
        return {"active": True}

    def handle(self, request):
        identifier = request.get("id") if isinstance(request, dict) else None
        operation = request.get("op") if isinstance(request, dict) else None
        secrets = []
        try:
            if not isinstance(request, dict) or set(request) - {"id", "op", "params", "confirmed"} or not isinstance(identifier, (str, int)) or isinstance(identifier, bool):
                raise AdapterError("protocol", "Invalid request envelope")
            with self.lock:
                if self.mock:
                    return self.mock_handle(request)
                if operation == "init":
                    data = self.initialize()
                elif operation == "snapshot":
                    data = {}
                    try:
                        data["exported-settings"] = {"ok": True, "data": parse_output("exported-settings", self.run(["export-settings", "-"]))}
                    except AdapterError as error:
                        data["exported-settings"] = {"ok": False, "error": {"code":error.code, "detail":str(error)}}
                    for op in CATALOG:
                        if op["readonly"] and not any(f["required"] for f in op["fields"]) and not op["stream"] and op["id"] not in ("cli.version", "status"):
                            try:
                                data[op["id"]] = {"ok": True, "data": parse_output(op["id"], self.run(arguments(op, {})))}
                            except AdapterError as error:
                                data[op["id"]] = {"ok": False, "error": {"code": error.code, "detail": str(error)}}
                    try:
                        data["status"] = {"ok": True, "data": parse_output("status", self.run(["status", "--json"]))}
                    except AdapterError as error:
                        data["status"] = {"ok": False, "error": {"code": error.code, "detail": str(error)}}
                elif operation == "stream.stop":
                    target = request.get("params", {}).get("operation")
                    if target not in ("status.listen", "log.listen"):
                        raise AdapterError("validation", "Unknown stream")
                    self.stop_stream(target)
                    data = {"active": False}
                else:
                    op = OPERATIONS.get(operation)
                    if not op:
                        raise AdapterError("operation", "Unknown operation")
                    params = request.get("params", {})
                    secrets = [str(params.get(f["name"], "")) for f in op["fields"] if f.get("secret")]
                    argv = arguments(op, params)
                    if op["confirm"] and request.get("confirmed") is not True:
                        raise AdapterError("confirmation", "Contextual confirmation required")
                    if self.supported and not self.supported.get(operation):
                        raise AdapterError("unsupported", "Unavailable in installed CLI")
                    if operation == "split.launch":
                        exclude = shutil.which("mullvad-exclude")
                        if not exclude:
                            raise AdapterError("binary", "mullvad-exclude not found")
                        child = subprocess.Popen([exclude, params["executable"], *params.get("arguments", [])], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                        try:
                            child.wait(timeout=0.25)
                            if child.returncode:
                                raise AdapterError("command", "mullvad-exclude could not launch the application")
                        except subprocess.TimeoutExpired:
                            threading.Thread(target=child.wait, daemon=True).start()
                        data = {"pid": child.pid}
                    elif op["stream"]:
                        data = self.start_stream(operation, argv)
                    elif operation == "relay.set.custom":
                        data = parse_output(operation, self.run(argv, stdin=params["private_key"] + "\n", secrets=secrets))
                    elif operation == "status" and (params.get("verbose") or params.get("debug")):
                        diagnostics = self.run(argv, secrets=secrets)
                        data = parse_output("status", self.run(["status", "--json"]))
                        data["text"] = redact(diagnostics, secrets)
                    elif operation == "import-settings":
                        path = Path(params["file"])
                        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                        with os.fdopen(descriptor, "r") as source:
                            info = os.fstat(source.fileno())
                            if not stat.S_ISREG(info.st_mode) or info.st_size > LIMIT:
                                raise AdapterError("validation", "Unsafe import file")
                            content = source.read(LIMIT + 1)
                        if len(content) > LIMIT:
                            raise AdapterError("validation", "Import exceeds limit")
                        if not isinstance(json.loads(content), dict):
                            raise AdapterError("validation", "Expected a JSON object")
                        data = parse_output(operation, self.run(["import-settings", "-"], stdin=content, secrets=secrets))
                    elif operation == "export-settings":
                        content = self.run(["export-settings", "-"])
                        if not isinstance(json.loads(content), dict):
                            raise AdapterError("format", "Expected a JSON object")
                        target = Path(params["file"])
                        descriptor, temporary = tempfile.mkstemp(prefix=".mullvad-export-", dir=target.parent)
                        try:
                            with os.fdopen(descriptor, "w") as output:
                                output.write(content)
                                output.flush()
                                os.fsync(output.fileno())
                            os.link(temporary, target)
                        finally:
                            os.unlink(temporary)
                        data = {"text": "Export saved", "path": str(target)}
                    else:
                        data = parse_output(operation, self.run(argv, secrets=secrets))
            return {"id": identifier, "op": operation, "ok": True, "data": redact(data, secrets)}
        except (AdapterError, OSError, ValueError, TypeError, AttributeError) as error:
            code = error.code if isinstance(error, AdapterError) else "validation" if isinstance(error, (ValueError, TypeError, AttributeError)) else "file"
            # Never stringify file/JSON exceptions: imports may contain secrets.
            detail = str(error) if isinstance(error, AdapterError) else "Invalid input or inaccessible file"
            return {"id": identifier, "op": operation, "ok": False, "error": {"code": code, "detail": redact(detail, secrets)}}

    def mock_handle(self, request):
        operation = request["op"]
        if operation == "init":
            data = {"version": "2026.5 (mock)", "supported": {op["id"]: True for op in CATALOG}, "catalog": CATALOG}
        elif operation == "snapshot":
            fixture = json.loads((ROOT / "tests/fixtures/read-only-linux-2026.5.json").read_text())
            data = {k.replace(" ", "."): {"ok": True, "data": parse_output(k.replace(" ", "."), v["stdout"])} for k, v in fixture.items() if v["code"] == 0}
            data["status"] = {"ok": True, "data": self.mock_status}
            data["exported-settings"] = {"ok": True, "data": {"settings": {"allow_lan": True, "tunnel_options": {"wireguard": {"daita": {"enabled":False,"direct_only":False}}, "wireguard_userspace":False}}}}
        elif operation == "stream.stop":
            data = {"active": False}
        else:
            op = OPERATIONS.get(operation)
            if not op:
                raise AdapterError("operation")
            arguments(op, request.get("params", {}))
            if op["confirm"] and request.get("confirmed") is not True:
                raise AdapterError("confirmation")
            data = {"text": "Simulated operation", "active": op["stream"]}
            if operation in ("connect", "disconnect", "reconnect"):
                self.mock_status = {"state": "disconnected"} if operation == "disconnect" else {"state":"connected", "details":{"location":{"city":"Fortaleza","country":"Brazil"}}}
            elif operation == "status":
                data = self.mock_status
            elif op["readonly"] and not op["stream"]:
                fixture = json.loads((ROOT / "tests/fixtures/read-only-linux-2026.5.json").read_text())
                entry = fixture.get(" ".join(op["argv"]))
                if entry:
                    data = parse_output(operation, entry["stdout"])
        return {"id": request["id"], "op": operation, "ok": True, "data": data}

    def close(self):
        self.closed.set()
        with self.process_lock:
            for process in self.processes:
                if process.poll() is None:
                    process.terminate()
        for operation in list(self.streams):
            self.stop_stream(operation)


def serve(mock=False):
    output_lock = threading.Lock()
    def emit(message):
        with output_lock:
            print(json.dumps(message, ensure_ascii=False), flush=True)
    adapter = Adapter(emit=emit, mock=mock)
    pending = queue.Queue(maxsize=64)
    def worker():
        while not adapter.closed.is_set():
            try:
                request = pending.get(timeout=0.1)
            except queue.Empty:
                continue
            emit(adapter.handle(request))
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    def stop(*_):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while line := sys.stdin.buffer.readline(LIMIT + 1):
            try:
                if len(line) > LIMIT:
                    raise ValueError()
                request = json.loads(line)
                pending.put_nowait(request)
            except (ValueError, queue.Full):
                emit({"id": None, "ok": False, "error": {"code": "protocol", "detail": "Invalid JSON or queue full"}})
    finally:
        adapter.close()
        thread.join(timeout=3)


if __name__ == "__main__":
    serve(mock="--mock" in sys.argv)
