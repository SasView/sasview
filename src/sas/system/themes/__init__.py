"""The base themes shipped with SasView."""
import os
import logging
from typing import Dict
from pathlib import Path

from sas.system import user

logger = logging.getLogger()

# The base dictionary mapping theme names to their location on disk.
OPTIONS = {
    'Light': Path(os.path.join(os.path.dirname(__file__), 'default.css')),
    'Dark': Path(os.path.join(os.path.dirname(__file__), 'dark.css')),
    'Classic': Path(os.path.join(os.path.dirname(__file__), 'classic.css')),
}
USES_STYLE_BASE = ['Light', 'Dark']

# A template string for setting the font size
FONT = "* {{font-size: {}pt; font-family: Helvetica, Arial, Verdana, sans-serif}}\n"


def load_theme(theme: str = None) -> str:
    """Using a theme name, load the associated CSS file. User themes will be based off the Classic theme.
    :param theme: The key value in OPTIONS
    :return: The CSS string loaded from file
    """
    themes = find_available_themes()
    if not theme or theme not in find_available_themes():
        logger.warning(f"Invalid theme name provided: {theme}")
        theme = 'Light'
    css = "" if theme not in USES_STYLE_BASE else STYLE_BASE
    # User themes should use the classic theme as a basis and build on it from there
    if theme.startswith('User:'):
        with open(themes.get('Classic').absolute()) as fd:
            css += fd.read()
    with open(themes.get(theme).absolute()) as fd:
        css += fd.read()
    return css


def find_available_themes() -> Dict:
    """Find all available themes and return the list of options.

    The default themes should be shipped in the same directory as this file.
    User created themes should be kept in ~/.sasview/themes.
    """
    themes = OPTIONS.copy()
    user_path = os.path.join(user.get_user_dir(), 'themes')
    if not os.path.exists(user_path):
        os.mkdir(user_path)
    for file in os.listdir(user_path):
        name = f'User:{file}'
        themes[name] = Path(os.path.join(user_path, file))
    return themes


def format_font_size(font_size: float) -> str:
    """Formats the FONT string to include a specific size.

    :param font_size: The font size, in pt units, to use.
    :return: FONT.format(font_size)"""
    return FONT.format(font_size)


STYLE_BASE = """
/* QWidget Properties */
QWidget:focus {outline: none;}

/* QMainWindow Properties */
QMainWindow::separator {width: 4px; height: 4px;}

/* QCheckBox and QRadioButton Properties */
QCheckBox, QRadioButton {border-top: 2px solid transparent; border-bottom: 2px solid transparent;}
QCheckBox::indicator:enabled, QRadioButton::indicator:enabled {height: 14px; width: 14px;}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {height: 14px; width: 14px;}

/* QGroupBox Properties */
QGroupBox {font-weight: bold; margin-top: 8px; padding: 2px 1px 1px 1px; border-radius: 4px;}
QGroupBox::title {subcontrol-origin: margin; subcontrol-position: top left; left: 7px; margin: 0 2px 0 3px;}
QGroupBox:flat {border-color: transparent;}

/* QToolTip Properties */
QToolTip {font-size: 80%;}

/* QMenuBar Properties */
QMenuBar {padding: 2px;}
QMenuBar::item {background: transparent; padding: 4px;}
QMenuBar::item:selected {padding: 4px; border-radius: 4px;}
QMenuBar::item:pressed {padding: 4px; margin-bottom: 0; padding-bottom: 0;}

/* QToolBar */
/* QToolBar must override `border-style` to set the style. */
QToolBar { padding: 1px; font-weight: bold; spacing: 2px; margin: 1px; border-style: none;}
QToolBar::separator:horizontal {width: 2px; margin: 0 6px;}
QToolBar::separator:vertical {height: 2px; margin: 6px 0;}
QToolBar > QToolButton {background: transparent; padding: 3px; border-radius: 4px;}
QToolBar > QToolButton::menu-button {border-top-right-radius: 4px; border-bottom-right-radius: 4px;}
QToolBar > QWidget {background: transparent;}

/* Qmenu Properties */
QMenu {padding: 8px 0; border-radius: 4px;}
QMenu::separator {margin: 4px 0; height: 1px;}
QMenu::item {background: transparent; padding: 4px 19px;}
QMenu::icon {padding-left: 10px; width: 14px; height: 14px;}

/* QScrollBar */
QScrollBar {border-radius: 4px;}
QScrollBar:horizontal {height: 14px;}
QScrollBar::handle {border-radius: 3px;}
QScrollBar::handle:horizontal {min-width: 8px; margin: 4px 14px;}
QScrollBar::handle:horizontal:hover {margin: 2px 14px;}
QScrollBar::handle:vertical {min-height: 8px; margin: 14px 4px;}
QScrollBar::handle:vertical:hover {margin: 14px 2px;}
/*
Hide QScrollBar background.
The `sub-page` and `add-page` are not colored by default on most OS, but are colored on Windows.
*/
QScrollBar::sub-page, QScrollBar::add-page {background: transparent;}
QScrollBar::sub-line, QScrollBar::add-line {background: transparent;}
QPushButton, QToolButton {padding: 4px 8px; border-radius: 4px;}

/* QDialogButtonBox */
QDialogButtonBox {dialogbuttonbox-buttons-have-icons: 0;}
QDialogButtonBox QPushButton {min-width: 65px;}

/* QComboBox */
QComboBox {min-height: 1.5em; padding: 0 8px 0 4px; border-radius: 4px;}
QComboBox::drop-down {margin: 2px 2px 2px -6px; border-radius: 4px;  /* This remove default style. */}
/* Setting background color of selected item when editable is false. */
QComboBox::item:selected {border: none;  /* This remove the border of indicator. */ border-radius: 4px;}

/* QAbstractItemView in QComboBox is NoFrame. Override default settings and show border. */
QComboBox QListView {margin: 0; padding: 4px; border-radius: 4px;}
QComboBox QListView::item {border-radius: 4px;}

/* QListView QTreeView */
QListView {padding: 1px}
QTreeView::branch:open:has-children:!has-siblings, QTreeView::branch:open:has-children:has-siblings  {border-image: unset;}

/*
Following arrow settings are for QColumnView.
QColumnView::left-arrow and QColumnView::right-arrow are not working.
*/
QListView::left-arrow {margin: -2px;}
QListView::right-arrow {margin: -2px;}

/* QTabWidget QTabBar */
QTabWidget::pane {border-radius: 4px;}
QTabBar {qproperty-drawBase: 0;}
QTabBar::close-button:hover {border-radius: 4px;}
QTabBar::tab {padding: 3px; border-style: solid;}
QTabBar::tab:top {
    border-bottom-width: 2px;
    margin: 3px 6px 0 0;
    border-top-left-radius: 2px;
    border-top-right-radius: 2px;
}
QTabBar::tab:bottom {border-top-width: 2px; margin: 0 6px 3px 0; border-bottom-left-radius: 2px; border-bottom-right-radius: 2px;}
QTabBar::tab:left {border-right-width: 2px; margin: 0 0 6px 3px; border-top-left-radius: 2px; border-bottom-left-radius: 2px;}
QTabBar::tab:right {border-left-width: 2px; margin-bottom: 6px; margin: 0 3px 6px 0; border-top-right-radius: 2px; border-bottom-right-radius: 2px;}
QTabBar::tab:top:first, QTabBar::tab:top:only-one, QTabBar::tab:bottom:first, QTabBar::tab:bottom:only-one {margin-left: 2px;}
QTabBar::tab:top:last, QTabBar::tab:top:only-one, QTabBar::tab:bottom:last, QTabBar::tab:bottom:only-one {margin-right: 2px;}
QTabBar::tab:left:first, QTabBar::tab:left:only-one, QTabBar::tab:right:first, QTabBar::tab:right:only-one {margin-top: 2px;}
QTabBar::tab:left:last, QTabBar::tab:left:only-one, QTabBar::tab:right:last, QTabBar::tab:right:only-one {margin-bottom: 2px;}

/* QColumnView */
QColumnViewGrip {margin: -4px;}

/* QTableView */
QTableView QTableCornerButton::section {margin: 0 1px 1px 0; border-top-left-radius: 2px;}
QTableView > QHeaderView {border-radius: 3px;}

/* QLineEdit */
/* Adjust the min-height of QLineEdit to the height of the characters. */
QLineEdit {padding: 3px 4px; min-height: 1em; border-radius: 4px;}

/* QFileDialog */
QFileDialog QFrame {border: none;}

/* Check */
QComboBox::indicator,
QMenu::indicator {width: 18px; height: 18px;}
QMenu::indicator {margin-left: 3px; border-radius: 4px;}

/* Check indicator */
QCheckBox, QRadioButton {spacing: 8px;}
QGroupBox::title, QAbstractItemView::item {spacing: 6px;}
QCheckBox::indicator, QGroupBox::indicator, QAbstractItemView::indicator, QRadioButton::indicator {height: 18px; width: 18px;}
QCheckBox::indicator:checked, QGroupBox::indicator:checked, QAbstractItemView::indicator:checked, QRadioButton::indicator:checked {height: 14px; width: 14px;}

QProgressBar {border: 2px solid grey; border-radius: 5px; text-align: center}
QProgressBar::chunk {background-color: #b1daf9; width: 10px; margin: 1px;}
QTextBrowser[warning=true] {border: 5px solid red; background-color: lightyellow}
QCodeEditor {font-family: 'monospace, monospace'}
QCodeEditor[warning=true] {border: 5px solid red; background-color: lightyellow}
QLabel[bold=true] {font-weight: bold;}
QTreeView::item[base=true] {color: rgb(77,81,87); font-style: normal; font-weight: normal;}
QTreeView::item[disabled=true] {font-style: italic;}
QTreeView::item[constrained=true] {font-style: italic; color: blue;}
QHeaderView {font-weight: bold}"""