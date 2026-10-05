import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import Quickshell
import qs.Common
import qs.Widgets

FloatingWindow {
    id: root
    required property var engine
    required property var translations
    property var widgetRoot: null
    property string section: "connection"
    property int operationIndex: 0
    property bool preferences: false
    property string outputTab: "result"
    property alias operationForm: form
    property alias surfaceItem: content
    property alias searchField: search
    property alias confirmationDialog: confirmation
    readonly property bool compact: content.width < 820
    readonly property var sections: ["connection", "account", "servers", "tunnel", "network", "split", "api", "maintenance"]
    readonly property var sectionIcons: ["power_settings_new", "account_circle", "public", "shield", "dns", "call_split", "cloud", "build"]
    readonly property string query: search.text.trim().toLocaleLowerCase()
    readonly property var operations: engine.catalog.filter(op => query ? (translations.tr(op.label) + " " + translations.tr("section." + op.section) + " " + op.id + " " + op.argv.join(" ")).toLocaleLowerCase().includes(query) : op.section === section)
    readonly property var operation: operations[operationIndex] || null
    readonly property var currentRead: operation ? engine.snapshot[operation.state] : null
    readonly property var details: engine.status.details || {}
    readonly property var location: details.location || {}
    readonly property string vpnState: engine.status.state || "unknown"
    readonly property bool connected: vpnState === "connected"
    readonly property bool changing: ["connecting", "disconnecting"].includes(vpnState)
    readonly property color statusColor: vpnState === "error" ? Theme.error : connected ? Theme.success : changing ? Theme.warning : Theme.surfaceVariantText
    readonly property string locationText: [location.city, location.country].filter(Boolean).join(", ") || translations.tr("location.unavailable")
    readonly property string technicalText: [location.hostname, location.ipv4, location.ipv6, (details.endpoint || {}).tunnel_type].filter(v => typeof v === "string" && v).join("  ·  ")
    readonly property var outputTabs: ["result", "current", "settings", "help"].concat(engine.logs.length > 0 || (operation && operation.id === "log.listen") ? ["logs"] : [])
    readonly property string outputText: {
        const show = entry => entry ? (entry.ok ? (entry.data.text || JSON.stringify(entry.data, null, 2)) : translations.tr("error." + entry.error.code) + (entry.error.detail ? "\n" + entry.error.detail : "")) : translations.tr("loading");
        switch (outputTab) {
        case "current": return show(currentRead);
        case "settings": {
            const settings = engine.snapshot["exported-settings"];
            return settings && settings.ok ? JSON.stringify(settings.data, null, 2) : show(settings);
        }
        case "help": return operation ? operation.help : "";
        case "logs": return engine.logs.join("\n");
        default: return engine.result ? show(engine.result) : "";
        }
    }
    visible: false
    title: "Dank Mullvad VPN"
    implicitWidth: 1080
    implicitHeight: 800
    minimumSize: Qt.size(520, 480)
    color: Theme.surface
    onClosed: close()

    onSectionChanged: operationIndex = 0
    onQueryChanged: operationIndex = 0
    onOutputTabsChanged: if (!outputTabs.includes(outputTab)) outputTab = "result"
    onVisibleChanged: {
        if (!visible) {
            engine.pending = null;
            form.values = ({});
        }
    }
    function openSettings() {
        preferences = true;
        open();
        Qt.callLater(() => language.forceActiveFocus());
    }
    function open() {
        visible = true;
        Qt.callLater(() => {
            if (content.Window.window) content.Window.window.requestActivate();
            if (engine.pending) confirmation.open();
            else if (!preferences) search.forceActiveFocus();
        });
    }
    function close() { visible = false; }
    function toggleConnection() {
        if (engine.ready && !engine.busy && !changing)
            engine.prepare(connected ? "disconnect" : "connect", {});
    }
    function selectSection(name) {
        search.text = "";
        section = name;
        preferences = false;
    }
    function moveSelection(step) {
        if (operations.length)
            operationIndex = (operationIndex + step + operations.length) % operations.length;
    }

    Connections {
        target: root.engine
        function onResultChanged() { if (root.engine.result) root.outputTab = "result"; }
        function onPendingChanged() {
            if (root.engine.pending && root.visible) confirmation.open();
            else if (!root.engine.pending) confirmation.close();
        }
    }

    component NavRow: StyledRect {
        id: row
        property string iconName: ""
        property string text: ""
        property string trailing: ""
        property bool selected: false
        property bool child: false
        property bool dimmed: false
        property string chevron: ""
        signal activated()
        Layout.fillWidth: true
        implicitHeight: child ? 34 : 40
        radius: Theme.cornerRadius
        color: selected ? Theme.primarySelected : "transparent"
        border.width: activeFocus ? 2 : 0
        border.color: Theme.primary
        opacity: dimmed ? 0.5 : 1
        activeFocusOnTab: true
        Accessible.role: Accessible.Button
        Accessible.name: text
        Accessible.selected: selected
        Keys.onReturnPressed: activated()
        Keys.onEnterPressed: activated()
        Keys.onSpacePressed: activated()
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: row.child ? Theme.spacingXL + Theme.spacingS : Theme.spacingS
            anchors.rightMargin: Theme.spacingS
            spacing: Theme.spacingS
            DankIcon {
                name: row.iconName
                size: row.child ? 16 : 20
                color: row.selected ? Theme.primary : Theme.surfaceVariantText
            }
            StyledText {
                Layout.fillWidth: true
                text: row.text
                elide: Text.ElideRight
                wrapMode: Text.NoWrap
                color: row.selected ? Theme.primary : Theme.surfaceText
                font.pixelSize: row.child ? Theme.fontSizeSmall + 1 : Theme.fontSizeMedium
                font.weight: row.child && !row.selected ? Font.Normal : Font.Medium
            }
            StyledText {
                visible: row.trailing !== ""
                text: row.trailing
                color: Theme.surfaceVariantText
                font.pixelSize: Theme.fontSizeSmall
            }
            DankIcon {
                visible: row.chevron !== ""
                name: row.chevron
                size: 18
                color: Theme.surfaceVariantText
            }
        }
        StateLayer { stateColor: Theme.primary; onClicked: row.activated() }
    }

    component Panel: StyledRect {
        radius: Theme.cornerRadius
        color: Theme.surfaceContainer
        border.width: 1
        border.color: Theme.outlineStrong
    }

    Control {
        id: content
        anchors.fill: parent
        property bool disablePopupTransparency: true
        background: Rectangle { color: Theme.surface }
        font.pixelSize: Theme.fontSizeMedium
        palette.window: Theme.surface
        palette.windowText: Theme.surfaceText
        palette.base: Theme.surfaceContainerHigh
        palette.text: Theme.surfaceText
        palette.button: Theme.surfaceContainerHigh
        palette.buttonText: Theme.surfaceText
        palette.highlight: Theme.primary
        palette.highlightedText: Theme.primaryText
        Keys.onEscapePressed: {
            if (root.engine.pending) root.engine.pending = null;
            else if (root.preferences) root.preferences = false;
            else root.close();
        }
        Keys.onPressed: event => {
            if (root.engine.pending || !(event.modifiers & Qt.ControlModifier)) return;
            if (event.key === Qt.Key_F) {
                root.preferences = false;
                search.forceActiveFocus();
                event.accepted = true;
            } else if (event.key === Qt.Key_R && !root.engine.busy) {
                root.engine.retry();
                event.accepted = true;
            } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                form.submit();
                event.accepted = true;
            }
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: root.compact ? Theme.spacingM : Theme.spacingL
            spacing: Theme.spacingM

            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.spacingS
                DankIcon { name: "vpn_lock"; size: 26; color: Theme.primary }
                StyledText {
                    text: "Mullvad VPN"
                    font.pixelSize: Theme.fontSizeLarge
                    font.weight: Font.Medium
                    color: Theme.surfaceText
                }
                StyledRect {
                    visible: root.engine.mock
                    implicitWidth: mockLabel.implicitWidth + Theme.spacingM
                    implicitHeight: 22
                    radius: height / 2
                    color: Theme.withAlpha(Theme.warning, 0.16)
                    StyledText { id: mockLabel; anchors.centerIn: parent; text: root.translations.tr("badge.simulation"); color: Theme.warning; font.pixelSize: Theme.fontSizeSmall; font.weight: Font.Medium }
                }
                StyledText {
                    Layout.fillWidth: true
                    text: root.engine.version ? "CLI " + root.engine.version : ""
                    isMonospace: true
                    font.pixelSize: Theme.fontSizeSmall
                    color: Theme.surfaceVariantText
                    elide: Text.ElideRight
                }
                DankSpinner {
                    visible: root.engine.busy
                    size: 20
                    Accessible.name: root.translations.tr("loading")
                }
                DankActionButton {
                    iconName: "refresh"
                    enabled: !root.engine.busy
                    tooltipText: root.translations.tr("refresh") + " (Ctrl+R)"
                    onClicked: root.engine.retry()
                    Accessible.name: root.translations.tr("refresh")
                }
                DankActionButton {
                    iconName: "settings"
                    iconColor: root.preferences ? Theme.primary : Theme.surfaceText
                    backgroundColor: root.preferences ? Theme.primarySelected : "transparent"
                    tooltipText: root.translations.tr("settings")
                    onClicked: root.preferences = !root.preferences
                    Accessible.name: root.translations.tr("settings")
                }
                DankActionButton {
                    iconName: "close"
                    tooltipText: root.translations.tr("close") + " (Esc)"
                    onClicked: root.close()
                    Accessible.name: root.translations.tr("close")
                }
            }

            Panel {
                Layout.fillWidth: true
                implicitHeight: summary.implicitHeight + Theme.spacingM * 2
                RowLayout {
                    id: summary
                    anchors.fill: parent
                    anchors.margins: Theme.spacingM
                    spacing: Theme.spacingM
                    StyledRect {
                        implicitWidth: root.compact ? 44 : 52
                        implicitHeight: implicitWidth
                        radius: width / 2
                        color: Theme.withAlpha(root.statusColor, 0.16)
                        DankIcon {
                            anchors.centerIn: parent
                            name: root.connected ? "vpn_lock" : root.vpnState === "error" ? "error" : root.changing ? "sync" : "vpn_lock_off"
                            size: root.compact ? 24 : 28
                            color: root.statusColor
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        StyledText {
                            Layout.fillWidth: true
                            text: root.translations.tr("state." + root.vpnState)
                            color: root.statusColor === Theme.surfaceVariantText ? Theme.surfaceText : root.statusColor
                            font.pixelSize: Theme.fontSizeLarge
                            font.weight: Font.Bold
                            wrapMode: Text.Wrap
                            Accessible.role: Accessible.StatusBar
                        }
                        StyledText {
                            Layout.fillWidth: true
                            text: root.locationText
                            color: Theme.surfaceText
                            wrapMode: Text.Wrap
                        }
                        StyledText {
                            Layout.fillWidth: true
                            visible: text !== ""
                            text: root.technicalText
                            isMonospace: true
                            color: Theme.surfaceVariantText
                            font.pixelSize: Theme.fontSizeSmall
                            elide: Text.ElideRight
                        }
                        StyledText {
                            Layout.fillWidth: true
                            text: root.translations.tr(root.engine.mock ? "mock.notice" : "status.notice", {version: root.engine.version || "—"})
                            color: Theme.surfaceVariantText
                            font.pixelSize: Theme.fontSizeSmall
                            wrapMode: Text.Wrap
                        }
                    }
                    DankActionButton {
                        visible: root.connected && !root.compact
                        iconName: "autorenew"
                        buttonSize: 40
                        enabled: root.engine.ready && !root.engine.busy && !root.engine.pending
                        tooltipText: root.translations.tr("op.reconnect")
                        onClicked: root.engine.prepare("reconnect", {})
                        Accessible.name: root.translations.tr("op.reconnect")
                    }
                    MullvadButton {
                        objectName: "connectionToggle"
                        text: root.translations.tr(root.connected || root.vpnState === "connecting" ? "op.disconnect" : "op.connect")
                        iconName: "power_settings_new"
                        backgroundColor: root.connected ? Theme.surfaceContainerHighest : Theme.primary
                        textColor: root.connected ? Theme.error : Theme.primaryText
                        enabled: root.engine.ready && !root.engine.busy && !root.changing && !root.engine.pending
                        onClicked: root.toggleConnection()
                        Accessible.name: text
                        ToolTip.visible: hovered
                        ToolTip.text: root.translations.tr("execute.tip")
                    }
                }
            }

            Panel {
                visible: root.preferences
                Layout.fillWidth: true
                implicitHeight: preferenceContent.implicitHeight + Theme.spacingM * 2
                ColumnLayout {
                    id: preferenceContent
                    anchors.fill: parent
                    anchors.margins: Theme.spacingM
                    spacing: Theme.spacingS
                    StyledText {
                        text: root.translations.tr("settings")
                        font.weight: Font.Medium
                        color: Theme.surfaceText
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Theme.spacingM
                        StyledText { text: root.translations.tr("language"); color: Theme.surfaceText }
                        DankDropdown {
                            id: language
                            Layout.fillWidth: true
                            options: [root.translations.tr("language.auto"), "English", "Português (Brasil)"]
                            currentValue: options[Math.max(0, ["auto", "en", "pt-BR"].indexOf(root.translations.language))]
                            onValueChanged: value => {
                                const code = ["auto", "en", "pt-BR"][options.indexOf(value)];
                                if (root.widgetRoot && root.widgetRoot.pluginService)
                                    root.widgetRoot.pluginService.savePluginData("dankMullvadVpn", "language", code);
                                else root.translations.language = code;
                            }
                            Accessible.name: root.translations.tr("language")
                        }
                    }
                    DankToggle {
                        Layout.fillWidth: true
                        text: root.translations.tr("location.show")
                        checked: root.widgetRoot ? root.widgetRoot.showLocation : true
                        enabled: !!(root.widgetRoot && root.widgetRoot.pluginService)
                        onToggled: checked => root.widgetRoot.pluginService.savePluginData("dankMullvadVpn", "showLocation", checked)
                        Accessible.name: text
                    }
                    StyledText {
                        Layout.fillWidth: true
                        text: root.translations.tr("settings.notice")
                        color: Theme.surfaceVariantText
                        font.pixelSize: Theme.fontSizeSmall
                        wrapMode: Text.Wrap
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.spacingS
                DankTextField {
                    id: search
                    Layout.fillWidth: true
                    leftIconName: "search"
                    showClearButton: true
                    hidePlaceholderOnFocus: false
                    placeholderText: root.translations.tr("operation.search") + " (Ctrl+F)"
                    Accessible.name: root.translations.tr("operation.search")
                    Keys.onEscapePressed: event => {
                        if (text) { text = ""; event.accepted = true; }
                        else event.accepted = false;
                    }
                    Keys.onUpPressed: root.moveSelection(-1)
                    Keys.onDownPressed: root.moveSelection(1)
                }
                StyledText {
                    visible: root.query !== ""
                    text: root.translations.tr("search.results", {count: root.operations.length})
                    color: Theme.surfaceVariantText
                    font.pixelSize: Theme.fontSizeSmall
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Theme.spacingM

                Panel {
                    visible: !root.compact
                    Layout.preferredWidth: 300
                    Layout.fillHeight: true
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: Theme.spacingS
                        spacing: Theme.spacingS
                        ScrollView {
                            id: navigation
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            contentWidth: availableWidth
                            clip: true
                            ColumnLayout {
                                width: navigation.availableWidth
                                spacing: 2
                                Repeater {
                                    model: root.sections
                                    ColumnLayout {
                                        id: group
                                        required property string modelData
                                        required property int index
                                        readonly property var items: root.query ? root.operations.filter(op => op.section === modelData) : root.section === modelData ? root.operations : []
                                        Layout.fillWidth: true
                                        visible: !root.query || items.length > 0
                                        spacing: 2
                                        NavRow {
                                            iconName: root.sectionIcons[group.index]
                                            text: root.translations.tr("section." + group.modelData)
                                            trailing: String(root.query ? group.items.length : root.engine.catalog.filter(op => op.section === group.modelData).length)
                                            selected: !root.query && root.section === group.modelData && !root.operation
                                            chevron: root.query ? "" : root.section === group.modelData ? "expand_less" : "expand_more"
                                            onActivated: root.selectSection(group.modelData)
                                        }
                                        Repeater {
                                            model: group.items
                                            NavRow {
                                                required property var modelData
                                                child: true
                                                iconName: modelData.stream ? "sensors" : modelData.readonly ? "visibility" : "edit"
                                                text: root.translations.tr(modelData.label)
                                                selected: root.operation === modelData
                                                dimmed: root.engine.supported[modelData.id] !== true
                                                onActivated: { root.operationIndex = root.operations.indexOf(modelData); root.preferences = false; }
                                            }
                                        }
                                    }
                                }
                                StyledText {
                                    Layout.fillWidth: true
                                    Layout.margins: Theme.spacingS
                                    visible: root.query !== "" && root.operations.length === 0
                                    text: root.translations.tr("operation.empty")
                                    color: Theme.surfaceVariantText
                                    wrapMode: Text.Wrap
                                }
                            }
                        }
                        Flow {
                            Layout.fillWidth: true
                            Layout.margins: Theme.spacingS
                            spacing: Theme.spacingM
                            Repeater {
                                model: [["visibility", "legend.read"], ["edit", "legend.change"], ["sensors", "legend.stream"]]
                                Row {
                                    required property var modelData
                                    spacing: Theme.spacingXS
                                    DankIcon { name: parent.modelData[0]; size: 14; color: Theme.surfaceVariantText; anchors.verticalCenter: parent.verticalCenter }
                                    StyledText { text: root.translations.tr(parent.modelData[1]); color: Theme.surfaceVariantText; font.pixelSize: Theme.fontSizeSmall; anchors.verticalCenter: parent.verticalCenter }
                                }
                            }
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: Theme.spacingM
                    // Compact layouts trade the navigation tree for two selectors.
                    Loader {
                        Layout.fillWidth: true
                        active: root.compact
                        visible: active
                        sourceComponent: ColumnLayout {
                            spacing: Theme.spacingS
                            DankDropdown {
                                Layout.fillWidth: true
                                visible: root.query === ""
                                options: root.sections.map(section => root.translations.tr("section." + section))
                                currentValue: root.translations.tr("section." + root.section)
                                onValueChanged: value => root.selectSection(root.sections[options.indexOf(value)])
                                Accessible.name: root.translations.tr("navigation.sections")
                            }
                            DankDropdown {
                                Layout.fillWidth: true
                                visible: root.operations.length > 0
                                options: root.operations.map(op => (root.query ? root.translations.tr("section." + op.section) + " / " : "") + root.translations.tr(op.label))
                                currentValue: options[root.operationIndex] || ""
                                enableFuzzySearch: true
                                onValueChanged: value => root.operationIndex = options.indexOf(value)
                                Accessible.name: root.translations.tr("operation.select")
                            }
                        }
                    }
                    ScrollView {
                        id: scroll
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        contentWidth: availableWidth
                        ColumnLayout {
                            width: scroll.availableWidth
                            spacing: Theme.spacingM
                            StyledText {
                                Layout.fillWidth: true
                                Layout.margins: Theme.spacingL
                                visible: !root.operation
                                text: root.engine.ready ? root.translations.tr("operation.empty") : root.translations.tr(root.engine.result && !root.engine.result.ok ? "backend.retry" : "loading")
                                color: Theme.surfaceVariantText
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.Wrap
                            }
                            Panel {
                                id: formCard
                                visible: !!root.operation
                                Layout.fillWidth: true
                                implicitHeight: form.implicitHeight + Theme.spacingL * 2
                                OperationForm {
                                    id: form
                                    anchors.fill: parent
                                    anchors.margins: Theme.spacingL
                                    engine: root.engine
                                    translations: root.translations
                                    operation: root.operation
                                }
                            }
                            Panel {
                                visible: !!root.operation
                                Layout.fillWidth: true
                                implicitHeight: Math.max(280, scroll.availableHeight - (formCard.visible ? formCard.height + Theme.spacingM : 0))
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: Theme.spacingM
                                    spacing: Theme.spacingS
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: Theme.spacingS
                                        DankButtonGroup {
                                            Layout.fillWidth: true
                                            size: "small"
                                            checkEnabled: false
                                            model: root.outputTabs.map(tab => root.translations.tr("tab." + tab))
                                            currentIndex: root.outputTabs.indexOf(root.outputTab)
                                            onSelectionChanged: (index, selected) => { if (selected) root.outputTab = root.outputTabs[index]; }
                                            Accessible.name: root.translations.tr("output")
                                        }
                                        DankActionButton {
                                            iconName: "content_copy"
                                            enabled: output.text !== ""
                                            tooltipText: root.translations.tr("copy")
                                            onClicked: { output.selectAll(); output.copy(); output.deselect(); }
                                            Accessible.name: root.translations.tr("copy")
                                        }
                                        DankActionButton {
                                            visible: root.outputTab === "result" && root.engine.result !== null
                                            iconName: "clear_all"
                                            tooltipText: root.translations.tr("clear")
                                            onClicked: root.engine.result = null
                                            Accessible.name: root.translations.tr("clear")
                                        }
                                    }
                                    StyledRect {
                                        Layout.fillWidth: true
                                        visible: root.outputTab === "result" && root.engine.result !== null
                                        implicitHeight: resultRow.implicitHeight + Theme.spacingS * 2
                                        radius: Theme.cornerRadius
                                        color: Theme.withAlpha(root.engine.result && !root.engine.result.ok ? Theme.error : Theme.success, 0.12)
                                        RowLayout {
                                            id: resultRow
                                            anchors.fill: parent
                                            anchors.margins: Theme.spacingS
                                            spacing: Theme.spacingS
                                            readonly property bool ok: !!root.engine.result && root.engine.result.ok
                                            readonly property var spec: root.engine.result ? root.engine.catalog.find(op => op.id === root.engine.result.op) : null
                                            DankIcon {
                                                name: resultRow.ok ? "check_circle" : "error"
                                                size: 20
                                                color: resultRow.ok ? Theme.success : Theme.error
                                            }
                                            StyledText {
                                                Layout.fillWidth: true
                                                text: root.engine.result ? root.translations.tr(root.engine.result.ok ? "success" : "error." + (root.engine.result.error || {}).code) + (resultRow.spec ? "  ·  " + root.translations.tr(resultRow.spec.label) : "") : ""
                                                color: resultRow.ok ? Theme.surfaceText : Theme.error
                                                font.weight: Font.Medium
                                                wrapMode: Text.Wrap
                                                Accessible.role: Accessible.AlertMessage
                                            }
                                        }
                                    }
                                    StyledRect {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        radius: Theme.cornerRadius
                                        color: Theme.surfaceContainerLowest
                                        ScrollView {
                                            id: outputScroll
                                            anchors.fill: parent
                                            anchors.margins: Theme.spacingXS
                                            clip: true
                                            TextArea {
                                                id: output
                                                readOnly: true
                                                selectByMouse: true
                                                wrapMode: TextEdit.Wrap
                                                text: root.outputText
                                                placeholderText: root.translations.tr("result.empty")
                                                placeholderTextColor: Theme.surfaceVariantText
                                                font.family: Theme.monoFontFamily
                                                font.pixelSize: Theme.fontSizeSmall
                                                color: Theme.surfaceText
                                                selectionColor: Theme.primarySelected
                                                background: null
                                                Accessible.name: root.translations.tr("tab." + root.outputTab)
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        Dialog {
            id: confirmation
            readonly property var spec: root.engine.pending ? root.engine.catalog.find(op => op.id === root.engine.pending.operation) || null : null
            readonly property bool destructive: !!spec && ["factory-reset", "reset-settings", "account.logout", "account.revoke-device", "split-tunnel.clear", "relay.override.clear-all", "custom-list.delete", "api-access.remove"].includes(spec.id)
            readonly property color accent: destructive ? Theme.error : Theme.primary
            parent: Overlay.overlay
            anchors.centerIn: parent
            width: Math.min(content.width - Theme.spacingL * 2, 620)
            height: Math.min(content.height - Theme.spacingL * 2, implicitHeight)
            modal: true
            focus: true
            closePolicy: Popup.CloseOnEscape
            padding: Theme.spacingL
            background: Rectangle { color: Theme.surfaceContainerHigh; radius: Theme.cornerRadius; border.color: confirmation.accent; border.width: 1 }
            Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.45) }
            onOpened: if (!confirmButton.activeFocus) cancelButton.forceActiveFocus()
            onClosed: {
                if (root.engine.pending) root.engine.pending = null;
                if (root.visible) search.forceActiveFocus();
            }
            contentItem: ScrollView {
                id: confirmationScroll
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    width: confirmationScroll.availableWidth
                    spacing: Theme.spacingM
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Theme.spacingM
                        StyledRect {
                            implicitWidth: 44
                            implicitHeight: 44
                            radius: width / 2
                            color: Theme.withAlpha(confirmation.accent, 0.16)
                            DankIcon { anchors.centerIn: parent; name: confirmation.destructive ? "warning" : "fact_check"; size: 24; color: confirmation.accent }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            StyledText {
                                Layout.fillWidth: true
                                text: root.translations.tr("confirm.title")
                                color: Theme.surfaceVariantText
                                font.pixelSize: Theme.fontSizeSmall
                            }
                            StyledText {
                                Layout.fillWidth: true
                                text: confirmation.spec ? root.translations.tr(confirmation.spec.label) : ""
                                color: Theme.surfaceText
                                font.pixelSize: Theme.fontSizeLarge
                                font.weight: Font.Bold
                                wrapMode: Text.Wrap
                            }
                        }
                    }
                    StyledText {
                        Layout.fillWidth: true
                        text: confirmation.spec ? root.translations.tr("confirm." + confirmation.spec.section) : ""
                        color: Theme.surfaceText
                        wrapMode: Text.Wrap
                    }
                    StyledRect {
                        Layout.fillWidth: true
                        implicitHeight: confirmCommand.implicitHeight + Theme.spacingM * 2
                        radius: Theme.cornerRadius
                        color: Theme.surfaceContainerLowest
                        TextEdit {
                            id: confirmCommand
                            anchors.fill: parent
                            anchors.margins: Theme.spacingM
                            readOnly: true
                            selectByMouse: true
                            wrapMode: TextEdit.WrapAnywhere
                            text: root.engine.pending ? "$ " + root.engine.commandLine(root.engine.pending.operation, root.engine.pending.params) : ""
                            font.family: Theme.monoFontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: Theme.surfaceText
                            selectionColor: Theme.primarySelected
                            Accessible.name: root.translations.tr("confirm.parameters")
                        }
                    }
                    StyledText {
                        Layout.fillWidth: true
                        text: root.translations.tr("confirm.keys")
                        color: Theme.surfaceVariantText
                        font.pixelSize: Theme.fontSizeSmall
                        wrapMode: Text.Wrap
                    }
                }
            }
            footer: Item {
                implicitHeight: footerRow.implicitHeight + Theme.spacingL
                RowLayout {
                    id: footerRow
                    anchors.right: parent.right
                    anchors.rightMargin: Theme.spacingL
                    spacing: Theme.spacingS
                MullvadButton {
                    id: cancelButton
                    objectName: "confirmationCancel"
                    text: root.translations.tr("cancel")
                    backgroundColor: Theme.surfaceContainerHighest
                    textColor: Theme.surfaceText
                    onClicked: root.engine.pending = null
                    Accessible.name: text
                    KeyNavigation.tab: confirmButton
                    KeyNavigation.backtab: confirmButton
                }
                MullvadButton {
                    id: confirmButton
                    objectName: "confirmationExecute"
                    text: root.translations.tr("confirm.execute")
                    iconName: confirmation.destructive ? "warning" : "check"
                    backgroundColor: confirmation.accent
                    textColor: confirmation.destructive ? Theme.surface : Theme.primaryText
                    enabled: !root.engine.busy
                    onClicked: root.engine.confirm()
                    Accessible.name: text
                    KeyNavigation.tab: cancelButton
                    KeyNavigation.backtab: cancelButton
                }
                }
            }
        }
    }
}
