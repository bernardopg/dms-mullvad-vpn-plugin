import QtQuick
import Quickshell
import Quickshell.Io

Item {
    id: root
    property bool mock: Quickshell.env("DANK_MULLVAD_MOCK") === "1"
    property bool ready: false
    property var catalog: []
    property var supported: ({})
    property var snapshot: ({})
    property var status: ({state: "unknown"})
    property string version: ""
    property var requests: ({})
    property int serial: 0
    property var pending: null
    property var result: null
    property var logs: []
    property bool logging: false
    property bool watching: false
    readonly property bool busy: Object.keys(requests).length > 0
    signal confirmationRequired()
    signal completed(string operation, bool success)

    function request(operation, params, confirmed, quiet) {
        if (!adapter.running) {
            result = {ok: false, error: {code: "backend", detail: ""}};
            return;
        }
        const id = ++serial;
        const next = Object.assign({}, requests);
        next[id] = {operation: operation, quiet: quiet === true}; // No parameters or credentials retained in history.
        requests = next;
        adapter.write(JSON.stringify({id: id, op: operation, params: params || {}, confirmed: confirmed === true}) + "\n");
    }

    function prepare(operation, params) {
        if (!ready || busy || pending)
            return;
        const spec = catalog.find(op => op.id === operation);
        if (spec && spec.confirm) {
            pending = {operation: operation, params: params};
            confirmationRequired();
        } else {
            request(operation, params);
        }
    }

    function confirm() {
        const action = pending;
        pending = null;
        if (action)
            request(action.operation, action.params, true);
    }

    // Display-only preview; backend.py arguments() stays authoritative.
    function commandLine(operation, params) {
        const spec = catalog.find(op => op.id === operation);
        if (!spec)
            return "";
        params = params || {};
        const quote = value => /^[\w@%+=:,.\/-]+$/.test(value) ? value : "'" + value.replace(/'/g, "'\\''") + "'";
        const words = spec.id === "split.launch" ? ["mullvad-exclude"] : ["mullvad"].concat(spec.argv);
        for (const field of spec.fields) {
            const value = params[field.name];
            if (value === undefined || value === "" || value === false || (Array.isArray(value) && value.length === 0))
                continue;
            if (field.kind === "bool") {
                words.push(field.flag);
                continue;
            }
            if (field.stdin) {
                words.push("< stdin");
                continue;
            }
            const values = (Array.isArray(value) ? value : [value]).map(v => field.secret ? "••••" : quote(String(v)));
            if (field.flag && values.length === 1 && values[0].startsWith("-"))
                words.push(field.flag + "=" + values[0]);
            else
                words.push(...(field.flag ? [field.flag] : []), ...values);
        }
        if (spec.id === "factory-reset" || spec.id === "reset-settings")
            words.push("--assume-yes");
        if (spec.id === "relay.override.clear-all")
            words.push("--confirm");
        if (spec.id === "status.listen" || (spec.id === "status" && !params.verbose && !params.debug))
            words.splice(2, 0, "--json");
        return words.join(" ");
    }

    function refresh() {
        if (ready && !busy)
            request("snapshot");
    }

    function retry() {
        if (!adapter.running)
            adapter.running = true;
        else if (!busy)
            request(ready ? "snapshot" : "init");
    }

    function updateStatus(message) {
        status = message.ok ? message.data : {state: "unknown"};
        const updated = Object.assign({}, snapshot);
        updated.status = message;
        snapshot = updated;
    }

    function receive(message) {
        if (message.event) {
            if (message.event === "daemon.changed") {
                stateDebounce.restart();
            } else if (message.event === "status.listen") {
                watching = message.ok;
                updateStatus(message);
                if (!message.ok)
                    result = message;
            } else {
                if (message.ok) {
                    logs = logs.concat([message.data.text]).slice(-200);
                } else {
                    logging = false;
                    result = message;
                }
            }
            return;
        }
        const quiet = (requests[message.id] || {}).quiet === true;
        const next = Object.assign({}, requests);
        delete next[message.id];
        requests = next;
        if (message.op === "init" && message.ok) {
            catalog = message.data.catalog;
            supported = message.data.supported;
            version = message.data.version;
            ready = true;
            request("snapshot");
            request("status.listen");
        } else if (message.op === "snapshot" && message.ok) {
            snapshot = message.data;
            if (snapshot.status && snapshot.status.ok)
                status = snapshot.status.data;
            else if (snapshot.status) {
                status = ({state: "unknown"});
                result = snapshot.status;
            }
        } else if (message.op === "status" && message.ok) {
            updateStatus(message);
            if (!quiet) result = message;
        } else if (message.op === "status.listen" && message.ok) {
            watching = true;
        } else if (message.op === "log.listen" && message.ok) {
            logging = true;
        } else {
            result = message;
            if (message.op === "status" && !message.ok)
                updateStatus(message);
            const spec = catalog.find(op => op.id === message.op);
            if (spec && spec.confirm)
                request("snapshot");
            if (message.ok && spec && spec.readonly && !spec.stream) {
                const updated = Object.assign({}, snapshot);
                updated[message.op] = message;
                snapshot = updated;
            }
        }
        completed(message.op || "", message.ok);
    }

    Process {
        id: adapter
        running: true
        stdinEnabled: true
        command: ["python3", Qt.resolvedUrl("backend.py").toString().replace("file://", "")].concat(root.mock ? ["--mock"] : [])
        onStarted: root.request("init")
        stdout: SplitParser {
            onRead: line => {
                try {
                    root.receive(JSON.parse(line));
                } catch (error) {
                    root.result = {ok: false, error: {code: "protocol", detail: ""}};
                }
            }
        }
        // Never forward backend stderr: it could contain sensitive exception data.
        stderr: SplitParser { onRead: line => {} }
        onExited: {
            root.ready = false;
            root.watching = false;
            root.logging = false;
            root.requests = ({});
            root.pending = null;
            root.result = {ok: false, error: {code: "backend", detail: ""}};
        }
    }
    Timer {
        id: stateDebounce
        interval: 500
        onTriggered: { if (root.busy) restart(); else root.refresh(); }
    }
    Timer {
        interval: 30000
        repeat: true
        running: root.ready
        onTriggered: {
            if (!root.busy) {
                root.request("status", {}, false, true);
                if (!root.watching)
                    root.request("status.listen");
            }
        }
    }
    Component.onDestruction: {
        pending = null;
        adapter.running = false;
    }
}
