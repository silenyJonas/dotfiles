// Přihlašovací obrazovka Island (SDDM).
// Nejdřív jen velké hodiny na tapetě, po stisku klávesy nebo kliknutí přihlášení:
// účet, heslo a výběr prostředí (Hyprland, GNOME…). Jen QtQuick, funguje s Qt 5 i Qt 6.
import QtQuick 2.15

Rectangle {
    id: root
    width: 1440
    height: 900
    color: "#0a1e2c"

    // jednotka velikosti: na 1440×900 je 1, větší obrazovka = vše úměrně větší
    readonly property real u: Math.max(0.6, Math.min(width / 1440, height / 900))
    readonly property color fg: "#dbe7ee"
    readonly property color dim: "#9fb3bf"
    readonly property color accent: config.accent || "#8fcdeb"
    readonly property color pill: "#e6eef2"
    readonly property color pillFg: "#0a1e2c"
    readonly property color card: Qt.rgba(10 / 255, 30 / 255, 44 / 255, 0.72)
    readonly property color line: Qt.rgba(125 / 255, 190 / 255, 220 / 255, 0.25)
    readonly property color tile: Qt.rgba(1, 1, 1, 0.07)
    readonly property color bad: "#e08a93"
    readonly property color warn: "#ebcb8b"

    property bool unlocked: false          // false = hodiny, true = přihlášení
    property var now: new Date()
    property int sessionIndex: sessionModel.lastIndex >= 0 ? sessionModel.lastIndex : 0
    property int userIndex: userModel.lastIndex >= 0 ? userModel.lastIndex : 0
    property string userName: ""
    property string realName: ""
    property string userIcon: ""
    property var users: []
    property var sessions: []
    property string message: ""
    property bool busy: false

    // písma instaluje instalační skript do systému (SDDM do domovské složky nevidí)
    readonly property string fontName: "Nunito"
    readonly property string iconFont: "JetBrainsMono Nerd Font"
    readonly property string blurred: {
        var b = config.blurBackground || "background-blur.jpg"
        return b.indexOf("/") === 0 ? "file://" + b : b
    }
    readonly property string background: {
        var b = config.background || "background.jpg"
        return b.indexOf("/") === 0 ? "file://" + b : b
    }

    // ------------------------------------------------------------ účty a prostředí (SDDM je dává jako modely)
    Repeater {
        model: userModel
        delegate: Item {
            Component.onCompleted: {
                var list = root.users.slice()
                list[index] = { name: model.name, real: model.realName || model.name, icon: model.icon || "" }
                root.users = list
                root.pickUser(root.userIndex)
            }
        }
    }
    Repeater {
        model: sessionModel
        delegate: Item {
            Component.onCompleted: {
                var list = root.sessions.slice()
                list[index] = model.name
                root.sessions = list
            }
        }
    }

    function dateText(d) {
        var f = config.dateFormat
        if (f && typeof f !== "string") f = f.join(", ")   // čárka v theme.conf bez uvozovek = seznam
        return d.toLocaleDateString(Qt.locale("en_US"), f || "dddd, MMMM d")
    }

    function pickUser(i) {
        if (!users.length) return
        userIndex = (i + users.length) % users.length
        var user = users[userIndex]
        if (!user) return
        userName = user.name
        realName = user.real
        userIcon = user.icon
    }

    function unlock() {
        if (unlocked) return
        unlocked = true
        message = ""
        password.forceActiveFocus()
        idle.restart()
    }

    function lockAgain() {
        if (busy) return
        unlocked = false
        sessionList.open = false
        password.text = ""
        message = ""
        root.forceActiveFocus()
    }

    function login() {
        if (!userName || busy) return
        message = ""
        busy = true
        sddm.login(userName, password.text, sessionIndex)
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            root.busy = false
            password.text = ""
            root.message = "Wrong password"
            shake.start()
            password.forceActiveFocus()
        }
        function onLoginSucceeded() { root.busy = false }
    }

    Timer {
        interval: 1000; running: true; repeat: true
        onTriggered: root.now = new Date()
    }
    Timer {                                 // nečinnost na přihlášení -> zpátky na hodiny
        id: idle
        interval: 1000 * Number(config.idleSeconds || 45)
        onTriggered: if (root.unlocked && !password.text) root.lockAgain()
    }

    // ------------------------------------------------------------ pozadí
    Image {
        id: wall
        anchors.fill: parent
        source: root.background
        fillMode: Image.PreserveAspectCrop
        smooth: true
        asynchronous: false
    }
    // rozmazaná verze pro přihlášení: připravuje ji island-sddm-bg spolu s tapetou
    Item {
        anchors.fill: parent
        opacity: root.unlocked ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 450; easing.type: Easing.OutCubic } }
        Image {
            id: soft
            anchors.fill: parent
            source: root.blurred
            fillMode: Image.PreserveAspectCrop
            smooth: true
            cache: false
        }
        Image {                                 // náhradní, kdyby rozmazaná verze chyběla
            anchors.fill: parent
            visible: soft.status !== Image.Ready
            source: visible ? root.background : ""
            sourceSize.width: 160
            fillMode: Image.PreserveAspectCrop
            smooth: true
        }
    }
    Rectangle {
        anchors.fill: parent
        color: "#06121b"
        opacity: root.unlocked ? 0.45 : 0.22
        Behavior on opacity { NumberAnimation { duration: 450; easing.type: Easing.OutCubic } }
    }

    // ------------------------------------------------------------ úvod: velké hodiny
    Item {
        id: intro
        anchors.fill: parent
        opacity: root.unlocked ? 0 : 1
        scale: root.unlocked ? 0.92 : 1
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 350; easing.type: Easing.OutCubic } }
        Behavior on scale { NumberAnimation { duration: 450; easing.type: Easing.OutCubic } }

        Text {
            x: 30 * u; y: 26 * u
            text: root.dateText(root.now)
            font.family: root.fontName; font.pixelSize: 17 * u; font.weight: Font.DemiBold
            color: root.accent
        }
        Column {
            anchors.centerIn: parent
            anchors.verticalCenterOffset: -10 * u
            spacing: -48 * u
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Qt.formatTime(root.now, "HH")
                font.family: root.fontName; font.pixelSize: 168 * u; font.weight: Font.Bold
                color: root.accent
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Qt.formatTime(root.now, "mm")
                font.family: root.fontName; font.pixelSize: 168 * u; font.weight: Font.Bold
                color: root.accent
            }
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 64 * u
            text: "Press any key to unlock"
            font.family: root.fontName; font.pixelSize: 14 * u; font.weight: Font.DemiBold
            color: root.fg
            opacity: 0.75
            SequentialAnimation on opacity {          // jemné "dýchání"
                loops: Animation.Infinite
                NumberAnimation { to: 0.45; duration: 1600; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0.85; duration: 1600; easing.type: Easing.InOutSine }
            }
        }
        MouseArea { anchors.fill: parent; onClicked: root.unlock() }
    }

    // ------------------------------------------------------------ přihlášení
    Item {
        id: login
        anchors.fill: parent
        opacity: root.unlocked ? 1 : 0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }

        MouseArea {                             // klik mimo seznam prostředí ho zavře
            anchors.fill: parent
            onClicked: { sessionList.open = false; password.forceActiveFocus(); idle.restart() }
        }

        Column {
            id: top
            anchors.horizontalCenter: parent.horizontalCenter
            y: (root.unlocked ? 70 : 40) * u
            Behavior on y { NumberAnimation { duration: 450; easing.type: Easing.OutCubic } }
            spacing: 2 * u
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Qt.formatTime(root.now, "HH:mm")
                font.family: root.fontName; font.pixelSize: 64 * u; font.weight: Font.Bold
                color: root.accent
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: root.dateText(root.now)
                font.family: root.fontName; font.pixelSize: 16 * u; font.weight: Font.DemiBold
                color: root.fg
                opacity: 0.8
            }
        }

        Rectangle {
            id: box
            width: 380 * u
            height: content.height + 56 * u
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.horizontalCenterOffset: shakeX
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: (root.unlocked ? 30 : 70) * u
            Behavior on anchors.verticalCenterOffset { NumberAnimation { duration: 450; easing.type: Easing.OutCubic } }
            property real shakeX: 0
            color: "transparent"               // bez rámečku, prvky leží přímo na rozmazané tapetě

            SequentialAnimation {
                id: shake
                NumberAnimation { target: box; property: "shakeX"; to: -14 * u; duration: 60 }
                NumberAnimation { target: box; property: "shakeX"; to: 12 * u; duration: 80 }
                NumberAnimation { target: box; property: "shakeX"; to: -8 * u; duration: 70 }
                NumberAnimation { target: box; property: "shakeX"; to: 0; duration: 60 }
            }

            Column {
                id: content
                anchors.horizontalCenter: parent.horizontalCenter
                y: 30 * u
                spacing: 14 * u

                Avatar {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 104 * u; height: 104 * u
                    source: root.userIcon
                    name: root.realName
                    fontName: root.fontName
                    ring: root.accent
                }

                // jméno; víc účtů = šipky vedle
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 10 * u
                    IconButton {
                        visible: root.users.length > 1
                        anchors.verticalCenter: parent.verticalCenter
                        size: 28 * u; icon: ""; iconFont: root.iconFont; fg: root.dim
                        onClicked: { root.pickUser(root.userIndex - 1); password.forceActiveFocus() }
                    }
                    Text {
                        text: root.realName || root.userName || "User"
                        font.family: root.fontName; font.pixelSize: 22 * u; font.weight: Font.Bold
                        color: root.fg
                    }
                    IconButton {
                        visible: root.users.length > 1
                        anchors.verticalCenter: parent.verticalCenter
                        size: 28 * u; icon: ""; iconFont: root.iconFont; fg: root.dim
                        onClicked: { root.pickUser(root.userIndex + 1); password.forceActiveFocus() }
                    }
                }

                // heslo
                Rectangle {
                    id: field
                    width: 300 * u; height: 46 * u
                    radius: height / 2
                    color: root.tile
                    border.width: Math.max(1, u)
                    border.color: password.activeFocus ? root.accent : root.line
                    Behavior on border.color { ColorAnimation { duration: 150 } }

                    TextInput {
                        id: password
                        anchors.left: parent.left; anchors.leftMargin: 20 * u
                        anchors.right: go.left; anchors.rightMargin: 10 * u
                        anchors.verticalCenter: parent.verticalCenter
                        echoMode: TextInput.Password
                        passwordCharacter: "•"
                        font.family: root.fontName; font.pixelSize: 16 * u
                        font.letterSpacing: 2 * u
                        color: root.fg
                        selectionColor: root.accent
                        clip: true
                        enabled: !root.busy
                        onTextChanged: { root.message = ""; idle.restart() }
                        Keys.onReturnPressed: root.login()
                        Keys.onEnterPressed: root.login()
                        Keys.onEscapePressed: root.lockAgain()
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            visible: !password.text
                            text: "Password"
                            font.family: root.fontName; font.pixelSize: 15 * u
                            color: root.dim
                            opacity: 0.8
                        }
                    }
                    Rectangle {
                        id: go
                        width: 36 * u; height: 36 * u; radius: width / 2
                        anchors.right: parent.right; anchors.rightMargin: 5 * u
                        anchors.verticalCenter: parent.verticalCenter
                        color: goMouse.containsMouse ? root.accent : root.pill
                        Behavior on color { ColorAnimation { duration: 150 } }
                        Text {
                            anchors.centerIn: parent
                            visible: !root.busy
                            text: ""
                            font.family: root.iconFont; font.pixelSize: 15 * u
                            color: root.pillFg
                        }
                        Rectangle {                     // točící se kroužek během přihlašování
                            anchors.centerIn: parent
                            visible: root.busy
                            width: 16 * u; height: 16 * u; radius: width / 2
                            color: "transparent"
                            border.width: 2.5 * u
                            border.color: root.pillFg
                            Rectangle {
                                width: 6 * u; height: 6 * u; radius: 3 * u
                                color: root.pill
                                x: parent.width - width; y: 0
                            }
                            RotationAnimation on rotation { running: root.busy; loops: Animation.Infinite; from: 0; to: 360; duration: 800 }
                        }
                        MouseArea {
                            id: goMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.login()
                        }
                    }
                }

                // chyba / Caps Lock
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    height: 16 * u
                    text: root.message ? root.message : (keyboard.capsLock ? "Caps Lock is on" : "")
                    color: root.message ? root.bad : root.warn
                    font.family: root.fontName; font.pixelSize: 13 * u; font.weight: Font.DemiBold
                }

            }
        }

        // výběr prostředí
        Rectangle {
            id: sessionButton
            anchors.right: parent.right; anchors.rightMargin: 24 * u
            anchors.bottom: parent.bottom; anchors.bottomMargin: 22 * u
            height: 34 * u
            width: sessionRow.width + 30 * u
            radius: height / 2
            color: sessionMouse.containsMouse || sessionList.open ? Qt.rgba(1, 1, 1, 0.12) : root.tile
            Behavior on color { ColorAnimation { duration: 150 } }
            Row {
                id: sessionRow
                anchors.centerIn: parent
                spacing: 9 * u
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: ""
                    font.family: root.iconFont; font.pixelSize: 13 * u
                    color: root.dim
                }
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.sessions[root.sessionIndex] || "Session"
                    font.family: root.fontName; font.pixelSize: 14 * u; font.weight: Font.DemiBold
                    color: root.fg
                }
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: ""
                    font.family: root.iconFont; font.pixelSize: 12 * u
                    color: root.dim
                    rotation: sessionList.open ? 180 : 0
                    Behavior on rotation { NumberAnimation { duration: 200 } }
                }
            }
            MouseArea {
                id: sessionMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: { sessionList.open = !sessionList.open; idle.restart() }
            }
        }

        // seznam prostředí: vyjede nad tlačítkem vpravo dole
        Rectangle {
            id: sessionList
            property bool open: false
            width: Math.max(220 * u, sessionColumn.width + 16 * u)
            height: sessionColumn.height + 16 * u
            anchors.right: sessionButton.right
            y: sessionButton.y - height - (open ? 10 : 0) * u
            Behavior on y { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }
            opacity: open ? 1 : 0
            visible: opacity > 0
            Behavior on opacity { NumberAnimation { duration: 180 } }
            radius: 18 * u
            color: Qt.rgba(10 / 255, 30 / 255, 44 / 255, 0.92)
            border.width: Math.max(1, u)
            border.color: root.line

            Column {
                id: sessionColumn
                anchors.centerIn: parent
                spacing: 2 * u
                Repeater {
                    model: root.sessions
                    delegate: Rectangle {
                        width: Math.max(204 * u, label.implicitWidth + 40 * u)
                        height: 36 * u
                        radius: 12 * u
                        color: index === root.sessionIndex ? root.pill
                             : (rowMouse.containsMouse ? Qt.rgba(1, 1, 1, 0.1) : "transparent")
                        Text {
                            id: label
                            anchors.verticalCenter: parent.verticalCenter
                            x: 16 * u
                            text: modelData
                            font.family: root.fontName; font.pixelSize: 14 * u; font.weight: Font.DemiBold
                            color: index === root.sessionIndex ? root.pillFg : root.fg
                        }
                        MouseArea {
                            id: rowMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                root.sessionIndex = index
                                sessionList.open = false
                                password.forceActiveFocus()
                            }
                        }
                    }
                }
            }
        }
    }

    // ------------------------------------------------------------ vpravo nahoře: uspat, restart, vypnout
    Row {
        anchors.top: parent.top; anchors.topMargin: 18 * u
        anchors.right: parent.right; anchors.rightMargin: 22 * u
        spacing: 4 * u
        IconButton {
            visible: sddm.canSuspend
            size: 36 * u; icon: ""; iconFont: root.iconFont; fg: root.fg
            onClicked: sddm.suspend()
        }
        IconButton {
            visible: sddm.canReboot
            size: 36 * u; icon: ""; iconFont: root.iconFont; fg: root.fg
            onClicked: sddm.reboot()
        }
        IconButton {
            visible: sddm.canPowerOff
            size: 36 * u; icon: ""; iconFont: root.iconFont; fg: root.fg
            hoverColor: Qt.rgba(191 / 255, 97 / 255, 106 / 255, 0.55)
            onClicked: sddm.powerOff()
        }
    }

    // ------------------------------------------------------------ klávesy
    focus: true
    Keys.onPressed: function(event) {
        if (!root.unlocked) {
            root.unlock()
            // první stisknuté písmeno už patří do hesla
            if (event.text && event.text.length === 1 && event.text >= " ")
                password.text += event.text
            event.accepted = true
        }
    }
    Component.onCompleted: root.forceActiveFocus()
}
