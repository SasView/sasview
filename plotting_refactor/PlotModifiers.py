from PySide6.QtWidgets import QTreeWidgetItem

class PlotModifier(QTreeWidgetItem):
    def __init__(self, parent, name):
        super().__init__(parent, name)
        self.setData(0, 1, self)

class ModifierLinestyle(PlotModifier):
    def __init__(self, parent, name):
        super().__init__(parent, name)

    def clone(self):
        copy = super().clone()
        return ModifierLinestyle(copy.parent(), [copy.text(0)])

class ModifierLinecolor(PlotModifier):
    def __init__(self, parent, name):
        super().__init__(parent, name)

    def clone(self):
        copy = super().clone()
        return ModifierLinecolor(copy.parent(), [copy.text(0)])


class ModifierColormap(PlotModifier):
    def __init__(self, parent, name):
        super().__init__(parent, name)

    def clone(self):
        copy = super().clone()
        return ModifierColormap(copy.parent(), [copy.text(0)])
