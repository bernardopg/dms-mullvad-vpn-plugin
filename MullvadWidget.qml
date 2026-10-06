import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.Common
import qs.Widgets
import qs.Modules.Plugins
import "Shared.js" as Shared

PluginComponent {
    id: root
    readonly property bool showLocation: pluginData.showLocation !== false
    readonly property string stateText: translations.tr("state." + root.backend.status.state)
    readonly property var location: (root.backend.status.details || {}).location || {}
    readonly property string label: stateText + (showLocation && location.city ? " · " + location.city : "")
    readonly property string vpnState: root.backend.status.state || "unknown"
    readonly property bool changing: ["connecting", "disconnecting"].includes(vpnState)
    readonly property color statusColor: vpnState === "error" ? Theme.error : vpnState === "connected" ? Theme.success : changing ? Theme.warning : Theme.surfaceVariantText
    readonly property string statusIcon: vpnState === "connected" ? "vpn_lock" : vpnState === "error" ? "error" : changing ? "sync" : "vpn_lock_off"
    // The logo stands for steady states; error and in-progress keep their glyphs.
    readonly property bool showLogo: vpnState !== "error" && !changing
    // DMS reloads the widget URL but caches child types. Version the adapter component
    // so this release can be applied without restarting the user's shell.
    readonly property string engineVersion: "1.3.0"
    readonly property var backend: Shared.engine(engineVersion, () => Qt.createComponent(Qt.resolvedUrl("MullvadEngine.qml").toString() + "?v=" + engineVersion, Component.PreferSynchronous).createObject(null))
    property alias window: fullWindow
    property alias i18n: translations
    popoutWidth: 420
    popoutHeight: 0
    pillRightClickAction: () => root.openWindow()
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: "Mullvad VPN · " + label
    Accessible.description: translations.tr("bar.tip")
    Accessible.onPressAction: root.triggerPopout()
    Keys.onReturnPressed: root.triggerPopout()
    Keys.onSpacePressed: root.triggerPopout()

    Component.onCompleted: Shared.attach(engineVersion, root)
    Component.onDestruction: Shared.detach(engineVersion, root)

    Translations {
        id: translations
        language: root.pluginData.language || "auto"
    }
    Connections {
        target: root.backend
        // Only the bar the user last used (or the owner) opens its window for a confirmation.
        function onConfirmationRequired() {
            if (root.backend.target() === root)
                root.openWindow();
        }
    }
    MullvadWindow {
        id: fullWindow
        engine: root.backend
        translations: translations
        widgetRoot: root
    }

    function quickToggle() {
        if (!root.backend.ready || root.backend.busy || ["connecting", "disconnecting"].includes(root.backend.status.state))
            return;
        root.backend.activeWidget = root;
        root.backend.prepare(root.backend.status.state === "connected" ? "disconnect" : "connect", {});
    }

    function openWindow() {
        root.backend.activeWidget = root;
        closePopout();
        fullWindow.preferences = false;
        fullWindow.open();
    }

    function openPreferences() {
        root.backend.activeWidget = root;
        closePopout();
        fullWindow.openSettings();
    }

    horizontalBarPill: Component {
        Row {
            spacing: Theme.spacingS
            MullvadLogo {
                visible: root.showLogo
                color: root.statusColor
                size: root.iconSize
                anchors.verticalCenter: parent.verticalCenter
            }
            DankIcon {
                visible: !root.showLogo
                name: root.statusIcon
                color: root.statusColor
                size: root.iconSize
                anchors.verticalCenter: parent.verticalCenter
            }
            StyledText {
                text: root.label
                width: Math.min(implicitWidth, 230)
                elide: Text.ElideRight
                color: Theme.surfaceText
                anchors.verticalCenter: parent.verticalCenter
                Accessible.name: text
            }
        }
    }
    verticalBarPill: Component {
        Item {
            implicitWidth: root.iconSize
            implicitHeight: root.iconSize
            Accessible.name: root.label
            MullvadLogo {
                anchors.centerIn: parent
                visible: root.showLogo
                size: root.iconSize
                color: root.statusColor
            }
            DankIcon {
                anchors.centerIn: parent
                visible: !root.showLogo
                name: root.statusIcon
                size: root.iconSize
                color: root.statusColor
            }
        }
    }
    popoutContent: Component {
        PopoutComponent {
            headerText: "Mullvad VPN"
            detailsText: root.label
            ColumnLayout {
                width: parent.width
                spacing: Theme.spacingM
                StyledRect {
                    Layout.fillWidth: true
                    implicitHeight: statusRow.implicitHeight + Theme.spacingM * 2
                    radius: Theme.cornerRadius
                    color: Theme.surfaceContainerHigh
                    RowLayout {
                        id: statusRow
                        anchors.fill: parent
                        anchors.margins: Theme.spacingM
                        spacing: Theme.spacingM
                        StyledRect {
                            implicitWidth: 44
                            implicitHeight: 44
                            radius: width / 2
                            color: Theme.withAlpha(root.statusColor, 0.16)
                            MullvadLogo {
                                anchors.centerIn: parent
                                visible: root.showLogo
                                size: 26
                                color: root.statusColor
                            }
                            DankIcon {
                                anchors.centerIn: parent
                                visible: !root.showLogo
                                name: root.statusIcon
                                size: 26
                                color: root.statusColor
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            StyledText {
                                Layout.fillWidth: true
                                text: root.stateText
                                color: root.statusColor === Theme.surfaceVariantText ? Theme.surfaceText : root.statusColor
                                font.pixelSize: Theme.fontSizeLarge
                                font.weight: Font.Bold
                                elide: Text.ElideRight
                            }
                            StyledText {
                                Layout.fillWidth: true
                                text: [root.location.city, root.location.country].filter(Boolean).join(", ") || translations.tr("location.unavailable")
                                color: Theme.surfaceText
                                elide: Text.ElideRight
                            }
                            StyledText {
                                Layout.fillWidth: true
                                visible: text !== ""
                                text: [root.location.hostname, root.location.ipv4].filter(v => typeof v === "string" && v).join("  ·  ")
                                isMonospace: true
                                color: Theme.surfaceVariantText
                                font.pixelSize: Theme.fontSizeSmall
                                elide: Text.ElideRight
                            }
                        }
                    }
                }
                MullvadButton {
                    Layout.fillWidth: true
                    text: translations.tr(root.vpnState === "connected" ? "op.disconnect" : "op.connect")
                    iconName: "power_settings_new"
                    backgroundColor: root.vpnState === "connected" ? Theme.surfaceContainerHighest : Theme.primary
                    textColor: root.vpnState === "connected" ? Theme.error : Theme.primaryText
                    enabled: root.backend.ready && !root.backend.busy && !root.backend.pending && !root.changing
                    onClicked: root.quickToggle()
                    Accessible.name: text
                    ToolTip.visible: hovered
                    ToolTip.text: translations.tr("execute.tip")
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Theme.spacingS
                    MullvadButton {
                        objectName: "popoutOpenWindow"
                        Layout.fillWidth: true
                        text: translations.tr("window.open")
                        iconName: "open_in_new"
                        backgroundColor: Theme.surfaceContainerHigh
                        textColor: Theme.surfaceText
                        onClicked: root.openWindow()
                        Accessible.name: text
                    }
                    MullvadButton {
                        Layout.fillWidth: true
                        text: translations.tr("settings")
                        iconName: "settings"
                        backgroundColor: Theme.surfaceContainerHigh
                        textColor: Theme.surfaceText
                        onClicked: root.openPreferences()
                        Accessible.name: text
                    }
                }
                StyledText {
                    Layout.fillWidth: true
                    text: translations.tr(root.backend.mock ? "mock.notice" : "status.notice", {
                        version: root.backend.version || "—"
                    })
                    color: Theme.surfaceVariantText
                    font.pixelSize: Theme.fontSizeSmall
                    wrapMode: Text.Wrap
                }
            }
        }
    }
}
