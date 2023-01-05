# -*- coding: utf-8 -*-
@Given("SasView running")
def step(context):
    startApplication("sasview")
    test.compare(waitForObjectExists(":_QSplashScreen").visible, False)

@Given("empty File Explorer")
def step(context):
    test.compare(str(waitForObjectExists(":groupBox.treeView_QTreeView").objectName), "treeView")
    test.compare(waitForObjectExists(":groupBox.treeView_QTreeView").visible, True)

@When("I click on Load Data")
def step(context):
    sendEvent("QMouseEvent", waitForObject(":groupBox.cmdLoad_QPushButton"), QEvent.MouseButtonPress, 68, 20, Qt.LeftButton, 1, 0)
    sendEvent("QMouseEvent", waitForObject(":groupBox.cmdLoad_QPushButton"), QEvent.MouseButtonRelease, 68, 20, Qt.LeftButton, 0, 0)

@When("choose a 1D file")
def step(context):
    waitForObjectItem(":stackedWidget.listView_QListView", "test")
    doubleClickItem(":stackedWidget.listView_QListView", "test", 12, 8, 0, Qt.LeftButton)
    waitForObjectItem(":stackedWidget.listView_QListView", "1d\\_data")
    doubleClickItem(":stackedWidget.listView_QListView", "1d\\_data", 35, 14, 0, Qt.LeftButton)
    waitForObjectItem(":stackedWidget.listView_QListView", "cyl\\_400\\_40\\.txt")
    clickItem(":stackedWidget.listView_QListView", "cyl\\_400\\_40\\.txt", 64, 7, 0, Qt.LeftButton)
    clickButton(waitForObject(":buttonBox.Open_QPushButton"))

@Then("a new index will show up in File Explorer")
def step(context):
    test.compare(waitForObjectExists(":treeView.cyl_400_40.txt_QModelIndex").row, 0)
    test.compare(waitForObjectExists(":treeView.cyl_400_40.txt_QModelIndex").viewType, "QTreeView")

@Then("It will be checked")
def step(context):
    test.compare(waitForObjectExists(":treeView.cyl_400_40.txt_QModelIndex").checkState, "checked")


@Given("a 1D file loaded")
def step(context):
    clickButton(waitForObject(":groupBox.cmdLoad_QPushButton"))
    waitForObjectItem(":stackedWidget.listView_QListView", "test")
    doubleClickItem(":stackedWidget.listView_QListView", "test", 49, 9, 0, Qt.LeftButton)
    waitForObjectItem(":stackedWidget.listView_QListView", "1d\\_data")
    doubleClickItem(":stackedWidget.listView_QListView", "1d\\_data", 52, 11, 0, Qt.LeftButton)
    waitForObjectItem(":stackedWidget.listView_QListView", "cyl\\_400\\_20\\.txt")
    doubleClickItem(":stackedWidget.listView_QListView", "cyl\\_400\\_20\\.txt", 64, 5, 0, Qt.LeftButton)
    test.compare(waitForObjectExists(":treeView.cyl_400_20.txt_QModelIndex").row, 0)
    test.compare(waitForObjectExists(":treeView.cyl_400_20.txt_QModelIndex").checkState, "checked")

@When("I select Uncheck All")
def step(context):
    mouseClick(waitForObject(":groupBox.cbSelect_QComboBox"), 76, 7, 0, Qt.LeftButton)
    mouseClick(waitForObjectItem(":groupBox.cbSelect_QComboBox", "Unselect all"), 62, 4, 0, Qt.LeftButton)

@Then("the 1D file index will be unchecked")
def step(context):
    test.compare(waitForObjectExists(":treeView.cyl_400_20.txt_QModelIndex").checkState, "unchecked")
