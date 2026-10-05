#!/usr/bin/env python3
"""Build the reviewed 2026.5 form catalog from the read-only help snapshot."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build():
    tree = json.loads((ROOT / "tests/fixtures/cli-help-2026.5.json").read_text())
    catalog = []
    for path, help_text in tree.items():
        if "Commands:" in help_text and path != "status":
            continue
        fields = []
        usage = re.search(r"Usage: ([^\n]+)", help_text)[1]
        arguments = help_text.split("Arguments:\n")
        if len(arguments) > 1:
            for match in re.finditer(r"^  ([<\[])([A-Z_]+)[>\]](\.\.\.)?", arguments[1].split("Options:")[0], re.M):
                name = match[2].lower()
                # Both location syntaxes use a single country/hostname input.
                required = match[1] == "<"
                fields.append(dict(name=name, kind="text", required=required, many=bool(match[3])))
        options = help_text.split("Options:\n")[-1]
        for match in re.finditer(r"^\s+(?:-[a-zA-Z], )?--([a-z0-9-]+)(?: ([^\n]*))?", options, re.M):
            flag, remainder = match[1], match[2] or ""
            if flag in ("help", "version", "assume-yes", "confirm", "json"):
                continue
            name = flag.replace("-", "_")
            boolean = "<" not in remainder
            required = bool(re.search(r"(?<!\[)--" + flag + r" <", usage))
            fields.append(dict(name=name, kind="bool" if boolean else "text", required=required, flag="--" + flag, many="..." in remainder))
        for field in fields:
            name = field["name"]
            enums = re.search(r"\[possible values: ([^\]]+)\]", help_text)
            if enums and field.get("flag") is None and len([f for f in fields if not f.get("flag")]) == 1:
                field.update(kind="enum", choices=enums[1].split(", "))
            if name in ("ip", "remote_ip", "address", "v4_gateway", "v6_gateway", "servers", "tunnel_ip"):
                field["kind"] = "ip"
            if name in ("port", "remote_port", "local_port"):
                field.update(kind="port", allow_any="'any'" in help_text)
            if name == "pid":
                field.update(kind="integer", minimum=1, maximum=2147483647)
            if name == "index":
                field.update(kind="integer", minimum=1, maximum=100000)
            if name == "mtu":
                field.update(kind="integer", minimum=0, maximum=65535, allow_any=True)
            if name == "interval":
                field.update(kind="integer", minimum=24, maximum=720, allow_any=True)
            if name == "account":
                field.update(kind="account", secret=True, required=not bool(field.get("flag")))
            if name in ("password", "voucher", "username"):
                field["secret"] = True
            if name == "allowed_ips":
                field.update(kind="cidrs", allow_empty=True)
            if name == "peer_pubkey":
                field["kind"] = "key"
            if name == "transport_protocol":
                field.update(kind="enum", choices=["TCP", "UDP"])
            if name == "ownership":
                field.update(kind="enum", choices=["any", "owned", "rented"])
            if name == "ip_version":
                field.update(kind="enum", choices=["any", "ipv4", "ipv6"])
            if name == "level":
                field.update(kind="enum", choices=["off", "error", "warn", "info", "debug", "trace"])
            if name == "preserve":
                field.update(kind="multi", choices=["relay-settings", "anti-censorship", "custom-lists", "api-access", "update-default-location", "allow-lan", "lockdown-mode", "auto-connect", "tunnel-options", "relay-overrides", "show-beta-releases", "recents"])
            if name == "country":
                field["kind"] = "location"
            if name == "city":
                field["kind"] = "city"
            if name == "file":
                field["kind"] = "file"
            if name == "cipher":
                field.update(kind="cipher")
            if (path == "custom-list new" and name == "name") or (path == "custom-list edit rename" and name == "new_name"):
                field.update(max_length=30)
            if path == "api-access add socks5 remote" and name in ("username", "password"):
                field["max_bytes"] = 255
            field["label"] = "field." + name
        if path == "relay set custom":
            fields.append(dict(name="private_key", kind="key", required=True, secret=True, stdin=True, label="field.private_key"))
        if path.startswith("anti-censorship set ") and path != "anti-censorship set mode":
            for field in fields:
                if field["name"] == "port": field["allow_any"] = True
        section = {"account": "account", "relay": "servers", "custom-list": "servers", "tunnel": "tunnel", "anti-censorship": "tunnel", "dns": "network", "lan": "network", "lockdown-mode": "network", "auto-connect": "connection", "split-tunnel": "split", "api-access": "api"}.get(path.split()[0], "maintenance")
        if path in ("connect", "disconnect", "reconnect", "status", "status listen"):
            section = "connection"
        readonly = path.endswith((" get", " list", "list-devices", " test")) or path in ("status", "version", "export-settings")
        stream = path in ("status listen", "log listen")
        catalog.append(dict(id=path.replace(" ", "."), argv=path.split(), section=section, fields=fields, readonly=readonly or stream, stream=stream, confirm=not (readonly or stream), label="op." + path.replace(" ", "."), help=help_text, state={"servers":"relay.get", "account":"account.get", "tunnel":"tunnel.get", "network":"dns.get", "split":"split-tunnel.list", "api":"api-access.list", "connection":"status", "maintenance":"version"}[section]))
    catalog.append(dict(id="split.launch", argv=[], section="split", fields=[dict(name="executable", kind="executable", required=True, label="field.executable"), dict(name="arguments", kind="argv", required=False, label="field.arguments")], readonly=False, confirm=True, stream=False, label="op.split.launch", state="split-tunnel.list", help="mullvad-exclude <executable> [arguments…]"))
    catalog.append(dict(id="cli.version", argv=["--version"], section="maintenance", fields=[], readonly=True, confirm=False, stream=False, label="op.cli.version", state="version", help="mullvad --version"))
    return catalog


if __name__ == "__main__":
    (ROOT / "operations.json").write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n")
