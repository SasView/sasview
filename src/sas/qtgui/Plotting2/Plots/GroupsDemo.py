from sas.qtgui.Plotting2.Plots.PlotGroup import PlotGroup
from sas.qtgui.Plotting2.PlotManagement import PlotRecord
from sas.qtgui.Plotting2.Plots.PlotGroupDialog import PlotGroupDialog
from sas.qtgui.Plotting2.Plots.NotionalPlot import NotionalPlot

g1 = PlotGroup()
g2 = PlotGroup()

gv1 = PlotGroupDialog(g1.identifier)
gv2 = PlotGroupDialog(g2.identifier)

p1 = NotionalPlot()
p2 = NotionalPlot()
p3 = NotionalPlot()

g1.add_plot(p1)
g2.add_plot(p1)
g2.add_plot(p1)

import os
from PySide6 import QtWidgets
from PySide6.QtCore import Qt

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
app = QtWidgets.QApplication([])

app.setAttribute(Qt.AA_EnableHighDpiScaling)
app.setAttribute(Qt.AA_ShareOpenGLContexts)

gv1.show()
gv2.show()

app.exec_()
