# -*- coding: utf-8 -*-

def main():
    startApplication("sasview")
    clickTab(waitForObject(":Data Explorer.DataLoadWidget_DataExplorerWindow"), "Theory")
    mouseClick(waitForObject(":groupBox_6.cbCategory_QComboBox"), 164, 12, 0, Qt.LeftButton)
    mouseClick(waitForObjectItem(":groupBox_6.cbCategory_QComboBox", "Cylinder"), 154, 1, 0, Qt.LeftButton)
    mouseClick(waitForObject(":groupBox_6.cbModel_QComboBox"), 53, 12, 0, Qt.LeftButton)
    mouseClick(waitForObjectItem(":groupBox_6.cbModel_QComboBox", "core\\_shell\\_bicelle\\_elliptical"), 80, 10, 0, Qt.LeftButton)    
    
    test.compare(str(waitForObjectExists(":FittingWidgetUI.cmdPlot_QPushButton_2").text), "Calculate")
    test.compare(waitForObjectExists(":FittingWidgetUI.cmdFit_QPushButton").visible, True)
    test.compare(waitForObjectExists(":FittingWidgetUI.cmdFit_QPushButton").enabled, False)
    test.compare(waitForObjectExists(":FittingWidgetUI.cmdHelp_QPushButton").enabled, True)
    clickButton(waitForObject(":FittingWidgetUI.cmdPlot_QPushButton_2"))
    snooze(2)
    test.compare(waitForObjectExists(":FittingWidgetUI.cmdPlot_QPushButton_2").enabled, True)
    test.compare(str(waitForObjectExists(":FittingWidgetUI.cmdPlot_QPushButton_2").text), "Show Plot")
    test.compare(waitForObjectExists(":freezeView.M1 [core_shell_bicelle_elliptical]_QModelIndex").checkState, "checked")
    test.compare(waitForObjectExists(":freezeView.M1 [core_shell_bicelle_elliptical]_QModelIndex").collapsed, True)
    test.compare(waitForObjectExists(":freezeView.M1 [core_shell_bicelle_elliptical]_QModelIndex").text, "M1 [core_shell_bicelle_elliptical]")
    waitForObjectItem(":groupBox_2.freezeView_QTreeView", "M1 [core\\_shell\\_bicelle\\_elliptical]")
    clickItem(":groupBox_2.freezeView_QTreeView", "M1 [core\\_shell\\_bicelle\\_elliptical]", -8, 8, 0, Qt.LeftButton)
    waitForObjectItem(":groupBox_2.freezeView_QTreeView", "M1 [core\\_shell\\_bicelle\\_elliptical].Info")
    clickItem(":groupBox_2.freezeView_QTreeView", "M1 [core\\_shell\\_bicelle\\_elliptical].Info", -5, 8, 0, Qt.LeftButton)
    clickButton(waitForObject(":groupBox_2.cmdFreeze_QPushButton"))
    clickTab(waitForObject(":Data Explorer.DataLoadWidget_DataExplorerWindow"), "Data")
    # Figure out how to use wildcards within waitForObjectExists() argument list
    
    #test.compare(waitForObjectExists(":treeView.M1 [core_shell_bicelle_elliptical]_@????_QModelIndex").enabled, True)
    #test.compare(waitForObjectExists("{column='0' container=':groupBox.treeView_QTreeView' text?='M1 [core_shell_bicelle_elliptical]_@*' type='QModelIndex'}").enabled, True)
    #test.compare(waitForObjectExists(":treeView.M1 [core_shell_bicelle_elliptical]_@????_QModelIndex").checkState, "checked")
    #test.compare(waitForObjectExists(":treeView.M1 [core_shell_bicelle_elliptical]_@????_QModelIndex").text, "M1 [core_shell_bicelle_elliptical]_@????")

    clickTab(waitForObject(":Data Explorer.DataLoadWidget_DataExplorerWindow"), "Theory")
    clickButton(waitForObject(":groupBox_4.cmdNew_2_QPushButton"))
    test.compare(waitForObjectExists(":qt_workspacechild.Graph1_QWorkspaceTitleBar").enabled, True)
    test.compare(waitForObjectExists(":qt_workspacechild.Graph1_QWorkspaceTitleBar").visible, True)
    test.compare(str(waitForObjectExists(":qt_workspacechild.Graph1_QWorkspaceTitleBar").windowTitle), "Graph1")
    test.vp("VP1")
    