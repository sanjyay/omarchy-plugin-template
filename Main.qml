import QtQuick
import qs.Ui
import qs.Commons

BarWidget {
    id: root
    moduleName: "@@ID@@"

    // Host settings are inputs. Reject invalid types rather than coercing them.
    readonly property string label: {
        const value = setting("label", "@@NAME@@")
        return typeof value === "string" && value.trim().length > 0
            ? value.slice(0, 80) : "@@NAME@@"
    }

    implicitWidth: vertical ? barSize : Math.min(caption.implicitWidth + Style.space(12), Style.space(180))
    implicitHeight: barSize

    Text {
        id: caption
        anchors.centerIn: parent
        width: Math.max(0, root.width - Style.space(8))
        text: root.label
        textFormat: Text.PlainText
        elide: Text.ElideRight
        horizontalAlignment: Text.AlignHCenter
        color: root.bar ? root.bar.foreground : Color.foreground
        font.family: root.bar ? root.bar.fontFamily : Style.font.family
        font.pixelSize: Style.font.body
    }
}
