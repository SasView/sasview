import sys
from os.path import abspath

from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication
from FittingWidget import Backend

app = QApplication(sys.argv)

# Create the QWebEngineView
view = QWebEngineView()

# Create the QWebChannel
channel = QWebChannel()

# Create the Python object
backend = Backend()

# Expose the Python object to JavaScript
channel.registerObject("backend", backend)

# Associate the QWebChannel with the QWebEngineView
view.page().setWebChannel(channel)

# Load the HTML file
htmlFile = r"test.html"
view.load(htmlFile)

# Show the QWebEngineView
view.show()

# Run the application event loop
sys.exit(app.exec_())