import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PC3
import org.kde.plasma.plasma5support as P5Support

PlasmoidItem {
    id: root
    property string title: "BGA · disconnected"
    property bool connected: false
    property bool paused: false
    property var tabs: []
    property var selectedId: null
    property real lastFlashId: 0
    property bool flashActive: false
    property bool flashVisible: true
    property real previewUntil: 0
    property int fastPollSequence: 0
    readonly property string tool: @BGA_TOOL@
    readonly property string statusTool: @BGA_STATUS_TOOL@
    readonly property int labelWidth: Math.max(140, Math.min(600, Plasmoid.configuration.labelWidth))
    toolTipMainText: title
    toolTipSubText: connected ? (paused ? "Page paused" : "Board Game Arena") : "Browser bridge disconnected"
    Plasmoid.icon: "applications-games"
    preferredRepresentation: compactRepresentation

    function run(command) {
        actions.connectSource(tool + " " + command)
    }
    function requestFocus() { if (connected && selectedId !== null) run("focus") }
    function selectTab(id) { if (Number.isInteger(id)) run("select " + id) }
    function stopFlash() {
        flashTimer.stop()
        flashActive = false
        flashVisible = true
        previewUntil = 0
    }
    function startFlash(until) {
        flashActive = true
        flashVisible = true
        previewUntil = until
        flashTimer.restart()
    }
    function applyStatus(data) {
        try {
            let state = JSON.parse(data.stdout)
            root.title = String(state.title || "BGA · no open tab")
            root.connected = Boolean(state.connected)
            root.paused = Boolean(state.paused)
            root.selectedId = state.selectedId
            root.tabs = state.tabs || []
            let hostFlashActive = Boolean(state.flashActive)
            if (root.flashActive && (!root.connected || !hostFlashActive ||
                    (!state.flashPreview && state.selectedVisible === true))) {
                root.stopFlash()
            }
            let flashId = Number(state.flashId || 0)
            if (flashId > root.lastFlashId) {
                root.lastFlashId = flashId
                let allowFlash = Boolean(state.flashPreview) ||
                                 !Plasmoid.configuration.flashOnlyWhenBgaInactive ||
                                 state.flashVisibleAtEvent === false
                if (allowFlash && root.connected && hostFlashActive &&
                        (state.flashPreview || state.selectedVisible !== true)) {
                    root.startFlash(state.flashPreview ? Number(state.flashUntil || 0) : 0)
                }
            }
        } catch (error) {
            root.stopFlash()
            root.title = "BGA · disconnected"
            root.connected = false
            root.tabs = []
            root.selectedId = null
        }
    }

    Timer {
        id: flashTimer
        interval: 350
        repeat: true
        onTriggered: {
            if (root.previewUntil > 0 && Date.now() >= root.previewUntil) {
                root.stopFlash()
            } else {
                root.flashVisible = !root.flashVisible
            }
        }
    }

    P5Support.DataSource {
        id: statusSource
        engine: "executable"
        connectedSources: [root.statusTool]
        interval: 1000
        onNewData: function(_source, data) { root.applyStatus(data) }
    }
    P5Support.DataSource {
        id: fastStatusSource
        engine: "executable"
        onNewData: function(source, data) {
            disconnectSource(source)
            root.applyStatus(data)
        }
    }
    Timer {
        id: fastStatusTimer
        interval: 100
        repeat: true
        running: root.flashActive
        onTriggered: {
            root.fastPollSequence += 1
            fastStatusSource.connectSource(root.statusTool + " " + root.fastPollSequence)
        }
    }
    P5Support.DataSource {
        id: actions
        engine: "executable"
        onNewData: function(source, _data) { disconnectSource(source) }
    }

    compactRepresentation: Item {
        Layout.minimumWidth: root.labelWidth
        Layout.preferredWidth: root.labelWidth
        Layout.maximumWidth: root.labelWidth
        implicitWidth: root.labelWidth
        implicitHeight: 28
        Rectangle {
            anchors.fill: parent
            color: "#ffffff"
            visible: root.flashActive && root.flashVisible
        }
        PC3.Label {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            text: root.title + (root.paused ? " ⏸" : "")
            visible: !root.flashActive || !root.flashVisible
            Accessible.name: root.title
        }
        PC3.Label {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            text: root.title + (root.paused ? " ⏸" : "")
            color: "#000000"
            visible: root.flashActive && root.flashVisible
            Accessible.name: root.title
        }
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: root.requestFocus()
        }
    }
    fullRepresentation: Item {
        implicitWidth: 420
        implicitHeight: Math.max(130, content.implicitHeight + 24)
        ColumnLayout {
            id: content
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8
            PC3.Label { text: root.title; wrapMode: Text.Wrap; Layout.fillWidth: true }
            PC3.Label {
                text: root.connected ? (root.paused ? "Page paused" : root.tabs.length + " BGA tab(s)") : "Browser bridge disconnected"
                Layout.fillWidth: true
            }
            Repeater {
                model: root.tabs
                delegate: PC3.Button {
                    required property var modelData
                    Layout.fillWidth: true
                    text: (root.selectedId === modelData.id ? "✓ " : "") + (modelData.title || "Untitled BGA tab")
                    onClicked: root.selectTab(modelData.id)
                }
            }
            RowLayout {
                PC3.Button { text: "Focus existing tab"; enabled: root.connected && root.selectedId !== null; onClicked: root.requestFocus() }
                PC3.Button { text: "Refresh"; onClicked: root.run("refresh") }
            }
        }
    }
}
