from typing import Optional

import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics

class CorfuncSlider(QtWidgets.QWidget):



    def __init__(self,
                 log_q_min: float,
                 log_q_point_1: float,
                 log_q_point_2: float,
                 log_q_point_3: float,
                 log_q_max: float,
                 *args, **kwargs):

        super().__init__(*args, **kwargs)

        if log_q_min >= log_q_point_1:
            raise ValueError("min_q should be smaller than q_point_1")

        if log_q_point_1 > log_q_point_2:
            raise ValueError("q_point_1 should be smaller or equal to q_point_2")

        if log_q_point_2 > log_q_point_3:
            raise ValueError("q_point_2 should be smaller or equal to q_point_3")

        if log_q_point_3 > log_q_max:
            raise ValueError("q_point_3 should be smaller or equal to max_q")


        self._min = log_q_min
        self._max = log_q_max
        self._point_1 = log_q_point_1
        self._point_2 = log_q_point_2
        self._point_3 = log_q_point_3

        # Parameters
        self.vertical_size = 70
        self.guinier_color = QtGui.QColor('orange')
        self.data_color = QtGui.QColor('white')
        self.porod_color = QtGui.QColor('green')
        self.text_color = QtGui.QColor('black')
        self.line_drag_color = QtGui.QColor('light grey')

        # Mouse control
        self._drag_id: Optional[int] = None
        self._movement_line_position: Optional[int] = None

        # Size properties
        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.Fixed
        )
        


    def mousePressEvent(self, event: QtGui.QMouseEvent):
        mouse_x = event.x()
        distances = [abs(mouse_x - line_x) for line_x in self.line_paint_positions]
        self._drag_id = np.argmin(distances)
        self._movement_line_position = mouse_x

        self.update()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self._drag_id is not None:
            self._movement_line_position = event.x()

            self.update()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if self._drag_id is not None:
            self.set_boundary(self._drag_id, self.inverse_transform(event.x()))

        self._drag_id = None
        self._movement_line_position = None

        self.update()

    def set_scale(self, log_q_min: float, log_q_max: float):
        """ Set the range of q values this slider should represent"""
        self._min = log_q_min
        self._max = log_q_max

        self.update()

    def set_boundaries(self, q_point_1, q_point_2, q_point_3):
        """ Set the boundaries between the sections"""
        self._point_1 = q_point_1
        self._point_2 = q_point_2
        self._point_3 = q_point_3

        self.update()

    def set_boundary(self, index: int, q: float):
        """ Set the value of the boundary points by (0-)index"""
        if index == 0:
            self._point_1 = q
        elif index == 1:
            self._point_2 = q
        elif index == 2:
            self._point_3 = q
        else:
            raise IndexError("Boundary index must be 0,1 or 2")

        self.update()


    @property
    def data_width(self):
        """ Length of range spanned by the data"""
        return self._max - self._min

    @property
    def scale(self):
        """ Scale factor from input to draw scale e.g. A^-1 -> px"""
        return self.width() / self.data_width

    def transform(self, value: float) -> float:
        """Convert a value from input to draw coordinates"""
        return self.scale * (value - self._min)


    def inverse_transform(self, value: float) -> float:
        """Convert a value from draw coordinates to input value"""
        return (value / self.scale) + self._min

    @property
    def guinier_label_position(self):
        """ Position to put the text for the guinier region"""
        return 2

    @property
    def data_label_centre(self):
        """ Centre of the interpolation region"""
        return self.transform(0.5 * (self._point_1 + self._point_2))

    @property
    def transition_label_centre(self):
        """ Centre of the data-porod transition"""

        return self.transform(0.5 * (self._point_2 + self._point_3))

    @property
    def porod_label_centre(self):
        """ Centre of the Porod region"""

        return self.transform(0.5 * (self._point_3 + self._max))

    @property
    def line_paint_positions(self):
        """ x coordinate of the painted lines"""
        return [self.transform(self._point_1),
                self.transform(self._point_2),
                self.transform(self._point_3)]



    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        brush = QtGui.QBrush()
        brush.setColor(QtGui.QColor('black'))
        brush.setStyle(Qt.SolidPattern)
        rect = QtCore.QRect(0, 0, painter.device().width(), self.vertical_size)
        painter.fillRect(rect, brush)

        positions = [0,
                     self.transform(self._point_1),
                     self.transform(self._point_2),
                     self.transform(self._point_3),
                     self.transform(self._max)]



        positions = [int(x) for x in positions]
        widths = [positions[i+1] - positions[i] for i in range(4)]

        #
        # Draw the sections
        #
        brush.setStyle(Qt.SolidPattern)

        grad = QtGui.QLinearGradient(0, 0, widths[0], 0)
        grad.setColorAt(0.0, self.guinier_color)
        grad.setColorAt(1.0, self.data_color)
        rect = QtCore.QRect(positions[0], 0, widths[0], self.vertical_size)
        painter.fillRect(rect, grad)

        brush.setColor(self.data_color)
        rect = QtCore.QRect(positions[1], 0, widths[1], self.vertical_size)
        painter.fillRect(rect, brush)

        grad = QtGui.QLinearGradient(positions[2], 0, positions[3], 0)
        grad.setColorAt(0.0, self.data_color)
        grad.setColorAt(1.0, self.porod_color)
        rect = QtCore.QRect(positions[2], 0, widths[2], self.vertical_size)
        painter.fillRect(rect, grad)

        brush.setColor(self.porod_color)
        rect = QtCore.QRect(positions[3], 0, widths[3], self.vertical_size)
        painter.fillRect(rect, brush)

        #
        # Dividing lines
        #

        for i, x in enumerate(positions[1:-1]):

            # Grey line if its being moved
            if i == self._drag_id:
                pen = QtGui.QPen(self.line_drag_color, 5)
            else:
                pen = QtGui.QPen(self.text_color, 5)

            painter.setPen(pen)
            painter.drawLine(x, 0, x, self.vertical_size)

        if self._movement_line_position is not None:
            pen = QtGui.QPen(self.text_color, 5)
            painter.setPen(pen)
            painter.drawLine(self._movement_line_position, 0, self._movement_line_position, self.vertical_size)

        #
        # Labels
        #


        self._paint_label(self.guinier_label_position, "Guinier", False)
        self._paint_label(self.data_label_centre, "Data")
        # self._paint_label(self.transition_label_centre, "Transition") # Looks better without this
        self._paint_label(self.porod_label_centre, "Porod")


    def _paint_label(self, position: float, text: str, centre_justify=True):

        painter = QtGui.QPainter(self)

        pen = painter.pen()
        pen.setColor(self.text_color)
        painter.setPen(pen)

        font = painter.font()
        font.setFamily('Times')
        font.setPointSize(10)
        painter.setFont(font)

        font_metrics = QFontMetrics(font)
        text_height = font_metrics.height()

        if centre_justify:
            x_offset = -0.5*font_metrics.horizontalAdvance(text)
        else:
            x_offset = 0

        painter.drawText(int(position + x_offset), int(0.5*self.vertical_size + 0.3*text_height), text)
        painter.end()

    def sizeHint(self):
        return QtCore.QSize(800, self.vertical_size)

def main():
    """ Show a demo of the slider """
    app = QtWidgets.QApplication([])
    slider = CorfuncSlider(0, 0.25, 0.50, 0.75, 1)
    slider.show()
    app.exec_()

if __name__ == "__main__":
    main()
