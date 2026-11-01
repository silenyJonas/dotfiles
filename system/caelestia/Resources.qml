pragma ComponentBehavior: Bound

// Island panel → Caelestia: stálé hodnoty v liště (CPU + teplota, GPU, RAM, baterie).
// Kliknutí otevře/zavře dashboard (tam je záložka Performance s detaily).
import QtQuick
import QtQuick.Layouts
import Quickshell.Services.UPower
import Caelestia.Config
import Caelestia.Services
import qs.components
import qs.services
import qs.utils

StyledRect {
    id: root

    readonly property var font: Tokens.font.body.builders.small.scale(0.85).build()
    readonly property bool hasGpu: Gpu.type !== GpuType.None

    implicitWidth: Tokens.sizes.bar.innerWidth
    implicitHeight: layout.implicitHeight + Tokens.padding.medium * 2
    radius: Tokens.rounding.full
    color: Qt.alpha(Colours.tPalette.m3surfaceContainer, Colours.tPalette.m3surfaceContainer.a)

    ServiceRef {
        service: Cpu
    }

    ServiceRef {
        service: Memory
    }

    ServiceRef {
        service: Gpu
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            const s = ShellState.forActive();
            s.dashboard = !s.dashboard;
        }
    }

    ColumnLayout {
        id: layout

        anchors.centerIn: parent
        spacing: Tokens.spacing.small

        Stat {
            icon: "memory"
            value: Math.round(Cpu.percentage * 100) + "%"
            colour: Colours.palette.m3primary
        }

        Stat {
            icon: Cpu.temperature > 90 ? "thermometer_alert" : "thermometer"
            value: isNaN(Cpu.temperature) ? "–" : Math.round(Cpu.temperature) + "°"
            colour: Cpu.temperature > 90 ? Colours.palette.m3error : Colours.palette.m3primary
        }

        Stat {
            visible: root.hasGpu
            icon: "desktop_windows"
            value: Math.round(Gpu.percentage * 100) + "%"
            colour: Colours.palette.m3secondary
        }

        Stat {
            icon: "memory_alt"
            value: Math.round(Memory.percentage * 100) + "%"
            colour: Colours.palette.m3tertiary
        }

        Stat {
            visible: UPower.displayDevice.isLaptopBattery
            icon: Icons.getBatteryIcon(UPower.displayDevice.percentage, !UPower.onBattery)
            value: Math.round(UPower.displayDevice.percentage * 100) + "%"
            colour: UPower.onBattery && UPower.displayDevice.percentage <= 0.2 ? Colours.palette.m3error : Colours.palette.m3onSurface
        }
    }

    component Stat: ColumnLayout {
        id: stat

        required property string icon
        required property string value
        required property color colour

        Layout.alignment: Qt.AlignHCenter
        spacing: 0

        MaterialIcon {
            Layout.alignment: Qt.AlignHCenter
            text: stat.icon
            color: stat.colour
            fill: 1
        }

        StyledText {
            Layout.alignment: Qt.AlignHCenter
            text: stat.value
            font: root.font
            color: stat.colour
        }
    }
}
