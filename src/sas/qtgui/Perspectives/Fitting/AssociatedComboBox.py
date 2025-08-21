from PySide6 import QtGui, QtWidgets


class AssociatedComboBox(QtWidgets.QComboBox):
    """Just a regular combo box, but associated with a particular QStandardItem so that it can be used to display and
    select an item's current text and a restricted list of other possible text.

    When the combo box's current text is changed, the change is immediately reflected in the associated item; either
    the text itself is set as the item's data, or the current index is used; see constructor."""
    item: QtGui.QStandardItem = None

    def __init__(self, item: QtGui.QStandardItem, idx_as_value: bool = False, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize widget. idx_as_value indicates whether to use the combo box's current index (otherwise, current text)
        as the associated item's new data.
        """
        super(AssociatedComboBox, self).__init__(parent)
        self.item = item

        if idx_as_value:
            self.currentIndexChanged[int].connect(self._onIndexChanged)
        else:
            self.currentTextChanged.connect(self._onTextChanged)

    def _onTextChanged(self, text: str) -> None:
        """
        Callback for combo box's currentTextChanged. Set associated item's data to the new text.
        """
        self.item.setText(text)

    def _onIndexChanged(self, idx: int) -> None:
        """
        Callback for combo box's currentIndexChanged. Set associated item's data to the new index.
        """
        self.item.setText(str(idx))
