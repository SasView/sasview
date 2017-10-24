# -*- coding: utf-8 -*-

def main():
    startApplication("sasview")
    test.compare(waitForObjectExists(":qt_workspacechild.Fit panel - Active Fitting Optimizer: Levenberg-Marquardt_QWorkspaceTitleBar").visible, True)
    mouseClick(waitForObject(":groupBox.cbFitting_QComboBox"), 70, 10, 0, Qt.LeftButton)
    mouseClick(waitForObjectItem(":groupBox.cbFitting_QComboBox", "Invariant"), 52, 4, 0, Qt.LeftButton)
    test.compare(str(waitForObjectExists(":groupBox.cbFitting_QComboBox").currentText), "Invariant")
    test.compare(waitForObjectExists(":qt_workspacechild.Invariant Perspective_QWorkspaceTitleBar").visible, True)
    test.compare(str(waitForObjectExists(":qt_workspacechild.Invariant Perspective_QWorkspaceTitleBar").windowTitle), "Invariant Perspective")
    mouseClick(waitForObject(":groupBox.cbFitting_QComboBox"), 76, 13, 0, Qt.LeftButton)
    mouseClick(waitForObjectItem(":groupBox.cbFitting_QComboBox", "Fitting"), 61, 6, 0, Qt.LeftButton)
    test.compare(str(waitForObjectExists(":groupBox.cbFitting_QComboBox").currentText), "Fitting")
    test.compare(waitForObjectExists(":qt_workspacechild.Fit panel - Active Fitting Optimizer: Levenberg-Marquardt_QWorkspaceTitleBar").visible, True)
    test.compare(str(waitForObjectExists(":qt_workspacechild.Fit panel - Active Fitting Optimizer: Levenberg-Marquardt_QWorkspaceTitleBar").windowTitle), "Fit panel - Active Fitting Optimizer: Levenberg-Marquardt")
