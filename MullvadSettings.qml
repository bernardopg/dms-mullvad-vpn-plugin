import QtQuick
import qs.Common
import qs.Widgets
import qs.Modules.Plugins

PluginSettings {
    id: root
    pluginId: "DankMullvadVPN"
    Translations { id: translations; language: root.loadValue("language", "auto") }
    SelectionSetting {
        settingKey: "language"
        label: translations.tr("language")
        defaultValue: "auto"
        options: [{label: translations.tr("language.auto"), value: "auto"}, {label: "English", value: "en"}, {label: "Português (Brasil)", value: "pt-BR"}]
        onValueChanged: translations.language = value
    }
    ToggleSetting {
        settingKey: "showLocation"
        label: translations.tr("location.show")
        defaultValue: true
    }
    StyledText {
        width: parent.width
        text: translations.tr("settings.notice")
        color: Theme.surfaceVariantText
        wrapMode: Text.Wrap
    }
}
