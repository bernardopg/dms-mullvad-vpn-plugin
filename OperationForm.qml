import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import qs.Common
import qs.Widgets

ColumnLayout {
    id: root
    required property var engine
    required property var translations
    property var operation: null
    property var values: ({})
    property string validation: ""
    readonly property bool available: operation !== null && engine.supported[operation.id] === true
    readonly property bool editable: available && !engine.busy && !engine.pending
    // Raw text is shown as typed; submit() remains the only parser that feeds requests.
    readonly property string command: {
        if (!operation)
            return "";
        const params = {};
        for (const field of operation.fields) {
            const raw = values[field.name];
            if (field.kind === "argv" && raw) {
                try { params[field.name] = JSON.parse(raw); } catch (error) { params[field.name] = raw; }
            } else if (field.many && field.kind !== "multi" && typeof raw === "string") {
                params[field.name] = raw.split(/\s+/).filter(v => v.length);
            } else {
                params[field.name] = raw;
            }
        }
        return engine.commandLine(operation.id, params);
    }
    spacing: Theme.spacingM
    onOperationChanged: { values = ({}); validation = ""; }

    function setValue(name, value) {
        const next = Object.assign({}, values);
        next[name] = value;
        if (operation && operation.id === "status" && value === true && (name === "verbose" || name === "debug"))
            next[name === "verbose" ? "debug" : "verbose"] = false;
        values = next;
    }

    function submit() {
        if (!operation || !available || engine.busy || engine.pending)
            return;
        validation = "";
        const params = Object.assign({}, values);
        for (const field of operation.fields) {
            if (field.kind === "bool") {
                params[field.name] = params[field.name] === true;
            } else if (field.kind === "enum" && field.required && !params[field.name]) {
                params[field.name] = field.choices[0];
            } else if ((field.many && field.kind !== "multi") || field.kind === "argv") {
                const raw = params[field.name] || "";
                if (raw) {
                    try {
                        params[field.name] = field.kind === "argv" ? JSON.parse(raw) : raw.split(/\s+/).filter(v => v.length);
                        if (!Array.isArray(params[field.name]))
                            throw new Error();
                    } catch (error) {
                        validation = translations.tr("invalid.arguments");
                        return;
                    }
                }
            }
            if (field.required && !field.allow_empty && (params[field.name] === undefined || params[field.name] === "" || params[field.name].length === 0)) {
                validation = translations.tr("invalid.required", {field: translations.tr(field.label)});
                return;
            }
            if (!field.required && params[field.name] === "")
                delete params[field.name];
            if (field.allow_empty && params[field.name] === undefined)
                params[field.name] = "";
        }
        engine.prepare(operation.id, params);
        // Credentials live only in the transient request/confirmation.
        for (const field of operation.fields)
            if (field.secret)
                setValue(field.name, "");
    }

    component Badge: StyledRect {
        id: badge
        property alias text: badgeText.text
        property string iconName: ""
        property color accent: Theme.surfaceVariantText
        implicitWidth: badgeRow.implicitWidth + Theme.spacingS * 2
        implicitHeight: 24
        radius: height / 2
        color: Theme.withAlpha(accent, 0.14)
        Row {
            id: badgeRow
            anchors.centerIn: parent
            spacing: Theme.spacingXS
            DankIcon { name: badge.iconName; size: 14; color: badge.accent; visible: name !== ""; anchors.verticalCenter: parent.verticalCenter }
            StyledText { id: badgeText; color: badge.accent; font.pixelSize: Theme.fontSizeSmall; font.weight: Font.Medium; anchors.verticalCenter: parent.verticalCenter }
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: Theme.spacingM
        StyledRect {
            implicitWidth: 40
            implicitHeight: 40
            radius: Theme.cornerRadius
            color: Theme.withAlpha(Theme.primary, 0.14)
            DankIcon {
                anchors.centerIn: parent
                name: !root.operation ? "" : root.operation.stream ? "sensors" : root.operation.readonly ? "visibility" : "edit"
                size: 22
                color: Theme.primary
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: Theme.spacingXS
            StyledText {
                Layout.fillWidth: true
                text: root.operation ? root.translations.tr(root.operation.label) : ""
                font.pixelSize: Theme.fontSizeLarge
                font.weight: Font.Medium
                color: Theme.surfaceText
                wrapMode: Text.Wrap
                Accessible.role: Accessible.Heading
            }
            Flow {
                Layout.fillWidth: true
                spacing: Theme.spacingXS
                Badge {
                    text: root.translations.tr("section." + (root.operation ? root.operation.section : "connection"))
                }
                Badge {
                    visible: !!root.operation && root.operation.readonly && !root.operation.stream
                    text: root.translations.tr("badge.read")
                    iconName: "visibility"
                    accent: Theme.primary
                }
                Badge {
                    visible: !!root.operation && root.operation.confirm
                    text: root.translations.tr("badge.confirm")
                    iconName: "verified_user"
                    accent: Theme.warning
                }
                Badge {
                    visible: !!root.operation && root.operation.stream
                    text: root.translations.tr("badge.stream")
                    iconName: "sensors"
                    accent: Theme.primary
                }
                Badge {
                    visible: !!root.operation && !root.available
                    text: root.translations.tr("badge.unavailable")
                    iconName: "block"
                    accent: Theme.error
                }
            }
        }
    }

    StyledText {
        Layout.fillWidth: true
        text: root.operation && !root.available ? root.translations.tr("unsupported", {version: root.engine.version}) : root.translations.tr("form.hint")
        color: root.operation && !root.available ? Theme.error : Theme.surfaceVariantText
        font.pixelSize: Theme.fontSizeSmall
        wrapMode: Text.Wrap
    }

    Repeater {
        id: fields
        model: root.operation ? root.operation.fields : []
        delegate: ColumnLayout {
            id: fieldRow
            required property var modelData
            required property int index
            readonly property bool toggle: modelData.kind === "bool"
            Layout.fillWidth: true
            spacing: Theme.spacingXS
            RowLayout {
                Layout.fillWidth: true
                visible: !fieldRow.toggle
                StyledText {
                    Layout.fillWidth: true
                    text: root.translations.tr(fieldRow.modelData.label) + (fieldRow.modelData.required ? " *" : "")
                    color: Theme.surfaceText
                    font.weight: Font.Medium
                    wrapMode: Text.Wrap
                }
                StyledText {
                    text: fieldRow.modelData.flag || "<" + fieldRow.modelData.name.toUpperCase() + ">"
                    isMonospace: true
                    font.pixelSize: Theme.fontSizeSmall
                    color: Theme.surfaceVariantText
                }
            }
            Loader {
                Layout.fillWidth: true
                sourceComponent: fieldRow.toggle ? boolInput : fieldRow.modelData.kind === "enum" ? enumInput : fieldRow.modelData.kind === "multi" ? multiInput : textInput
                Component {
                    id: boolInput
                    DankToggle {
                        width: parent.width
                        text: root.translations.tr(fieldRow.modelData.label)
                        description: fieldRow.modelData.flag
                        enabled: root.available && !root.engine.busy
                        checked: root.values[fieldRow.modelData.name] === true
                        onToggled: checked => root.setValue(fieldRow.modelData.name, checked)
                        Accessible.name: text
                    }
                }
                Component {
                    id: enumInput
                    DankDropdown {
                        width: parent.width
                        options: (fieldRow.modelData.required ? [] : [root.translations.tr("field.omit")]).concat(fieldRow.modelData.choices)
                        currentValue: root.values[fieldRow.modelData.name] || (fieldRow.modelData.required ? fieldRow.modelData.choices[0] : root.translations.tr("field.omit"))
                        enabled: root.available && !root.engine.busy
                        onValueChanged: value => root.setValue(fieldRow.modelData.name, value === root.translations.tr("field.omit") ? "" : value)
                        Accessible.name: root.translations.tr(fieldRow.modelData.label)
                    }
                }
                Component {
                    id: multiInput
                    Flow {
                        spacing: Theme.spacingS
                        Repeater {
                            model: fieldRow.modelData.choices
                            DankToggle {
                                required property string modelData
                                width: Math.max(160, implicitWidth)
                                height: 44
                                text: modelData
                                enabled: root.available && !root.engine.busy
                                checked: (root.values[fieldRow.modelData.name] || []).indexOf(modelData) !== -1
                                onToggled: checked => {
                                    let items = (root.values[fieldRow.modelData.name] || []).filter(v => v !== modelData);
                                    if (checked) items.push(modelData);
                                    root.setValue(fieldRow.modelData.name, items);
                                }
                                Accessible.name: modelData
                            }
                        }
                    }
                }
                Component {
                    id: textInput
                    DankTextField {
                        width: parent.width
                        enabled: root.available && !root.engine.busy
                        text: String(root.values[fieldRow.modelData.name] || "")
                        placeholderText: root.translations.tr("hint." + (fieldRow.modelData.many ? "many" : fieldRow.modelData.kind)) + (fieldRow.modelData.allow_any ? root.translations.tr("hint.any") : "")
                        echoMode: fieldRow.modelData.secret ? TextInput.Password : TextInput.Normal
                        maximumLength: 8192
                        onTextChanged: {
                            if (text !== String(root.values[fieldRow.modelData.name] || ""))
                                root.setValue(fieldRow.modelData.name, text);
                        }
                        Accessible.name: root.translations.tr(fieldRow.modelData.label)
                        Accessible.description: placeholderText
                    }
                }
            }
        }
    }

    StyledRect {
        Layout.fillWidth: true
        visible: root.validation !== ""
        implicitHeight: validationRow.implicitHeight + Theme.spacingS * 2
        radius: Theme.cornerRadius
        color: Theme.withAlpha(Theme.error, 0.12)
        RowLayout {
            id: validationRow
            anchors.fill: parent
            anchors.margins: Theme.spacingS
            spacing: Theme.spacingS
            DankIcon { name: "error"; size: 18; color: Theme.error }
            StyledText {
                Layout.fillWidth: true
                text: root.validation
                color: Theme.error
                wrapMode: Text.Wrap
                Accessible.role: Accessible.AlertMessage
            }
        }
    }

    StyledRect {
        Layout.fillWidth: true
        visible: root.command !== ""
        implicitHeight: commandRow.implicitHeight + Theme.spacingS * 2
        radius: Theme.cornerRadius
        color: Theme.surfaceContainer
        Accessible.name: root.translations.tr("command.preview")
        RowLayout {
            id: commandRow
            anchors.fill: parent
            anchors.margins: Theme.spacingS
            anchors.leftMargin: Theme.spacingM
            spacing: Theme.spacingS
            StyledText {
                text: "$"
                isMonospace: true
                color: Theme.primary
            }
            TextEdit {
                id: commandText
                Layout.fillWidth: true
                text: root.command
                readOnly: true
                selectByMouse: true
                wrapMode: TextEdit.WrapAnywhere
                font.family: Theme.monoFontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.surfaceText
                selectionColor: Theme.primarySelected
                Accessible.name: root.translations.tr("command.preview")
            }
            DankActionButton {
                iconName: "content_copy"
                buttonSize: 28
                iconSize: 16
                tooltipText: root.translations.tr("copy")
                onClicked: { commandText.selectAll(); commandText.copy(); commandText.deselect(); }
                Accessible.name: root.translations.tr("copy")
            }
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: Theme.spacingS
        MullvadButton {
            objectName: "operationExecute"
            text: root.translations.tr(root.operation && root.operation.stream ? "start" : root.operation && root.operation.confirm ? "execute.review" : "execute")
            iconName: root.operation && root.operation.confirm ? "fact_check" : "play_arrow"
            backgroundColor: Theme.primary
            textColor: Theme.primaryText
            enabled: root.editable
            onClicked: root.submit()
            Accessible.name: text
            ToolTip.visible: hovered
            ToolTip.text: root.translations.tr("execute.tip") + " (Ctrl+Enter)"
        }
        MullvadButton {
            visible: !!root.operation && root.operation.stream
            text: root.translations.tr("stop")
            iconName: "stop"
            backgroundColor: Theme.surfaceContainerHighest
            textColor: Theme.surfaceText
            enabled: !root.engine.busy && (root.operation && root.operation.id === "log.listen" ? root.engine.logging : root.engine.watching)
            onClicked: {
                root.engine.request("stream.stop", {operation: root.operation.id});
                if (root.operation.id === "log.listen") root.engine.logging = false;
                else root.engine.watching = false;
            }
            Accessible.name: text
        }
        Item { Layout.fillWidth: true }
        StyledText {
            visible: !!root.operation && root.operation.stream
            text: root.translations.tr((root.operation && root.operation.id === "log.listen" ? root.engine.logging : root.engine.watching) ? "stream.active" : "stream.inactive")
            color: Theme.surfaceVariantText
            font.pixelSize: Theme.fontSizeSmall
        }
    }
}
