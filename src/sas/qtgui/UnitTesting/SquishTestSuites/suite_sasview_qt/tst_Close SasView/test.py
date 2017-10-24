# -*- coding: utf-8 -*-

def main():
    startApplication("sasview")
    sendEvent("QCloseEvent", waitForObject(":MainWindow_MainSasViewWindow"))
    test.compare(waitForObjectExists(":Information_QMessageBox").enabled, True)
    test.compare(str(waitForObjectExists(":Information_QMessageBox").text), "Are you sure you want to exit the application?")
    test.compare(waitForObjectExists(":Information_QMessageBox").visible, True)
    test.compare(waitForObjectExists(":Information.Yes_QPushButton").default, True)
    test.compare(waitForObjectExists(":Information.Yes_QPushButton").enabled, True)
    test.compare(waitForObjectExists(":Information.No_QPushButton").default, False)
    test.compare(waitForObjectExists(":Information.No_QPushButton").enabled, True)
    clickButton(waitForObject(":Information.No_QPushButton"))
    test.compare(waitForObjectExists(":MainWindow_MainSasViewWindow").visible, True)
