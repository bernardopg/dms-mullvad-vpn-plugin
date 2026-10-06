#!/usr/bin/env python3
"""Test real DMS imports and interactions in an isolated Wayland instance."""
import os
import shutil
import subprocess
import tempfile
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from test_backend import sample


def find_dms():
    candidates = list(Path(os.environ.get("XDG_RUNTIME_DIR", "/run/user/1000")).glob("danklinux-shell/*"))
    candidates.extend([Path.home() / ".config/quickshell/dms", Path("/usr/share/dms/quickshell")])
    override = os.environ.get("DMS_QML_ROOT")
    if override:
        candidates.insert(0, Path(override))
    for path in candidates:
        version = path / "VERSION"
        if version.exists() and (path / "Modules/Plugins/PluginComponent.qml").exists():
            return path
    raise SystemExit("DMS QML root not found; set DMS_QML_ROOT to DMS 1.6.2 or newer")


def run():
    dms = find_dms()
    if not shutil.which("quickshell"):
        raise SystemExit("quickshell is required for the QML runtime check")
    with tempfile.TemporaryDirectory(prefix="mullvad-qml-") as directory:
        target = Path(directory)
        # qs.* resolves relative to this shell; reuse actual modules, not stubs.
        for child in dms.iterdir():
            if child.name != "shell.qml":
                (target / child.name).symlink_to(child)
        (target / "Plugin").symlink_to(ROOT)
        artifacts = ROOT / "test-results"
        artifacts.mkdir(exist_ok=True)
        catalog = json.loads((ROOT / "operations.json").read_text())
        samples = {}
        for operation in catalog:
            samples[operation["id"]] = {field["name"]: sample(field) for field in operation["fields"]}
            if operation["id"].endswith("ipv6") and "address" in samples[operation["id"]]:
                samples[operation["id"]]["address"] = "::1"
        shell = '''import QtQuick
import QtQuick.Controls
import QtTest
import Quickshell
import qs.Common
import qs.DankCommon.Common as DC
import qs.Plugin

ShellRoot {
    Component.onCompleted: {
        DC.Style.theme = Theme;
        DC.Style.settings = SettingsData;
        DC.I18n.backend = I18n;
    }
    PanelWindow {
        id: bar
        anchors { top: true; left: true; right: true }
        exclusionMode: ExclusionMode.Ignore
        implicitHeight: 48
        color: Theme.surface
        MullvadWidget {
            id: widget
            x: 16
            anchors.verticalCenter: parent.verticalCenter
            pluginId: "dankMullvadVpn"
            parentScreen: bar.screen
            axis: QtObject { property bool isVertical: false; property string edge: "top" }
        }
    }
    TestCase { id: input; parent: widget.window.surfaceItem; when: false }
    MullvadSettings { id: preferences }
    Loader { id: horizontal; sourceComponent: widget.horizontalBarPill }
    Loader { id: vertical; sourceComponent: widget.verticalBarPill }
    Loader { id: popout; sourceComponent: widget.popoutContent }
    Connections {
        target: widget.backend
        function onCompleted(operation, success) {
            if (!success) { console.error("SMOKE operation failed", operation); Qt.quit(); }
        }
    }
    property int step: 0
    property int ticks: 0
    property int phase: 0
    property int navigation: 0
    property bool checking: false
    property bool compactCaptured: false
    function expect(condition, detail) {
        if (!condition) { console.error("SMOKE navigation", detail); Qt.quit(); return false; }
        return true;
    }
    property var samples: SAMPLES
    Timer {
        interval: 15
        repeat: true
        running: true
        onTriggered: {
            if (checking) return;
            checking = true;
            try {
                ticks++;
                if (ticks > 3300) { console.error("SMOKE TIMEOUT"); Qt.quit(); return; }
                if (!widget.backend.ready || widget.backend.busy || !widget.i18n.ready) return;
                if (navigation < 12) {
                    switch (navigation) {
                    case 0:
                        widget.i18n.language = "en"; // Deterministic screenshots for the README.
                        input.mouseClick(widget, widget.width / 2, widget.height / 2, Qt.RightButton);
                        if (!expect(widget.window.visible && !widget.window.preferences, "right-click opens window")) return;
                        widget.window.close();
                        input.mouseClick(widget, widget.width / 2, widget.height / 2, Qt.LeftButton);
                        break;
                    case 1:
                        const openButton = input.findChild(widget, "popoutOpenWindow");
                        if (!expect(openButton && openButton.visible && openButton.width > 0, "bar opens summary")) return;
                        input.mouseClick(openButton, openButton.width / 2, openButton.height / 2);
                        if (!expect(widget.window.visible, "summary opens full window")) return;
                        widget.window.searchField.text = "daita";
                        break;
                    case 2:
                        if (!expect(widget.window.operations.length > 0 && widget.window.operations.every(op => op.id.includes("daita")), "global search")) return;
                        if (!expect(widget.window.operationForm.command === "mullvad tunnel set daita on", "preview shows required enum default")) return;
                        widget.window.searchField.text = "no-such-function-xyz";
                        break;
                    case 3:
                        if (!expect(widget.window.operation === null, "empty search")) return;
                        const serial = widget.backend.serial;
                        widget.window.operationForm.submit();
                        if (!expect(widget.backend.serial === serial, "empty form cannot submit")) return;
                        widget.window.searchField.text = "";
                        widget.window.section = "account";
                        widget.window.operationIndex = widget.window.operations.findIndex(op => op.id === "account.login");
                        break;
                    case 4:
                        widget.window.operationForm.setValue("account", "1234567890123456");
                        widget.window.operationForm.submit();
                        break;
                    case 5:
                        if (!expect(widget.backend.pending && widget.window.confirmationDialog.visible && widget.window.confirmationDialog.height > 160, "modal confirmation")) return;
                        widget.window.confirmationDialog.contentItem.parent.grabToImage(result => result.saveToFile(ARTIFACTS + "/confirmation.png"));
                        input.mouseClick(widget.window.confirmationDialog.contentItem, 20, 20);
                        input.wait(50);
                        const cancel = input.findChild(widget.window.surfaceItem, "confirmationCancel");
                        const confirm = input.findChild(widget.window.surfaceItem, "confirmationExecute");
                        if (!expect(cancel && confirm, "confirmation controls")) return;
                        cancel.forceActiveFocus();
                        input.keyClick(Qt.Key_Tab);
                        if (!expect(confirm.activeFocus, "Tab stays in confirmation")) return;
                        input.keyClick(Qt.Key_Tab);
                        if (!expect(cancel.activeFocus, "confirmation focus wraps")) return;
                        input.keyClick(Qt.Key_Escape);
                        input.wait(200);
                        if (!expect(!widget.backend.pending, "Escape cancels")) return;
                        widget.window.preferences = true;
                        widget.window.surfaceItem.forceActiveFocus();
                        input.keyClick(Qt.Key_F, Qt.ControlModifier);
                        if (!expect(widget.window.searchField.getActiveFocus() && !widget.window.preferences, "Ctrl+F focuses search")) return;
                        widget.backend.prepare("disconnect", {});
                        widget.window.close();
                        if (!expect(!widget.backend.pending && Object.keys(widget.window.operationForm.values).length === 0, "close discards pending action and fields")) return;
                        widget.openPreferences();
                        break;
                    case 6:
                        if (!expect(widget.window.visible && widget.window.preferences, "preferences entry point")) return;
                        widget.openWindow();
                        if (!expect(!widget.window.preferences, "ordinary open leaves preferences")) return;
                        widget.backend.receive({event: "status.listen", ok: true, data: {state: "connecting"}});
                        if (!expect(widget.backend.snapshot.status.data.state === "connecting", "live status updates current settings")) return;
                        widget.quickToggle();
                        if (!expect(!widget.backend.pending, "transition disables quick connect")) return;
                        widget.backend.receive({event: "status.listen", ok: true, data: {state: "connected", details: {location: {city: "Fortaleza", country: "Brazil"}}}});
                        widget.quickToggle();
                        break;
                    case 7:
                        if (!expect(widget.backend.pending && widget.backend.pending.operation === "disconnect", "quick toggle requires confirmation")) return;
                        widget.backend.pending = null;
                        // Constrain the rendered surface independently of compositor tiling policies.
                        widget.window.surfaceItem.anchors.fill = null;
                        widget.window.surfaceItem.width = 640;
                        widget.window.surfaceItem.height = 700;
                        break;
                    case 8:
                        break; // Let the compositor deliver the constrained size.
                    case 9:
                        if (!expect(widget.window.compact, "compact window")) return;
                        widget.window.surfaceItem.grabToImage(result => {
                            result.saveToFile(ARTIFACTS + "/compact.png");
                            compactCaptured = true;
                        });
                        break;
                    case 10:
                        if (!compactCaptured) return;
                        widget.window.surfaceItem.anchors.fill = widget.window.surfaceItem.parent;
                        widget.window.section = "connection";
                        widget.window.close();
                        widget.triggerPopout();
                        break;
                    case 11:
                        widget.openWindow();
                        widget.backend.result = null;
                        widget.backend.request("status", {}, false, true);
                        console.log("SMOKE NAVIGATION PASS");
                        break;
                    }
                    navigation++;
                    return;
                }
                if (step === 0) {
                    if (!expect(widget.backend.result === null, "background status preserves operation results")) return;
                    console.log("SMOKE READY", widget.backend.catalog.length);
                }
                if (step < widget.backend.catalog.length * 4) {
                    const op = widget.backend.catalog[step % widget.backend.catalog.length];
                    widget.i18n.language = Math.floor(step / widget.backend.catalog.length) % 2 ? "pt-BR" : "en";
                    Theme.isLightMode = Math.floor(step / (widget.backend.catalog.length * 2)) % 2 === 1;
                    widget.window.section = op.section;
                    widget.window.operationIndex = widget.window.operations.findIndex(item => item.id === op.id);
                    if (phase === 0) { phase = 1; return; }
                    if (step % widget.backend.catalog.length === 0) {
                        const variant = Math.floor(step / widget.backend.catalog.length);
                        widget.window.surfaceItem.grabToImage(function(result) { result.saveToFile(ARTIFACTS + "/window-" + variant + ".png"); });
                    }
                    const form = widget.window.operationForm;
                    if (!form.operation || form.operation.id !== op.id) { console.error("SMOKE form mismatch"); Qt.quit(); return; }
                    for (const field of op.fields) {
                        const value = samples[op.id][field.name];
                        form.setValue(field.name, field.kind === "argv" ? JSON.stringify(value) : field.many && field.kind !== "multi" ? value.join(" ") : value);
                    }
                    form.submit();
                    if (form.validation) { console.error("SMOKE validation", op.id, form.validation); Qt.quit(); return; }
                    for (const field of op.fields) {
                        if (field.secret && form.values[field.name] !== "") { console.error("SMOKE credentials retained"); Qt.quit(); return; }
                    }
                    if (op.confirm) {
                        if (!widget.backend.pending) { console.error("SMOKE confirmation missing", op.id); Qt.quit(); return; }
                        widget.backend.confirm();
                    }
                    phase = 0;
                    step++;
                    return;
                }
                if (step === widget.backend.catalog.length * 4) {
                    widget.backend.prepare("disconnect", {});
                    step++;
                    return;
                }
                if (!widget.backend.pending) { console.error("SMOKE confirmation missing"); Qt.quit(); return; }
                widget.backend.pending = null;
                widget.window.openSettings();
                console.log("SMOKE PASS", step);
                Qt.quit();
            } finally { checking = false; }
        }
    }
}'''
        (target / "shell.qml").write_text(shell.replace("SAMPLES", json.dumps(samples)).replace("ARTIFACTS", json.dumps(str(artifacts))))
        runtime = target / "runtime"
        runtime.mkdir(mode=0o700)
        original_runtime = os.environ.get("XDG_RUNTIME_DIR", "/run/user/1000")
        sockets = [path for path in Path(original_runtime).glob("wayland-*") if path.is_socket()]
        display = os.environ.get("WAYLAND_DISPLAY") or (str(sockets[0]) if sockets else "wayland-0")
        display = display if display.startswith("/") else str(Path(original_runtime) / display)
        env = {**os.environ, "QT_QPA_PLATFORM": "wayland", "WAYLAND_DISPLAY": display, "XDG_RUNTIME_DIR": str(runtime), "HOME": str(target), "XDG_CONFIG_HOME": str(target / "config"), "XDG_CACHE_HOME": str(target / "cache"), "XDG_DATA_HOME": str(target / "data"), "QT_QUICK_BACKEND": "software", "DANK_MULLVAD_MOCK": "1", "QML_XHR_ALLOW_FILE_READ": "1", "QT_LOGGING_RULES": "qml.debug=true"}  # SMOKE markers are console.log output.
        result = subprocess.run(["quickshell", "--path", str(target / "shell.qml"), "--no-color"], env=env, capture_output=True, text=True, timeout=55)
        output = result.stdout + result.stderr
        print(output)
        errors = ("TypeError:", "ReferenceError:", "is not a type", "Cannot assign", "Unable to assign", "Cannot load", "Error:", "Binding loop", "SMOKE TIMEOUT", "SMOKE confirmation", "SMOKE form mismatch", "SMOKE validation", "SMOKE credentials retained", "SMOKE operation failed", "SMOKE navigation")
        if result.returncode or "SMOKE PASS" not in output or "SMOKE NAVIGATION PASS" not in output or any(error in output for error in errors):
            raise SystemExit(1)
        print("QML runtime passed with real DMS imports:", dms, (dms / "VERSION").read_text().strip())


if __name__ == "__main__":
    run()
