# Global
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import QSize
from PySide6.QtDataVisualization import Q3DScatter, QScatter3DSeries, QScatterDataItem, QValue3DAxis
from PySide6.QtGui import QColor, QVector3D
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QLabel, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget

from sas.qtgui.Calculators.Shape2SAS.PlotAspects.plotAspects import ViewerPlotDesign

# Local Perspectives
from sas.qtgui.Calculators.Shape2SAS.ViewerAllOptions import ViewerButtons, ViewerModelRadius
from sas.sascalc.shape2sas.Shape2SAS import ModelPointDistribution, TheoreticalScattering


class ViewerModel(QWidget):
    """Graphics view of designed model"""
    def __init__(self, parent=None):
        super().__init__()

        ### Qt setup ###
        ###3D plot view of model
        self.scatter = Q3DScatter()

        """
        NOTE: Orignal intend was to create
        QScatter3DSeries() in setPlot() method. However,
        this causes some initialisation problems.
        Initialising setPlot() method might fix this,
        but then a fictive model would be needed.
        TODO: Investigate a better solution.
        """
        self.seriesRed = QScatter3DSeries()
        self.seriesGreen = QScatter3DSeries()
        self.seriesBlue = QScatter3DSeries()
        self.seriesRed.setBaseColor("Red")
        self.seriesGreen.setBaseColor("Green")
        self.seriesBlue.setBaseColor("Blue")
        self.scatter.addSeries(self.seriesRed)
        self.scatter.addSeries(self.seriesGreen)
        self.scatter.addSeries(self.seriesBlue)
        self.dict_series = {"Red": self.seriesRed, "Green": self.seriesGreen, "Blue": self.seriesBlue}

        self.scatterContainer = QWidget.createWindowContainer(self.scatter)
        self.scatter.setMinimumSize(QSize(271, 271))
        self.scatter.setHorizontalAspectRatio(1.0)
        self.scatter.setAspectRatio(1.0)
        self.scatterContainer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.initialiseAxis()

        #General controls
        ### xy, xz, yz buttons (Class ViewerButtons)
        self.viewerButtons = ViewerButtons()
        self.viewerModelRadius = ViewerModelRadius()

        self.viewerButtons.pushButton_2.clicked.connect(self.onXYClicked)
        self.viewerButtons.pushButton_3.clicked.connect(self.onYZClicked)
        self.viewerButtons.pushButton.clicked.connect(self.onZXClicked)
        self.scatter.scene().activeCamera().zoomLevelChanged.connect(self.onZoomChanged)
        self.viewerModelRadius.doubleSpinBox.valueChanged.connect(self.setZoom)

        #2D plot of P(q)
        self.scattering = QGraphicsView()
        self.scattering.setMinimumSize(QSize(271, 271))
        self.scattering.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scattering.setBackgroundBrush(QColor(255, 255, 255))
        self.scene = QGraphicsScene()
        self.scattering.setScene(self.scene)

        ###Layout for GUI
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 10, 0, 0)#remove margins

        spacer = QSpacerItem(271, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        subunitTableLabel = QLabel("Scattering of P(q)")

        layout.addWidget(self.scatterContainer)
        layout.addWidget(self.viewerButtons)
        layout.addWidget(self.viewerModelRadius)
        layout.addItem(spacer)
        layout.addWidget(subunitTableLabel)
        layout.addWidget(self.scattering)

        self.setLayout(layout)

        self.Viewmodel_modul = QWidget()
        self.Viewmodel_modul.setLayout(layout)

    def setScatteringPlot(self, theo: TheoreticalScattering):
        """Set the scattering plot"""

        self.scene.clear()

        figure = Figure()
        ax = figure.add_subplot(111)
        ax.set_title("P(q) plot")
        ax.set_xlabel("q")
        ax.set_ylabel("P(q)")
        ax.plot(theo.q, theo.I, "-k", label="P(q)")

        ax.set_xscale('log')
        ax.set_yscale('log')

        ax.legend()
        ax.grid(True)


        canvas = FigureCanvas(figure)
        self.scene.addWidget(canvas)
        self.scattering.fitInView(self.scene.sceneRect())
        self.scatter.show()

    def initialiseAxis(self):
        """Initialise axis for the model"""

        self.X_ax = QValue3DAxis()
        self.X_ax.setTitle("X")
        self.X_ax.setRange(-10, 10)

        self.Y_ax = QValue3DAxis()
        self.Y_ax.setTitle("Y")
        self.Y_ax.setRange(-10, 10)

        self.Z_ax = QValue3DAxis()
        self.Z_ax.setTitle("Z")
        self.Z_ax.setRange(-10, 10)

        self.X_ax.setLabelFormat("%.2f")  # Set the label format
        self.Y_ax.setLabelFormat("%.2f")
        self.Z_ax.setLabelFormat("%.2f")

        self.X_ax.setLabelAutoRotation(30)  # Set the label auto-rotation
        self.Y_ax.setLabelAutoRotation(30)
        self.Z_ax.setLabelAutoRotation(30)

        self.X_ax.setTitleVisible(True)
        self.Y_ax.setTitleVisible(True)
        self.Z_ax.setTitleVisible(True)

        self.scatter.setAxisX(self.X_ax)
        self.scatter.setAxisY(self.Y_ax)
        self.scatter.setAxisZ(self.Z_ax)

    def setAxis(self, x_range: (float, float), y_range: (float, float), z_range: (float, float)):
        """Set axis for the model"""

        #FIXME: even if min and max are the same for X, Y, Z, a sphere still looks like an ellipsoid
        #Tried with global min and max, and by centering the model, but no success.
        self.X_ax.setRange(*x_range)
        self.Y_ax.setRange(*y_range)
        self.Z_ax.setRange(*z_range)

        self.scatter.setAxisX(self.X_ax)
        self.scatter.setAxisY(self.Y_ax)
        self.scatter.setAxisZ(self.Z_ax)

    def setPlot(self, distr: ModelPointDistribution, design: ViewerPlotDesign):
        """Plot the model"""

        colours = design.colour

        for series in self.dict_series.values():
           data = []
           series.dataProxy().resetArray(data)

        # Check if we have any data at all
        if not distr.x or len(distr.x) == 0:
            return

        minx, maxx = min(distr.x[0]), max(distr.x[0])
        miny, maxy = min(distr.y[0]), max(distr.y[0])
        minz, maxz = min(distr.z[0]), max(distr.z[0])

        for subunit in range(len(colours)):
            # Skip empty subunits - handle numpy arrays properly
            try:
                if (subunit >= len(distr.x)
                        or not hasattr(distr.x[subunit], '__len__')
                        or len(distr.x[subunit]) == 0):
                    continue
            except (ValueError, TypeError):
                # Handle numpy array comparison issues
                continue

            series = self.dict_series[colours[subunit]]
            data = []
            for index in range(len(distr.x[subunit])):
                data.append(QScatterDataItem(QVector3D(distr.x[subunit][index], distr.y[subunit][index], distr.z[subunit][index])))

            minx = min(minx, min(distr.x[subunit]))
            maxx = max(maxx, max(distr.x[subunit]))
            miny = min(miny, min(distr.y[subunit]))
            maxy = max(maxy, max(distr.y[subunit]))
            minz = min(minz, min(distr.z[subunit]))
            maxz = max(maxz, max(distr.z[subunit]))

            series.dataProxy().addItems(data)

        self.setAxis((minx, maxx), (miny, maxy), (minz, maxz))

    def onXYClicked(self):
        """XY view"""
        self.scatter.scene().activeCamera().setCameraPosition(0, 0, 110)

    def onYZClicked(self):
        """YZ view"""
        self.scatter.scene().activeCamera().setCameraPosition(-90, 0, 110)

    def onZXClicked(self):
        """ZX view"""
        self.scatter.scene().activeCamera().setCameraPosition(0, -90, 110)

    def setZoom(self):
        """Zoom in/out"""
        self.scatter.scene().activeCamera().setZoomLevel(self.viewerModelRadius.doubleSpinBox.value())

    def onZoomChanged(self):
        """Change zoom value on doubleSpinBox"""
        zoom_val = self.scatter.scene().activeCamera().zoomLevel()
        self.viewerModelRadius.doubleSpinBox.setValue(zoom_val)

    def setClearScatteringPlot(self):
        """Clear the Scattering plot"""
        self.scene.clear()

    def setClearModelPlot(self):
        """Clear the model plot"""

        #reset model
        for series in self.dict_series.values():
            data = []
            series.dataProxy().resetArray(data)

        #reset view
        self.scene.clear()
        self.scatter.scene().activeCamera().setCameraPosition(0, 0, 110)

        #reset axis
        self.setAxis((-10, 10), (-10, 10), (-10, 10))
