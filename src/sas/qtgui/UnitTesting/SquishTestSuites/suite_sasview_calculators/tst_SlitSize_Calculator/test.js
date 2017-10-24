function main() {
    startApplication("sasview");
    activateItem(waitForObjectItem(":MainWindow.menubar_QMenuBar", "Tool"));
    activateItem(waitForObjectItem(":MainWindow.menuTool_QMenu", "Slit Size Calculator"));
    test.compare(waitForObjectExists(":groupBox.data_file_QLineEdit").text, "");
    test.compare(waitForObjectExists(":groupBox_2.slit_length_out_QLineEdit").text, "");
    clickButton(waitForObject(":SlitSizeCalculator.browseButton_QPushButton"));
    waitForObjectItem(":stackedWidget.listView_QListView", "test");
    doubleClickItem(":stackedWidget.listView_QListView", "test", 28, 5, 0, Qt.LeftButton);
    waitForObjectItem(":stackedWidget.listView_QListView", "1d\\_data");
    doubleClickItem(":stackedWidget.listView_QListView", "1d\\_data", 24, 7, 0, Qt.LeftButton);
    waitForObjectItem(":stackedWidget.listView_QListView", "cyl\\_400\\_20\\.txt");
    doubleClickItem(":stackedWidget.listView_QListView", "cyl\\_400\\_20\\.txt", 62, 13, 0, Qt.LeftButton);
    test.compare(waitForObjectExists(":groupBox.data_file_QLineEdit").text, "cyl_400_20.txt");
    test.compare(waitForObjectExists(":groupBox_2.slit_length_out_QLineEdit").text, "0.10238");
    clickButton(waitForObject(":SlitSizeCalculator.browseButton_QPushButton"));
    clickButton(waitForObject(":QFileDialog.toParentButton_QToolButton"));
    waitForObjectItem(":stackedWidget.listView_QListView", "2d\\_data");
    doubleClickItem(":stackedWidget.listView_QListView", "2d\\_data", 31, 5, 0, Qt.LeftButton);
    waitForObjectItem(":stackedWidget.listView_QListView", "P123\\_D2O\\_40\\_percent\\.dat");
    doubleClickItem(":stackedWidget.listView_QListView", "P123\\_D2O\\_40\\_percent\\.dat", 75, 14, 0, Qt.LeftButton);
    sendEvent("QWheelEvent", waitForObject(":MainWindow.Welcome to SasView_QLabel"), 756, 5, -120, 0, 2);
    sendEvent("QWheelEvent", waitForObject(":MainWindow.Welcome to SasView_QLabel"), 756, 5, -120, 0, 2);
    test.compare(waitForObjectExists(":groupBox.data_file_QLineEdit").text, "P123_D2O_40_percent.dat");
    test.compare(waitForObjectExists(":groupBox_2.slit_length_out_QLineEdit").text, "ERROR!");
    test.compare(waitForObjectExists(":SlitSizeCalculator.browseButton_QPushButton").toolTip, "<html><head/><body><p>Compute the thickness or diameter.</p></body></html>");
    clickButton(waitForObject(":SlitSizeCalculator.closeButton_QPushButton"));
}
