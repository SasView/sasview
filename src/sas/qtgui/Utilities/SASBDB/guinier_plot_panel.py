"""
Embedded Guinier plot (ln(I) vs q²) for the SASBDB export dialog.
"""
from __future__ import annotations

import logging

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6 import QtWidgets

logger = logging.getLogger(__name__)


class GuinierPlotPanel(QtWidgets.QWidget):
    """
    Matplotlib panel: scatter ln(I) vs q², fit segment, extrapolation to q²=0.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Figure size scaled with Guinier plot widget (see SASBDBDialogUI.ui).
        self._figure = Figure(figsize=(5.5, 2.1), dpi=100, layout="none")
        self._canvas = FigureCanvas(self._figure)
        self._axes = self._figure.add_subplot(111)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._canvas)
        self._show_placeholder()

    def _apply_compact_margins(self) -> None:
        """Tight margins so axis labels fit in a short vertical space."""
        self._figure.subplots_adjust(
            left=0.2, right=0.99, top=0.86, bottom=0.3
        )

    def _show_placeholder(self, message: str = "No 1D data") -> None:
        self._axes.clear()
        self._axes.set_axis_off()
        self._axes.text(
            0.5,
            0.5,
            message,
            ha="center",
            va="center",
            transform=self._axes.transAxes,
            fontsize=16,
            color="gray",
        )
        self._apply_compact_margins()
        self._canvas.draw_idle()

    def update_plot(
        self,
        q: np.ndarray | None,
        I: np.ndarray | None,
        q_start: float | None,
        q_end: float | None,
        fit_a: float | None,
        fit_b: float | None,
    ) -> None:
        """
        Redraw the Guinier plot.

        :param q: Scattering vector (same units as UI Q start / Q end)
        :param I: Intensity
        :param q_start: Left vertical marker (native q)
        :param q_end: Right vertical marker (native q)
        :param fit_a: Intercept of ln(I) = a + b q²
        :param fit_b: Slope (must be < 0 for a physical Guinier line)
        """
        if q is None or I is None or len(q) == 0:
            self._show_placeholder()
            return

        q = np.asarray(q, dtype=float)
        I = np.asarray(I, dtype=float)
        valid = (
            np.isfinite(q)
            & np.isfinite(I)
            & (q > 0)
            & (I > 0)
        )
        if not np.any(valid):
            self._show_placeholder("No valid I(q) > 0")
            return

        qv = q[valid]
        Iv = I[valid]
        q2 = qv**2
        ln_i = np.log(Iv)

        self._axes.clear()
        self._axes.set_axis_on()
        self._axes.set_title("Guinier", fontsize=11, pad=2)
        self._axes.set_xlabel(r"$q^2$", fontsize=10, labelpad=2)
        self._axes.set_ylabel(r"$\ln(I(q))$", fontsize=10, labelpad=2)
        self._axes.tick_params(axis="both", labelsize=9, length=4, pad=2)
        self._axes.scatter(q2, ln_i, s=16, c="C0", zorder=2)

        if q_start is not None and q_end is not None:
            qs_lo = min(q_start, q_end)
            qs_hi = max(q_start, q_end)
            x0 = qs_lo**2
            x1 = qs_hi**2
            for xv in (x0, x1):
                self._axes.axvline(xv, color="red", linestyle="--", linewidth=1.6, zorder=1)

            if fit_a is not None and fit_b is not None and fit_b < 0:
                xs = np.array([x0, x1], dtype=float)
                ys = fit_a + fit_b * xs
                self._axes.plot(xs, ys, color="red", linestyle="-", linewidth=2.2, zorder=3)
                xs_green = np.array([0.0, x0], dtype=float)
                ys_green = fit_a + fit_b * xs_green
                self._axes.plot(
                    xs_green,
                    ys_green,
                    color="green",
                    linestyle="--",
                    linewidth=1.8,
                    zorder=3,
                )

        self._axes.relim()
        self._axes.autoscale_view()
        self._apply_compact_margins()
        self._canvas.draw_idle()
