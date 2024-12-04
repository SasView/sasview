# This Python file uses the following encoding: utf-8
import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QSpacerItem, 
    QSizePolicy, QLabel, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem)
from PySide6.QtCore import QSize 
from PySide6.QtDataVisualization import (Q3DScatter, QScatterDataItem, 
QScatter3DSeries, QValue3DAxis)
from PySide6.QtGui import QVector3D, QColor, QImage, QPixmap
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py

from ViewerAllOptions import ViewerButtons, ViewerModelRadius
from sas.qtgui.Perspectives.Shape2SAS.calculations.Shape2SAS import ModelPointDistribution, TheoreticalScattering
from sas.qtgui.Perspectives.Shape2SAS.PlotAspects.plotAspects import ViewerPlotDesign

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
        self.scatterContainer.setFixedHeight(200)
        self.scatterContainer.setFixedWidth(271)

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
        self.scattering.setMinimumSize(QSize(271, 200))  
        self.scattering.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.scattering.setBackgroundBrush(QColor(255, 255, 255))
        self.scene = QGraphicsScene()
        self.scattering.setScene(self.scene)

        ###Layout for GUI
        layout = QVBoxLayout()
        layout.setContentsMargins(0,10,0,0)#remove margins

        spacer = QSpacerItem(271, 20, QSizePolicy.Minimum)
        subunitTableLabel = QLabel("Scattering of P(q)")

        layout.addWidget(self.scatterContainer)
        layout.addWidget(self.viewerButtons)
        layout.addWidget(self.viewerModelRadius)
        layout.addItem(spacer)
        layout.addWidget(subunitTableLabel)
        layout.addWidget(self.scattering)

        self.setLayout(layout)
        self.setFixedWidth(271)

        self.Viewmodel_modul = QWidget()
        self.Viewmodel_modul.setLayout(layout)
        self.Viewmodel_modul.setFixedWidth(271)


    def setScatteringPlot(self, theo: TheoreticalScattering):
        """Set the scattering plot"""

        self.scene.clear()

        figure = Figure(dpi=600)
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

        """#old code
        for i in range(len(theo.q) - 1):
            start_point = QPointF(theo.q[i], theo.I[i])
            end_point = QPointF(theo.q[i + 1], theo.I[i + 1])
            line = QGraphicsLineItem(QLineF(start_point, end_point))
            #line.setPen(pen)
            self.scene.addItem(line)

        self.scattering.fitInView(self.scene.sceneRect())
        self.scattering.update()
        """


    def setAxis(self, minx: float, maxx: float, miny: float, maxy: float, minz: float, maxz: float):
        """Set axis for the model"""

        X_ax = QValue3DAxis()
        X_ax.setTitle("X")
        X_ax.setRange(minx, maxx)

        Y_ax = QValue3DAxis()
        Y_ax.setTitle("Y")
        Y_ax.setRange(miny, maxy)

        Z_ax = QValue3DAxis()
        Z_ax.setTitle("Z")
        Z_ax.setRange(minz, maxz)

        X_ax.setLabelFormat("%.2f")  # Set the label format
        Y_ax.setLabelFormat("%.2f")
        Z_ax.setLabelFormat("%.2f")

        X_ax.setLabelAutoRotation(30)  # Set the label auto-rotation
        Y_ax.setLabelAutoRotation(30)
        Z_ax.setLabelAutoRotation(30)

        X_ax.setTitleVisible(True)
        Y_ax.setTitleVisible(True)
        Z_ax.setTitleVisible(True)

        self.scatter.setAxisX(X_ax)
        self.scatter.setAxisY(Y_ax)
        self.scatter.setAxisZ(Z_ax)


    def setPlot(self, distr: ModelPointDistribution, design: ViewerPlotDesign):
        """Plot the model"""

        colours = design.colour

        for series in self.dict_series.values():
           data = []
           series.dataProxy().resetArray(data)

        #due to inhomogeneous lists, np.min, np.max cannot be used
        minx, maxx = [], []
        miny, maxy = [], []
        minz, maxz = [], []
        for subunit in range(len(colours)):
            series = self.dict_series[colours[subunit]]
            data = []
            for index in range(len(distr.x[subunit])):
                data.append(QScatterDataItem(QVector3D(distr.x[subunit][index], distr.y[subunit][index], distr.z[subunit][index])))
            minx.append(min(distr.x[subunit]))
            maxx.append(max(distr.x[subunit]))
            miny.append(min(distr.y[subunit]))
            maxy.append(max(distr.y[subunit]))
            minz.append(min(distr.z[subunit]))
            maxz.append(max(distr.z[subunit]))
            
            series.dataProxy().addItems(data)

        self.setAxis(min(minx), max(maxx), min(miny), max(maxy), min(minz), max(maxz))


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
        pass




if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = ViewerModel()
    widget.show()
    sys.exit(app.exec())
