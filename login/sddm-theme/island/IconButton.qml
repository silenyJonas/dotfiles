// Kulaté tlačítko s ikonou z Nerd Fontu (vpravo nahoře: uspat, restart, vypnout).
import QtQuick 2.15

Rectangle {
    id: button
    property string icon: ""
    property string tip: ""
    property string iconFont: ""
    property real size: 34
    property color fg: "#ffffff"
    property color hoverColor: Qt.rgba(1, 1, 1, 0.12)
    signal clicked()

    width: size; height: size; radius: size / 2
    color: mouse.containsMouse ? hoverColor : "transparent"
    Behavior on color { ColorAnimation { duration: 150 } }

    Text {
        anchors.centerIn: parent
        text: button.icon
        font.family: button.iconFont
        font.pixelSize: button.size * 0.46
        color: button.fg
    }
    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: button.clicked()
    }
}
