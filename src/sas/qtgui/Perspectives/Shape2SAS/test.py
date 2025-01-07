from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QPixmap, QPdfWriter, QPainter, QPageSize
from PySide6.QtCore import QRect

class DesignWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tab Widget Example")
        self.setGeometry(100, 100, 800, 600)

        self.tabWidget = QTabWidget()
        self.setCentralWidget(self.tabWidget)

        # Add tabs
        for i in range(3):
            tab = QWidget()
            layout = QVBoxLayout()
            label = QLabel(f"Content of Tab {i+1}")
            layout.addWidget(label)
            tab.setLayout(layout)
            self.tabWidget.addTab(tab, f"Tab {i+1}")

        # Add a button to export tabs to PDF
        self.export_button = QPushButton("Export Tabs to PDF", self)
        self.export_button.clicked.connect(self.export_tabs_to_pdf)
        self.layout().addWidget(self.export_button)

    def capture_tabs(self):
        for i in range(self.tabWidget.count()):
            self.tabWidget.setCurrentIndex(i)
            tab = self.tabWidget.widget(i)
            pixmap = QPixmap(tab.size())
            tab.render(pixmap)
            pixmap.save(f"tab_{i+1}.png")
            print(f"Saved tab {i+1} as tab_{i+1}.png")

    def save_images_to_pdf(self, image_paths, pdf_path):
        pdf_writer = QPdfWriter(pdf_path)
        pdf_writer.setPageSize(QPageSize(QPageSize.A4))
        painter = QPainter(pdf_writer)

        for image_path in image_paths:
            pixmap = QPixmap(image_path)
            rect = QRect(0, 0, pdf_writer.width(), pdf_writer.height())
            painter.drawPixmap(rect, pixmap)
            pdf_writer.newPage()
            print(f"Added {image_path} to PDF")

        painter.end()
        print(f"PDF saved as {pdf_path}")

    def export_tabs_to_pdf(self):
        self.capture_tabs()
        image_paths = [f"tab_{i+1}.png" for i in range(self.tabWidget.count())]
        pdf_path = "tabs_report.pdf"
        self.save_images_to_pdf(image_paths, pdf_path)

if __name__ == "__main__":
    app = QApplication([])
    widget = DesignWindow()
    widget.show()
    app.exec()