
import sys, os, traceback

from sas.qtgui.Plotting2.Plots.PlotGroup import PlotGroup

from sas.qtgui.Plotting2.Plots.PlotGroupDialog import PlotGroupDialog
from sas.qtgui.Plotting2.Plots.NotionalPlot import NotionalPlot


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

    print("error message:\n", tb)
    QtWidgets.QApplication.quit()

sys.excepthook = excepthook


from PySide6 import QtWidgets
from PySide6.QtCore import Qt

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

app = QtWidgets.QApplication([])

app.setAttribute(Qt.AA_EnableHighDpiScaling)
app.setAttribute(Qt.AA_ShareOpenGLContexts)


g1 = PlotGroup()
g2 = PlotGroup()

p1 = NotionalPlot()
p2 = NotionalPlot()
p3 = NotionalPlot()

g1.add_plot(p1)
g2.add_plot(p1)
g2.add_plot(p2)

gv1 = PlotGroupDialog(g1.identifier)
gv2 = PlotGroupDialog(g2.identifier)

from sas.qtgui.Plotting2.PlotManagement import PlotRecord
print([PlotRecord.plot_group(i) for i in PlotRecord._plot_groups])

gv1.show()
gv2.show()

app.exec_()
