from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QTableView, QApplication, QStyledItemDelegate, QLineEdit

class FloatStandardItem(QStandardItem):
    def setData(self, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            try:
                float_value = float(value)
                super().setData(float_value, role)
            except ValueError:
                # Ignore invalid input or handle it accordingly
                pass
        else:
            super().setData(value, role)

class CustomStandardItemModel(QStandardItemModel):
    def __init__(self, prefix="R = ", tooltip="Tooltip: ", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prefix = prefix
        self.tooltip = tooltip

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            value = super().data(index, role)
            return f"{self.prefix}{value}"
        elif role == Qt.ToolTipRole:
            value = super().data(index, role)
            return f"{self.tooltip}{value}"
        return super().data(index, role)

class FloatDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        return editor

    def setModelData(self, editor, model, index):
        text = editor.text()
        print("TEST", text)
        try:
            float_value = float(text)
            model.setData(index, float_value, Qt.EditRole)
        except ValueError:
            # Ignore invalid input or handle it accordingly
            pass

app = QApplication([])

model = CustomStandardItemModel(prefix="Custom : ", tooltip="Custom Tooltip: ")
model.setHorizontalHeaderLabels(['Column 1'])

item = FloatStandardItem('7')
model.appendRow(item)

view = QTableView()
view.setModel(model)
view.setItemDelegate(FloatDelegate())
view.show()

app.exec()