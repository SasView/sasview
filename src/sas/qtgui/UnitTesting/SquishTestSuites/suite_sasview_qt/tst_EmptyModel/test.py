# -*- coding: utf-8 -*-

def main():
    startApplication("sasview")
    mouseClick(waitForObject(":groupBox_6.cbCategory_QComboBox"), 79, 12, 0, Qt.LeftButton)
    mouseClick(waitForObjectItem(":groupBox_6.cbCategory_QComboBox", "Cylinder"), 70, 7, 0, Qt.LeftButton)
    snooze(1)
    # Change category to Cylinder
    test.compare(str(waitForObjectExists(":groupBox_6.cbModel_QComboBox").currentText), "barbell")
    snooze(1)
    test.compare(waitForObjectExists(":lstParams.sld_solvent_QModelIndex").text, "sld_solvent")
    test.compare(waitForObjectExists(":groupBox_6.cbStructureFactor_QComboBox").enabled, False)
    #mouseClick(waitForObject(":groupBox_6.cbModel_QComboBox"), 98, 6, 0, Qt.LeftButton)
    
    test.compare(waitForObjectExists(":groupBox_7.chkPolydispersity_QCheckBox").enabled, True)
    test.compare(waitForObjectExists(":groupBox_7.chkPolydispersity_QCheckBox").checked, False)
    test.compare(waitForObjectExists(":groupBox_7.chk2DView_QCheckBox").enabled, True)
    test.compare(waitForObjectExists(":groupBox_7.chk2DView_QCheckBox").checked, False)
    test.compare(waitForObjectExists(":groupBox_7.chkMagnetism_QCheckBox").enabled, False)
    test.compare(waitForObjectExists(":groupBox_7.chkMagnetism_QCheckBox").checked, False)

    test.compare(str(waitForObjectExists(":groupBox_9.lblChi2Value_QLabel").text), "---")
    test.compare(waitForObjectExists(":groupBox_9.lblChi2Value_QLabel").visible, True)
    test.compare(waitForObjectExists(":FittingWidgetUI.cmdPlot_QPushButton_2").enabled, True)
    test.compare(str(waitForObjectExists(":FittingWidgetUI.cmdPlot_QPushButton_2").text), "Calculate")
    test.compare(waitForObjectExists(":FittingWidgetUI.cmdFit_QPushButton").enabled, False)
    test.compare(str(waitForObjectExists(":FittingWidgetUI.cmdFit_QPushButton").text), "Fit")
    test.compare(str(waitForObjectExists(":FittingWidgetUI.cmdHelp_QPushButton").text), "Help")
    test.compare(waitForObjectExists(":FittingWidgetUI.cmdHelp_QPushButton").enabled, True)
    test.compare(waitForObjectExists(":FittingWidgetUI.label_QLabel_2").visible, True)
    test.compare(str(waitForObjectExists(":FittingWidgetUI.label_QLabel_2").text), "No data loaded")
    test.compare(waitForObjectExists(":FittingWidgetUI.label_QLabel_2").enabled, True)


    waitForObjectItem(":groupBox_6.lstParams_QTreeView_4", "radius")
    clickItem(":groupBox_6.lstParams_QTreeView_4", "radius", -10, 8, 0, Qt.LeftButton)
    waitForObjectItem(":groupBox_6.lstParams_QTreeView_4", "radius.Polydispersity")
    clickItem(":groupBox_6.lstParams_QTreeView_4", "radius.Polydispersity", -7, 11, 0, Qt.LeftButton)
    
    test.compare(waitForObjectExists(":Polydispersity.0_QModelIndex").text, "0")
    test.compare(waitForObjectExists(":Polydispersity.0_QModelIndex").enabled, True)
    test.compare(waitForObjectExists(":Polydispersity.gaussian_QModelIndex_2").text, "gaussian")
    test.compare(str(waitForObjectExists(":groupBox_8.lblMinRangeDef_QLabel").text), "0.005")
    test.compare(waitForObjectExists(":groupBox_8.lblMinRangeDef_QLabel").visible, True)
    test.compare(waitForObjectExists(":groupBox_8.lblMaxRangeDef_QLabel").visible, True)
    test.compare(str(waitForObjectExists(":groupBox_8.lblMaxRangeDef_QLabel").text), "0.1")
    test.compare(str(waitForObjectExists(":groupBox_8.lblCurrentSmearing_QLabel").text), "None")
    test.compare(waitForObjectExists(":groupBox_8.lblCurrentSmearing_QLabel").visible, True)
