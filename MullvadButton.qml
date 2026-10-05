import QtQuick
import qs.Common
import qs.Widgets

DankButton {
    id: root
    // DMS 1.6.2 exposes width, but layouts need an implicit size that follows translations.
    implicitWidth: Math.max(64, labelMetrics.width + horizontalPadding * 2 + (iconName ? iconSize + Theme.spacingS : 0))
    implicitHeight: buttonHeight
    Accessible.role: Accessible.Button
    TextMetrics {
        id: labelMetrics
        text: root.text
        font.pixelSize: Theme.fontSizeMedium
        font.family: Theme.fontFamily
        font.weight: Font.Medium
    }
}
