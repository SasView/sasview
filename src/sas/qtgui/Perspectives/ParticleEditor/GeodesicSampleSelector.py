
from PySide6.QtWidgets import QSpinBox, QWidget

from sas.qtgui.Perspectives.ParticleEditor.sampling.geodesic import Geodesic


class GeodesicSamplingSpinBox(QSpinBox):
    """ SpinBox that only takes values that corresponds to the number of vertices on a geodesic sphere """

    def __init__(self, parent: QWidget | None=None):
        super().__init__(parent)

        self.setMaximum(
            Geodesic.points_for_division_amount(
                Geodesic.minimal_divisions_for_points(99999999)))

        self.setMinimum(
            Geodesic.points_for_division_amount(1))

        self.n_divisions = 3

        self.editingFinished.connect(self.onEditingFinished)

        self.updateDisplayValue()



    def updateDisplayValue(self):
        self.setValue(Geodesic.points_for_division_amount(self.n_divisions))

    def onEditingFinished(self):
        value = self.value()
        self.n_divisions = Geodesic.minimal_divisions_for_points(value)
        self.updateDisplayValue()

    def getNDivisions(self):
        return self.n_divisions

    def stepBy(self, steps: int):

        self.n_divisions = max([1, self.n_divisions + steps])
        self.updateDisplayValue()


def main():
    """ Show a demo of the spinner """

    from PySide6 import QtWidgets

    app = QtWidgets.QApplication([])
    slider = GeodesicSamplingSpinBox()
    slider.show()
    app.exec_()


if __name__ == "__main__":
    main()
