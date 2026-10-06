import contextlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import backend

FAKE = str(ROOT / "tests/fake_mullvad.py")


def sample(field):
    kind, name = field["kind"], field["name"]
    value = {
        "bool": True,
        "enum": (field.get("choices") or [""])[0],
        "cipher": "aes-256-gcm",
        "ip": "1.2.3.4",
        "port": "443",
        "integer": str(field.get("minimum", 1)),
        "account": "1234567890123456",
        "key": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        "location": "se",
        "city": "got",
        "cidrs": "10.0.0.0/24,::/0",
        "file": "/tmp/config.json",
        "executable": "/usr/bin/true",
        "argv": ["--help"],
        "multi": ["allow-lan"],
    }.get(kind, "example")
    if name == "v6_gateway":
        value = "::1"
    if name == "hostname":
        value = "se-got-wg-001"
    return [value] if field.get("many") and kind not in ("multi", "argv") else value


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.adapter = backend.Adapter(binary=FAKE, timeout=2, cache=None)
        self.addCleanup(self.adapter.close)

    def request(self, operation, params=None, confirmed=True):
        return self.adapter.handle(
            {"id": 1, "op": operation, "params": params or {}, "confirmed": confirmed}
        )

    def test_all_operation_arguments(self):
        for operation in backend.CATALOG:
            with self.subTest(operation=operation["id"]):
                params = {f["name"]: sample(f) for f in operation["fields"]}
                if operation["id"] == "status":
                    params["verbose"] = False
                if operation["id"].endswith("ipv6") and "address" in params:
                    params["address"] = "::1"
                argv = backend.arguments(operation, params)
                self.assertEqual(
                    argv[: len(operation["argv"])],
                    operation["argv"]
                    if operation["id"] not in ("status", "status.listen")
                    else argv[: len(operation["argv"])],
                )
                for field in operation["fields"]:
                    if field.get("flag") and (
                        field["kind"] != "bool" or params.get(field["name"])
                    ):
                        self.assertIn(field["flag"], argv)
                self.assertNotIn("sh", argv)

    def test_all_finite_operations_execute(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            source.write_text('{"settings":{"allow_lan":true}}')
            for op in backend.CATALOG:
                if op["stream"] or op["id"] == "split.launch":
                    continue
                params = {f["name"]: sample(f) for f in op["fields"]}
                if op["id"] == "status":
                    params["verbose"] = False
                if op["id"].endswith("ipv6") and "address" in params:
                    params["address"] = "::1"
                if op["id"] == "import-settings":
                    params["file"] = str(source)
                if op["id"] == "export-settings":
                    params["file"] = str(Path(directory) / "export.json")
                with self.subTest(operation=op["id"]):
                    result = self.request(op["id"], params)
                    self.assertTrue(result["ok"], result)

    def test_exclude_launcher_uses_literal_argument_array(self):
        with (
            patch("backend.shutil.which", return_value="/usr/bin/mullvad-exclude"),
            patch("backend.subprocess.Popen") as launch,
        ):
            launch.return_value.pid = 42
            launch.return_value.returncode = 0
            result = self.request(
                "split.launch",
                {
                    "executable": "/usr/bin/true",
                    "arguments": ["--arg", "literal;$(false)"],
                },
            )
            self.assertTrue(result["ok"])
            self.assertEqual(
                launch.call_args.args[0],
                [
                    "/usr/bin/mullvad-exclude",
                    "/usr/bin/true",
                    "--arg",
                    "literal;$(false)",
                ],
            )
            launch.return_value.returncode = 1
            self.assertFalse(
                self.request("split.launch", {"executable": "/usr/bin/true"})["ok"]
            )

    def test_known_argument_contracts(self):
        cases = {
            "relay.set.custom": (
                {
                    "host": "vpn.example.org",
                    "port": "51820",
                    "peer_pubkey": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
                    "tunnel_ip": ["10.0.0.2"],
                    "v4_gateway": "10.0.0.1",
                    "v6_gateway": "::1",
                },
                [
                    "relay",
                    "set",
                    "custom",
                    "vpn.example.org",
                    "51820",
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
                    "10.0.0.2",
                    "--v4-gateway",
                    "10.0.0.1",
                    "--v6-gateway",
                    "::1",
                ],
            ),
            "dns.set.custom": (
                {"servers": ["1.1.1.1", "::1"]},
                ["dns", "set", "custom", "1.1.1.1", "::1"],
            ),
            "relay.set.location": (
                {"country": "se-got-wg-001"},
                ["relay", "set", "location", "se-got-wg-001"],
            ),
            "anti-censorship.set.udp2tcp": (
                {"port": "any"},
                ["anti-censorship", "set", "udp2tcp", "--port", "any"],
            ),
            "reset-settings": (
                {"preserve": ["allow-lan", "relay-settings"]},
                [
                    "reset-settings",
                    "--preserve",
                    "allow-lan",
                    "relay-settings",
                    "--assume-yes",
                ],
            ),
            "status.listen": ({}, ["status", "--json", "listen"]),
            "status": ({"debug": True}, ["status", "--debug"]),
            "tunnel.set.allowed-ips": (
                {"allowed_ips": ""},
                ["tunnel", "set", "allowed-ips", ""],
            ),
            "api-access.add.socks5.remote": (
                {
                    "name": "Office",
                    "remote_ip": "1.2.3.4",
                    "remote_port": "1080",
                    "username": "user",
                    "password": "secret",
                    "disabled": True,
                },
                [
                    "api-access",
                    "add",
                    "socks5",
                    "remote",
                    "Office",
                    "1.2.3.4",
                    "1080",
                    "--disabled",
                    "--username",
                    "user",
                    "--password",
                    "secret",
                ],
            ),
        }
        for op, (params, expected) in cases.items():
            if op == "relay.set.custom":
                params["private_key"] = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
            with self.subTest(op=op):
                self.assertEqual(
                    backend.arguments(backend.OPERATIONS[op], params), expected
                )

    def test_custom_wireguard_private_key_only_uses_stdin(self):
        op = backend.OPERATIONS["relay.set.custom"]
        params = {f["name"]: sample(f) for f in op["fields"] if f["required"]}
        params["private_key"] = "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE="
        with patch.object(self.adapter, "run", return_value="ok") as run:
            self.assertTrue(self.request(op["id"], params)["ok"])
            self.assertNotIn(params["private_key"], run.call_args[0][0])
            self.assertEqual(
                run.call_args.kwargs["stdin"], params["private_key"] + "\n"
            )

    def test_populated_lists_custom_dns_and_proxy_redaction(self):
        proxies = "1. Direct *\n    Protocol: Socks5\n    Peer: 1.2.3.4:1080\n    Username: sample\n    Password: secret\n\n2. Other\n"
        data = backend.parse_output("api-access.list", proxies)
        self.assertEqual(len(data["entries"]), 2)
        self.assertNotIn("secret", json.dumps(data))
        self.assertNotIn("sample", json.dumps(data))
        self.assertEqual(
            backend.parse_output(
                "dns.get", "Custom DNS: yes\nServers:\n1.1.1.1\n::1\n"
            )["servers"],
            ["1.1.1.1", "::1"],
        )
        self.assertEqual(
            backend.parse_output("custom-list.list", "Work\n\tSweden\nEmpty\n")[
                "entries"
            ],
            [
                {"name": "Work", "locations": ["Sweden"]},
                {"name": "Empty", "locations": []},
            ],
        )
        self.assertEqual(
            backend.parse_output("account.get", "The current device has been revoked")[
                "text"
            ],
            "The current device has been revoked",
        )
        self.assertIn(
            "text", backend.parse_output("relay.get", "Custom endpoint: WireGuard")
        )
        exported = backend.parse_output(
            "exported-settings", '{"proxy":{"password":"secret","username":"sample"}}'
        )
        self.assertNotIn("secret", json.dumps(exported))
        self.assertNotIn("sample", json.dumps(exported))
        self.assertEqual(
            backend.status_event(
                {"relay_settings": {}, "tunnel_options": {}, "password": "secret"}
            ),
            ("daemon.changed", {"kind": "settings"}),
        )
        with self.assertRaises(backend.AdapterError):
            backend.status_event({"new_format": True})
        warning = backend.parse_output(
            "status", 'Warning: This device has been revoked.\n{"state":"error"}'
        )
        self.assertEqual(warning["state"], "error")

    def test_rejects_invalid_and_injected_parameters(self):
        cases = [
            ("account.login", {"account": "123"}),
            ("split-tunnel.add", {"pid": "-1"}),
            ("split-tunnel.add", {"pid": True}),
            ("dns.set.custom", {"servers": ["not-an-ip"]}),
            ("relay.set.location", {"country": "se", "hostname": "host"}),
            ("relay.set.provider", {"providers": ["--help"]}),
            ("api-access.enable", {"index": "0"}),
            ("tunnel.set.allowed-ips", {"allowed_ips": "10.0.0.1/24"}),
            ("relay.override.set.ipv4", {"hostname": "host", "address": "::1"}),
            (
                "api-access.add.socks5.remote",
                {
                    "name": "Proxy",
                    "remote_ip": "1.2.3.4",
                    "remote_port": "1080",
                    "password": "secret",
                },
            ),
            ("connect", {"unexpected": True}),
            ("connect", {"wait": "true"}),
            ("import-settings", {"file": "relative.json"}),
        ]
        for op, params in cases:
            with self.subTest(op=op):
                self.assertEqual(
                    self.request(op, params)["error"]["code"], "validation"
                )

    def test_literal_metacharacters_are_never_a_shell(self):
        with patch.object(self.adapter, "run", return_value="ok") as run:
            self.assertTrue(
                self.request("custom-list.new", {"name": "office;$(touch /tmp/nope)"})[
                    "ok"
                ]
            )
            self.assertEqual(run.call_args[0][0][-1], "office;$(touch /tmp/nope)")

    def test_confirmation_all_mutations(self):
        for operation in backend.CATALOG:
            if operation["confirm"]:
                params = {
                    f["name"]: sample(f) for f in operation["fields"] if f["required"]
                }
                if operation["id"].endswith("ipv6") and "address" in params:
                    params["address"] = "::1"
                with self.subTest(op=operation["id"]):
                    self.assertEqual(
                        self.request(operation["id"], params, False)["error"]["code"],
                        "confirmation",
                    )

    def test_protocol_and_unknown_operation(self):
        for request in (
            [],
            {},
            {"id": True, "op": "connect"},
            {"id": 1, "op": "status", "extra": True},
        ):
            self.assertEqual(self.adapter.handle(request)["error"]["code"], "protocol")
        self.assertEqual(self.request("shell")["error"]["code"], "operation")

    def test_init_and_version_capabilities(self):
        result = self.request("init")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["data"]["version"], "2026.5")
        self.assertTrue(result["data"]["supported"]["relay.set.custom"])
        self.adapter.supported["connect"] = False
        self.assertEqual(self.request("connect")["error"]["code"], "unsupported")

    def test_probe_cache_and_partial_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / "probe.json"
            first = backend.Adapter(binary=FAKE, timeout=2, cache=cache)
            supported = first.handle({"id": 1, "op": "init"})["data"]["supported"]
            self.assertTrue(cache.exists())
            second = backend.Adapter(binary=FAKE, timeout=2, cache=cache)
            with patch.object(second, "run", wraps=second.run) as run:
                self.assertEqual(
                    second.handle({"id": 1, "op": "init"})["data"]["supported"],
                    supported,
                )
            self.assertEqual(run.call_count, 1)  # --version only, no --help probes
        result = self.request("snapshot", {"only": ["dns.get"]})
        self.assertEqual(
            set(result["data"]), {"dns.get", "status", "exported-settings"}
        )
        self.assertEqual(
            self.request("snapshot", {"only": ["account.login"]})["error"]["code"],
            "validation",
        )

    def test_failure_timeout_missing_binary(self):
        # Generous limit for failure: a loaded machine must not turn it into a timeout.
        for mode, expected, limit in (
            ("failure", "daemon", 10),
            ("timeout", "timeout", 0.1),
        ):
            with patch.dict(backend.ENV, {"FAKE_MODE": mode}):
                self.adapter.timeout = limit
                result = self.request("status")
                self.assertEqual(result["error"]["code"], expected)
                self.assertNotIn("secret", json.dumps(result))
        self.adapter.binary = "/no/mullvad"
        self.assertEqual(self.request("status")["error"]["code"], "binary")
        self.assertEqual(len(self.adapter.processes), 0)

    def test_real_read_formats_and_changed_format(self):
        fixture = json.loads(
            (ROOT / "tests/fixtures/read-only-linux-2026.5.json").read_text()
        )
        for command, data in fixture.items():
            with self.subTest(command=command):
                parsed = backend.parse_output(command.replace(" ", "."), data["stdout"])
                self.assertIsInstance(parsed, dict)
        for command in (
            "status",
            "auto-connect.get",
            "dns.get",
            "relay.get",
            "api-access.list",
            "relay.list",
            "split-tunnel.list",
            "version",
        ):
            with self.subTest(command=command):
                with self.assertRaises(backend.AdapterError):
                    backend.parse_output(command, "format changed")
        snapshot = self.request("snapshot")
        self.assertTrue(snapshot["ok"])
        self.assertTrue(snapshot["data"]["status"]["ok"])
        self.assertEqual(snapshot["data"]["split-tunnel.list"]["data"]["pids"], [4242])

    def test_serializes_concurrent_mutations(self):
        active = 0
        maximum = 0

        def run(*args, **kwargs):
            nonlocal active, maximum
            active += 1
            maximum = max(maximum, active)
            time.sleep(0.03)
            active -= 1
            return "ok"

        with patch.object(self.adapter, "run", side_effect=run):
            threads = [
                threading.Thread(target=self.request, args=("connect",))
                for _ in range(5)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        self.assertEqual(maximum, 1)

    def test_events_log_redaction_and_cleanup(self):
        messages = []
        self.adapter.emit = messages.append
        self.assertTrue(self.request("status.listen")["ok"])
        self.assertTrue(self.request("log.listen")["ok"])
        deadline = time.monotonic() + 3
        while len(messages) < 5 and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(
            [m["data"]["state"] for m in messages if m["event"] == "status.listen"],
            ["connecting", "connected"],
        )
        self.assertNotIn("1234567890123456", json.dumps(messages))
        self.assertNotIn("secret", json.dumps(messages))
        processes = [entry[0] for entry in self.adapter.streams.values()]
        self.adapter.close()
        self.assertTrue(all(process.poll() is not None for process in processes))
        self.assertEqual(self.adapter.streams, {})

    def test_redaction_nested_and_secret_errors(self):
        raw = {
            "password": "secret",
            "nested": ["1234567890123456", "voucher-value"],
            "public_key": "secret",
        }
        result = backend.redact(raw, ["voucher-value"])
        self.assertNotIn("secret", json.dumps(result))
        self.assertNotIn("voucher-value", json.dumps(result))
        with patch.object(
            self.adapter,
            "run",
            side_effect=backend.AdapterError("command", "failed voucher-value"),
        ):
            result = self.request("account.redeem", {"voucher": "voucher-value"})
            self.assertNotIn("voucher-value", json.dumps(result))

    def test_import_export_permissions_and_no_clobber(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            result = self.request("export-settings", {"file": str(path)})
            self.assertTrue(result["ok"], result)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(
                json.loads(path.read_text()), {"settings": {"allow_lan": True}}
            )
            self.assertEqual(
                self.request("export-settings", {"file": str(path)})["error"]["code"],
                "file",
            )
            self.assertTrue(self.request("import-settings", {"file": str(path)})["ok"])
            link = Path(directory) / "symlink.json"
            link.symlink_to(path)
            self.assertFalse(self.request("import-settings", {"file": str(link)})["ok"])
            fifo = Path(directory) / "pipe"
            os.mkfifo(fifo)
            self.assertEqual(
                self.request("import-settings", {"file": str(fifo)})["error"]["code"],
                "validation",
            )
            path.write_text('["secret"]')
            self.assertEqual(
                self.request("import-settings", {"file": str(path)})["error"]["code"],
                "validation",
            )
            path.write_text('{"secret":"unterminated}')
            self.assertNotIn(
                "secret",
                json.dumps(self.request("import-settings", {"file": str(path)})),
            )

    def test_jsonl_process_roundtrip_and_shutdown(self):
        process = subprocess.Popen(
            [sys.executable, str(ROOT / "backend.py"), "--mock"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            process.stdin.write('{"id":77,"op":"status","params":{}}\n')
            process.stdin.flush()
            response = json.loads(process.stdout.readline())
            self.assertEqual(response["id"], 77)
            self.assertTrue(response["ok"])
            process.stdin.write("bad JSON\n")
            process.stdin.flush()
            self.assertEqual(
                json.loads(process.stdout.readline())["error"]["code"], "protocol"
            )
        finally:
            process.terminate()
            process.communicate(timeout=5)


if __name__ == "__main__":
    unittest.main()
