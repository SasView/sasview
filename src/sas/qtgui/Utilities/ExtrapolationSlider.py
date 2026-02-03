import math
from enum import Enum

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics

from sas.sascalc.util import ExtrapolationInteractionState, ExtrapolationParameters


class SliderPerspective(Enum):
    INVARIANT = "Invariant"
    CORFUNC = "Corfunc"

class ExtrapolationSlider(QtWidgets.QWidget):
    """ Slider that allows the selection of the different Q-ranges involved in interpolation,
    and that provides some visual cues to how it works."""

    valueEdited = Signal(ExtrapolationParameters, name='valueEdited')
    valueEditing = Signal(ExtrapolationInteractionState, name='valueEditing')

    def __init__(self,
                 lower_label: str,
                 upper_label: str,
                 perspective: SliderPerspective,
                 parameters: ExtrapolationParameters = ExtrapolationParameters(1,2,4,8,16,32,64),
                 enabled: bool = False,
                 *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.setEnabled(enabled)

        parameter_problems = self.find_parameter_problems(parameters)
        if parameter_problems is not None:
            raise ValueError(parameter_problems)

        self._min = parameters.ex_q_min         # extrapolation min
        self._data_min = parameters.data_q_min  # actual data min
        self._point_1 = parameters.point_1
        self._point_2 = parameters.point_2
        self._point_3 = parameters.point_3
        self._data_max = parameters.data_q_max  # actual data max
        self._max = parameters.ex_q_max         # extrapolation max

        # Default to data min/max if extrapolation min/max not set
        if self._min is None:
            self._min = self._data_min
        if self._max is None:
            self._max = self._data_max

        self._lower_label = lower_label
        self._upper_label = upper_label

        self.perspective = perspective

        # Display Parameters
        self.vertical_size = 20
        self.left_pad = 60
        self.right_pad = 60
        self.line_width = 3
        self.lower_color = QtGui.QColor('orange')
        self.data_color = QtGui.QColor('white')
        self.upper_color = QtGui.QColor('green')
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
        self.lower_hover_color = mix_colours(self.lower_color, mix_color, mix_fraction)
        self.data_hover_color = mix_colours(self.data_color, mix_color, mix_fraction)
        self.upper_hover_color = mix_colours(self.upper_color, mix_color, mix_fraction)

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
        """ Check an extrapolation parameters object for consistency

        :param params: An extrapolation parameters object describing a desired state
        :returns: A description of the problem if it exists, otherwise None
        """
        ex_min = params.ex_q_min
        data_min = params.data_q_min
        p1, p2, p3 = params.point_1, params.point_2, params.point_3
        data_max = params.data_q_max
        ex_max = params.ex_q_max

        checks = [
            (p1 < data_min, "q_point_1 should be larger than min_q"),
            (ex_min is not None and p1 <= ex_min, "q_point_1 should be larger than ex_q_min"),
            (p1 >= p2, "q_point_1 should be smaller than q_point_2"),
            (p2 >= p3, "q_point_2 should be smaller than q_point_3"),
        ]
        for cond, msg in checks:
            if cond:
                return msg

        if ex_max is not None:  # extrapolating
            if p2 >= data_max:
                return "q_point_2 should be smaller than max_q"
            if p3 >= ex_max:
                return "q_point_3 should be smaller than ex_q_max"
        else:
            if p3 >= data_max:
                return "q_point_3 should be smaller than max_q"

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
                safe_pos = self._sanitise_new_position(self._drag_id, self._movement_line_position)
                self.set_boundary(self._drag_id, self.inverse_transform(safe_pos))

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
        data_min_px = int(self.transform(self._data_min))
        data_max_px = int(self.transform(self._data_max))

        if line_id == 0:
            if self.left_pad > new_position or new_position <= data_min_px:
                return data_min_px + delta
            elif new_position > l2:
                return l2 - delta
            else:
                return new_position

        elif line_id == 1:
            if l1 > new_position:
                return l1 + delta
            elif new_position > l3:
                return l3 - delta
            elif new_position >= data_max_px:
                return data_max_px - delta
            else:
                return new_position

        elif line_id == 2:
            if l2 > new_position:
                return l2 + delta
            elif new_position >= self.width() - self.right_pad:
                return self.width() - self.right_pad - delta
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
        return ExtrapolationParameters(self._min, self._data_min, self._point_1, self._point_2, self._point_3, self._data_max, self._max)

    @extrapolation_parameters.setter
    def extrapolation_parameters(self, params: ExtrapolationParameters):
        if params is not None:
            self._min = params.ex_q_min if params.ex_q_min is not None else params.data_q_min
            self._data_min = params.data_q_min
            self._point_1 = params.point_1
            self._point_2 = params.point_2
            self._point_3 = params.point_3
            self._data_max = params.data_q_max
            self._max = params.ex_q_max if params.ex_q_max is not None else params.data_q_max
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
    def lower_label_position(self) -> float:
        """ Position to put the text for the lower region"""
        return 0.5 * self.transform(self._point_1)

    @property
    def data_label_centre(self) -> float:
        """ Centre of the interpolation region"""
        return 0.5 * (self.transform(self._point_1) + self.transform(self._point_2))

    @property
    def transition_label_centre(self) -> float:
        """ Centre of the data-upper transition"""
        return 0.5 * (self.transform(self._point_2) + self.transform(self._point_3))

    @property
    def upper_label_centre(self) -> float:
        """
        Centre of the upper region
        - Between point 2 and point 3 for invariant
        - Between point 3 and widget edge for corfunc
        """
        if self.perspective == "Invariant":
            return 0.5 * (self.transform(self._point_2) + self.transform(self._point_3))

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
                     self.transform(self._data_min),
                     self.transform(self._point_1),
                     self.transform(self._point_2),
                     self.transform(self._point_3),
                     self.transform(self._data_max),
                     self.transform(self._max)]

        positions = [int(x) for x in positions]

        # compute widths for all adjacent segments
        segment_widths = [positions[i+1] - positions[i] for i in range(len(positions)-1)]

        #
        # Draw the sections covering the entire widget
        #
        brush.setStyle(Qt.SolidPattern)
        if self.isEnabled():
            if self._hovering or self._dragging:
                lower_color = self.lower_hover_color
                data_color = self.data_hover_color
                upper_color = self.upper_hover_color
            else:
                lower_color = self.lower_color
                data_color = self.data_color
                upper_color = self.upper_color
        else:
            lower_color = self.disabled_non_data_color
            data_color = self.data_color
            upper_color = self.disabled_non_data_color

        brush.setColor(lower_color)
        rect = QtCore.QRect(0, 0, self.left_pad, self.vertical_size)
        painter.fillRect(rect, brush)

        # segment 0: lower; (gradient lower -> data) -> white; min/data_min -> point_1 (positions[2])
        lower_width = segment_widths[0] + segment_widths[1]
        if lower_width > 0:
            grad = QtGui.QLinearGradient(positions[0], 0, positions[2], 0)
            grad.setColorAt(0.0, lower_color)
            grad.setColorAt(1.0, data_color)
            rect = QtCore.QRect(positions[0], 0, lower_width, self.vertical_size)
            painter.fillRect(rect, grad)

        # segment 1: data; solid data color; point 1 -> point 2 (positions[3])
        if segment_widths[2] > 0:
            brush.setColor(data_color)
            rect = QtCore.QRect(positions[2], 0, segment_widths[2], self.vertical_size)
            painter.fillRect(rect, brush)

        # segment 2: upper; gradient data->upper; point 2 -> point_3 (positions[4])
        if segment_widths[3] > 0:
            grad = QtGui.QLinearGradient(positions[3], 0, positions[4], 0)
            grad.setColorAt(0.0, data_color)
            grad.setColorAt(1.0, upper_color)
            rect = QtCore.QRect(positions[3], 0, segment_widths[3], self.vertical_size)
            painter.fillRect(rect, grad)

        # remaining area from point_2 to right boundary: paint with upper_color
        right_boundary = self.width() - self.right_pad
        rest_start = positions[4]
        rest_width = max(0, right_boundary - rest_start)
        if rest_width > 0:
            brush.setColor(upper_color)
            rect = QtCore.QRect(rest_start, 0, rest_width, self.vertical_size)
            painter.fillRect(rect, brush)

        # right pad (ensure full coverage to widget edge)
        brush.setColor(upper_color)
        rect = QtCore.QRect(self.width() - self.right_pad, 0, self.right_pad, self.vertical_size)
        painter.fillRect(rect, brush)

        #
        # Dividing lines
        #

        pen = QtGui.QPen(self.disabled_non_data_color, self.line_width)
        painter.setPen(pen)

        # extrapolation boundaries - min / max - render as grey (non-moveable)
        if self._min is not None and self._max is not None:
            painter.drawLine(positions[0], 0, positions[0], self.vertical_size)
            painter.drawLine(positions[6], 0, positions[6], self.vertical_size)

        # data_min / data_max - render as grey (non-moveable)
        painter.drawLine(positions[1], 0, positions[1], self.vertical_size)  # data_min
        painter.drawLine(positions[5], 0, positions[5], self.vertical_size)  # data_max

        # Main lines (point_1, point_2, point_3)
        for i, x in enumerate(positions[2:5]):
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
        self._paint_label(self.lower_label_position, self._lower_label)
        self._paint_label(self.data_label_centre, "Data")
        self._paint_label(self.upper_label_centre, self._upper_label)

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
    slider = ExtrapolationSlider(lower_label="Low-Q", upper_label="High-Q", enabled=True)
    slider.show()
    app.exec_()


if __name__ == "__main__":
    main()
