// Tlačítko v liště: otevře správce souborů (Thunar, s průhledným pozadím z tvých dotfiles).
import QtQuick
import Quickshell
import Caelestia.Config
import qs.components
import qs.services

Item {
    id: root

    implicitWidth: icon.implicitHeight + Tokens.padding.small
    implicitHeight: icon.implicitHeight

    StateLayer {
        anchors.fill: undefined
        anchors.centerIn: parent
        implicitWidth: implicitHeight
        implicitHeight: icon.implicitHeight + Tokens.padding.small
        radius: Tokens.rounding.full
        onClicked: Quickshell.execDetached(["thunar"])
    }

    MaterialIcon {
        id: icon

        anchors.centerIn: parent
        text: "hard_disk"
        color: Colours.palette.m3primary
        fontStyle: Tokens.font.icon.builders.small.weight(Font.Bold).build()
    }
}
