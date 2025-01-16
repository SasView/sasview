import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super(PlotWidget, self).__init__(parent)
        
        # Create a figure and canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        
        # Create a layout and add the canvas to the layout
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        
        # Set the layout to the QWidget
        self.setLayout(layout)
        
        # Adjust layout margins (left, top, right, bottom)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Plot something
        self.plot()

    def plot(self):
        ax = self.figure.add_subplot(111)
        ax.plot([0, 1, 2, 3], [10, 1, 20, 3])
        self.canvas.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Plot Example")
        
        # Create an instance of PlotWidget
        self.plot_widget = PlotWidget()
        
        # Set the central widget of the main window
        self.setCentralWidget(self.plot_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())