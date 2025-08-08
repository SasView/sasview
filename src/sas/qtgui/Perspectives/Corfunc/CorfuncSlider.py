import math

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics

from sas.sascalc.corfunc.calculation_data import ExtrapolationInteractionState, ExtrapolationParameters


class CorfuncSlider(QtWidgets.QWidget):
    """ Slider that allows the selection of the different Q-ranges involved in interpolation,
    and that provides some visual cues to how it works."""

    valueEdited = Signal(ExtrapolationParameters, name='valueEdited')
    valueEditing = Signal(ExtrapolationInteractionState, name='valueEditing')

    def __init__(self,
                 parameters: ExtrapolationParameters = ExtrapolationParameters(1,2,4,8,16),
                 enabled: bool = False,
                 *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.setEnabled(enabled)

        parameter_problems = self.find_parameter_problems(parameters)
        if parameter_problems is not None:
            raise ValueError(parameter_problems)

        self._min = parameters.data_q_min
        self._point_1 = parameters.point_1
        self._point_2 = parameters.point_2
        self._point_3 = parameters.point_3
        self._max = parameters.data_q_max


        # Display Parameters
        self.vertical_size = 20
        self.left_pad = 60
        self.right_pad = 60
        self.line_width = 3
        self.guinier_color = QtGui.QColor('orange')
        self.data_color = QtGui.QColor('white')
        self.porod_color = QtGui.QColor('green')
        self.text_color = QtGui.QColor('black')
        self.line_drag_color = mix_colours(QtGui.QColor('white'), QtGui.QColor('black'), 0.4)
        self.hover_colour = QtGui.QColor('white')
        self.disabled_line_color = QtGui.QColor('light grey')
        self.disabled_line_color.setAlpha(0)
        self.disabled_text_color = QtGui.QColor('grey')
        self.disabled_non_data_color = QtGui.QColor('light grey')

        # - define hover colours by mixing with a grey
        mix_color = QtGui.QColor('grey')
        mix_fraction = 0.7
        self.guinier_hover_color = mix_colours(self.guinier_color, mix_color, mix_fraction)
        self.data_hover_color = mix_colours(self.data_color, mix_color, mix_fraction)
        self.porod_hover_color = mix_colours(self.porod_color, mix_color, mix_fraction)

        # Mouse control
        self._hovering = False
        self._hover_id: int | None = None

        self._drag_id: int | None = None
        self._movement_line_position: int | None = None

        # Qt things
        # self.setAttribute(Qt.WA_Hover)
        self.setMouseTracking(True)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.Fixed
        )

    @staticmethod
    def find_parameter_problems(params: ExtrapolationParameters) -> str | None:
        """ Check an extratpolation prarameters object for consistency

        :param params: An extrapolation parameters object describing a desired state
        :returns: A description of the problem if it exists, otherwise None
        """
        if params.data_q_min >= params.point_1:
            return "min_q should be smaller than q_point_1"

        if params.point_1 > params.point_2:
            return "q_point_1 should be smaller or equal to q_point_2"

        if params.point_2 > params.point_3:
            return "q_point_2 should be smaller or equal to q_point_3"

        if params.point_3 > params.data_q_max:
            return "q_point_3 should be smaller or equal to max_q"

        return None


    def enterEvent(self, a0: QtCore.QEvent) -> None:
        if self.isEnabled():
            self._hovering = True

        self.update()

    def leaveEvent(self, a0: QtCore.QEvent) -> None:
        if self.isEnabled():
            self._hovering = False

        self.update()

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if self.isEnabled():
            mouse_x = event.x()

            self._drag_id = self._nearest_line(mouse_x)
            self._movement_line_position = mouse_x
            self._hovering = False

        self.update()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.isEnabled():
            mouse_x = event.x()

            if self._hovering:
                self._hover_id = self._nearest_line(mouse_x)

            if self._drag_id is not None:
                self._movement_line_position = self._sanitise_new_position(self._drag_id, mouse_x)
                self.valueEditing.emit(self.interaction_state)


        self.update()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if self.isEnabled():
            if self._drag_id is not None and self._movement_line_position is not None:
                self.set_boundary(self._drag_id, self.inverse_transform(self._movement_line_position))

            self._drag_id = None
            self._movement_line_position = None

            x, y = event.x(), event.y()

            self._hovering = self._mouse_inside(x, y)
            if self._hovering:
                self._hover_id = self._nearest_line(x)
            else:
                self._hover_id = None

            self.valueEdited.emit(self.extrapolation_parameters)
        self.update()

    def _mouse_inside(self, x, y):
        """ Is the mouse inside the window"""
        return (0 < x < self.width()) and (0 < y < self.height())

    def _sanitise_new_position(self, line_id: int, new_position: int, delta=1) -> int:
        """ Returns a revised position for a line position that prevents the bounds being exceeded """
        l1, l2, l3 = (int(x) for x in self.line_paint_positions)

        if line_id == 0:
            if self.left_pad > new_position:
                return self.left_pad
            elif new_position > l2:
                return l2 - delta
            else:
                return new_position

        elif line_id == 1:
            if l1 > new_position:
                return l1 + delta
            elif new_position > l3:
                return l3 - delta
            else:
                return new_position

        elif line_id == 2:
            if l2 > new_position:
                return l2 + delta
            elif new_position > self.width() - self.right_pad:
                return self.width() - self.right_pad
            else:
                return new_position

        else:
            raise IndexError("line_id must be 0, 1 or 2")

    def _nearest_line(self, x: float) -> int:
        """ Get id of the nearest line"""
        distances = [abs(x - line_x) for line_x in self.line_paint_positions]
        return int(np.argmin(distances))

    def set_boundaries(self, q_point_1: float, q_point_2: float, q_point_3: float):
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
    def extrapolation_parameters(self):
        return ExtrapolationParameters(self._min, self._point_1, self._point_2, self._point_3, self._max)

    @extrapolation_parameters.setter
    def extrapolation_parameters(self, params: ExtrapolationParameters):
        if params is not None:
            self._min = params.data_q_min
            self._point_1 = params.point_1
            self._point_2 = params.point_2
            self._point_3 = params.point_3
            self._max = params.data_q_max

        self.update()

    @property
    def interaction_state(self) -> ExtrapolationInteractionState:
        """ The current state of the slider, including temporary data about how it is being moved"""
        return ExtrapolationInteractionState(
            self.extrapolation_parameters,
            self._drag_id,
            None if self._movement_line_position is None else self.inverse_transform(self._movement_line_position)
        )

    @property
    def _dragging(self) -> bool:
        """ Are we dragging? """
        return self._drag_id is not None

    @property
    def data_width(self) -> float:
        """ Length of range spanned by the data"""
        return math.log(self._max/self._min)

    @property
    def input_width(self) -> float:
        """ Width of the part of the widget representing input data"""
        return self.width() - (self.left_pad + self.right_pad)

    @property
    def scale(self) -> float:
        """ Scale factor from input to draw scale e.g. A^-1 -> px"""
        return self.input_width / self.data_width

    def transform(self, q_value: float) -> float:
        """Convert a value from input to draw coordinates"""

        if q_value == 0:
            return 0

        if self._min == 0:
            return self.input_width + self.left_pad

        return self.left_pad + self.scale * (math.log(q_value) - math.log(self._min))

    def inverse_transform(self, px_value: float) -> float:
        """Convert a value from draw coordinates to input value"""
        return self._min*math.exp((px_value - self.left_pad)/self.scale)

    @property
    def guinier_label_position(self) -> float:
        """ Position to put the text for the guinier region"""
        return 0.5*self.left_pad

    @property
    def data_label_centre(self) -> float:
        """ Centre of the interpolation region"""
        return 0.5 * (self.transform(self._point_1) + self.transform(self._point_2))

    @property
    def transition_label_centre(self) -> float:
        """ Centre of the data-porod transition"""
        return 0.5 * (self.transform(self._point_2) + self.transform(self._point_3))

    @property
    def porod_label_centre(self) -> float:
        """ Centre of the Porod region"""

        return 0.5 * (self.transform(self._point_3) + self.width())

    @property
    def line_paint_positions(self) -> tuple[float, float, float]:
        """ x coordinate of the painted lines"""
        return (self.transform(self._point_1),
                self.transform(self._point_2),
                self.transform(self._point_3))

    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        brush = QtGui.QBrush()
        brush.setColor(QtGui.QColor('black'))
        brush.setStyle(Qt.SolidPattern)
        rect = QtCore.QRect(0, 0, painter.device().width(), self.vertical_size)
        painter.fillRect(rect, brush)

        positions = [self.transform(self._min),
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
        if self.isEnabled():
            if self._hovering or self._dragging:
                guinier_color = self.guinier_hover_color
                data_color = self.data_hover_color
                porod_color = self.porod_hover_color
            else:
                guinier_color = self.guinier_color
                data_color = self.data_color
                porod_color = self.porod_color
        else:
            guinier_color = self.disabled_non_data_color
            data_color = self.data_color
            porod_color = self.disabled_non_data_color


        brush.setColor(guinier_color)
        rect = QtCore.QRect(0, 0, self.left_pad, self.vertical_size)
        painter.fillRect(rect, brush)

        grad = QtGui.QLinearGradient(positions[0], 0, positions[1], 0)
        grad.setColorAt(0.0, guinier_color)
        grad.setColorAt(1.0, data_color)
        rect = QtCore.QRect(positions[0], 0, widths[0], self.vertical_size)
        painter.fillRect(rect, grad)

        brush.setColor(data_color)
        rect = QtCore.QRect(positions[1], 0, widths[1], self.vertical_size)
        painter.fillRect(rect, brush)

        grad = QtGui.QLinearGradient(positions[2], 0, positions[3], 0)
        grad.setColorAt(0.0, data_color)
        grad.setColorAt(1.0, porod_color)
        rect = QtCore.QRect(positions[2], 0, widths[2], self.vertical_size)
        painter.fillRect(rect, grad)

        brush.setColor(porod_color)
        rect = QtCore.QRect(positions[3], 0, widths[3] + self.right_pad, self.vertical_size)
        painter.fillRect(rect, brush)

        #
        # Dividing lines
        #

        # Data range lines
        if self.isEnabled():
            pen = QtGui.QPen(mix_colours(self.hover_colour, guinier_color, 0.5), self.line_width)
        else:
            pen = QtGui.QPen(self.disabled_line_color, self.line_width)

        painter.setPen(pen)
        painter.drawLine(self.left_pad, 0, self.left_pad, self.vertical_size)


        if self.isEnabled():
            pen = QtGui.QPen(mix_colours(self.hover_colour, porod_color, 0.5), self.line_width)
        else:
            pen = QtGui.QPen(self.disabled_line_color, self.line_width)

        painter.setPen(pen)
        painter.drawLine(self.width() - self.right_pad, 0, self.width()-self.right_pad, self.vertical_size)

        # Main lines
        for i, x in enumerate(positions[1:-1]):
            if self.isEnabled():
                # different color if it's the one that will be moved
                if self._hovering and i == self._hover_id:
                    pen = QtGui.QPen(self.hover_colour, self.line_width)
                else:
                    pen = QtGui.QPen(self.text_color, self.line_width)
            else:
                pen = QtGui.QPen(self.disabled_line_color, self.line_width)

            painter.setPen(pen)
            painter.drawLine(x, 0, x, self.vertical_size)

        # Moving line
        if self._movement_line_position is not None:
            pen = QtGui.QPen(self.line_drag_color, self.line_width)
            painter.setPen(pen)
            painter.drawLine(self._movement_line_position, 0, self._movement_line_position, self.vertical_size)



        #
        # Labels
        #


        self._paint_label(self.guinier_label_position, "Guinier")
        self._paint_label(self.data_label_centre, "Data")
        # self._paint_label(self.transition_label_centre, "Transition") # Looks better without this
        self._paint_label(self.porod_label_centre, "Porod")


    def _paint_label(self, position: float, text: str, centre_justify=True):

        painter = QtGui.QPainter(self)

        pen = painter.pen()

        if self.isEnabled():
            pen.setColor(self.text_color)
        else:
            pen.setColor(self.disabled_text_color)

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


def mix_colours(a: QtGui.QColor, b: QtGui.QColor, k: float) -> QtGui.QColor:
    return QtGui.QColor(
        int(k * a.red() + (1-k) * b.red()),
        int(k * a.green() + (1-k) * b.green()),
        int(k * a.blue() + (1-k) * b.blue()),
        int(k * a.alpha() + (1-k) * b.alpha()))


def main():
    """ Show a demo of the slider """
    app = QtWidgets.QApplication([])
    slider = CorfuncSlider(enabled=True)
    slider.show()
    app.exec_()


if __name__ == "__main__":
    main()
