// Kulatá fotka uživatele; bez fotky první písmeno jména.
import QtQuick 2.15

Item {
    id: avatar
    property string source: ""
    property string name: ""
    property string fontName: ""
    property color ring: "#ffffff"
    property color fill: "#1a1a1a"
    property bool loaded: false

    onSourceChanged: { loaded = false; if (source) canvas.loadImage(url()) ; canvas.requestPaint() }
    function url() { return source.indexOf("/") === 0 ? "file://" + source : source }

    // kreslí se ve 3× větším rozlišení a zmenší se, aby byla fotka ostrá i na HiDPI displeji
    readonly property real k: 3
    Canvas {
        id: canvas
        width: avatar.width * avatar.k
        height: avatar.height * avatar.k
        scale: 1 / avatar.k
        transformOrigin: Item.TopLeft
        smooth: true
        antialiasing: true
        onImageLoaded: { avatar.loaded = true; requestPaint() }
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            var r = Math.min(width, height) / 2
            ctx.save()
            ctx.beginPath()
            ctx.arc(width / 2, height / 2, r - avatar.k, 0, 2 * Math.PI)
            ctx.closePath()
            ctx.clip()
            ctx.fillStyle = avatar.fill
            ctx.fillRect(0, 0, width, height)
            if (avatar.source && isImageLoaded(avatar.url()))
                ctx.drawImage(avatar.url(), 0, 0, width, height)
            ctx.restore()
            ctx.beginPath()
            ctx.arc(width / 2, height / 2, r - 1.5 * avatar.k, 0, 2 * Math.PI)
            ctx.lineWidth = 3 * avatar.k
            ctx.strokeStyle = avatar.ring
            ctx.stroke()
        }
    }
    Text {
        anchors.centerIn: parent
        visible: !avatar.loaded
        text: avatar.name ? avatar.name.charAt(0).toUpperCase() : "?"
        font.family: avatar.fontName
        font.pixelSize: avatar.height * 0.42
        font.weight: Font.Bold
        color: avatar.ring
    }
}
