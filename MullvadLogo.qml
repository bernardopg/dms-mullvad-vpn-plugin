import QtQuick
import QtQuick.Effects
import qs.Common

// The plugin logo, sized and tinted like a DankIcon. The asset is white with
// alpha, so `color` decides the final colour (theme or connection state).
Image {
    id: root

    property color color: Theme.surfaceText
    property real size: Theme.iconSize

    width: size
    height: size
    source: Qt.resolvedUrl("assets/logo.png")
    sourceSize: Qt.size(size * 2, size * 2)
    fillMode: Image.PreserveAspectFit
    smooth: true
    mipmap: true
    layer.enabled: true
    layer.effect: MultiEffect {
        colorization: 1
        colorizationColor: root.color
    }
}
