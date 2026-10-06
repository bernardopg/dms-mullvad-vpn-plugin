#!/usr/bin/env python3
"""Portable contract checks, without third-party dependencies."""

import json
import re
from pathlib import Path
from build_catalog import build
from build_matrix import matrix

ROOT = Path(__file__).resolve().parents[1]


def verify():
    manifest = json.loads((ROOT / "plugin.json").read_text())
    assert manifest["id"] == "dankMullvadVpn"
    assert manifest["type"] == "widget"
    assert manifest["capabilities"] == ["dankbar-widget"]
    assert manifest["requires_dms"] == ">=1.6.2"
    for field in ("component", "settings"):
        assert (ROOT / manifest[field]).is_file()
    assert set(manifest["permissions"]) == {
        "settings_read",
        "settings_write",
        "process",
        "network",
    }
    catalog = json.loads((ROOT / "operations.json").read_text())
    assert catalog == build(), "registry differs from its reviewed generator"
    ids = [op["id"] for op in catalog]
    assert len(set(ids)) == len(ids)
    tree = json.loads((ROOT / "tests/fixtures/cli-help-2026.5.json").read_text())
    leaves = {
        path.replace(" ", ".")
        for path, help_text in tree.items()
        if "Commands:" not in help_text
    }
    assert set(ids) == leaves | {"status", "cli.version", "split.launch"}
    for op in catalog:
        assert len({f["name"] for f in op["fields"]}) == len(op["fields"])
        assert op["state"] in ids
        if op["id"] in ("split.launch", "cli.version"):
            continue
        flags = set(re.findall(r"--([a-z0-9-]+)", tree[" ".join(op["argv"])]))
        mapped = {field["flag"][2:] for field in op["fields"] if field.get("flag")}
        assert flags - mapped <= {"help", "version", "json", "assume-yes", "confirm"}, (
            op["id"],
            flags - mapped,
        )
    en = json.loads((ROOT / "i18n/en.json").read_text())
    pt = json.loads((ROOT / "i18n/pt-BR.json").read_text())
    assert en.keys() == pt.keys(), "translation keys differ"
    for key in en:
        assert en[key] and pt[key], key
        assert set(re.findall(r"\{\w+\}", en[key])) == set(
            re.findall(r"\{\w+\}", pt[key])
        ), key
    for op in catalog:
        assert op["label"] in en
        assert "section." + op["section"] in en
        for field in op["fields"]:
            assert field["label"] in en
            if field["kind"] not in ("bool", "enum", "multi"):
                assert "hint." + field["kind"] in en
    for file in ROOT.glob("*.qml"):
        for key in re.findall(r'\.tr\("([a-z][a-z.]+)"[,)\s]', file.read_text()):
            if not key.endswith("."):
                assert key in en, (file.name, key)
    assert (ROOT / "docs/matriz-cli.md").read_text() == matrix(), (
        "run scripts/build_matrix.py"
    )
    guidelines = (ROOT / "AGENTS.md").read_text()
    assert guidelines.startswith("# Repository Guidelines")
    assert 200 <= len(guidelines.split()) <= 400
    widget = (ROOT / "MullvadEngine.qml").read_text()
    for command in ("toggle", "open", "settings"):
        assert "function " + command + "(): void" in widget
    print(
        f"Contracts passed: {len(catalog)} forms, all 2026.5 commands/options, {len(en)} translation keys"
    )


if __name__ == "__main__":
    verify()
