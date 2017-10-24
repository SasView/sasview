function main() {
    startApplication("sasview");
    activateItem(waitForObjectItem(":MainWindow.menubar_QMenuBar", "Tool"));
    activateItem(waitForObjectItem(":MainWindow.menuTool_QMenu", "Density/Volume Calculator"));
    test.compare(waitForObjectExists(":DensityPanel.editMolecularFormula_QLineEdit").visible, true);
    test.compare(waitForObjectExists(":DensityPanel.editMolecularFormula_QLineEdit").text, "H2O");
    test.compare(waitForObjectExists(":DensityPanel.editMolecularFormula_QLineEdit").displayText, "H2O");
    test.compare(waitForObjectExists(":DensityPanel.editMolarMass_QLineEdit").text, "18.0153");
    test.compare(waitForObjectExists(":DensityPanel.editMolarMass_QLineEdit").enabled, true);
    test.compare(waitForObjectExists(":DensityPanel.editMolarVolume_QLineEdit").visible, true);
    test.compare(waitForObjectExists(":DensityPanel.editMolarVolume_QLineEdit").text, "");
    test.compare(waitForObjectExists(":DensityPanel.editMassDensity_QLineEdit").text, "");
    test.compare(waitForObjectExists(":DensityPanel.editMassDensity_QLineEdit").visible, true);
    type(waitForObject(":DensityPanel.editMolecularFormula_QLineEdit"), "2");
    type(waitForObject(":DensityPanel.editMolecularFormula_QLineEdit"), "<Tab>");
    type(waitForObject(":DensityPanel.editMolarMass_QLineEdit"), "<Tab>");
    type(waitForObject(":DensityPanel.editMolarVolume_QLineEdit"), "35");
    type(waitForObject(":DensityPanel.editMolarVolume_QLineEdit"), "<Tab>");
    test.compare(waitForObjectExists(":DensityPanel.editMolarMass_QLineEdit").text, "34.0147");
    test.compare(waitForObjectExists(":DensityPanel.editMassDensity_QLineEdit").text, "0.971848571429");
    clickButton(waitForObject(":DensityPanel.Reset_QPushButton"));
    test.compare(waitForObjectExists(":DensityPanel.editMolecularFormula_QLineEdit").text, "H2O");
    test.compare(waitForObjectExists(":DensityPanel.editMolarMass_QLineEdit").text, "18.0153");
    test.compare(waitForObjectExists(":DensityPanel.editMolarVolume_QLineEdit").text, "");
    test.compare(waitForObjectExists(":DensityPanel.editMassDensity_QLineEdit").text, "");
    clickButton(waitForObject(":DensityPanel.Close_QPushButton"));
}
