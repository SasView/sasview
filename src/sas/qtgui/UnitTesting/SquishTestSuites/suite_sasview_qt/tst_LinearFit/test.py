# -*- coding: utf-8 -*-

def main():
    startApplication("sasview")
    clickButton(waitForObject(":groupBox.cmdLoad_QPushButton"))
    waitForObjectItem(":stackedWidget.listView_QListView", "test")
    doubleClickItem(":stackedWidget.listView_QListView", "test", 28, 5, 0, Qt.LeftButton)
    waitForObjectItem(":stackedWidget.listView_QListView", "1d\\_data")
    doubleClickItem(":stackedWidget.listView_QListView", "1d\\_data", 48, 16, 0, Qt.LeftButton)
    waitForObjectItem(":stackedWidget.listView_QListView", "cyl\\_400\\_20\\.txt")
    doubleClickItem(":stackedWidget.listView_QListView", "cyl\\_400\\_20\\.txt", 80, 9, 0, Qt.LeftButton)
    clickButton(waitForObject(":groupBox_3.cmdNew_QPushButton"))
    openContextMenu(waitForObject(":qt_workspacechild_FigureCanvasQTAgg_4"), 192, 169, 0)
    activateItem(waitForObjectItem(":MainWindow_QMenu", "cyl\\_400\\_20.txt"))
    activateItem(waitForObjectItem(":cyl_400_20.txt_QMenu", "Linear Fit"))
    clickButton(waitForObject(":LinearFitUI.cmdFit_QPushButton"))
    clickButton(waitForObject(":LinearFitUI.cmdClose_QPushButton"))
    test.vp("VP1")
