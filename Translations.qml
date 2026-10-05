import QtQuick
import Quickshell.Io
import qs.Common

Item {
    id: root
    property string language: "auto"
    readonly property string locale: language === "auto" ? (SessionData.locale || Qt.locale().name) : language
    readonly property bool portuguese: locale.toLowerCase().startsWith("pt")
    property var english: ({})
    property var brazilian: ({})
    readonly property bool ready: Object.keys(english).length > 0 && Object.keys(brazilian).length > 0

    function tr(key, params) {
        let result = (portuguese ? brazilian[key] : english[key]) || english[key] || key;
        for (const name in params || {})
            result = result.split("{" + name + "}").join(String(params[name]));
        return result;
    }

    FileView {
        path: Qt.resolvedUrl("i18n/en.json").toString().replace("file://", "")
        onLoaded: root.english = JSON.parse(text())
    }
    FileView {
        path: Qt.resolvedUrl("i18n/pt-BR.json").toString().replace("file://", "")
        onLoaded: root.brazilian = JSON.parse(text())
    }
}
