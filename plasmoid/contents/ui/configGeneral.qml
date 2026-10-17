import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

Kirigami.FormLayout {
    property alias cfg_flashOnlyWhenBgaInactive: flashOnlyWhenBgaInactive.checked
    property alias cfg_labelWidth: labelWidth.value

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
}
