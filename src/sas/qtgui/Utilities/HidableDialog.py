from typing import NamedTuple

from PySide6 import QtWidgets


class HidableDialog(QtWidgets.QDialog):
    """ Dialog class with an 'ask me again' feature"""
    def __init__(self, window_title: str, message: str, parent=None, buttons=None):

        super().__init__(parent)

        self.setWindowTitle(window_title)

        if buttons is None:
            QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        else:
            QBtn = buttons


        self.layout = QtWidgets.QVBoxLayout()

        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.check_box = QtWidgets.QCheckBox()
        self.check_box.setChecked(True)
        self.check_box.setText("Ask me this again?")

        self.message = QtWidgets.QLabel(message)

        self.layout.addWidget(self.message)
        self.layout.addWidget(self.buttonBox)
        self.layout.addWidget(self.check_box)

        self.setLayout(self.layout)

    @property
    def show_again(self) -> bool:
        return self.check_box.isChecked()


class ShowAgainResult(NamedTuple):
    """ Data structure for the output of the hidable dialog"""
    result: bool
    ask_again: bool

def hidable_dialog(window_title: str, message: str, show: bool, parent=None, buttons=None) -> ShowAgainResult:
    """
    A dialog with an ask again feature.

    """
    if show:
        dialog = HidableDialog(window_title, message, parent=parent, buttons=buttons)
        result = dialog.exec()

        return ShowAgainResult(
            result == 1,
            dialog.show_again)

    else:
        return ShowAgainResult(True, False)


def main():

    app = QtWidgets.QApplication([])

    print(hidable_dialog("Title", "Text", True))

    app.exec()



if __name__ == "__main__":
    main()
