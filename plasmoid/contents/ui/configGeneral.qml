import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

Kirigami.FormLayout {
    property alias cfg_flashOnlyWhenBgaInactive: flashOnlyWhenBgaInactive.checked
    property alias cfg_labelWidth: labelWidth.value
    property alias cfg_raiseOnLowClock: raiseOnLowClock.checked
    property alias cfg_raiseAtSeconds: raiseAtSeconds.value

    QQC2.CheckBox {
        id: flashOnlyWhenBgaInactive
        Kirigami.FormData.label: i18n("Alerts:")
        text: i18n("Only flash when the selected BGA tab is not active")
    }

    QQC2.SpinBox {
        id: labelWidth
        Kirigami.FormData.label: i18n("Title width:")
        from: 140
        to: 600
        stepSize: 20
        editable: true
        textFromValue: function(value) { return i18n("%1 px", value) }
        valueFromText: function(text) { return parseInt(text) || 360 }
    }

    QQC2.CheckBox {
        id: raiseOnLowClock
        Kirigami.FormData.label: i18n("Turn clock:")
        text: i18n("Bring BGA to the front when my clock runs low")
    }

    QQC2.SpinBox {
        id: raiseAtSeconds
        Kirigami.FormData.label: i18n("Raise at:")
        enabled: raiseOnLowClock.checked
        from: 3
        to: 60
        stepSize: 1
        editable: true
        textFromValue: function(value) { return i18n("%1 s", value) }
        valueFromText: function(text) { return parseInt(text) || 10 }
    }

    QQC2.Label {
        Kirigami.FormData.label: ""
        text: i18n("Raised once per turn, only on your turn, only when BGA is not already in front. Needs a timed table.")
        wrapMode: Text.Wrap
        Layout.maximumWidth: Kirigami.Units.gridUnit * 24
        opacity: 0.7
    }
}
