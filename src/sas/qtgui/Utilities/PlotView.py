
from matplotlib.backends.qt_compat import QtWidgets

# The Figure object is used to create backend-independent plot representations.
from matplotlib.figure import Figure
from PySide6.QtWidgets import QComboBox, QLabel


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
