# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QSpacerItem, QSizePolicy, QLabel, QTableWidget
from PySide6.QtCore import QSize
from PySide6.QtDataVisualization import Q3DScatter, QScatterDataItem, QScatter3DSeries, QValue3DAxis
from PySide6.QtGui import QVector3D

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py

from ViewerAllOptions import ViewerButtons, ViewerModelRadius
from sas.qtgui.Perspectives.Shape2SAS.DataHandler.Parameters import ModelPointDistribution
from sas.qtgui.Perspectives.Shape2SAS.Tables.ViewerTable import ViewTable

class ViewerModel:
    """Graphics view of designed model"""
    def __init__(self, parent=None):
        
        ### Qt setup ###
        ###3D plot view of model
        self.scatter = Q3DScatter()
        self.series = QScatter3DSeries()
        self.scatter.addSeries(self.series)

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

        #NOTE:We should use QTableView instead of QTableWidget
        self.viewerSubunitOutlining = QTableWidget() #ViewerSubunitOutlining()
        self.viewerSubunitOutlining.setMinimumSize(QSize(271, 200))  
        self.viewerSubunitOutlining.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        

        ###Layout for GUI
        layout = QVBoxLayout()
        layout.setContentsMargins(0,10,0,0)#remove margins

        spacer = QSpacerItem(271, 20, QSizePolicy.Minimum)
        subunitTableLabel = QLabel("Subunit table")

        layout.addWidget(self.scatterContainer)
        layout.addWidget(self.viewerButtons)
        layout.addWidget(self.viewerModelRadius)
        layout.addItem(spacer)
        layout.addWidget(subunitTableLabel)
        layout.addWidget(self.viewerSubunitOutlining)

        self.setLayout(layout)
        self.setFixedWidth(271)

        self.Viewmodel_modul = QWidget()
        self.Viewmodel_modul.setLayout(layout)
        self.Viewmodel_modul.setFixedWidth(271)


    def setAxis(self, distr: ModelPointDistribution):
        """Set axis for the model"""
        X_ax = QValue3DAxis()
        X_ax.setTitle("X")
        X_ax.setRange(min(distr.x), max(distr.x))

        Y_ax = QValue3DAxis()
        Y_ax.setTitle("Y")
        Y_ax.setRange(min(distr.y), max(distr.y))

        Z_ax = QValue3DAxis()
        Z_ax.setTitle("Z")
        Z_ax.setRange(min(distr.z), max(distr.z))

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


    def setPlot(self, distr: ModelPointDistribution):
        """Plot the model"""
        data = []
        for i in range(len(distr.x)):
            data.append(QScatterDataItem(QVector3D(distr.x[i], distr.y[i], distr.z[i])))
        self.setAxis(distr)
        self.series.dataProxy().resetArray(data)

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

    #def onColourChanged(self):
    #    """Change the colour of the subunit"""
    #    #dynamically update colour of subunit based on input from the table







if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = ViewerModel()
    widget.show()
    sys.exit(app.exec())
