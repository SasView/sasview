import functools
import os
from importlib import resources

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

import sas.system.version
from sas.qtgui.Utilities import GuiUtils
from sas.system import legal, web


class About(QDialog):

    name_image_link = [
        ("University of Tennessee, Knoxville", "ut.svg", web.inst_url),
        ("University of Maryland", "umd.svg", web.umd_url),
        ("National Institute of Standards and Technology", "nist.svg", web.nist_url),
        ("Spallation Neutron Source", "ornl.png", web.sns_url),
        ("ISIS Neutron and Muon Source", "isis.svg", web.isis_url),
        ("European Spallation Source", "ess.svg", web.ess_url),
        ("Institute Laue-Langevin", "ill.png", web.ill_url),
        ("Australian Nuclear Science and Technology Organisation", "ansto.svg", web.ansto_url),
        ("Bundesanstalt für Materialforschung", "bam.png", web.bam_url),
        ("Technische Universiteit Delft", "delft.png", web.delft_url),
        ("Diamond Light Source", "diamond.png", web.diamond_url),
        ("SciLifeLab", "scilifelab.png", web.scilifelab_url)
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("About SasView")

        icon = QIcon()
        icon.addFile(":/res/ball.ico", QSize(), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        self.mainLayout = QVBoxLayout()

        # Top row of labels, title and version
        self.topRow = QWidget()
        self.topRowLayout = QHBoxLayout()
        self.topRow.setLayout(self.topRowLayout)

        self.sasviewTitle = QLabel("SasView")
        self.sasviewTitle.setStyleSheet("font-size: 28pt")

        version = sas.system.version.__version__
        self.versionLabel = QLabel(str(version))

        self.topRowLayout.addWidget(self.sasviewTitle)
        self.topRowLayout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.topRowLayout.addWidget(self.versionLabel)

        self.mainLabel = QLabel()
        self.mainLabel.setOpenExternalLinks(True)

        # A line...
        self.line = QFrame(self)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.line.sizePolicy().hasHeightForWidth())
        self.line.setSizePolicy(sizePolicy)
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        # Bottom text
        self.subLabel = QLabel()
        self.subLabel.setWordWrap(True)
        self.setText()


        # logos
        self.buttons = QWidget()
        self.button_layout = QGridLayout()
        for index, (name, logo, url) in enumerate(self.name_image_link):

            button = QPushButton()

            with resources.open_binary("sas.qtgui.Utilities.About.images", logo) as file:
                image_data = file.read()

                pixmap = QPixmap()
                pixmap.loadFromData(image_data)

                button.setIcon(QIcon(pixmap))

            button.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: black;
                }

                QPushButton:hover {
                    border: none;
                }
                """)

            button.setToolTip(name)
            button.clicked.connect(functools.partial(GuiUtils.openLink, url))

            button.setIconSize(QSize(80, 80))

            i, j = divmod(index, 4)
            self.button_layout.addWidget(button, i, j)

        self.buttons.setLayout(self.button_layout)


        # Put all widgets in
        self.mainLayout.addWidget(self.topRow)
        self.mainLayout.addWidget(self.mainLabel)
        self.mainLayout.addWidget(self.line)
        self.mainLayout.addWidget(self.subLabel)
        self.mainLayout.addWidget(self.buttons)

        self.setLayout(self.mainLayout)

        self.setModal(True)


    def setText(self):
        """
        Modify the labels so the text corresponds to the current version
        """

        dir_path = os.path.split(sas.__file__)[0]
        installation_path = os.path.split(dir_path)[0]

        about_text = f"""
        <html>
            <head/>
            <body>
                <p align="center">
                    {legal.copyright}
                </p>
                <p align="center">
                    <a href="{web.homepage_url}">{web.homepage_url}</a>
                </p>

                <p align="center">A list of individual contributors can be found at:
                <a href="{web.homepage_url}/people">{web.homepage_url}/people</a></p>
                <p align="center">
                    Comments? Bugs? Requests?
                    <a href="mailto:{web.help_email}">Send us a ticket</a>
                </p>
                <p align="center">
                    <a href="{web.download_url}">Get the latest version</a>
                </p>
                <p>
                    Installation path: <i>{installation_path}</i>
                </p>
            </body>
        </html>
        """

        more_text = """
        <html>
            <head/>
            <body>
                <p>
                    This work originally developed as part of the DANSE project funded by the NSF under
                     grant DMR-0520547, and currently maintained by UTK, NIST, UMD, ORNL, ISIS, ESS, ILL,
                     ANSTO, TU Delft, DLS, SciLifeLab, and the scattering community.
                </p>
                <p>
                    SasView also contains code developed with funding from the EU Horizon 2020 programme under
                     the SINE2020 project (Grant No 654000).
                </p>
            </body>
        </html>"""

        self.mainLabel.setText(about_text)
        self.subLabel.setText(more_text)




if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication


    app = QApplication([])

    about = About()
    about.show()

    sys.exit(app.exec())
