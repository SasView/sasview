from matplotlib.backends.qt_compat import QtWidgets

# The Figure object is used to create backend-independent plot representations.
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHeaderView, QLabel, QTableWidget, QTableWidgetItem


class FitResultView(QtWidgets.QWidget):
    state = None
    show_plot_selector = False

    def __init__(self, **kw):
        QtWidgets.QWidget.__init__(self, **kw)
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as Toolbar

        # Can specify name on
        if 'title' in kw:
            self.title = kw['title']

        self.state = None

        # Instantiate a figure object that will contain our plots.
        figure = Figure(figsize=(10,10), dpi=72)

        # Initialize the figure canvas, mapping the figure object to the plot
        # engine backend.
        canvas = FigureCanvas(figure)
        self.canvas = canvas
        self.figure = figure

        # Instantiate the matplotlib navigation toolbar and explicitly show it.
        mpl_toolbar = Toolbar(canvas, self, False)

        layout = QtWidgets.QVBoxLayout()
        if self.show_plot_selector:
            label = QLabel("Select plot:")
            layout.addWidget(label)
            self.dropdown = QComboBox()
            layout.addWidget(self.dropdown)
            self.dropdown.currentIndexChanged.connect(self.plot)

        layout.addWidget(canvas)
        layout.addWidget(mpl_toolbar)
        self.setLayout(layout)

    def update(self, state):
        self.state = state
        self.plot()
        self.canvas.draw_idle()

    def plot(self):
        raise NotImplementedError("PlotView needs a plot method... subclass it")


class ConvergenceView(FitResultView):
    def plot(self):
        self.figure.clear()
        best, pop = self.state.convergence[:, 0], self.state.convergence[:, 1:]
        plot_convergence(pop, best, self.figure)
        self.canvas.draw_idle()


class CorrelationView(FitResultView):
    def plot(self):
        from bumps.dream.views import plot_corrmatrix

        draw = self.state.uncertainty_state.draw()
        self.figure.clear()
        plot_corrmatrix(draw=draw, fig=self.figure)
        self.canvas.draw_idle()

class CorrelationTable(QtWidgets.QWidget):
    def __init__(self, **kw):
        QtWidgets.QWidget.__init__(self, **kw)
        if 'title' in kw:
            self.title = kw['title']
        self.state = None
        self.table = QTableWidget()
        self.table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.table.setShowGrid(True)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #a0a0a0;
                border: 1px solid #a0a0a0;
            }
            QTableWidget::item {
                border: 1px solid #c0c0c0;
                padding: 5px;
            }
        """)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

    def update(self, state):
        self.state = state
        self.plot()

    def _parse_stats(self):
        """Parse correlation statistics from the uncertainty state.

        Returns:
            tuple: (headers, data_rows) where headers is a list of column names
                   and data_rows is a list of lists containing the formatted data.
        """
        from bumps.dream.stats import format_vars, parse_var, var_stats
        import re

        # Get formatted statistics from the uncertainty state
        draw = self.state.uncertainty_state.draw()
        stats = var_stats(draw)
        formatted_output = format_vars(stats)

        # Parse the formatted string into table data using parse_var
        lines = [line.strip() for line in formatted_output.split('\n') if line.strip()]
        if not lines:
            return [], []

        # Parse headers from the first line by extracting bracketed intervals and words
        header_line = lines[0]
        # Extract column headers, treating bracketed text as single units
        headers = re.findall(r'\[.*?\]|\S+', header_line)

        # Extract data rows using parse_var to parse each line, skipping the header
        data_rows = []
        for line in lines[1:]:
            parsed = parse_var(line)
            if parsed:
                # Use parse_var to extract all values, then format them for display
                row_data = [
                    parsed.name,
                    f"{parsed.mean:.6g}",
                    f"{parsed.median:.6g}",
                    f"{parsed.best:.6g}",
                    f"[ {parsed.p68[0]:.6g} {parsed.p68[1]:.6g} ]",
                    f"[ {parsed.p95[0]:.6g} {parsed.p95[1]:.6g} ]",
                ]
                data_rows.append(row_data)

        return headers, data_rows

    def plot(self):
        """Display correlation statistics in a table format."""
        headers, data_rows = self._parse_stats()
        if not headers or not data_rows:
            return

        # Configure table dimensions
        self.table.setRowCount(len(data_rows))
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        # Add tooltip to "best" column header
        if "best" in headers:
            best_column_index = headers.index("best")
            best_header_item = self.table.horizontalHeaderItem(best_column_index)
            if best_header_item is not None:
                best_header_item.setToolTip("Point estimate")

        # Populate table cells with left-aligned text
        for row_idx, row_data in enumerate(data_rows):
            for col_idx, cell_value in enumerate(row_data):
                item = QTableWidgetItem(cell_value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_idx, col_idx, item)

        # Make columns stretch to fill available width
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

class UncertaintyView(FitResultView):

    def plot(self):
        from bumps.dream.stats import var_stats
        from bumps.dream.varplot import plot_vars
        draw = self.state.uncertainty_state.draw()
        stats = var_stats(draw)
        self.figure.clear()
        plot_vars(draw, stats, fig=self.figure)
        self.canvas.draw_idle()

class TraceView(FitResultView):
    show_plot_selector = True

    def update(self, state):
        self.state = state
        vars = state.uncertainty_state.labels
        self.dropdown.clear()
        self.dropdown.addItems(vars)
        self.figure.clear()
        self.plot()

    def plot(self):
        from bumps.dream.views import plot_trace
        var = self.dropdown.currentIndex()
        self.figure.clear()
        plot_trace(self.state.uncertainty_state, var=var, fig=self.figure)
        self.canvas.draw_idle()


def plot_convergence(pop, best, fig):
    import numpy as np
    ni, npop = pop.shape
    iternum = np.arange(1, ni + 1)
    tail = int(0.25 * ni)
    axes = fig.add_subplot(111)
    if npop == 5:
        axes.fill_between(iternum[tail:], pop[tail:, 1], pop[tail:, 3], color="lightgreen", label="20% to 80% range")
        axes.plot(iternum[tail:], pop[tail:, 2], label="median", color="green", alpha=0.5)
        axes.plot(iternum[tail:], pop[tail:, 0], label="population best", linestyle="dashed", color="green")
    axes.plot(iternum[tail:], best[tail:], label="best", color="red")
    axes.set_xlabel("iteration number")
    axes.set_ylabel("chisq")
    axes.legend()
